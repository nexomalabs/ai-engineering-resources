"""Tests for Lab 5. Run against solution/ in CI.

Tests that encode text load the embedding model; the first run downloads it.
"""

import sys
from pathlib import Path

import faiss
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402


@pytest.fixture(scope="module")
def encoded():
    return lab.encode_corpus(lab.CORPUS)


def test_recall_against_exact_results():
    flat = [{"passage_id": i} for i in (1, 2, 3)]
    assert lab.compute_recall(flat, [{"passage_id": i} for i in (1, 2, 3)]) == 1.0
    assert lab.compute_recall(flat, [{"passage_id": i} for i in (1, 9, 8)]) == pytest.approx(1 / 3)
    assert lab.compute_recall([], []) == 0.0


def test_embeddings_are_normalized(encoded, capsys):
    embeddings, _ = encoded
    assert embeddings.shape == (15, 384)
    assert np.allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-5)


def test_flat_search_finds_the_asyncio_passage(encoded, capsys):
    embeddings, model = encoded
    index = lab.build_flat_index(embeddings)
    top = lab.search_index(
        index, "How does Python handle concurrent programming?", model, lab.CORPUS, k=1
    )
    assert "asyncio" in top[0]["passage"]


def test_hnsw_matches_flat_on_a_small_corpus(encoded, capsys):
    embeddings, model = encoded
    flat, hnsw = lab.build_flat_index(embeddings), lab.build_hnsw_index(embeddings)
    q = "What security protocol protects data in transit?"
    assert (
        lab.compute_recall(
            lab.search_index(flat, q, model, lab.CORPUS),
            lab.search_index(hnsw, q, model, lab.CORPUS),
        )
        == 1.0
    )


def test_placeholder_results_are_skipped(encoded, capsys):
    embeddings, model = encoded
    small = faiss.IndexFlatIP(embeddings.shape[1])
    small.add(embeddings[:2])
    results = lab.search_index(small, "anything", model, lab.CORPUS, k=5)
    assert len(results) == 2
    assert all(r["passage_id"] in (0, 1) for r in results)


def test_index_round_trips_through_disk(encoded, tmp_path, capsys):
    embeddings, _ = encoded
    path = str(tmp_path / "corpus.index")
    faiss.write_index(lab.build_hnsw_index(embeddings), path)
    assert faiss.read_index(path).ntotal == 15
