# backend

FastAPI service: Kafka consumer/scoring, PostgreSQL/pgvector access, and the
investigation API (`/transactions/flagged`, `/transactions/{id}`, `/investigate`).

## Run

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`

## Producer

Replays `data/creditcard.csv` onto the `transactions` Kafka topic to
simulate a live payment stream (requires `docker compose up` running
Redpanda, and the dataset in `data/` per `ml/README.md`):

```
python producer.py --delay 0.1
```

## Consumer / scoring service

Consumes the `transactions` topic, scores each message with the trained
XGBoost model (`python ml/train.py` must be run first), computes SHAP-based
top contributing features for flagged transactions, and writes results to
Postgres:

```
python consumer.py
```

## Embedding pipeline

Auto-creates a placeholder investigation case for any flagged transaction
that doesn't have one yet, then embeds every case without an embedding
(transaction summary + top SHAP features + analyst notes + outcome) into
`case_embeddings` using `all-MiniLM-L6-v2`:

```
python embeddings.py
```
