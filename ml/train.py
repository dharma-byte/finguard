"""Train the FinGuard fraud classifier on the Kaggle Credit Card Fraud dataset.

The Kaggle dataset is already PCA-anonymized (V1-V28) with no account_id,
merchant, or location columns, so account-level features (transaction
velocity, distance from home, merchant risk) described in the build guide
aren't derivable here -- those apply once this pipeline is pointed at a
richer dataset (e.g. IEEE-CIS) or a live feed with real account identifiers.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

DATA_PATH = Path(__file__).parent.parent / "data" / "creditcard.csv"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Download the Kaggle Credit Card Fraud "
            "Detection dataset and place creditcard.csv in data/."
        )
    return pd.read_csv(DATA_PATH)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour_of_day"] = (df["Time"] // 3600) % 24
    df["amount_log"] = np.log1p(df["Amount"])
    return df


def split(df: pd.DataFrame):
    feature_cols = [c for c in df.columns if c not in ("Time", "Amount", "Class")]
    X = df[feature_cols]
    y = df["Class"]
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def evaluate(model, X_test, y_test, name: str) -> dict:
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="binary", zero_division=0
    )
    auc = roc_auc_score(y_test, y_prob)
    metrics = {
        "model": name,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(auc, 4),
    }
    print(f"\n{name} -- {metrics}")
    print(classification_report(y_test, y_pred, digits=4))
    return metrics


def main():
    df = engineer_features(load_data())
    X_train, X_val, X_test, y_train, y_val, y_test = split(df)

    baseline = LogisticRegression(max_iter=1000, class_weight="balanced")
    baseline.fit(X_train, y_train)
    baseline_metrics = evaluate(baseline, X_test, y_test, "logistic_regression")

    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42,
    )
    xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    xgb_metrics = evaluate(xgb, X_test, y_test, "xgboost")

    joblib.dump(xgb, MODEL_DIR / "fraud_model.joblib")
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(
            {"logistic_regression": baseline_metrics, "xgboost": xgb_metrics},
            f,
            indent=2,
        )

    explainer = shap.TreeExplainer(xgb)
    shap_values = explainer.shap_values(X_test.iloc[:100])
    np.save(MODEL_DIR / "shap_sample.npy", shap_values)

    print(f"\nSaved model and metrics to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
