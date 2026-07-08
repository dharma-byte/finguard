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

## Investigation API

Requires `ANTHROPIC_API_KEY` in `.env`. Endpoints:

- `GET /transactions/flagged` — list flagged transactions
- `GET /transactions/{id}` — transaction detail
- `POST /investigate` — `{"transaction_id": "...", "question": "..."}` runs
  hybrid retrieval over similar past cases and returns an LLM investigation
  summary that cites case IDs, plus the cited cases themselves

```
uvicorn app.main:app --reload
```

## Tests

Covers feature extraction (producer message shape), the scoring function
(consumer feature vector + SHAP ranking), and the retrieval function (BM25
search). No live Kafka/Postgres/model needed:

```
pytest
```

## Retrieval evaluation

Measures precision@5 for the raw BM25+vector merge vs. the cross-encoder
reranked results, per the guide's evaluation step. Requires seeded
`investigation_cases` with `analyst_notes`/`outcome` (case IDs are visible
via `psql` or the flagged-transactions endpoint once cases exist):

```
cp eval/retrieval_eval.json.example eval/retrieval_eval.json
# fill in 20-30 real query / expected_case_ids pairs by hand
python evaluate_retrieval.py
```
