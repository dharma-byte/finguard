# backend

FastAPI service: Kafka consumer/scoring, PostgreSQL/pgvector access, and the
investigation API (`/transactions/flagged`, `/transactions/{id}`, `/investigate`).

## Run

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`
