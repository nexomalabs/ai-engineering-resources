"""Tests for Lab 4. Run against solution/ in CI. The first run downloads all-MiniLM-L6-v2."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from datetime import date  # noqa: E402

from rag_system import (  # noqa: E402
    KNOWLEDGE_BASE,
    RAGDocument,
    RAGGenerator,
    RAGIndexer,
    RAGRetriever,
    in_force,
    mock_llm_call,
)

BATTERY_QUERY = "Can I ship a laptop with a lithium battery by air?"


@pytest.fixture(scope="module")
def retriever():
    indexer = RAGIndexer()
    indexer.index(KNOWLEDGE_BASE)
    return RAGRetriever(indexer)


def ids(results):
    return [doc.doc_id for doc, _ in results]


def test_every_passage_is_indexed_with_a_unit_vector(retriever):
    docs = retriever.indexer.documents
    assert len(docs) == 14
    for doc in docs:
        assert abs(float((doc.embedding**2).sum()) - 1.0) < 1e-4


def test_jwt_query_finds_the_security_guide(retriever):
    results = retriever.retrieve("How does JWT token authentication work?")
    assert ids(results)[:2] == ["kb005", "kb006"]


def test_get_post_query_finds_both_rest_passages(retriever):
    results = retriever.retrieve("What is the difference between GET and POST requests?")
    assert set(ids(results)[:2]) == {"kb003", "kb004"}


def test_docker_query_ranks_volumes_first(retriever):
    assert ids(retriever.retrieve("How do I persist data in Docker containers?"))[0] == "kb010"


def test_scores_descend_and_top_k_is_respected(retriever):
    results = retriever.retrieve("database indexes", top_k=5)
    scores = [score for _, score in results]
    assert len(results) == 5
    assert scores == sorted(scores, reverse=True)


def test_in_force_respects_both_dates():
    old = RAGDocument("a", "s", "t", effective_from="2023-03-01", superseded_on="2025-04-01")
    new = RAGDocument("b", "s", "t", effective_from="2025-04-01")
    undated = RAGDocument("c", "s", "t")
    assert in_force(old, date(2024, 6, 1)) and not in_force(new, date(2024, 6, 1))
    assert not in_force(old, date(2025, 4, 1)) and in_force(new, date(2025, 4, 1))
    assert not in_force(new, date(2025, 3, 31))
    assert in_force(undated, date(2020, 1, 1))


def test_unfiltered_search_ranks_the_superseded_policy_first(retriever):
    # The chapter's opening story: the most similar text is the out-of-date policy
    results = retriever.retrieve(BATTERY_QUERY, top_k=2, in_force_only=False)
    assert ids(results) == ["kb013", "kb014"]


def test_in_force_filter_keeps_the_superseded_policy_out(retriever):
    results = retriever.retrieve(BATTERY_QUERY, top_k=3, as_of=date(2026, 10, 1))
    assert ids(results)[0] == "kb014"
    assert "kb013" not in ids(results)


def test_searching_as_of_an_earlier_date_finds_the_policy_then_in_force(retriever):
    results = retriever.retrieve(BATTERY_QUERY, top_k=3, as_of=date(2024, 6, 1))
    assert ids(results)[0] == "kb013"
    assert "kb014" not in ids(results)


def test_generator_numbers_the_context_and_cites_it(retriever):
    query = "How do I persist data in Docker containers?"
    result = RAGGenerator().generate(query, retriever.retrieve(query))
    assert [s["rank"] for s in result["sources"]] == [1, 2, 3]
    assert "[1], [2]" in result["answer"]


def test_mock_llm_reads_the_question_and_the_citations():
    prompt = (
        "## RETRIEVED CONTEXT\n\n[1] Source: A\nx\n\n[2] Source: B\ny\n\n## USER QUESTION\nWhy?"
    )
    answer = mock_llm_call(prompt)
    assert answer.startswith("Based on the retrieved context, why ")
    assert "[1], [2]" in answer
