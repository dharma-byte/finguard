"""Kafka consumer: scores each incoming transaction with the trained
XGBoost model and writes the result to PostgreSQL.

The model is loaded once at startup and reused for every message, per the
architecture doc's scoring engine design.
"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import shap
from dotenv import load_dotenv
from kafka import KafkaConsumer

from db import get_connection

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
MODEL_PATH = Path(__file__).parent.parent / "ml" / "models" / "fraud_model.joblib"
FLAG_THRESHOLD = float(os.getenv("FRAUD_FLAG_THRESHOLD", "0.5"))

# Must match the feature order produced by ml/train.py's engineer_features().
PCA_FEATURE_COLS = [f"V{i}" for i in range(1, 29)]
FEATURE_COLS = PCA_FEATURE_COLS + ["hour_of_day", "amount_log"]


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"{MODEL_PATH} not found. Run `python ml/train.py` first.")
    return joblib.load(MODEL_PATH)


def build_feature_vector(message: dict) -> np.ndarray:
    features = message["features"]
    hour_of_day = (message["time_offset_seconds"] // 3600) % 24
    amount_log = np.log1p(message["amount"])
    row = [features[col] for col in PCA_FEATURE_COLS] + [hour_of_day, amount_log]
    return np.array(row, dtype=float).reshape(1, -1)


def top_shap_features(explainer, x: np.ndarray, n: int = 3) -> list[dict]:
    shap_values = explainer.shap_values(x)
    contributions = list(zip(FEATURE_COLS, shap_values[0]))
    contributions.sort(key=lambda c: abs(c[1]), reverse=True)
    return [{"feature": f, "impact": round(float(v), 4)} for f, v in contributions[:n]]


def insert_transaction(
    conn, message: dict, fraud_score: float, is_flagged: bool, top_features: list
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions
                (account_id, amount, timestamp, raw_features, fraud_score, is_flagged)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                message["account_id"],
                message["amount"],
                message["timestamp"],
                json.dumps({**message["features"], "top_shap_features": top_features}),
                fraud_score,
                is_flagged,
            ),
        )
    conn.commit()


def main():
    model = load_model()
    explainer = shap.TreeExplainer(model)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="finguard-scoring",
    )
    conn = get_connection()

    print(f"Listening on '{TOPIC}' at {BOOTSTRAP_SERVERS}...")
    for record in consumer:
        message = record.value
        x = build_feature_vector(message)
        fraud_score = float(model.predict_proba(x)[0, 1])
        is_flagged = fraud_score >= FLAG_THRESHOLD

        top_features = top_shap_features(explainer, x) if is_flagged else []
        insert_transaction(conn, message, fraud_score, is_flagged, top_features)

        flag_marker = "FLAGGED" if is_flagged else "ok"
        print(f"[{flag_marker}] {message['transaction_id']} score={fraud_score:.4f}")


if __name__ == "__main__":
    main()
