from pathlib import Path

from bfsi_crew.rag import PolicyIndex

POLICIES = Path(__file__).resolve().parents[1] / "data" / "policies"


def test_each_topic_retrieves_its_own_policy():
    index = PolicyIndex.from_directory(POLICIES)
    cases = {
        "minimum credit score threshold": "credit-score.md",
        "debt to income ratio limit": "debt-to-income.md",
        "loan to value ratio down payment": "loan-to-value.md",
        "employment history stability years": "employment-history.md",
        "adverse action reasons notice": "fair-lending.md",
    }
    for query, expected in cases.items():
        assert index.search(query, k=1)[0].source == expected, query


def test_results_are_ranked_and_limited():
    index = PolicyIndex.from_directory(POLICIES)
    hits = index.search("ratio limit", k=2)
    assert len(hits) <= 2
    assert hits == sorted(hits, key=lambda h: h.score, reverse=True)


def test_unrelated_query_returns_nothing():
    index = PolicyIndex.from_directory(POLICIES)
    assert index.search("zebra xylophone quasar") == []
