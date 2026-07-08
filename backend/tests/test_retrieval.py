from retrieval import bm25_search


def _case(case_id, content):
    return {
        "case_id": case_id,
        "content": content,
        "outcome": "confirmed_fraud",
        "transaction_id": "tx",
    }


def test_bm25_search_ranks_keyword_matches_first():
    cases = [
        _case("c1", "Large offshore wire transfer flagged as suspicious by the fraud team"),
        _case("c2", "Routine grocery purchase at a local supermarket"),
        _case("c3", "Customer disputed a subscription renewal charge"),
        _case("c4", "Card declined due to insufficient funds at checkout"),
    ]

    results = bm25_search(cases, "offshore wire transfer", top_k=2)

    assert results[0]["case_id"] == "c1"


def test_bm25_search_excludes_zero_score_cases():
    cases = [_case("c1", "unrelated content about groceries")]

    results = bm25_search(cases, "wire transfer fraud", top_k=5)

    assert results == []
