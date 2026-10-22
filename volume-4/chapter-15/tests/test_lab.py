"""Tests for Lab 15. Run against solution/ in CI."""

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from cost_analyzer import CostAnalyzer, OptimizationSimulator  # noqa: E402
from cost_tracker import PRICING, RequestRecord, generate_sample_requests  # noqa: E402


def record(model="gpt-6.1-sol", tokens_in=1000, tokens_out=500, feature="faq", cached=False):
    return RequestRecord("r", model, tokens_in, tokens_out, feature, "u", cached=cached)


def test_pricing_charges_input_and_output_separately():
    assert PRICING["gpt-6.1-sol"].cost(1_000_000, 0) == pytest.approx(2.00)
    assert PRICING["gpt-6.1-sol"].cost(0, 1_000_000) == pytest.approx(10.00)
    assert record().cost_usd == pytest.approx(0.002 + 0.005)


def test_cached_request_costs_nothing():
    assert record(cached=True).cost_usd == 0.0


def test_unknown_model_falls_back_to_sol_prices():
    assert record(model="mystery").cost_usd == record().cost_usd


def test_sample_generation_is_reproducible_with_a_seed():
    random.seed(1)
    a = generate_sample_requests(50)
    random.seed(1)
    b = generate_sample_requests(50)
    assert [r.cost_usd for r in a] == [r.cost_usd for r in b]


def test_breakdowns_add_up_and_are_sorted():
    random.seed(2)
    analyzer = CostAnalyzer(generate_sample_requests(200))
    by_feature = analyzer.cost_by_feature()
    assert sum(by_feature.values()) == pytest.approx(analyzer.total_cost())
    assert list(by_feature.values()) == sorted(by_feature.values(), reverse=True)
    assert sum(analyzer.cost_by_model().values()) == pytest.approx(analyzer.total_cost())


def test_monthly_projection_scales_the_sample():
    analyzer = CostAnalyzer([record(), record()])
    assert analyzer.monthly_projection(sample_days=1) == pytest.approx(analyzer.total_cost() * 30)
    assert analyzer.monthly_projection(sample_days=2) == pytest.approx(analyzer.total_cost() * 15)


def test_compression_reduces_input_tokens_only():
    sim = OptimizationSimulator([record(tokens_in=1000, tokens_out=500)])
    (compressed,), cost = sim.simulate_prompt_compression(0.25)
    assert compressed.tokens_in == 750
    assert compressed.tokens_out == 500
    assert cost == pytest.approx(PRICING["gpt-6.1-sol"].cost(750, 500))


def test_compression_saves_less_than_its_ratio_when_output_costs_more():
    sim = OptimizationSimulator([record(tokens_in=1000, tokens_out=500)])
    _, cost = sim.simulate_prompt_compression(0.25)
    saving = 1 - cost / sim.baseline_cost
    assert 0 < saving < 0.25


def test_routing_moves_only_sol_requests():
    random.seed(3)
    sim = OptimizationSimulator([record(), record(model="gpt-6-luna")])
    routed, _ = sim.simulate_model_downgrade(downgrade_fraction=1.0)
    assert [r.model_id for r in routed] == ["gpt-6-luna", "gpt-6-luna"]


def test_full_cache_hit_rate_costs_nothing():
    sim = OptimizationSimulator([record(), record()])
    _, cost = sim.simulate_semantic_caching(cache_hit_rate=1.0)
    assert cost == 0.0
