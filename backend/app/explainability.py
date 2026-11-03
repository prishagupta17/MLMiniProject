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

from .features import FEATURE_COLUMNS

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
    Generate student-friendly, non-causal sentences based on actual feature values,
    cohort baseline averages, and calculated signed contributions.

    Key principles:
    1. Contextualize whether the raw value is above, below, or equal to the cohort average.
    2. Clearly describe whether the mathematical contribution increases or decreases predicted log-odds.
    3. Never describe a below-average value as inherently protective (e.g., zero revisions
       or low study time is not protective; it contributes less to the model's risk score
       relative to the cohort baseline).
    4. Strictly avoid causal claims (uses 'associated with higher/lower predicted forgetting risk').
    5. Handle zero, None, missing, and boundary values gracefully.
    """
    if contribution > 0:
        dir_phrase = "associated with higher predicted forgetting risk"
    elif contribution < 0:
        dir_phrase = "associated with lower predicted forgetting risk"
    else:
        dir_phrase = "having a neutral contribution to predicted forgetting risk"

    if mean is None:
        mean = PROD_FEATURE_MEANS.get(feature_name)

    mean_fmt = f"{mean:.2f}" if mean is not None and mean < 1.0 else (f"{mean:.1f}" if mean is not None else "")

    if feature_name == "days_since_last_studied":
        days = int(value) if value is not None else 0
        unit = "day" if days == 1 else "days"
        ref_mean = f", above cohort average of {mean_fmt} days" if (mean is not None and days > mean) else (
            f", below cohort average of {mean_fmt} days" if mean is not None else ""
        )
        if contribution > 0:
            if days == 0:
                return f"Studied today (0 days ago), which in this model context is {dir_phrase}."
            return f"Not revised for {days} {unit} ({days} {unit} ago{ref_mean}), which is {dir_phrase}."
        elif contribution < 0:
            if days == 0:
                return f"Studied today (0 days ago, recently studied relative to cohort average of {mean_fmt} days), which is {dir_phrase}."
            return f"Recently studied ({days} {unit} ago{ref_mean}), which is {dir_phrase}."
        else:
            return f"Studied {days} {unit} ago (matching cohort average of {mean_fmt} days), {dir_phrase}."

    elif feature_name == "times_studied":
        times = int(value) if value is not None else 0
        unit = "time" if times == 1 else "times"
        if contribution > 0:
            return f"Studied only {times} {unit}, below cohort average of {mean_fmt} times, which is {dir_phrase}."
        elif contribution < 0:
            return f"Studied {times} {unit}, above cohort average of {mean_fmt} times, which is {dir_phrase}."
        else:
            return f"Studied {times} {unit}, matching cohort average of {mean_fmt} times, {dir_phrase}."

    elif feature_name == "is_first_exposure":
        first_exp = int(value) if value is not None else 0
        if first_exp == 1:
            if contribution != 0:
                return f"This is the first recorded exposure to this topic, which is {dir_phrase}."
            return f"This is the first recorded exposure to this topic (baseline cohort prior), {dir_phrase}."
        else:
            if contribution != 0:
                return f"Topic has been studied previously (not first exposure), which is {dir_phrase}."
            return f"Topic has been studied previously (not first exposure, baseline cohort prior), {dir_phrase}."

    elif feature_name == "revision_frequency":
        freq = round(float(value), 2) if value is not None else 0.0
        if contribution > 0:
            return f"Revision frequency of {freq:.2f} revisions/day is above the cohort average of {mean_fmt} revisions/day, which is {dir_phrase}."
        elif contribution < 0:
            if freq == 0.0:
                return f"Revision frequency is 0.00 revisions/day (below cohort average of {mean_fmt} revisions/day); this contributes less than average to the model's risk score and is {dir_phrase} relative to the baseline."
            return f"Revision frequency of {freq:.2f} revisions/day is below the cohort average of {mean_fmt} revisions/day; this contributes less than average to the model's risk score and is {dir_phrase} relative to the baseline."
        else:
            return f"Revision frequency of {freq:.2f} revisions/day matches the cohort average, {dir_phrase}."

    elif feature_name == "self_reported_confidence":
        conf = round(float(value), 2) if value is not None else 0.0
        if contribution > 0:
            return f"Self-reported confidence rating is {conf:.2f} (above cohort average of {mean_fmt}), which in this model is {dir_phrase}."
        elif contribution < 0:
            return f"Self-reported confidence rating of {conf:.2f} is below the cohort average of {mean_fmt}, contributing less to the model's risk score and {dir_phrase} relative to the baseline."
        else:
            return f"Self-reported confidence rating of {conf:.2f} matches the cohort average, {dir_phrase}."

    elif feature_name == "universal_difficulty":
        diff = round(float(value), 2) if value is not None else 0.50
        if contribution > 0:
            return f"Topic difficulty rating is {diff:.2f} (above baseline prior of {mean_fmt}), which is {dir_phrase}."
        elif contribution < 0:
            return f"Topic difficulty rating is {diff:.2f} (below baseline prior of {mean_fmt}), which is {dir_phrase}."
        else:
            return f"Topic difficulty rating of {diff:.2f} (baseline syllabus prior), {dir_phrase}."

    elif feature_name == "topic_importance":
        imp = round(float(value), 2) if value is not None else 0.0
        if contribution > 0:
            return f"Course exam importance weight is {imp:.2f} (below cohort average of {mean_fmt}), which is {dir_phrase}."
        elif contribution < 0:
            return f"Course exam importance weight of {imp:.2f} is above cohort average of {mean_fmt}, which is {dir_phrase}."
        else:
            return f"Course exam importance weight of {imp:.2f} matches the cohort average, {dir_phrase}."

    elif feature_name == "time_spent_studying_min":
        mins = round(float(value), 1) if value is not None else 0.0
        if contribution > 0:
            return f"Cumulative study time is {mins:.1f} minutes (above cohort average of {mean_fmt} minutes), which in this model fit is {dir_phrase}."
        elif contribution < 0:
            return f"Cumulative study time of {mins:.1f} minutes is below the cohort average of {mean_fmt} minutes, contributing less to the model's risk score and {dir_phrase} relative to the baseline."
        else:
            return f"Cumulative study time of {mins:.1f} minutes matches the cohort average, {dir_phrase}."

    elif feature_name == "confusability_score":
        score = int(value) if value is not None else 0
        if score == 0:
            if contribution != 0:
                return f"No easily confusable topics flagged (score 0), which is {dir_phrase}."
            return f"No easily confusable topics flagged (score 0, baseline syllabus prior), {dir_phrase}."
        elif score == 1:
            if contribution != 0:
                return f"Easily confused with 1 other topic, which is {dir_phrase}."
            return f"Easily confused with 1 other topic (score 1), {dir_phrase}."
        else:
            if contribution != 0:
                return f"Easily confused with {score} other topics, which is {dir_phrase}."
            return f"Easily confused with {score} other topics (score {score}), {dir_phrase}."

    elif feature_name == "prerequisite_completion_ratio":
        pct = int(round(float(value) * 100)) if value is not None else 100
        if pct < 100:
            if contribution != 0:
                return f"Prerequisites are only partially completed ({pct}%), which is {dir_phrase}."
            return f"Prerequisites are partially completed ({pct}%), {dir_phrase}."
        else:
            if contribution != 0:
                return f"Prerequisites are fully completed (100%), which is {dir_phrase}."
            return f"Prerequisites are fully completed (100%, baseline syllabus prior), {dir_phrase}."

    elif feature_name == "concurrent_topic_load":
        load = int(value) if value is not None else 0
        unit = "topic" if load == 1 else "topics"
        if load == 0:
            if contribution > 0:
                return f"No other topics studied concurrently this week (0 topics, below cohort average of {mean_fmt} topics), which in this model's correlation structure is {dir_phrase}."
            elif contribution < 0:
                return f"No other topics studied concurrently this week (0 topics), which is {dir_phrase}."
            else:
                return f"No other topics studied concurrently this week, {dir_phrase}."
        else:
            if contribution > 0:
                return f"Concurrent study load of {load} {unit} this week is below the cohort average of {mean_fmt} topics, which in this model's correlation structure is {dir_phrase}."
            elif contribution < 0:
                return f"Concurrent study load of {load} {unit} this week is above the cohort average of {mean_fmt} topics, which is {dir_phrase}."
            else:
                return f"Concurrent study load of {load} {unit} this week matches the cohort average, {dir_phrase}."

    elif feature_name == "days_to_next_assessment":
        days = int(value) if value is not None else 60
        unit = "day" if days == 1 else "days"
        if days >= 60:
            return f"Next covering assessment is 60 or more days away (above cohort average of {mean_fmt} days), which is {dir_phrase}."
        else:
            if contribution > 0:
                return f"Upcoming assessment in {days} {unit} (below cohort average of {mean_fmt} days), which is {dir_phrase}."
            elif contribution < 0:
                return f"Upcoming assessment in {days} {unit} (above cohort average of {mean_fmt} days), which is {dir_phrase}."
            else:
                return f"Upcoming assessment in {days} {unit} (matching cohort average of {mean_fmt} days), {dir_phrase}."

    elif feature_name == "has_upcoming_assessment":
        has_up = int(value) if value is not None else 0
        if has_up == 1:
            if contribution > 0:
                return f"Has an upcoming assessment covering this topic within the planning window (value 1, above cohort average of {mean_fmt}), which is {dir_phrase}."
            elif contribution < 0:
                return f"Has an upcoming assessment covering this topic within the planning window (value 1), which is {dir_phrase}."
            else:
                return f"Has an upcoming assessment covering this topic within the planning window, {dir_phrase}."
        else:
            if contribution < 0:
                return f"No upcoming assessment is scheduled in the immediate 7-day window (value 0, below cohort average of {mean_fmt}), contributing less to the model's risk score and {dir_phrase} relative to the baseline."
            elif contribution > 0:
                return f"No upcoming assessment is scheduled in the immediate 7-day window (value 0), which in this model context is {dir_phrase}."
            else:
                return f"No upcoming assessment is scheduled in the immediate 7-day window, {dir_phrase}."

    return f"Feature '{feature_name}' has value {value}, which is {dir_phrase}."


def compute_logistic_regression_contributions(
    bundle: Dict[str, Any],
    features: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate exact linear contributions for a Logistic Regression model.

    For each feature i:
      scaled_val_i = (features[feature_name] - mean_i) / std_i  (if scaler present)
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

    if scaler is not None:
        X_scaled = scaler.transform(X_df)[0]
    else:
        X_scaled = X_df.values[0]

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
        feat_mean = means.get(col, PROD_FEATURE_MEANS.get(col))
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
