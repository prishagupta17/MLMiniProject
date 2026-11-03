"""
Trains and compares classical models for predicting forgetting probability.
Self-check (RecallEvent.is_correct) is used ONLY as the training label,
never as an input feature — see FEATURE_COLUMNS in features.py.

Run: python -m app.train
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, accuracy_score, classification_report,
    brier_score_loss, log_loss, precision_score, recall_score, f1_score
)

from .database import SessionLocal, init_db
from .synthetic_data import generate_all
from .features import build_feature_table, FEATURE_COLUMNS, apply_feature_transforms

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def bootstrap_if_empty(db):
    from .models import Topic
    if db.query(Topic).count() == 0:
        print("No data found — generating synthetic bootstrap dataset...")
        generate_all(db, n_users=25, days_span=120)


def train_and_compare(df: pd.DataFrame):
    X = df[FEATURE_COLUMNS]
    y = df["forgot"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=6, class_weight="balanced", random_state=42
        ),
    }

    results = {}
    for name, model in candidates.items():
        if name == "logistic_regression":
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)
            probs = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, probs)
        acc = accuracy_score(y_test, preds)
        results[name] = {"model": model, "auc": auc, "acc": acc}
        print(f"\n=== {name} ===")
        print(f"ROC-AUC: {auc:.3f}   Accuracy: {acc:.3f}")
        print(classification_report(y_test, preds, target_names=["recalled", "forgot"]))

    best_name = max(results, key=lambda n: results[n]["auc"])
    best_model = results[best_name]["model"]
    print(f"\n>> Best model: {best_name} (AUC={results[best_name]['auc']:.3f})")

    if best_name == "random_forest":
        importances = dict(zip(FEATURE_COLUMNS, best_model.feature_importances_))
    else:
        importances = dict(zip(FEATURE_COLUMNS, best_model.coef_[0]))
    importances = dict(sorted(importances.items(), key=lambda kv: -abs(kv[1])))

    print("\nTop factors driving forgetting risk:")
    for feat, weight in list(importances.items())[:8]:
        print(f"  {feat:35s} {weight:+.4f}")

    joblib.dump({
        "model": best_model,
        "model_name": best_name,
        "scaler": scaler if best_name == "logistic_regression" else None,
        "feature_columns": FEATURE_COLUMNS,
        "importances": importances,
    }, os.path.join(MODEL_DIR, "forgetting_model.joblib"))
    print(f"\nSaved model to {MODEL_DIR}/forgetting_model.joblib")

    return results, importances


def train_candidate_v2(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Train Model 6 (Log1p, Balanced Logistic Regression) candidate artifact.
    Uses Student-Grouped split (24 training students, 6 held-out test students).
    Saves candidate bundle to backend/models/forgetting_model_v2.joblib.
    Does NOT overwrite production forgetting_model.joblib.
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=random_seed)
    train_idx, test_idx = next(gss.split(df, groups=df["user_id"]))

    df_train = df.iloc[train_idx].copy()
    df_test = df.iloc[test_idx].copy()

    # Raw feature means before transformation
    raw_feature_means = {col: float(df_train[col].mean()) for col in FEATURE_COLUMNS}

    transforms = {"days_since_last_studied": "log1p"}
    X_train = apply_feature_transforms(df_train[FEATURE_COLUMNS], transforms)
    y_train = df_train["forgot"]
    X_test = apply_feature_transforms(df_test[FEATURE_COLUMNS], transforms)
    y_test = df_test["forgot"]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_seed)
    model.fit(X_train_scaled, y_train)

    probs = model.predict_proba(X_test_scaled)[:, 1]
    preds = model.predict(X_test_scaled)

    auc = float(roc_auc_score(y_test, probs))
    brier = float(brier_score_loss(y_test, probs))
    logloss = float(log_loss(y_test, probs))
    acc = float(accuracy_score(y_test, preds))
    rec = float(recall_score(y_test, preds, zero_division=0))
    prec = float(precision_score(y_test, preds, zero_division=0))
    f1 = float(f1_score(y_test, preds, zero_division=0))

    importances = dict(zip(FEATURE_COLUMNS, model.coef_[0]))
    importances = dict(sorted(importances.items(), key=lambda kv: -abs(kv[1])))

    save_path = output_path or os.path.join(MODEL_DIR, "forgetting_model_v2.joblib")
    bundle = {
        "model": model,
        "model_name": "logistic_regression",
        "model_version": "2.0.0",
        "schema_version": 2,
        "feature_columns": FEATURE_COLUMNS,
        "feature_transforms": transforms,
        "scaler": scaler,
        "raw_feature_means": raw_feature_means,
        "importances": importances,
        "training_metadata": {
            "trained_at": datetime.utcnow().isoformat(),
            "split_strategy": "Student-Grouped (24 train, 6 test)",
            "n_train_students": int(df_train["user_id"].nunique()),
            "n_test_students": int(df_test["user_id"].nunique()),
            "test_students": sorted(df_test["user_id"].unique().tolist()),
            "random_seed": random_seed,
            "metrics": {
                "roc_auc": auc,
                "brier_score": brier,
                "log_loss": logloss,
                "accuracy": acc,
                "recall": rec,
                "precision": prec,
                "f1": f1,
            },
        },
    }
    joblib.dump(bundle, save_path)
    print(f"\n[Model 6 Candidate] Saved candidate model to {save_path}")
    print(f"ROC-AUC: {auc:.4f} | Brier: {brier:.4f} | Recall: {rec:.4f} | F1: {f1:.4f}")

    return bundle


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    bootstrap_if_empty(db)
    df = build_feature_table(db)
    print(f"Feature table: {len(df)} rows (self-check events)")
    print(f"Forgetting rate in data: {df['forgot'].mean():.2%}")
    train_and_compare(df)
    db.close()
