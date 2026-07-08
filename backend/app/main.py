import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection  # noqa: E402
from retrieval import Retriever  # noqa: E402

from .llm import generate_investigation_summary

app = FastAPI(title="FinGuard API")
retriever = Retriever()


class TransactionOut(BaseModel):
    id: str
    account_id: str
    amount: float
    timestamp: datetime
    fraud_score: float | None
    is_flagged: bool
    top_shap_features: list[dict] = []


class InvestigateRequest(BaseModel):
    transaction_id: str
    question: str | None = None


class CitedCase(BaseModel):
    case_id: str
    transaction_id: str
    outcome: str
    relevance_score: float


class InvestigateResponse(BaseModel):
    summary: str
    cited_cases: list[CitedCase]


def _to_transaction_out(row: dict) -> TransactionOut:
    raw_features = row.get("raw_features") or {}
    return TransactionOut(
        id=str(row["id"]),
        account_id=row["account_id"],
        amount=float(row["amount"]),
        timestamp=row["timestamp"],
        fraud_score=row["fraud_score"],
        is_flagged=row["is_flagged"],
        top_shap_features=raw_features.get("top_shap_features", []),
    )


def _fetch_transaction(transaction_id: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_id, amount, timestamp, fraud_score, is_flagged, raw_features
                FROM transactions WHERE id = %s
                """,
                (transaction_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/transactions/flagged", response_model=list[TransactionOut])
def list_flagged(limit: int = 50):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_id, amount, timestamp, fraud_score, is_flagged, raw_features
                FROM transactions
                WHERE is_flagged = TRUE
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [_to_transaction_out(row) for row in rows]


@app.get("/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str):
    row = _fetch_transaction(transaction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_transaction_out(row)


@app.post("/investigate", response_model=InvestigateResponse)
def investigate(request: InvestigateRequest):
    row = _fetch_transaction(request.transaction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction = _to_transaction_out(row)
    query = request.question or (
        f"Similar past fraud cases for a ${transaction.amount} transaction "
        f"with features {transaction.top_shap_features}"
    )
    cases = retriever.retrieve(query)
    summary = generate_investigation_summary(
        transaction.model_dump(mode="json"), cases, request.question
    )

    return InvestigateResponse(
        summary=summary,
        cited_cases=[
            CitedCase(
                case_id=c["case_id"],
                transaction_id=c["transaction_id"],
                outcome=c["outcome"],
                relevance_score=c["relevance_score"],
            )
            for c in cases
        ],
    )
