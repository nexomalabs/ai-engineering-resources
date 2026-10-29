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


from attribution import SCRIPT_USER, by_feature, simulate_peak_day, users_of  # noqa: E402

DAY = simulate_peak_day()


def test_the_warehouse_assistant_costs_most_although_wren_makes_the_most_calls():
    features = by_feature(DAY)
    assert next(iter(features)) == "warehouse_assistant"
    assert max(features, key=lambda f: features[f][0]) == "wren"


def test_one_user_makes_nearly_all_the_warehouse_cost_with_a_call_every_thirty_seconds():
    users = users_of(DAY, "warehouse_assistant")
    user, (calls, cost, night) = next(iter(users.items()))
    assert user == SCRIPT_USER
    assert calls == 24 * 60 * 2
    assert night == 6 * 60 * 2
    assert cost / sum(u[1] for u in users.values()) > 0.9


def test_people_do_not_use_the_warehouse_assistant_at_night():
    users = users_of(DAY, "warehouse_assistant")
    people = [u for name, u in users.items() if name != SCRIPT_USER]
    assert len(people) > 30
    assert all(night == 0 for _, _, night in people)


def test_replacing_the_script_with_a_query_roughly_halves_the_bill():
    after = [r for r in DAY if r.user_id != SCRIPT_USER]
    assert sum(r.cost_usd for r in after) < 0.55 * sum(r.cost_usd for r in DAY)
    assert next(iter(by_feature(after))) == "wren"
