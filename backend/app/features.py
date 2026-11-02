"""
One row = one self-check RecallEvent (used ONLY as the training label source,
never as an input feature). All features are computed from data strictly
before that event's timestamp.
"""
import pandas as pd
from sqlalchemy.orm import Session
from .models import RecallEvent, LearningEvent, Topic

FEATURE_COLUMNS = [
    "times_studied",
    "is_first_exposure",
    "days_since_last_studied",
    "revision_frequency",
    "self_reported_confidence",
    "universal_difficulty",
    "topic_importance",
    "time_spent_studying_min",
    "confusability_score",
    "prerequisite_completion_ratio",
    "concurrent_topic_load",
]

CONCURRENT_WINDOW_DAYS = 7


def _prereq_completion_ratio(db, user_id, topic, as_of):
    prereqs = topic.prerequisites
    if not prereqs:
        return 1.0  # no prerequisites -> nothing blocking, treat as fully "ready"
    prereq_ids = [p.id for p in prereqs]
    studied = (
        db.query(LearningEvent.topic_id)
        .filter(LearningEvent.user_id == user_id,
                 LearningEvent.topic_id.in_(prereq_ids),
                 LearningEvent.timestamp <= as_of)
        .distinct()
        .count()
    )
    return studied / len(prereq_ids)


def _concurrent_topic_load(db, user_id, topic_id, as_of, window_days=CONCURRENT_WINDOW_DAYS):
    from datetime import timedelta
    window_start = as_of - timedelta(days=window_days)
    rows = (
        db.query(LearningEvent.topic_id)
        .filter(LearningEvent.user_id == user_id,
                 LearningEvent.timestamp >= window_start,
                 LearningEvent.timestamp <= as_of,
                 LearningEvent.topic_id != topic_id)
        .distinct()
        .all()
    )
    return len(rows)


def _confusability_score(topic: Topic) -> int:
    if not topic.confusable_topic_names:
        return 0
    return len([n for n in topic.confusable_topic_names.split(",") if n.strip()])


def build_feature_table(db: Session) -> pd.DataFrame:
    recall_events = (
        db.query(RecallEvent)
        .order_by(RecallEvent.user_id, RecallEvent.topic_id, RecallEvent.timestamp)
        .all()
    )
    learning_events = db.query(LearningEvent).all()
    topics = {t.id: t for t in db.query(Topic).all()}

    learn_by_pair = {}
    for le in learning_events:
        learn_by_pair.setdefault((le.user_id, le.topic_id), []).append(le)
    for k in learn_by_pair:
        learn_by_pair[k].sort(key=lambda e: e.timestamp)

    rows = []
    for re in recall_events:
        key = (re.user_id, re.topic_id)
        prior_learns = [le for le in learn_by_pair.get(key, []) if le.timestamp <= re.timestamp]
        if not prior_learns:
            continue

        topic = topics[re.topic_id]
        first_learn_time = prior_learns[0].timestamp
        last_learn_time = prior_learns[-1].timestamp

        times_studied = len(prior_learns)
        is_first_exposure = int(times_studied == 1)
        days_since_last_studied = max((re.timestamp - last_learn_time).days, 0)
        days_since_first_learned = max((re.timestamp - first_learn_time).days, 1)
        revision_frequency = (times_studied - 1) / days_since_first_learned

        confidences = [le.self_reported_confidence for le in prior_learns if le.self_reported_confidence is not None]
        self_reported_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        time_spent_studying_min = sum(le.time_spent_seconds for le in prior_learns) / 60

        rows.append({
            "user_id": re.user_id,
            "topic_id": re.topic_id,
            "recall_event_id": re.id,
            "timestamp": re.timestamp,
            "times_studied": times_studied,
            "is_first_exposure": is_first_exposure,
            "days_since_last_studied": days_since_last_studied,
            "revision_frequency": revision_frequency,
            "self_reported_confidence": self_reported_confidence,
            "universal_difficulty": topic.difficulty,
            "topic_importance": topic.importance,
            "time_spent_studying_min": time_spent_studying_min,
            "confusability_score": _confusability_score(topic),
            "prerequisite_completion_ratio": _prereq_completion_ratio(db, re.user_id, topic, re.timestamp),
            "concurrent_topic_load": _concurrent_topic_load(db, re.user_id, re.topic_id, re.timestamp),
            "forgot": int(not re.is_correct),   # TARGET — from self-check, never used as a feature
        })

    return pd.DataFrame(rows)
