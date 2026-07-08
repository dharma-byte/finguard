"""Hybrid retrieval over investigation cases: BM25 keyword search plus
pgvector cosine similarity, merged and reranked with a cross-encoder.

This hybrid-plus-rerank approach is what separates the retrieval step from
a basic top-k cosine similarity lookup, per the guide's RAG design.
"""

import os

from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from db import get_connection

load_dotenv()

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
BM25_CANDIDATES = 20
VECTOR_CANDIDATES = 20
FINAL_TOP_K = 5


def fetch_all_cases(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ce.case_id, ce.content, ic.outcome, ic.transaction_id
            FROM case_embeddings ce
            JOIN investigation_cases ic ON ic.id = ce.case_id
            """
        )
        return cur.fetchall()


def bm25_search(cases: list[dict], query: str, top_k: int) -> list[dict]:
    tokenized_corpus = [c["content"].lower().split() for c in cases]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query.lower().split())
    ranked = sorted(zip(cases, scores), key=lambda pair: pair[1], reverse=True)
    return [c for c, score in ranked[:top_k] if score > 0]


def vector_search(conn, query_embedding, top_k: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ce.case_id, ce.content, ic.outcome, ic.transaction_id
            FROM case_embeddings ce
            JOIN investigation_cases ic ON ic.id = ce.case_id
            ORDER BY ce.embedding <=> %s
            LIMIT %s
            """,
            (query_embedding, top_k),
        )
        return cur.fetchall()


class Retriever:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.reranker = CrossEncoder(RERANKER_MODEL_NAME)

    def retrieve(self, query: str, top_k: int = FINAL_TOP_K) -> list[dict]:
        conn = get_connection()
        try:
            all_cases = fetch_all_cases(conn)
            if not all_cases:
                return []

            bm25_hits = bm25_search(all_cases, query, BM25_CANDIDATES)

            query_embedding = self.embedder.encode(query, normalize_embeddings=True)
            vector_hits = vector_search(conn, query_embedding, VECTOR_CANDIDATES)
        finally:
            conn.close()

        merged = {c["case_id"]: c for c in bm25_hits}
        merged.update({c["case_id"]: c for c in vector_hits})
        candidates = list(merged.values())
        if not candidates:
            return []

        pairs = [[query, c["content"]] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        reranked = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)

        return [
            {
                "case_id": str(c["case_id"]),
                "transaction_id": str(c["transaction_id"]),
                "content": c["content"],
                "outcome": c["outcome"],
                "relevance_score": round(float(score), 4),
            }
            for c, score in reranked[:top_k]
        ]
