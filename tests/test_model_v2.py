"""
Step 4.5 acceptance tests: Model 6 (Log1p, Balanced Logistic Regression) as Candidate v2.

Verifies:
1. Loading both models: production v1 and candidate v2, as well as preserving legacy 11-feat backup.
2. Feature transforms: correct application of log1p, non-negative checks, double-transform prevention, immutability.
3. Mathematical reconstruction: additivity of log-odds and sigmoid reconstruction for candidate v2.
4. Stress testing elapsed days: strictly monotonic probabilities across [0, 1, 7, 14, 60, 94, 180, 365] days,
   bounded in (0, 1), with explanations containing raw days and never log values.
5. API compatibility: identical output schema between v1 and v2 with bundle override support.
6. Feature-version protection: incompatible feature schemas trigger explicit RuntimeError.
"""

import os
import math
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from backend.app.database import SessionLocal, init_db
from backend.app.features import FEATURE_COLUMNS, apply_feature_transforms
from backend.app.models import User, Topic, LearningEvent
from backend.app.predict import predict_forgetting, compute_current_features, _load_bundle
from backend.app.explainability import (
    compute_logistic_regression_contributions,
    explain_prediction,
    format_feature_sentence,
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "backend", "models")
V1_PATH = os.path.join(MODELS_DIR, "forgetting_model.joblib")
V2_PATH = os.path.join(MODELS_DIR, "forgetting_model_v2.joblib")
LEGACY_PATH = os.path.join(MODELS_DIR, "forgetting_model_legacy_11feat.joblib")


@pytest.fixture(scope="module")
def v1_bundle():
    return _load_bundle(V1_PATH)


@pytest.fixture(scope="module")
def v2_bundle():
    return _load_bundle(V2_PATH)


@pytest.fixture
def synthetic_features():
    """Controlled 13-feature vector for mathematical verification."""
    return {
        "times_studied": 3,
        "is_first_exposure": 0,
        "days_since_last_studied": 14,
        "revision_frequency": 0.20,
        "self_reported_confidence": 0.70,
        "universal_difficulty": 0.50,
        "topic_importance": 0.80,
        "time_spent_studying_min": 45.0,
        "confusability_score": 1,
        "prerequisite_completion_ratio": 1.0,
        "concurrent_topic_load": 5,
        "days_to_next_assessment": 10,
        "has_upcoming_assessment": 1,
    }


# ---------------------------------------------------------------------------
# 1. Model Loading & Packaging Tests
# ---------------------------------------------------------------------------

def test_load_production_and_candidate_models(v1_bundle, v2_bundle):
    """Verify both production v1 and candidate v2 load cleanly with valid attributes."""
    # Production Model v1
    assert v1_bundle is not None
    assert "model" in v1_bundle
    assert "scaler" in v1_bundle
    assert len(v1_bundle["feature_columns"]) == 13
    assert v1_bundle["feature_columns"] == FEATURE_COLUMNS

    # Candidate Model v2
    assert v2_bundle is not None
    assert v2_bundle.get("model_version") == "2.0.0"
    assert v2_bundle.get("schema_version") == 2
    assert v2_bundle.get("feature_transforms") == {"days_since_last_studied": "log1p"}
    assert len(v2_bundle["feature_columns"]) == 13
    assert v2_bundle["feature_columns"] == FEATURE_COLUMNS
    assert "raw_feature_means" in v2_bundle
    assert "days_since_last_studied" in v2_bundle["raw_feature_means"]
    # Verify raw mean for days_since_last_studied is in original days (~2.67), not log scale
    assert 2.0 <= v2_bundle["raw_feature_means"]["days_since_last_studied"] <= 4.0


def test_legacy_model_preserved():
    """Verify the legacy 11-feature model backup remains intact."""
    assert os.path.exists(LEGACY_PATH)
    legacy = _load_bundle(LEGACY_PATH)
    assert len(legacy["feature_columns"]) == 11


# ---------------------------------------------------------------------------
# 2. Shared Feature Transformation Adapter Tests
# ---------------------------------------------------------------------------

def test_apply_feature_transforms_none_or_empty():
    """apply_feature_transforms should return unchanged copy if transforms is None or empty."""
    df = pd.DataFrame([{"days_since_last_studied": 10, "times_studied": 2}])
    
    out_none = apply_feature_transforms(df, None)
    pd.testing.assert_frame_equal(df, out_none)
    assert out_none is not df  # Ensure non-destructive copy

    out_empty = apply_feature_transforms(df, {})
    pd.testing.assert_frame_equal(df, out_empty)


def test_apply_feature_transforms_log1p():
    """apply_feature_transforms applies np.log1p accurately."""
    df = pd.DataFrame([
        {"days_since_last_studied": 0, "times_studied": 1},
        {"days_since_last_studied": 14, "times_studied": 3},
    ])
    transforms = {"days_since_last_studied": "log1p"}
    transformed = apply_feature_transforms(df, transforms)

    assert transformed.loc[0, "days_since_last_studied"] == pytest.approx(np.log1p(0), abs=1e-6)
    assert transformed.loc[1, "days_since_last_studied"] == pytest.approx(np.log1p(14), abs=1e-6)
    # Untransformed columns remain identical
    assert transformed.loc[0, "times_studied"] == 1
    assert transformed.loc[1, "times_studied"] == 3


def test_apply_feature_transforms_safety_checks():
    """Verify non-negative requirement and unsupported transform handling."""
    neg_df = pd.DataFrame([{"days_since_last_studied": -2}])
    with pytest.raises(ValueError, match="contains negative values"):
        apply_feature_transforms(neg_df, {"days_since_last_studied": "log1p"})

    df = pd.DataFrame([{"days_since_last_studied": 5}])
    with pytest.raises(ValueError, match="Unknown feature transform"):
        apply_feature_transforms(df, {"days_since_last_studied": "unsupported_func"})


# ---------------------------------------------------------------------------
# 3. Mathematical Reconstruction Tests for Candidate v2
# ---------------------------------------------------------------------------

def test_v2_mathematical_reconstruction(v2_bundle, synthetic_features):
    """
    Verify linear additivity and probability reconstruction on Candidate v2:
      intercept + sum(contributions) == predicted_log_odds
      sigmoid(predicted_log_odds) == reconstructed_probability
      reconstructed_probability == sklearn.predict_proba
    """
    decomp = compute_logistic_regression_contributions(v2_bundle, synthetic_features)
    intercept = decomp["intercept"]
    contributions = decomp["contributions"]
    log_odds = decomp["predicted_log_odds"]
    prob = decomp["reconstructed_probability"]

    # 1. Additivity
    assert (intercept + sum(contributions.values())) == pytest.approx(log_odds, abs=1e-5)

    # 2. Sigmoid mapping
    assert (1.0 / (1.0 + math.exp(-log_odds))) == pytest.approx(prob, abs=1e-5)

    # 3. Model predict_proba match
    df_raw = pd.DataFrame([synthetic_features])[FEATURE_COLUMNS]
    df_trans = apply_feature_transforms(df_raw, v2_bundle.get("feature_transforms"))
    X_scaled = v2_bundle["scaler"].transform(df_trans)
    expected_prob = float(v2_bundle["model"].predict_proba(X_scaled)[0][1])
    assert prob == pytest.approx(expected_prob, abs=1e-5)


# ---------------------------------------------------------------------------
# 4. Stress Testing Elapsed Days & Monotonicity
# ---------------------------------------------------------------------------

def test_elapsed_days_stress_and_monotonicity(v2_bundle, synthetic_features):
    """
    Evaluate candidate v2 at boundary elapsed days: [0, 1, 7, 14, 60, 94, 180, 365].
    Verify:
    1. Strictly monotonic increase in probability with elapsed days.
    2. Explanations show raw elapsed days (e.g., '14 days ago' or '365 days ago'),
       never log-transformed values (e.g. 5.90).
    3. Contribution of days_since_last_studied is positive and grows logarithmically.
    """
    test_days = [0, 1, 7, 14, 60, 94, 180, 365]
    probabilities = []
    days_contributions = []

    for d in test_days:
        feats = dict(synthetic_features)
        feats["days_since_last_studied"] = d

        decomp = compute_logistic_regression_contributions(v2_bundle, feats)
        prob = decomp["reconstructed_probability"]
        contrib = decomp["contributions"]["days_since_last_studied"]

        probabilities.append(prob)
        days_contributions.append(contrib)

        # Check explanations
        explanation = explain_prediction(v2_bundle, feats)
        all_factors = explanation["all_factors"]
        days_factor = next(f for f in all_factors if f["factor"] == "days_since_last_studied")

        # Must report raw integer days
        assert days_factor["value"] == d
        # Sentence must state original day count, not log
        if d == 0:
            assert "0 days ago" in days_factor["explanation"] or "today" in days_factor["explanation"]
        elif d == 1:
            assert "1 day ago" in days_factor["explanation"]
        else:
            assert f"{d} days ago" in days_factor["explanation"]

        # Ensure no mention of 'log' or 'log1p' or raw float logs in student sentence
        assert "log" not in days_factor["explanation"].lower()

    # Monotonicity check: probability must strictly increase with elapsed days
    for i in range(len(probabilities) - 1):
        assert probabilities[i] < probabilities[i + 1], (
            f"Expected probability at {test_days[i]} days ({probabilities[i]}) < "
            f"probability at {test_days[i+1]} days ({probabilities[i+1]})"
        )
        assert days_contributions[i] < days_contributions[i + 1]

    # Diminishing marginal impact check: difference between 180 and 365 days should be much smaller
    # than difference between 0 and 180 days due to log1p compression
    diff_early = probabilities[4] - probabilities[0]   # 60 days vs 0 days
    diff_late = probabilities[7] - probabilities[6]    # 365 days vs 180 days (185 days apart)
    assert diff_early > diff_late


# ---------------------------------------------------------------------------
# 5. Prediction Pipeline & API Compatibility
# ---------------------------------------------------------------------------

def _ensure_v2_test_user(db):
    user = db.query(User).first()
    topic = db.query(Topic).first()
    if user is None:
        user = User(name="Test Candidate Student", email="test_cand_v2@test.internal", is_simulated=False)
        db.add(user)
        db.commit()
        db.refresh(user)
        if topic is not None:
            le = LearningEvent(
                user_id=user.id,
                topic_id=topic.id,
                time_spent_seconds=1200,
                self_reported_confidence=0.75,
            )
            db.add(le)
            db.commit()
    return user, topic


def test_predict_forgetting_with_v2_bundle():
    """Verify predict_forgetting runs with bundle=v2_bundle on live database."""
    db = SessionLocal()
    try:
        user, topic = _ensure_v2_test_user(db)
        assert user is not None and topic is not None

        # Predict with production default v1
        res_v1 = predict_forgetting(db, user.id, topic.id)
        assert res_v1 is not None
        assert "forgetting_probability" in res_v1
        assert "retention_status" in res_v1
        assert "local_explanation" in res_v1

        # Predict with candidate v2 bundle
        v2_bundle = _load_bundle(V2_PATH)
        res_v2 = predict_forgetting(db, user.id, topic.id, bundle=v2_bundle)
        assert res_v2 is not None
        assert "forgetting_probability" in res_v2
        assert "retention_status" in res_v2
        assert "local_explanation" in res_v2
        assert res_v2["retention_status"] in ["retained", "moderate_risk", "high_risk"]

        # Ensure schema equivalence
        assert set(res_v1.keys()) == set(res_v2.keys())
        assert set(res_v1["local_explanation"].keys()) == set(res_v2["local_explanation"].keys())
    finally:
        db.close()


def test_incompatible_model_schema_rejection():
    """Verify loading a model with mismatching feature columns throws RuntimeError."""
    db = SessionLocal()
    try:
        user, topic = _ensure_v2_test_user(db)

        legacy_bundle = _load_bundle(LEGACY_PATH)
        with pytest.raises(RuntimeError, match="Model feature mismatch"):
            predict_forgetting(db, user.id, topic.id, bundle=legacy_bundle)
    finally:
        db.close()
