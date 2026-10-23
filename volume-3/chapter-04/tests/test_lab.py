"""Tests for Lab 4. Run against solution/ in CI. The first run downloads all-MiniLM-L6-v2."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from rag_system import (  # noqa: E402
    KNOWLEDGE_BASE,
    RAGGenerator,
    RAGIndexer,
    RAGRetriever,
    mock_llm_call,
)


@pytest.fixture(scope="module")
def retriever():
    indexer = RAGIndexer()
    indexer.index(KNOWLEDGE_BASE)
    return RAGRetriever(indexer)


def ids(results):
    return [doc.doc_id for doc, _ in results]


def test_every_passage_is_indexed_with_a_unit_vector(retriever):
    docs = retriever.indexer.documents
    assert len(docs) == 12
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
