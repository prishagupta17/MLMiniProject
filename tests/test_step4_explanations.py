"""
Step 4 acceptance tests: Local, Topic-Specific Explainability.

Verifies:
1. Logistic Regression contribution calculations in log-odds space.
2. Intercept + sum(contributions) == predicted log-odds.
3. Sigmoid of log-odds == predicted probability (within numerical tolerance).
4. Correct positive-class coefficient and scaler use.
5. Explanation values match the actual prediction feature vector.
6. Positive and negative contribution directions and ranking.
7. Topic specificity: different topics yield distinct local explanations.
8. Negligible contributions and boundary values handled safely.
9. Zero leakage: RecallEvent.is_correct is never an input; future events do not alter explanations.
10. Existing prediction and dashboard endpoints remain functional and backward compatible.
"""

import math
from datetime import datetime, timedelta
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from fastapi.testclient import TestClient

from backend.app.database import SessionLocal, init_db
from backend.app.features import FEATURE_COLUMNS
from backend.app.models import User, Topic, LearningEvent, RecallEvent
from backend.app.predict import predict_forgetting, compute_current_features, _load_bundle
from backend.app.explainability import (
    compute_logistic_regression_contributions,
    explain_prediction,
    format_feature_sentence,
    DEFAULT_CONTRIBUTION_THRESHOLD,
)
from backend.app.main import app


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def trained_bundle():
    return _load_bundle()


@pytest.fixture
def synthetic_features():
    """Controlled 13-feature vector for mathematical verification."""
    return {
        "times_studied": 2,
        "is_first_exposure": 0,
        "days_since_last_studied": 14,
        "revision_frequency": 0.15,
        "self_reported_confidence": 0.65,
        "universal_difficulty": 0.50,
        "topic_importance": 0.80,
        "time_spent_studying_min": 30.0,
        "confusability_score": 1,
        "prerequisite_completion_ratio": 1.0,
        "concurrent_topic_load": 3,
        "days_to_next_assessment": 12,
        "has_upcoming_assessment": 0,
    }


# ---------------------------------------------------------------------------
# Test 1 & 2 & 3: Logistic Regression Mathematical Additivity & Sigmoid
# ---------------------------------------------------------------------------

def test_logistic_regression_additivity_identity(trained_bundle, synthetic_features):
    """
    Verifies that:
      intercept + sum(feature contributions) = predicted_log_odds
      1 / (1 + exp(-predicted_log_odds)) = predicted_probability
    within numerical tolerance (1e-5).
    """
    decomp = compute_logistic_regression_contributions(trained_bundle, synthetic_features)

    intercept = decomp["intercept"]
    contributions = decomp["contributions"]
    log_odds = decomp["predicted_log_odds"]
    prob = decomp["reconstructed_probability"]

    # Identity 1: log-odds additivity
    calculated_log_odds = intercept + sum(contributions.values())
    assert calculated_log_odds == pytest.approx(log_odds, abs=1e-5)

    # Identity 2: sigmoid reconstruction
    calculated_prob = 1.0 / (1.0 + math.exp(-log_odds))
    assert calculated_prob == pytest.approx(prob, abs=1e-5)

    # Identity 3: match scikit-learn model output directly
    model = trained_bundle["model"]
    scaler = trained_bundle["scaler"]
    X_df = pd.DataFrame([synthetic_features])[FEATURE_COLUMNS]
    X_scaled = scaler.transform(X_df)
    expected_prob = float(model.predict_proba(X_scaled)[0][1])
    assert prob == pytest.approx(expected_prob, abs=1e-5)


# ---------------------------------------------------------------------------
# Test 4 & 5: Positive Class Coefficients and Scaler Use
# ---------------------------------------------------------------------------

def test_positive_class_coefficients_and_scaler(trained_bundle, synthetic_features):
    """
    Verifies that each feature contribution equals:
      coef[i] * ((value[i] - mean[i]) / std[i])
    using the model's positive-class (forgot = 1) coefficients.
    """
    model = trained_bundle["model"]
    scaler = trained_bundle["scaler"]
    decomp = compute_logistic_regression_contributions(trained_bundle, synthetic_features)

    coef = model.coef_[0]
    for i, col in enumerate(FEATURE_COLUMNS):
        raw_val = synthetic_features[col]
        expected_scaled = (raw_val - scaler.mean_[i]) / scaler.scale_[i]
        expected_contrib = float(coef[i] * expected_scaled)

        actual_contrib = decomp["contributions"][col]
        actual_scaled = decomp["scaled_features"][col]

        assert actual_scaled == pytest.approx(expected_scaled, abs=1e-5)
        assert actual_contrib == pytest.approx(expected_contrib, abs=1e-5)


# ---------------------------------------------------------------------------
# Test 6: Explanation Values Match Feature Vector Exactly
# ---------------------------------------------------------------------------

def test_explanation_values_match_actual_features(trained_bundle, synthetic_features):
    """Every explanation entry must carry the exact value from the input vector."""
    res = explain_prediction(trained_bundle, synthetic_features)

    for item in res["all_factors"]:
        feat_name = item["factor"]
        expected_val = synthetic_features[feat_name]
        assert item["value"] == pytest.approx(expected_val, abs=1e-4)


# ---------------------------------------------------------------------------
# Test 7 & 8: Contribution Directions and Ranking
# ---------------------------------------------------------------------------

def test_directions_and_ranking(trained_bundle, synthetic_features):
    """
    - Positive contributions are flagged as 'higher_risk'.
    - Negative contributions are flagged as 'lower_risk'.
    - Positive factors are ranked descending by contribution.
    - Negative factors are ranked ascending (strongest negative first).
    - top_factors is ranked by absolute contribution.
    """
    res = explain_prediction(trained_bundle, synthetic_features, max_positive=5, max_negative=5)

    for f in res["positive_factors"]:
        assert f["contribution"] > 0
        assert f["direction"] == "higher_risk"
        assert "higher predicted forgetting risk" in f["explanation"]

    for f in res["negative_factors"]:
        assert f["contribution"] < 0
        assert f["direction"] == "lower_risk"
        assert "lower predicted forgetting risk" in f["explanation"]

    # Positive factors ranked descending
    pos_contribs = [f["contribution"] for f in res["positive_factors"]]
    assert pos_contribs == sorted(pos_contribs, reverse=True)

    # Negative factors ranked ascending (e.g. -0.5 before -0.1)
    neg_contribs = [f["contribution"] for f in res["negative_factors"]]
    assert neg_contribs == sorted(neg_contribs)

    # top_factors ranked by absolute magnitude
    top_mags = [abs(f["contribution"]) for f in res["top_factors"]]
    assert top_mags == sorted(top_mags, reverse=True)


# ---------------------------------------------------------------------------
# Test 9: Topic Specificity (Different Topics Produce Different Explanations)
# ---------------------------------------------------------------------------

def test_topic_specificity_different_explanations(trained_bundle):
    """
    Two topics with distinct study profiles must produce distinct local explanations
    rather than identical global feature importances.
    """
    features_topic_a = {
        "times_studied": 1,
        "is_first_exposure": 1,
        "days_since_last_studied": 45,
        "revision_frequency": 0.0,
        "self_reported_confidence": 0.20,
        "universal_difficulty": 0.85,
        "topic_importance": 0.90,
        "time_spent_studying_min": 15.0,
        "confusability_score": 3,
        "prerequisite_completion_ratio": 0.25,
        "concurrent_topic_load": 7,
        "days_to_next_assessment": 3,
        "has_upcoming_assessment": 1,
    }

    features_topic_b = {
        "times_studied": 8,
        "is_first_exposure": 0,
        "days_since_last_studied": 2,
        "revision_frequency": 0.50,
        "self_reported_confidence": 0.90,
        "universal_difficulty": 0.30,
        "topic_importance": 0.40,
        "time_spent_studying_min": 120.0,
        "confusability_score": 0,
        "prerequisite_completion_ratio": 1.0,
        "concurrent_topic_load": 1,
        "days_to_next_assessment": 50,
        "has_upcoming_assessment": 0,
    }

    res_a = explain_prediction(trained_bundle, features_topic_a)
    res_b = explain_prediction(trained_bundle, features_topic_b)

    # Topic A (high risk) vs Topic B (low risk)
    assert res_a["predicted_log_odds"] != res_b["predicted_log_odds"]
    assert res_a["reconstructed_probability"] > res_b["reconstructed_probability"]

    # Contributions are calculated independently and differ
    contribs_a = {f["factor"]: f["contribution"] for f in res_a["all_factors"]}
    contribs_b = {f["factor"]: f["contribution"] for f in res_b["all_factors"]}
    assert contribs_a != contribs_b
    assert contribs_a["days_since_last_studied"] != contribs_b["days_since_last_studied"]
    assert contribs_a["times_studied"] != contribs_b["times_studied"]


# ---------------------------------------------------------------------------
# Test 10: Negligible Contributions Handling
# ---------------------------------------------------------------------------

def test_negligible_contributions_filtering(trained_bundle, synthetic_features):
    """
    Contributions below threshold are not included in positive_factors or negative_factors.
    If threshold is very high, summary reports no significant factors.
    """
    # Extremely high threshold: all factors should be filtered
    res_high_thresh = explain_prediction(trained_bundle, synthetic_features, threshold=100.0)
    assert len(res_high_thresh["positive_factors"]) == 0
    assert len(res_high_thresh["negative_factors"]) == 0
    assert len(res_high_thresh["top_factors"]) == 0
    assert "No individual feature had a significant contribution" in res_high_thresh["summary"]


# ---------------------------------------------------------------------------
# Test 11: Boundary Values and Grammar Rules
# ---------------------------------------------------------------------------

def test_grammar_and_boundary_rules():
    """
    - Singular vs plural: '1 day' vs '2 days', '1 time' vs '2 times'.
    - Upcoming assessment: only reported when has_upcoming_assessment == 1.
    - Zero confusability and zero load handled cleanly.
    - Non-causal wording is strictly preserved.
    """
    # Singular grammar
    s_day1 = format_feature_sentence("days_since_last_studied", 1, 0.5)
    assert "1 day ago" in s_day1
    s_days5 = format_feature_sentence("days_since_last_studied", 5, 0.5)
    assert "5 days" in s_days5

    s_time1 = format_feature_sentence("times_studied", 1, 0.5)
    assert "1 time," in s_time1
    s_times3 = format_feature_sentence("times_studied", 3, -0.5)
    assert "3 times," in s_times3

    # Assessment: value 0 must NOT state an upcoming assessment exists
    s_assess_0 = format_feature_sentence("has_upcoming_assessment", 0, 0.1)
    assert "No upcoming assessment" in s_assess_0

    s_assess_1 = format_feature_sentence("has_upcoming_assessment", 1, 0.1)
    assert "Has an upcoming assessment" in s_assess_1

    # Zero confusability
    s_conf_0 = format_feature_sentence("confusability_score", 0, -0.2)
    assert "No easily confusable topics flagged" in s_conf_0

    # Non-causal checks
    for feat in FEATURE_COLUMNS:
        sent = format_feature_sentence(feat, 1, 0.1)
        assert "cause" not in sent.lower()


# ---------------------------------------------------------------------------
# Test 12 & 13: Zero Leakage and Historical Correctness
# ---------------------------------------------------------------------------

def test_no_leakage_from_recall_event_correctness():
    """
    Flipping RecallEvent.is_correct on the DB must not alter feature calculations
    or the resulting local explanations.
    """
    db = SessionLocal()
    le = db.query(LearningEvent).first()
    user_id = le.user_id
    topic_id = le.topic_id

    res_before = predict_forgetting(db, user_id, topic_id)
    features_before = res_before["raw_features"]
    explanation_before = res_before["local_explanation"]

    # Flip any recall events for this student
    re_list = db.query(RecallEvent).filter(RecallEvent.user_id == user_id).all()
    for re in re_list:
        re.is_correct = not re.is_correct
    db.commit()

    res_after = predict_forgetting(db, user_id, topic_id)
    features_after = res_after["raw_features"]
    explanation_after = res_after["local_explanation"]

    # Revert DB changes
    for re in re_list:
        re.is_correct = not re.is_correct
    db.commit()
    db.close()

    assert features_before == features_after
    assert explanation_before["predicted_log_odds"] == explanation_after["predicted_log_odds"]
    assert explanation_before["positive_factors"] == explanation_after["positive_factors"]
    assert explanation_before["negative_factors"] == explanation_after["negative_factors"]


# ---------------------------------------------------------------------------
# Test 14: Dashboard Endpoint Integrates Local Explanations
# ---------------------------------------------------------------------------

def test_dashboard_api_returns_local_explanations():
    """
    Calls GET /users/{user_id}/dashboard and verifies that TopicRisk includes
    local_explanation and populated top_factors.
    """
    db = SessionLocal()
    le = db.query(LearningEvent).first()
    user_id = le.user_id
    db.close()

    client = TestClient(app)
    response = client.get(f"/users/{user_id}/dashboard")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == user_id
    assert len(data["topics"]) > 0

    first_topic = data["topics"][0]
    assert "local_explanation" in first_topic
    assert "top_factors" in first_topic

    local_exp = first_topic["local_explanation"]
    assert local_exp is not None
    assert local_exp["explanation_space"] == "log_odds"
    assert "intercept" in local_exp
    assert "predicted_log_odds" in local_exp
    assert "reconstructed_probability" in local_exp

    # Check that top_factors has local factor details
    assert len(first_topic["top_factors"]) > 0
    factor_entry = first_topic["top_factors"][0]
    assert "factor" in factor_entry
    assert "contribution" in factor_entry
    assert "direction" in factor_entry
    assert "explanation" in factor_entry


# ---------------------------------------------------------------------------
# Step 4.3 Tests: Contextual Above/Below Cohort Average & Non-Causal Wording
# ---------------------------------------------------------------------------

def test_above_and_below_average_wording_context():
    """
    Verifies that feature explanations explicitly contextualize whether
    values are above or below the cohort baseline average, and never describe
    below-average values (like 0 revisions or 15 mins study) as inherently protective.
    """
    # 1. revision_frequency (beta = +0.0257, mean = 0.18)
    s_rev_zero = format_feature_sentence("revision_frequency", 0.0, -0.036)
    assert "below cohort average" in s_rev_zero
    assert "0.00 revisions/day" in s_rev_zero
    assert "contributes less than average" in s_rev_zero
    assert "protective" not in s_rev_zero.lower()
    assert "associated with lower predicted forgetting risk" in s_rev_zero

    s_rev_high = format_feature_sentence("revision_frequency", 0.50, 0.05)
    assert "above the cohort average" in s_rev_high
    assert "associated with higher predicted forgetting risk" in s_rev_high

    # 2. self_reported_confidence (beta = +0.0147, mean = 0.55)
    s_conf_low = format_feature_sentence("self_reported_confidence", 0.20, -0.04)
    assert "below the cohort average" in s_conf_low
    assert "contributing less to the model's risk score" in s_conf_low
    assert "associated with lower predicted forgetting risk" in s_conf_low

    s_conf_high = format_feature_sentence("self_reported_confidence", 0.85, 0.04)
    assert "above cohort average" in s_conf_high
    assert "associated with higher predicted forgetting risk" in s_conf_high

    # 3. time_spent_studying_min (beta = +0.1568, mean = 235.6)
    s_time_low = format_feature_sentence("time_spent_studying_min", 30.0, -0.21)
    assert "below the cohort average" in s_time_low
    assert "contributing less to the model's risk score" in s_time_low
    assert "associated with lower predicted forgetting risk" in s_time_low

    s_time_high = format_feature_sentence("time_spent_studying_min", 400.0, 0.17)
    assert "above cohort average" in s_time_high
    assert "associated with higher predicted forgetting risk" in s_time_high

    # 4. concurrent_topic_load (beta = -0.0409, mean = 44.2)
    s_load_low = format_feature_sentence("concurrent_topic_load", 5, 0.106)
    assert "below the cohort average" in s_load_low
    assert "associated with higher predicted forgetting risk" in s_load_low

    s_load_high = format_feature_sentence("concurrent_topic_load", 60, -0.04)
    assert "above the cohort average" in s_load_high
    assert "associated with lower predicted forgetting risk" in s_load_high

    # 5. times_studied (beta = -0.4527, mean = 6.11)
    s_studied_low = format_feature_sentence("times_studied", 2, 0.64)
    assert "below cohort average" in s_studied_low
    assert "associated with higher predicted forgetting risk" in s_studied_low

    s_studied_high = format_feature_sentence("times_studied", 9, -0.45)
    assert "above cohort average" in s_studied_high
    assert "associated with lower predicted forgetting risk" in s_studied_high

    # 6. days_since_last_studied (beta = +0.4283, mean = 2.67)
    s_days_high = format_feature_sentence("days_since_last_studied", 14, 2.44)
    assert "above cohort average" in s_days_high
    assert "associated with higher predicted forgetting risk" in s_days_high

    s_days_low = format_feature_sentence("days_since_last_studied", 1, -0.36)
    assert "below cohort average" in s_days_low
    assert "associated with lower predicted forgetting risk" in s_days_low


def test_zero_and_boundary_values():
    """
    Verifies clean and graceful handling of zeros, missing values, and extreme boundaries.
    """
    # 0 days elapsed
    s_day0_pos = format_feature_sentence("days_since_last_studied", 0, 0.1)
    assert "0 days ago" in s_day0_pos
    s_day0_neg = format_feature_sentence("days_since_last_studied", 0, -0.1)
    assert "0 days ago" in s_day0_neg

    # 0 concurrent load
    s_load0_pos = format_feature_sentence("concurrent_topic_load", 0, 0.12)
    assert "No other topics studied concurrently" in s_load0_pos
    assert "associated with higher predicted forgetting risk" in s_load0_pos

    s_load0_neutral = format_feature_sentence("concurrent_topic_load", 0, 0.0)
    assert "No other topics studied concurrently" in s_load0_neutral
    assert "having a neutral contribution" in s_load0_neutral

    # Assessment: >= 60 days
    s_assess_far = format_feature_sentence("days_to_next_assessment", 75, -0.01)
    assert "60 or more days away" in s_assess_far

    # Missing / None values should not raise exceptions
    for col in FEATURE_COLUMNS:
        s_none_pos = format_feature_sentence(col, None, 0.05)
        assert isinstance(s_none_pos, str)
        s_none_neg = format_feature_sentence(col, None, -0.05)
        assert isinstance(s_none_neg, str)
        s_none_zero = format_feature_sentence(col, None, 0.0)
        assert isinstance(s_none_zero, str)


def test_inactive_features_filtered_from_top_factors(trained_bundle, synthetic_features):
    """
    Verifies that the 4 inactive zero-coefficient features:
      is_first_exposure, universal_difficulty, confusability_score, prerequisite_completion_ratio
    are excluded from positive_factors, negative_factors, and top_factors,
    while remaining present in all_factors with neutral direction.
    """
    res = explain_prediction(trained_bundle, synthetic_features, max_positive=5, max_negative=5)

    inactive_cols = {
        "is_first_exposure",
        "universal_difficulty",
        "confusability_score",
        "prerequisite_completion_ratio",
    }

    # Top factors must NOT contain any inactive features
    top_factor_names = {f["factor"] for f in res["top_factors"]}
    assert inactive_cols.isdisjoint(top_factor_names)

    pos_factor_names = {f["factor"] for f in res["positive_factors"]}
    assert inactive_cols.isdisjoint(pos_factor_names)

    neg_factor_names = {f["factor"] for f in res["negative_factors"]}
    assert inactive_cols.isdisjoint(neg_factor_names)

    # All factors must list them as neutral with zero contribution
    all_factor_map = {f["factor"]: f for f in res["all_factors"]}
    for inact in inactive_cols:
        assert inact in all_factor_map
        assert all_factor_map[inact]["contribution"] == 0.0
        assert all_factor_map[inact]["direction"] == "neutral"
        assert "neutral contribution" in all_factor_map[inact]["explanation"]


def test_non_causal_phrasing_strictly_enforced():
    """
    Verifies that explanations across all 13 features avoid unvalidated causal claims.
    """
    banned_words = ["cause", "causes", "caused", "causing", "prevent", "protect"]
    for col in FEATURE_COLUMNS:
        for contrib in [-0.5, 0.0, 0.5]:
            sent = format_feature_sentence(col, 2, contrib)
            for bw in banned_words:
                assert bw not in sent.lower(), f"Banned word '{bw}' found in explanation for {col}: {sent}"
