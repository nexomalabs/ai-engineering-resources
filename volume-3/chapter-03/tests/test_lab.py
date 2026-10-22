"""Tests for Lab 3. Run against solution/ in CI."""

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import (  # noqa: E402
    EpisodicMemory,
    MemorySystem,
    SemanticMemory,
    WorkingMemory,
    cosine_similarity,
    mock_embed,
)


def test_embedding_is_deterministic_and_normalized():
    a, b = mock_embed("JWT tokens are signed"), mock_embed("JWT tokens are signed")
    assert np.array_equal(a, b)
    assert abs(float(np.linalg.norm(a)) - 1.0) < 1e-6


def test_shared_words_score_higher_than_unrelated_text():
    q = mock_embed("verify a JWT token")
    related = mock_embed("JWT tokens are verified with a secret")
    unrelated = mock_embed("Python uses indentation for blocks")
    assert cosine_similarity(q, related) > cosine_similarity(q, unrelated)


def test_stopwords_only_text_embeds_to_zero_and_scores_zero():
    v = mock_embed("what is the")
    assert not v.any()
    assert cosine_similarity(v, mock_embed("JWT")) == 0.0


def test_working_memory_keeps_only_the_last_turns():
    wm = WorkingMemory(max_turns=3)
    for i in range(5):
        wm.add_turn("user", f"turn {i}")
    assert [t["content"] for t in wm.turns] == ["turn 2", "turn 3", "turn 4"]
    assert wm.get_context().splitlines()[0] == "USER: turn 2"


def test_semantic_memory_deduplicates():
    sm = SemanticMemory()
    first = sm.store_fact("Alex prefers Python")
    again = sm.store_fact("Alex prefers Python")
    assert again is first
    assert len(sm.facts) == 1


def test_semantic_threshold_filters_unrelated_facts():
    sm = SemanticMemory()
    sm.store_fact("JWT tokens have three parts")
    sm.store_fact("Bananas are yellow")
    hits = sm.retrieve("How many parts does a JWT token have?", threshold=0.1)
    assert [f.content for f, _ in hits] == ["JWT tokens have three parts"]


def test_episodic_recency_breaks_a_tie():
    em = EpisodicMemory(recency_weight=0.3)
    now = time.time()
    em.store("Use PyJWT to decode tokens", timestamp=now - 1000)
    em.store("Use PyJWT to decode tokens", timestamp=now - 10)
    (newest, s1), (older, s2) = em.retrieve("PyJWT tokens", top_k=2)
    assert newest.timestamp > older.timestamp
    assert s1 > s2


def test_episodic_similarity_outweighs_a_little_recency():
    em = EpisodicMemory(recency_weight=0.3)
    now = time.time()
    em.store("Use PyJWT to decode JWT tokens", timestamp=now - 1000)
    em.store("The office closes at six", timestamp=now - 10)
    top, _ = em.retrieve("decode JWT tokens with PyJWT", top_k=1)[0]
    assert "PyJWT" in top.content


def test_recall_combines_all_three_stores():
    ms = MemorySystem()
    ms.learn_fact("JWT tokens consist of three base64-encoded parts", source="kb")
    ms.record_turn("user", "How do JWT tokens work?")
    ms.record_turn("assistant", "A JWT token is signed by the server.")
    out = ms.recall("Explain JWT tokens")
    assert "USER: How do JWT tokens work?" in out["working_memory"]
    assert out["episodic_memories"][0]["outcome"] == "delivered"
    assert out["semantic_memories"][0]["source"] == "kb"


def test_only_assistant_turns_become_episodes():
    ms = MemorySystem()
    ms.record_turn("user", "hello")
    ms.record_turn("assistant", "hi")
    assert [e.content for e in ms.episodic.episodes] == ["hi"]
