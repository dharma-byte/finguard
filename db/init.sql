CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE transactions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id         TEXT NOT NULL,
    amount             NUMERIC NOT NULL,
    merchant           TEXT,
    merchant_category  TEXT,
    location           TEXT,
    timestamp          TIMESTAMPTZ NOT NULL,
    raw_features        JSONB,
    fraud_score        FLOAT,
    is_flagged         BOOLEAN DEFAULT FALSE,
    created_at         TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE investigation_cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID REFERENCES transactions(id),
    analyst_notes   TEXT,
    outcome         TEXT, -- confirmed_fraud, false_positive, unresolved
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE case_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id     UUID REFERENCES investigation_cases(id),
    content     TEXT NOT NULL,
    embedding   VECTOR(384), -- matches MiniLM output dimension
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON case_embeddings USING ivfflat (embedding vector_cosine_ops);
