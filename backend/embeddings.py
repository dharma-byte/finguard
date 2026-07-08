"""Embedding pipeline: turns flagged transactions and their investigation
notes into vectors stored in pgvector for retrieval.

Chunks by logical case -- one investigation case becomes one passage
(transaction summary + top SHAP features + analyst notes + outcome) --
rather than fixed token windows, per the guide's chunking strategy.
"""

import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from db import get_connection

load_dotenv()

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def build_case_passage(case: dict) -> str:
    lines = [
        f"Transaction {case['transaction_id']}: account {case['account_id']}, "
        f"amount {case['amount']}, timestamp {case['timestamp']}, "
        f"fraud score {case['fraud_score']:.4f}."
    ]
    top_features = (case.get("raw_features") or {}).get("top_shap_features") or []
    if top_features:
        feature_str = ", ".join(f"{f['feature']} (impact {f['impact']})" for f in top_features)
        lines.append(f"Top contributing features: {feature_str}.")
    if case.get("analyst_notes"):
        lines.append(f"Analyst notes: {case['analyst_notes']}")
    lines.append(f"Outcome: {case.get('outcome') or 'unresolved'}.")
    return " ".join(lines)


def ensure_cases_for_flagged_transactions(conn) -> None:
    """Auto-create a placeholder investigation case for any flagged
    transaction that doesn't have one yet, so it becomes retrievable even
    before an analyst adds notes."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO investigation_cases (transaction_id, outcome)
            SELECT t.id, 'unresolved'
            FROM transactions t
            LEFT JOIN investigation_cases ic ON ic.transaction_id = t.id
            WHERE t.is_flagged = TRUE AND ic.id IS NULL
            """
        )
    conn.commit()


def fetch_cases_needing_embeddings(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ic.id AS case_id, ic.analyst_notes, ic.outcome,
                   t.id AS transaction_id, t.account_id, t.amount,
                   t.timestamp, t.fraud_score, t.raw_features
            FROM investigation_cases ic
            JOIN transactions t ON t.id = ic.transaction_id
            LEFT JOIN case_embeddings ce ON ce.case_id = ic.id
            WHERE ce.id IS NULL
            """
        )
        return cur.fetchall()


def embed_pending_cases(conn, model: SentenceTransformer) -> int:
    cases = fetch_cases_needing_embeddings(conn)
    if not cases:
        return 0

    passages = [build_case_passage(case) for case in cases]
    vectors = model.encode(passages, normalize_embeddings=True)

    with conn.cursor() as cur:
        for case, passage, vector in zip(cases, passages, vectors):
            cur.execute(
                "INSERT INTO case_embeddings (case_id, content, embedding) VALUES (%s, %s, %s)",
                (case["case_id"], passage, vector),
            )
    conn.commit()
    return len(cases)


def main():
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    conn = get_connection()

    ensure_cases_for_flagged_transactions(conn)
    count = embed_pending_cases(conn, model)
    print(f"Embedded {count} case(s).")


if __name__ == "__main__":
    main()
