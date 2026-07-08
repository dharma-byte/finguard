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
