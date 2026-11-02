"""
Trains and compares classical models for predicting forgetting probability.
Self-check (RecallEvent.is_correct) is used ONLY as the training label,
never as an input feature — see FEATURE_COLUMNS in features.py.

Run: python -m app.train
"""
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report

from .database import SessionLocal, init_db
from .synthetic_data import generate_all
from .features import build_feature_table, FEATURE_COLUMNS

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


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    bootstrap_if_empty(db)
    df = build_feature_table(db)
    print(f"Feature table: {len(df)} rows (self-check events)")
    print(f"Forgetting rate in data: {df['forgot'].mean():.2%}")
    train_and_compare(df)
    db.close()
