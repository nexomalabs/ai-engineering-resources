"""Tests for Lab 7. Run against solution/ in CI.

Tests that build the compressor load the embedding model; the first run downloads it.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402


@pytest.fixture(scope="module")
def result():
    compressor = lab.ExtractiveSentenceCompressor()
    return compressor.compress(lab.LONG_CONTEXT, lab.QUERY, lab.TOKEN_BUDGET)


def test_sentences_are_split_joined_and_filtered():
    text = "First sentence here.\nIt continues on. Short. Another full sentence!"
    assert lab.sentence_tokenize(text) == [
        "First sentence here.",
        "It continues on.",
        "Another full sentence!",
    ]


def test_budget_is_respected(result):
    assert result["compressed_tokens"] <= lab.TOKEN_BUDGET
    assert result["compression_ratio"] > 0.4


def test_kept_sentences_stay_in_document_order(result):
    sentences = lab.sentence_tokenize(lab.LONG_CONTEXT)
    kept = [s for s in sentences if s in result["text"]]
    positions = [result["text"].index(s) for s in kept]
    assert positions == sorted(positions)


def test_top_sentences_are_sorted_by_score(result):
    scores = [score for _, score in result["top_sentences"]]
    assert scores == sorted(scores, reverse=True)
    assert result["top_sentences"][0][0].startswith("Evaluation campaigns like TREC")


def test_best_first_beats_truncation_on_relevance(result):
    # The best-matching sentence is in the last paragraph: truncation to 400 tokens drops it
    assert "Evaluation campaigns like TREC" in result["text"]


def test_measured_terms(result):
    text = result["text"].lower()
    found = [t for t in ["precision", "recall", "MRR", "NDCG", "F1"] if t.lower() in text]
    assert found == ["precision", "recall", "NDCG"]
