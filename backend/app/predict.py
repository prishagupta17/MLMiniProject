import os
import joblib
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from .models import LearningEvent, Topic
from .features import _prereq_completion_ratio, _concurrent_topic_load, _confusability_score

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "models", "forgetting_model.joblib"
)

_bundle = None


def _load_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("No trained model found. Run `python -m app.train` first.")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def compute_current_features(db: Session, user_id: int, topic_id: int, as_of: datetime = None):
    as_of = as_of or datetime.utcnow()
    topic = db.query(Topic).get(topic_id)
    if topic is None:
        return None

    learns = (
        db.query(LearningEvent)
        .filter(LearningEvent.user_id == user_id, LearningEvent.topic_id == topic_id,
                 LearningEvent.timestamp <= as_of)
        .order_by(LearningEvent.timestamp)
        .all()
    )
    if not learns:
        return None  # hasn't studied this topic yet

    first_learn_time = learns[0].timestamp
    last_learn_time = learns[-1].timestamp

    times_studied = len(learns)
    is_first_exposure = int(times_studied == 1)
    days_since_last_studied = max((as_of - last_learn_time).days, 0)
    days_since_first_learned = max((as_of - first_learn_time).days, 1)
    revision_frequency = (times_studied - 1) / days_since_first_learned

    confidences = [le.self_reported_confidence for le in learns if le.self_reported_confidence is not None]
    self_reported_confidence = sum(confidences) / len(confidences) if confidences else 0.5

    time_spent_studying_min = sum(le.time_spent_seconds for le in learns) / 60

    return {
        "times_studied": times_studied,
        "is_first_exposure": is_first_exposure,
        "days_since_last_studied": days_since_last_studied,
        "revision_frequency": revision_frequency,
        "self_reported_confidence": self_reported_confidence,
        "universal_difficulty": topic.difficulty,
        "topic_importance": topic.importance,
        "time_spent_studying_min": time_spent_studying_min,
        "confusability_score": _confusability_score(topic),
        "prerequisite_completion_ratio": _prereq_completion_ratio(db, user_id, topic, as_of),
        "concurrent_topic_load": _concurrent_topic_load(db, user_id, topic_id, as_of),
    }


def predict_forgetting(db: Session, user_id: int, topic_id: int):
    bundle = _load_bundle()
    features = compute_current_features(db, user_id, topic_id)
    if features is None:
        return None

    X = pd.DataFrame([features])[bundle["feature_columns"]]
    if bundle["scaler"] is not None:
        X = bundle["scaler"].transform(X)
    prob_forgot = float(bundle["model"].predict_proba(X)[0][1])

    top_factors = []
    for feat, weight in list(bundle["importances"].items())[:5]:
        top_factors.append({
            "factor": feat,
            "value": round(features[feat], 2),
            "model_weight": round(float(weight), 4),
        })

    return {
        "topic_id": topic_id,
        "forgetting_probability": round(prob_forgot, 3),
        "retention_status": (
            "high_risk" if prob_forgot >= 0.6 else
            "moderate_risk" if prob_forgot >= 0.35 else
            "retained"
        ),
        "top_factors": top_factors,
        "raw_features": features,
    }
