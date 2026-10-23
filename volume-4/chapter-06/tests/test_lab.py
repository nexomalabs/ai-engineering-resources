"""Tests for Lab 6. Run against solution/ in CI, with the simulated API sped up 100x."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
os.environ["NEXOMA_LATENCY_SCALE"] = "0.01"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solution"))

import lab06_benchmark as lab  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_cache():
    lab._cache.clear()
    lab._in_flight.clear()


@pytest.fixture
def call_log(monkeypatch):
    """Record each real model call, and the most that were in flight at once."""
    log = {"calls": 0, "active": 0, "peak": 0}
    original = lab._call_model

    async def counting(prompt, model, max_tokens):
        log["calls"] += 1
        log["active"] += 1
        log["peak"] = max(log["peak"], log["active"])
        try:
            return await original(prompt, model, max_tokens)
        finally:
            log["active"] -= 1

    monkeypatch.setattr(lab, "_call_model", counting)
    return log


def run(coro):
    return asyncio.run(coro)


def test_second_request_is_served_from_cache(call_log):
    async def twice():
        first = await lab.cached_complete("hello")
        second = await lab.cached_complete("hello")
        return first, second

    first, second = run(twice())
    assert first[1] == lab.MISS and second[1] == lab.FROM_CACHE
    assert second[2:] == (0, 0) and call_log["calls"] == 1


def test_concurrent_duplicates_share_one_call(call_log):
    async def together():
        return await asyncio.gather(*[lab.cached_complete("same prompt") for _ in range(5)])

    results = run(together())
    assert call_log["calls"] == 1
    assert sorted(r[1] for r in results) == [lab.MISS] + [lab.SHARED] * 4


def test_no_cache_means_every_request_calls_the_model(call_log):
    result = run(lab.run_benchmark(["a", "a", "a"], use_cache=False))
    assert call_log["calls"] == 3 and result.cache_hits == result.shared_requests == 0


def test_mixed_set_saves_half_the_calls(call_log):
    result = run(lab.run_benchmark(lab.MIXED, concurrency=5))
    assert result.cache_hits + result.shared_requests == 20
    assert call_log["calls"] == 20


def test_cost_uses_usage_and_both_prices():
    result = run(lab.run_benchmark(["What is caching?"], use_cache=False))
    _, _, prompt_tokens, completion_tokens = run(
        lab.cached_complete("What is caching?", use_cache=False)
    )
    expected = (prompt_tokens * lab.INPUT_PER_1K + completion_tokens * lab.OUTPUT_PER_1K) / 1000
    assert result.total_tokens == prompt_tokens + completion_tokens
    assert result.total_cost_usd == pytest.approx(expected)


@pytest.mark.parametrize("concurrency", [1, 3, 7])
def test_concurrency_limit_is_respected(call_log, concurrency):
    run(lab.run_benchmark([f"p{i}" for i in range(15)], concurrency=concurrency, use_cache=False))
    assert call_log["peak"] == concurrency
