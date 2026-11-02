"""
Generates a synthetic but behaviorally-realistic dataset so the ML pipeline
and demo work end to end before real classmate data exists.

Recall probability now depends on: universal difficulty, memory strength
(times studied), days since last studied, prerequisite completion, and
interference from confusable topics / concurrent topic load — matching the
feature set the model is actually trained on, so the synthetic data isn't
trivially disconnected from what we'll compute for real users.
"""
import random
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import User, Course, Module, Topic, LearningEvent, RecallEvent

random.seed(42)

COURSE_STRUCTURE = {
    "Machine Learning": {
        "Supervised Learning": [
            "Linear Regression", "Logistic Regression", "Decision Trees",
            "Random Forests", "Support Vector Machines", "k-Nearest Neighbors",
        ],
        "Unsupervised Learning": [
            "k-Means Clustering", "Hierarchical Clustering", "PCA",
            "DBSCAN", "Anomaly Detection",
        ],
        "Model Evaluation": [
            "Bias-Variance Tradeoff", "Cross-Validation", "Confusion Matrix",
            "ROC-AUC", "Regularization (L1/L2)",
        ],
    }
}

# manually-seeded "confusable" pairs for synthetic realism (mimics what the LLM would flag)
CONFUSABLE_PAIRS = [
    ("Linear Regression", "Logistic Regression"),
    ("k-Means Clustering", "k-Nearest Neighbors"),
    ("Hierarchical Clustering", "DBSCAN"),
    ("Confusion Matrix", "ROC-AUC"),
]


def seed_course_structure(db: Session):
    confusable_map = {}
    for a, b in CONFUSABLE_PAIRS:
        confusable_map.setdefault(a, []).append(b)
        confusable_map.setdefault(b, []).append(a)

    topic_objs = {}
    for course_name, modules in COURSE_STRUCTURE.items():
        course = Course(name=course_name)
        db.add(course)
        db.flush()
        for m_idx, (module_name, topic_names) in enumerate(modules.items()):
            module = Module(course_id=course.id, name=module_name, order_index=m_idx)
            db.add(module)
            db.flush()
            for t_idx, topic_name in enumerate(topic_names):
                llm_diff = round(random.uniform(0.25, 0.85), 2)
                importance = round(random.uniform(0.4, 1.0), 2)
                confusables = confusable_map.get(topic_name, [])
                topic = Topic(
                    module_id=module.id, name=topic_name,
                    llm_difficulty=llm_diff, difficulty=llm_diff,
                    importance=importance,
                    confusable_topic_names=",".join(confusables) if confusables else None,
                    confusable_note=(
                        f"Don't mix up with {', '.join(confusables)}." if confusables else None
                    ),
                )
                db.add(topic)
                db.flush()
                topic_objs[(course_name, module_name, topic_name)] = topic

            # simple linear prerequisite chain within each module for realism
            names = topic_names
            for t_idx in range(1, len(names)):
                prev_topic = topic_objs[(course_name, module_name, names[t_idx - 1])]
                cur_topic = topic_objs[(course_name, module_name, names[t_idx])]
                if random.random() < 0.5:  # not every topic has a hard prerequisite
                    cur_topic.prerequisites.append(prev_topic)
    db.commit()


def recall_probability(days_since_studied, difficulty, times_studied,
                        prereq_ratio, confusability, concurrent_load):
    strength = 1.0 + (times_studied - 1) * 1.3
    decay_rate = (0.15 + difficulty * 0.35) / strength
    base = math.exp(-decay_rate * days_since_studied)

    prereq_penalty = 0.15 * (1 - prereq_ratio)          # missing prereqs hurts recall
    confusion_penalty = 0.04 * confusability             # each confusable neighbor chips away
    load_penalty = 0.015 * concurrent_load               # interference from studying many things at once

    p = base - prereq_penalty - confusion_penalty - load_penalty
    return min(max(p, 0.05), 0.97)


def simulate_users(db: Session, n_users=25, days_span=90):
    topics = db.query(Topic).all()
    start_date = datetime.utcnow() - timedelta(days=days_span)

    for u in range(n_users):
        user = User(name=f"Student {u+1}", email=f"student{u+1}@example.edu")
        db.add(user)
        db.flush()

        diligence = random.uniform(0.3, 1.0)
        studied_topic_ids = set()

        for topic in topics:
            if random.random() > 0.85:
                continue

            learned_day = random.randint(0, days_span - 20)
            first_learn_time = start_date + timedelta(days=learned_day)
            cursor_time = first_learn_time

            n_study_sessions = int(random.uniform(1, 5) * diligence) + 1
            study_times = [cursor_time]
            for _ in range(n_study_sessions - 1):
                gap = max(1, int(random.expovariate(1 / (6 / max(diligence, 0.2)))))
                cursor_time = cursor_time + timedelta(days=gap)
                if cursor_time > datetime.utcnow():
                    break
                study_times.append(cursor_time)

            for i, t in enumerate(study_times):
                db.add(LearningEvent(
                    user_id=user.id, topic_id=topic.id, timestamp=t,
                    time_spent_seconds=random.randint(300, 2400),
                    self_reported_confidence=round(random.uniform(0.2, 0.9), 2),
                ))
            studied_topic_ids.add(topic.id)
            db.flush()

            # a couple of self-checks after study sessions, spaced out over time
            n_checks = random.randint(1, 3)
            last_time = study_times[-1]
            for _ in range(n_checks):
                gap_days = max(1, int(random.expovariate(1 / (5 / max(diligence, 0.2)))))
                check_time = last_time + timedelta(days=gap_days)
                if check_time > datetime.utcnow():
                    break

                times_studied_so_far = len([t for t in study_times if t <= check_time])
                if times_studied_so_far == 0:
                    continue
                days_since = (check_time - study_times[times_studied_so_far - 1]).days

                prereq_ids = [p.id for p in topic.prerequisites]
                prereq_ratio = (
                    len([pid for pid in prereq_ids if pid in studied_topic_ids]) / len(prereq_ids)
                    if prereq_ids else 1.0
                )
                confusability = len(topic.confusable_topic_names.split(",")) if topic.confusable_topic_names else 0
                concurrent_load = min(len(studied_topic_ids) - 1, 8)

                p_correct = recall_probability(
                    days_since, topic.difficulty, times_studied_so_far,
                    prereq_ratio, confusability, concurrent_load,
                )
                db.add(RecallEvent(
                    user_id=user.id, topic_id=topic.id, timestamp=check_time,
                    is_correct=random.random() < p_correct,
                    time_spent_seconds=random.randint(20, 120),
                    is_upcoming_assessment_prep=random.random() < 0.15,
                ))
                last_time = check_time
    db.commit()


def generate_all(db: Session, n_users=25, days_span=90):
    seed_course_structure(db)
    simulate_users(db, n_users=n_users, days_span=days_span)
