"""Tests for Lab 6. Run against solution/ in CI.

The last test loads the embedding model; the first run downloads it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402


def test_rrf_rewards_agreement():
    fused = lab.reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]])
    assert fused[:2] == [1, 3]
    assert set(fused) == {1, 2, 3, 4}


def test_rrf_scores_follow_the_formula():
    fused = lab.reciprocal_rank_fusion([[7, 8], [8]], k=60)
    assert fused == [8, 7]  # 1/62 + 1/61 beats 1/61


def test_recall_divides_by_relevant_count():
    assert lab.recall_at_k({1, 2}, [1, 9, 9, 9, 9], k=5) == 0.5
    assert lab.recall_at_k({1, 2, 3, 4}, [1, 2, 3, 4, 5], k=5) == 1.0
    assert lab.recall_at_k(set(), [1], k=5) == 0.0


def test_recall_counts_only_the_top_k():
    assert lab.recall_at_k({6}, [1, 2, 3, 4, 5, 6], k=5) == 0.0


def test_bm25_finds_the_keyword_match():
    bm25 = lab.build_bm25(lab.CORPUS)
    assert lab.bm25_retrieve(bm25, "how does BM25 work for information retrieval", k=1) == [6]


def test_full_evaluation_reports_measured_results(capsys):
    lab.evaluate(lab.CORPUS, lab.TEST_QUERIES)
    out = capsys.readouterr().out
    assert "Mean Recall@5                                     0.69     0.75     0.75" in out
    assert "Hybrid retrieval matches the better single method." in out
