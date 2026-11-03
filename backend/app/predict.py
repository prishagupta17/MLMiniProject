import os
import joblib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from .models import LearningEvent, Topic
from .explainability import explain_prediction
from .features import (
    FEATURE_COLUMNS,
    apply_feature_transforms,
    _prereq_completion_ratio,
    _concurrent_topic_load,
    _confusability_score,
    compute_assessment_timing,
)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "models", "forgetting_model.joblib"
)

_bundle = None
MODEL_FEATURE_VERSION = "2.0"


def _load_bundle(model_path: Optional[str] = None):
    global _bundle
    if model_path is not None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No trained model found at {model_path}.")
        return joblib.load(model_path)

    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("No trained model found. Run `python -m app.train` first.")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def compute_current_features(db: Session, user_id: int, topic_id: int, as_of: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    as_of = as_of or datetime.utcnow()
    topic = db.query(Topic).get(topic_id)
    if topic is None:
        return None

    learns = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.user_id == user_id,
            LearningEvent.topic_id == topic_id,
            LearningEvent.timestamp <= as_of,
        )
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

    days_to_next, has_upcoming = compute_assessment_timing(db, topic, as_of)

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
        "days_to_next_assessment": days_to_next,
        "has_upcoming_assessment": has_upcoming,
    }


def predict_forgetting(
    db: Session,
    user_id: int,
    topic_id: int,
    as_of: Optional[datetime] = None,
    bundle: Optional[Dict[str, Any]] = None,
):
    bundle = bundle or _load_bundle()

    # Feature version validation
    model_features = bundle.get("feature_columns", [])
    if model_features != FEATURE_COLUMNS:
        raise RuntimeError(
            f"Model feature mismatch: saved model was trained on {len(model_features)} features, "
            f"but current pipeline requires {len(FEATURE_COLUMNS)} features. Retrain required."
        )

    features = compute_current_features(db, user_id, topic_id, as_of=as_of)
    if features is None:
        return None

    X_raw = pd.DataFrame([features])[FEATURE_COLUMNS]
    transforms = bundle.get("feature_transforms")
    X_trans = apply_feature_transforms(X_raw, transforms)

    if bundle.get("scaler") is not None:
        X_scaled = bundle["scaler"].transform(X_trans)
    else:
        X_scaled = X_trans.values
    prob_forgot = float(bundle["model"].predict_proba(X_scaled)[0][1])

    try:
        explanation = explain_prediction(bundle, features)
        top_factors = explanation["top_factors"]
    except Exception:
        explanation = None
        top_factors = []
        for feat, weight in list(bundle.get("importances", {}).items())[:5]:
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
        "local_explanation": explanation,
        "raw_features": features,
    }
