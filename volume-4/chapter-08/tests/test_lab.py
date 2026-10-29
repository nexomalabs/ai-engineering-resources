"""Tests for Lab 8. Run against solution/ in CI, with the simulated API sped up 100x."""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
os.environ["NEXOMA_LATENCY_SCALE"] = "0.01"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solution"))

import lab08_benchmark as bench  # noqa: E402
import semantic_cache  # noqa: E402
from semantic_cache import SemanticCache  # noqa: E402


@pytest.fixture
def embed_calls(monkeypatch):
    calls = []
    original = semantic_cache.client.embeddings.create

    def counting(**kwargs):
        calls.append(kwargs["input"])
        return original(**kwargs)

    monkeypatch.setattr(semantic_cache.client.embeddings, "create", counting)
    return calls


def test_store_fills_both_levels():
    cache = SemanticCache()
    cache.store("What is gradient descent?", "answer")
    assert len(cache._exact) == 1 and len(cache._semantic) == 1


def test_exact_key_ignores_case_and_surrounding_spaces():
    cache = SemanticCache()
    cache.store("What is gradient descent?", "answer")
    assert cache.lookup("  WHAT IS GRADIENT DESCENT?  ") == "answer"
    assert cache.stats["exact_hits"] == 1


def test_paraphrase_with_the_same_key_words_is_a_semantic_hit():
    cache = SemanticCache()
    cache.store("What is gradient descent?", "answer")
    assert cache.lookup("Can you explain gradient descent?") == "answer"
    assert cache.stats["semantic_hits"] == 1


def test_reworded_paraphrase_misses_at_the_default_threshold():
    cache = SemanticCache()
    cache.store("What is the vanishing gradient problem?", "answer")
    assert cache.lookup("Why do gradients vanish in deep networks?") is None
    assert cache.stats["misses"] == 1


def test_lower_threshold_accepts_looser_matches():
    cache = SemanticCache(similarity_threshold=0.5)
    cache.store("What is the difference between precision and recall?", "answer")
    assert cache.lookup("Explain precision versus recall.") == "answer"


def test_semantic_hit_is_promoted_to_the_exact_level(embed_calls):
    cache = SemanticCache()
    cache.store("What is gradient descent?", "answer")
    cache.lookup("Can you explain gradient descent?")
    calls_before = len(embed_calls)
    assert cache.lookup("Can you explain gradient descent?") == "answer"
    assert len(embed_calls) == calls_before
    assert cache.stats["exact_hits"] == 1


def test_full_dataset():
    cache, results = bench.run()
    assert cache.stats == {"exact_hits": 10, "semantic_hits": 6, "misses": 34}
    assert cache.hit_rate() == pytest.approx(0.32)
    sources = [r["source"] for r in results]
    assert sources[:10] == ["llm"] * 10 and sources[20:30] == ["exact_cache"] * 10


def test_destinations_are_read_from_the_question():
    assert semantic_cache.destinations("Can I send batteries to Canada?") == frozenset({"canada"})
    assert semantic_cache.destinations("What is gradient descent?") == frozenset()


def test_a_threshold_cannot_tell_the_countries_apart():
    cache = SemanticCache()
    china = cache._embed(bench.QUESTION.format("China"))
    canada = cache._embed(bench.QUESTION.format("Canada"))
    paraphrase = cache._embed(bench.CHINA_PARAPHRASE)
    assert cache._cosine_similarity(china, canada) >= cache.threshold
    assert cache._cosine_similarity(china, canada) >= cache._cosine_similarity(china, paraphrase)


def test_similarity_alone_gives_canada_the_answer_for_china(capsys):
    answers = bench.battery_incident()
    assert answers["similarity alone"] == "[the answer written for China's rules]"
    assert answers["with the country rule"] is None


def test_the_country_rule_still_reuses_answers_for_the_same_country():
    cache = SemanticCache()
    cache.store(bench.QUESTION.format("China"), "china answer")
    assert cache.lookup(bench.CHINA_PARAPHRASE) == "china answer"
    assert cache.lookup(bench.QUESTION.format("Canada")) is None
