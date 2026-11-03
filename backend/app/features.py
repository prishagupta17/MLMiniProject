"""
One row = one self-check RecallEvent (used ONLY as the training label source,
never as an input feature). All features are computed from data strictly
before that event's timestamp (zero label leakage).
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from .models import RecallEvent, LearningEvent, Topic, Course, Module, Assessment

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
    "days_to_next_assessment",
    "has_upcoming_assessment",
]

CONCURRENT_WINDOW_DAYS = 7


def apply_feature_transforms(
    df: pd.DataFrame,
    transforms: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Apply declared mathematical transformations to a copy of the feature DataFrame.
    Guarantees raw feature data remains unmodified and prevents double transformations.
    """
    if not transforms:
        return df.copy()

    df_out = df.copy()
    for col, transform_name in transforms.items():
        if col in df_out.columns:
            if transform_name == "log1p":
                if (df_out[col] < 0).any():
                    raise ValueError(f"Feature '{col}' contains negative values, cannot apply log1p.")
                df_out[col] = np.log1p(df_out[col].astype(float))
            else:
                raise ValueError(f"Unknown feature transform '{transform_name}' for column '{col}'.")
    return df_out


def _prereq_completion_ratio(db: Session, user_id: int, topic: Topic, as_of: datetime) -> float:
    prereqs = topic.prerequisites
    if not prereqs:
        return 1.0  # no prerequisites -> nothing blocking, treat as fully "ready"
    prereq_ids = [p.id for p in prereqs]
    studied = (
        db.query(LearningEvent.topic_id)
        .filter(
            LearningEvent.user_id == user_id,
            LearningEvent.topic_id.in_(prereq_ids),
            LearningEvent.timestamp <= as_of,
        )
        .distinct()
        .count()
    )
    return studied / len(prereq_ids)


def _concurrent_topic_load(
    db: Session, user_id: int, topic_id: int, as_of: datetime, window_days: int = CONCURRENT_WINDOW_DAYS
) -> int:
    window_start = as_of - timedelta(days=window_days)
    rows = (
        db.query(LearningEvent.topic_id)
        .filter(
            LearningEvent.user_id == user_id,
            LearningEvent.timestamp >= window_start,
            LearningEvent.timestamp <= as_of,
            LearningEvent.topic_id != topic_id,
        )
        .distinct()
        .all()
    )
    return len(rows)


def _confusability_score(topic: Topic) -> int:
    if not topic.confusable_topic_names:
        return 0
    return len([n for n in topic.confusable_topic_names.split(",") if n.strip()])


def compute_assessment_timing(db: Session, topic: Topic, as_of: datetime) -> Tuple[int, int]:
    """
    Computes days_to_next_assessment and has_upcoming_assessment for a topic as of a date:
    - Considers only assessments covering this topic that have scheduled dates.
    - If as_of < start_date: days = (start_date - as_of).days.
    - If start_date <= as_of <= end_date (inclusive): days = 0.
    - If as_of > end_date: assessment has passed, not upcoming.
    - days_to_next_assessment is the smallest such value, capped at 60.
    - If no upcoming dated assessment exists: days = 60, has_upcoming_assessment = 0.
    - Otherwise has_upcoming_assessment = 1.
    """
    if topic is None or topic.lecture_num is None:
        return 60, 0

    course = None
    if topic.module and topic.module.course:
        course = topic.module.course
    elif topic.module_id:
        mod = db.query(Module).get(topic.module_id)
        if mod and mod.course:
            course = mod.course

    if not course:
        return 60, 0

    as_of_date = as_of.date() if isinstance(as_of, datetime) else as_of
    upcoming_diffs = []

    for a in course.assessments:
        if not a.start_date or not a.end_date:
            continue
        covered = a.covered_lectures_list
        if topic.lecture_num not in covered:
            continue

        start_d = a.start_date.date()
        end_d = a.end_date.date()

        if as_of_date < start_d:
            upcoming_diffs.append((start_d - as_of_date).days)
        elif start_d <= as_of_date <= end_d:
            upcoming_diffs.append(0)

    if not upcoming_diffs:
        return 60, 0

    min_days = min(upcoming_diffs)
    capped_days = min(min_days, 60)
    return capped_days, 1


def compute_topic_importances_for_course(db: Session, course_id: int):
    from .seed_loader import compute_topic_importances_for_course as _loader_compute
    _loader_compute(db, course_id)


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
        # Strict zero-leakage: prior learns must strictly be <= recall event timestamp
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

        days_to_next, has_upcoming = compute_assessment_timing(db, topic, re.timestamp)

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
            "days_to_next_assessment": days_to_next,
            "has_upcoming_assessment": has_upcoming,
            "forgot": int(not re.is_correct),   # TARGET — from self-check, never used as an input feature
        })

    return pd.DataFrame(rows)
