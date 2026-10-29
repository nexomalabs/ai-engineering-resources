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


def test_mrr_is_the_reciprocal_rank_of_the_first_hit():
    assert lab.mrr({16}, [16, 15]) == 1.0
    assert lab.mrr({16}, [15, 17, 16]) == 1 / 3
    assert lab.mrr({16}, [15, 17]) == 0.0


def test_bm25_finds_the_keyword_match():
    bm25 = lab.build_bm25(lab.CORPUS)
    assert lab.bm25_retrieve(bm25, "how does BM25 work for information retrieval", k=1) == [6]


def test_route_codes_dense_picks_the_wrong_bulletin_and_fusion_fixes_it():
    query = "is route R-417 delayed"  # bulletin 16 is R-417; bulletin 15 is R-471
    bm25 = lab.build_bm25(lab.CORPUS)
    model = lab.SentenceTransformer("all-MiniLM-L6-v2")
    index = lab.build_dense_index(lab.CORPUS, model)
    bm25_results = lab.bm25_retrieve(bm25, query, 10)
    dense_results = lab.dense_retrieve(query, model, index, 10)
    assert bm25_results[0] == 16
    assert dense_results[0] == 15
    assert lab.reciprocal_rank_fusion([bm25_results, dense_results])[0] == 16


def test_full_evaluation_reports_measured_results(capsys):
    lab.evaluate(lab.CORPUS, lab.TEST_QUERIES)
    out = capsys.readouterr().out
    assert "is route R-417 delayed               1.00   1.00   1.00     1.00   0.33   1.00" in out
    assert "Mean                                 0.79   0.83   0.83     1.00   0.89   1.00" in out
    assert "By Recall@5, hybrid retrieval matches the better single method." in out
    assert "By MRR, hybrid retrieval matches the better single method." in out
