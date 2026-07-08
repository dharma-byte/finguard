"""Replay the Kaggle Credit Card Fraud dataset as a live Kafka stream.

Publishes one message per transaction row to simulate a real-time payment
feed. The dataset's `Class` column (ground truth fraud label) is included
as `true_label` for offline evaluation only -- the scoring consumer must
not read it when producing a fraud_score.
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

DATA_PATH = Path(__file__).parent.parent / "data" / "creditcard.csv"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
FEATURE_COLS = [f"V{i}" for i in range(1, 29)]
NUM_SYNTHETIC_ACCOUNTS = 500


def load_rows() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Download the Kaggle Credit Card Fraud "
            "Detection dataset and place creditcard.csv in data/."
        )
    return pd.read_csv(DATA_PATH)


def to_message(idx: int, row: pd.Series, start_time: datetime) -> dict:
    return {
        "transaction_id": str(uuid.uuid4()),
        "account_id": f"acct_{idx % NUM_SYNTHETIC_ACCOUNTS:04d}",
        "amount": float(row["Amount"]),
        "timestamp": (start_time + timedelta(seconds=float(row["Time"]))).isoformat(),
        "features": {col: float(row[col]) for col in FEATURE_COLS},
        "true_label": int(row["Class"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.1, help="Seconds between messages")
    parser.add_argument("--limit", type=int, default=None, help="Max number of messages to send")
    args = parser.parse_args()

    df = load_rows()
    if args.limit:
        df = df.head(args.limit)

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    start_time = datetime.now(timezone.utc)

    print(f"Publishing {len(df)} transactions to '{TOPIC}' on {BOOTSTRAP_SERVERS}")
    for idx, row in df.iterrows():
        message = to_message(idx, row, start_time)
        producer.send(TOPIC, value=message)
        if idx % 1000 == 0:
            print(f"  sent {idx}/{len(df)}")
        time.sleep(args.delay)

    producer.flush()
    print("Done.")


if __name__ == "__main__":
    main()
