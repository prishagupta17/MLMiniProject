"""
Local, topic-specific explainability module for The Forgetting Engine.

For Logistic Regression models:
  - Contributions are calculated in log-odds space:
      contribution_i = coefficient_i * scaled_feature_i
  - Mathematical identity:
      intercept + sum(contributions) = predicted_log_odds
  - Sigmoid identity:
      1 / (1 + exp(-predicted_log_odds)) = predicted_probability
  - Contributions are strictly in log-odds space, not percentage points.
  - Positive contribution: pushes predicted forgetting risk upward relative to intercept.
  - Negative contribution: pushes predicted forgetting risk downward relative to intercept.
  - Explanations are topic-specific, student-specific, and non-causal.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from .features import FEATURE_COLUMNS, apply_feature_transforms

# Threshold below which a feature contribution is considered negligible
DEFAULT_CONTRIBUTION_THRESHOLD = 0.005

# Verified production model scaler means (from backend/models/forgetting_model.joblib)
PROD_FEATURE_MEANS: Dict[str, float] = {
    "times_studied": 6.11,
    "is_first_exposure": 0.00,
    "days_since_last_studied": 2.67,
    "revision_frequency": 0.18,
    "self_reported_confidence": 0.55,
    "universal_difficulty": 0.50,
    "topic_importance": 0.81,
    "time_spent_studying_min": 235.56,
    "confusability_score": 0.00,
    "prerequisite_completion_ratio": 1.00,
    "concurrent_topic_load": 44.21,
    "days_to_next_assessment": 17.06,
    "has_upcoming_assessment": 0.85,
}


def format_feature_sentence(
    feature_name: str,
    value: Any,
    contribution: float,
    mean: Optional[float] = None,
) -> str:
    """
    Generate student-friendly, neutral, non-causal explanations based on actual feature values,
    training baseline averages, and calculated signed contributions.

    Key principles:
    1. State the observed feature value.
    2. Contextualize it against the training average where useful.
    3. Clearly describe whether the mathematical contribution increases or decreases
       the model's predicted log-odds relative to the intercept baseline.
    4. Never describe below-average study time, revision frequency, or confidence as
       beneficial or protective.
    5. Strictly avoid causal claims.
    6. Use simple, concise student-friendly language.
    7. Handle zero, None, missing, and boundary values gracefully.
    """
    if contribution > 0:
        contrib_phrase = "This feature contributes positively to the model's risk score."
    elif contribution < 0:
        contrib_phrase = "This feature contributes negatively to the model's risk score."
    else:
        contrib_phrase = "This feature has a neutral contribution to the model's risk score."

    if mean is None:
        mean = PROD_FEATURE_MEANS.get(feature_name)

    mean_fmt = f"{mean:.2f}" if mean is not None and mean < 1.0 else (f"{mean:.1f}" if mean is not None else "")

    if feature_name == "days_since_last_studied":
        days = int(value) if value is not None else 0
        unit = "day" if days == 1 else "days"
        ref_mean = f", above the training average of {mean_fmt} days" if (mean is not None and days > mean) else (
            f", below the training average of {mean_fmt} days" if mean is not None else ""
        )
        if days == 0:
            return f"Last studied today (0 days ago{ref_mean}). {contrib_phrase}"
        elif days == 1:
            return f"Last studied 1 day ago (1 day ago{ref_mean}). {contrib_phrase}"
        else:
            return f"Last studied {days} {unit} ago ({days} {unit} ago{ref_mean}). {contrib_phrase}"

    elif feature_name == "times_studied":
        times = int(value) if value is not None else 0
        unit = "time" if times == 1 else "times"
        if times == 1:
            return f"Studied only 1 time, below the training average of {mean_fmt} times. {contrib_phrase}"
        elif mean is not None and times < mean:
            return f"Studied {times} times, below the training average of {mean_fmt} times. {contrib_phrase}"
        elif mean is not None and times > mean:
            return f"Studied {times} times, above the training average of {mean_fmt} times. {contrib_phrase}"
        else:
            return f"Studied {times} times, matching the training average of {mean_fmt} times. {contrib_phrase}"

    elif feature_name == "is_first_exposure":
        first_exp = int(value) if value is not None else 0
        if first_exp == 1:
            return f"First recorded exposure to this topic (baseline cohort prior). {contrib_phrase}"
        else:
            return f"Topic studied previously (not first exposure, baseline cohort prior). {contrib_phrase}"

    elif feature_name == "revision_frequency":
        freq = round(float(value), 2) if value is not None else 0.0
        if mean is not None and freq > mean:
            return f"Revision frequency is {freq:.2f} revisions/day, above the training average of {mean_fmt} revisions/day. {contrib_phrase}"
        elif mean is not None and freq < mean:
            return f"Revision frequency is {freq:.2f} revisions/day, below the training average of {mean_fmt} revisions/day. {contrib_phrase}"
        else:
            return f"Revision frequency is {freq:.2f} revisions/day, matching the training average. {contrib_phrase}"

    elif feature_name == "self_reported_confidence":
        conf = round(float(value), 2) if value is not None else 0.0
        if mean is not None and conf > mean:
            return f"Self-reported confidence rating is {conf:.2f}, above the training average of {mean_fmt}. {contrib_phrase}"
        elif mean is not None and conf < mean:
            return f"Self-reported confidence rating is {conf:.2f}, below the training average of {mean_fmt}. {contrib_phrase}"
        else:
            return f"Self-reported confidence rating is {conf:.2f}, matching the training average. {contrib_phrase}"

    elif feature_name == "universal_difficulty":
        diff = round(float(value), 2) if value is not None else 0.50
        return f"Topic difficulty rating is {diff:.2f} (baseline syllabus prior). {contrib_phrase}"

    elif feature_name == "topic_importance":
        imp = round(float(value), 2) if value is not None else 0.0
        if mean is not None and imp < mean:
            return f"Course exam importance weight is {imp:.2f}, below the training average of {mean_fmt}. {contrib_phrase}"
        elif mean is not None and imp > mean:
            return f"Course exam importance weight is {imp:.2f}, above the training average of {mean_fmt}. {contrib_phrase}"
        else:
            return f"Course exam importance weight is {imp:.2f}, matching the training average. {contrib_phrase}"

    elif feature_name == "time_spent_studying_min":
        mins = round(float(value), 1) if value is not None else 0.0
        if mean is not None and mins < mean:
            return f"Study time is {mins:.1f} minutes, below the training average of {mean_fmt} minutes. {contrib_phrase}"
        elif mean is not None and mins > mean:
            return f"Study time is {mins:.1f} minutes, above the training average of {mean_fmt} minutes. {contrib_phrase}"
        else:
            return f"Study time is {mins:.1f} minutes, matching the training average. {contrib_phrase}"

    elif feature_name == "confusability_score":
        score = int(value) if value is not None else 0
        if score == 0:
            return f"No easily confusable topics flagged (score 0, baseline syllabus prior). {contrib_phrase}"
        else:
            unit = "topic" if score == 1 else "topics"
            return f"Easily confused with {score} other {unit} (score {score}). {contrib_phrase}"

    elif feature_name == "prerequisite_completion_ratio":
        pct = int(round(float(value) * 100)) if value is not None else 100
        if pct >= 100:
            return f"Prerequisites are fully completed (100%, baseline syllabus prior). {contrib_phrase}"
        else:
            return f"Prerequisites are partially completed ({pct}%). {contrib_phrase}"

    elif feature_name == "concurrent_topic_load":
        load = int(value) if value is not None else 0
        unit = "topic" if load == 1 else "topics"
        if load == 0:
            return f"No other topics studied concurrently this week (0 topics, below the training average of {mean_fmt} topics). {contrib_phrase}"
        elif mean is not None and load < mean:
            return f"Concurrent study load is {load} other {unit} this week, below the training average of {mean_fmt} topics. {contrib_phrase}"
        elif mean is not None and load > mean:
            return f"Concurrent study load is {load} other {unit} this week, above the training average of {mean_fmt} topics. {contrib_phrase}"
        else:
            return f"Concurrent study load is {load} other {unit} this week, matching the training average. {contrib_phrase}"

    elif feature_name == "days_to_next_assessment":
        days = int(value) if value is not None else 60
        unit = "day" if days == 1 else "days"
        if days >= 60:
            return f"Next covering assessment is 60 or more days away, above the training average of {mean_fmt} days. {contrib_phrase}"
        elif mean is not None and days < mean:
            return f"Upcoming assessment is in {days} {unit}, below the training average of {mean_fmt} days. {contrib_phrase}"
        elif mean is not None and days > mean:
            return f"Upcoming assessment is in {days} {unit}, above the training average of {mean_fmt} days. {contrib_phrase}"
        else:
            return f"Upcoming assessment is in {days} {unit}, matching the training average. {contrib_phrase}"

    elif feature_name == "has_upcoming_assessment":
        has_up = int(value) if value is not None else 0
        if has_up == 1:
            return f"Has an upcoming assessment covering this topic within the planning window (value 1, above the training average of {mean_fmt}). {contrib_phrase}"
        else:
            return f"No upcoming assessment is scheduled in the immediate 7-day window (value 0, below the training average of {mean_fmt}). {contrib_phrase}"

    return f"Feature '{feature_name}' has value {value}. {contrib_phrase}"


def compute_logistic_regression_contributions(
    bundle: Dict[str, Any],
    features: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate exact linear contributions for a Logistic Regression model.

    For each feature i:
      transformed_val_i = apply_feature_transforms(features[feature_name])
      scaled_val_i = (transformed_val_i - mean_i) / std_i  (if scaler present)
      contribution_i = coefficient_i * scaled_val_i

    Log-odds identity:
      intercept + sum(contributions) = predicted_log_odds

    Sigmoid probability identity:
      1 / (1 + exp(-predicted_log_odds)) = predicted_probability
    """
    model = bundle["model"]
    scaler = bundle.get("scaler")
    feature_cols = bundle.get("feature_columns", FEATURE_COLUMNS)

    X_df = pd.DataFrame([features])[feature_cols]
    transforms = bundle.get("feature_transforms")
    X_trans = apply_feature_transforms(X_df, transforms)

    if scaler is not None:
        X_scaled = scaler.transform(X_trans)[0]
    else:
        X_scaled = X_trans.values[0]

    # Positive class (forgot = 1) coefficients
    if hasattr(model, "coef_"):
        coef = model.coef_[0]
        intercept = float(model.intercept_[0])
    else:
        raise ValueError(f"Model {type(model)} does not have coef_ attribute for linear decomposition.")

    contributions: Dict[str, float] = {}
    scaled_dict: Dict[str, float] = {}
    total_feature_contrib = 0.0

    for i, col in enumerate(feature_cols):
        c = float(coef[i] * X_scaled[i])
        contributions[col] = c
        scaled_dict[col] = float(X_scaled[i])
        total_feature_contrib += c

    predicted_log_odds = intercept + total_feature_contrib
    reconstructed_prob = 1.0 / (1.0 + math.exp(-predicted_log_odds))

    return {
        "model_name": bundle.get("model_name", "logistic_regression"),
        "explanation_space": "log_odds",
        "intercept": intercept,
        "predicted_log_odds": predicted_log_odds,
        "reconstructed_probability": reconstructed_prob,
        "contributions": contributions,
        "scaled_features": scaled_dict,
    }


def explain_prediction(
    bundle: Dict[str, Any],
    features: Dict[str, Any],
    max_positive: int = 3,
    max_negative: int = 3,
    threshold: float = DEFAULT_CONTRIBUTION_THRESHOLD,
) -> Dict[str, Any]:
    """
    Generate local, topic-specific feature explanations.

    Returns structured factor explanations separating positive contributions
    (increasing predicted risk) from negative contributions (decreasing predicted risk).
    """
    model_name = bundle.get("model_name", "")
    is_logistic = "logistic" in model_name or hasattr(bundle.get("model"), "coef_")

    if is_logistic:
        decomposition = compute_logistic_regression_contributions(bundle, features)
    else:
        raise NotImplementedError(f"Model architecture '{model_name}' does not have local explainability implemented.")

    contributions = decomposition["contributions"]
    feature_cols = bundle.get("feature_columns", FEATURE_COLUMNS)
    scaler = bundle.get("scaler")
    raw_means = bundle.get("raw_feature_means", {})
    means = {}
    if scaler is not None and hasattr(scaler, "mean_"):
        means = {col: float(scaler.mean_[i]) for i, col in enumerate(feature_cols)}

    all_factors: List[Dict[str, Any]] = []
    positive_candidates: List[Dict[str, Any]] = []
    negative_candidates: List[Dict[str, Any]] = []

    for col in feature_cols:
        val = features.get(col)
        contrib = contributions.get(col, 0.0)
        direction = "higher_risk" if contrib > 0 else ("lower_risk" if contrib < 0 else "neutral")
        feat_mean = raw_means.get(col) or means.get(col) or PROD_FEATURE_MEANS.get(col)
        sentence = format_feature_sentence(col, val, contrib, mean=feat_mean)

        factor_data = {
            "factor": col,
            "value": round(float(val), 4) if isinstance(val, (int, float)) and not isinstance(val, bool) else val,
            "contribution": round(contrib, 4),
            "direction": direction,
            "explanation": sentence,
            # Backward-compatibility alias for clients expecting model_weight:
            "model_weight": round(contrib, 4),
        }
        all_factors.append(factor_data)

        if abs(contrib) >= threshold:
            if contrib > 0:
                positive_candidates.append(factor_data)
            elif contrib < 0:
                negative_candidates.append(factor_data)

    # Rank positive factors: highest positive contribution first
    positive_factors = sorted(positive_candidates, key=lambda f: -f["contribution"])[:max_positive]

    # Rank negative factors: most negative (strongest risk reducer) first
    negative_factors = sorted(negative_candidates, key=lambda f: f["contribution"])[:max_negative]

    # Combined top_factors: ranked by absolute contribution magnitude
    top_factors = sorted(
        [f for f in (positive_candidates + negative_candidates)],
        key=lambda f: -abs(f["contribution"])
    )[:max_positive + max_negative]

    if not top_factors:
        summary = "No individual feature had a significant contribution beyond the baseline model intercept."
    else:
        summary = (
            f"Prediction explained by {len(positive_factors)} factor(s) increasing predicted risk "
            f"and {len(negative_factors)} factor(s) reducing predicted risk."
        )

    return {
        "explanation_space": decomposition["explanation_space"],
        "intercept": round(decomposition["intercept"], 4),
        "predicted_log_odds": round(decomposition["predicted_log_odds"], 4),
        "reconstructed_probability": round(decomposition["reconstructed_probability"], 4),
        "summary": summary,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "top_factors": top_factors,
        "all_factors": all_factors,
    }
