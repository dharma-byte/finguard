"""Retrieval evaluation harness: precision@5 before and after reranking.

Loads a hand-built set of (query, expected_case_ids) pairs and reports
precision@5 for the raw hybrid merge vs. the cross-encoder-reranked
results, per the guide's evaluation step.
"""

import json
from pathlib import Path

from retrieval import Retriever

EVAL_SET_PATH = Path(__file__).parent / "eval" / "retrieval_eval.json"


def load_eval_set() -> list[dict]:
    if not EVAL_SET_PATH.exists():
        raise FileNotFoundError(
            f"{EVAL_SET_PATH} not found. Copy eval/retrieval_eval.json.example to "
            "eval/retrieval_eval.json and fill in 20-30 query/expected-case pairs "
            "by hand once you have seeded investigation cases."
        )
    return json.loads(EVAL_SET_PATH.read_text())


def precision_at_5(results: list[dict], expected_case_ids: list[str]) -> float:
    if not results:
        return 0.0
    top_5_ids = {r["case_id"] for r in results[:5]}
    hits = len(top_5_ids & set(expected_case_ids))
    return hits / min(5, len(results))


def main():
    eval_set = load_eval_set()
    retriever = Retriever()

    baseline_scores = []
    reranked_scores = []
    for item in eval_set:
        query = item["query"]
        expected = item["expected_case_ids"]

        baseline = retriever.retrieve(query, top_k=5, rerank=False)
        reranked = retriever.retrieve(query, top_k=5, rerank=True)

        baseline_scores.append(precision_at_5(baseline, expected))
        reranked_scores.append(precision_at_5(reranked, expected))

    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_reranked = sum(reranked_scores) / len(reranked_scores)

    print(f"Queries evaluated:             {len(eval_set)}")
    print(f"Precision@5 before reranking:  {avg_baseline:.3f}")
    print(f"Precision@5 after reranking:   {avg_reranked:.3f}")


if __name__ == "__main__":
    main()
