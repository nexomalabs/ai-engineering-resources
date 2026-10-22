"""Tests for Lab 13. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import ai_service_monitored as svc  # noqa: E402
from alert_evaluator import AlertEvaluator, AlertRule  # noqa: E402

client = TestClient(svc.app)


def sample(name, **labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


@pytest.fixture
def fast_model(monkeypatch):
    def call(prompt):
        return {
            "response": "ok",
            "tokens_in": 120,
            "tokens_out": 80,
            "quality_score": 0.9,
            "safety_triggered": True,
            "latency": 0.0,
        }

    monkeypatch.setattr(svc, "simulate_ai_call", call)


@pytest.fixture
def failing_model(monkeypatch):
    def call(prompt):
        raise ValueError("upstream_timeout")

    monkeypatch.setattr(svc, "simulate_ai_call", call)


def test_success_is_counted_with_tokens_quality_and_safety(fast_model):
    before = {
        "ok": sample("ai_requests_total", endpoint="complete", status="success"),
        "in": sample("ai_tokens_input_total", model="m1"),
        "out": sample("ai_tokens_output_total", model="m1"),
        "q": sample("ai_response_quality_score_count"),
        "safety": sample("ai_safety_filter_triggered_total", action="warned"),
    }
    resp = client.post("/v1/complete", json={"prompt": "hi", "model": "m1"})
    assert resp.status_code == 200
    assert resp.json()["usage"] == {"tokens_in": 120, "tokens_out": 80}
    assert sample("ai_requests_total", endpoint="complete", status="success") == before["ok"] + 1
    assert sample("ai_tokens_input_total", model="m1") == before["in"] + 120
    assert sample("ai_tokens_output_total", model="m1") == before["out"] + 80
    assert sample("ai_response_quality_score_count") == before["q"] + 1
    assert sample("ai_safety_filter_triggered_total", action="warned") == before["safety"] + 1


def test_failure_returns_503_and_is_counted(failing_model):
    errors = sample("ai_errors_total", error_type="upstream_timeout")
    resp = client.post("/v1/complete", json={"prompt": "hi"})
    assert resp.status_code == 503
    assert sample("ai_errors_total", error_type="upstream_timeout") == errors + 1


def test_in_flight_gauge_returns_to_zero_after_success_and_failure(fast_model, monkeypatch):
    client.post("/v1/complete", json={"prompt": "hi"})
    assert sample("ai_active_requests") == 0

    def call(prompt):
        raise ValueError("upstream_timeout")

    monkeypatch.setattr(svc, "simulate_ai_call", call)
    client.post("/v1/complete", json={"prompt": "hi"})
    assert sample("ai_active_requests") == 0


def test_metrics_endpoint_serves_prometheus_text(fast_model):
    client.post("/v1/complete", json={"prompt": "hi"})
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "ai_request_duration_seconds_bucket" in resp.text


def rule(name, value, threshold=5.0, comparison="gt"):
    return AlertRule(
        name=name,
        description="d",
        severity="high",
        metric_query="m",
        threshold=threshold,
        comparison=comparison,
        window_seconds=60,
        evaluator=lambda: value["v"],
    )


@pytest.mark.parametrize(
    ("op", "value", "fires"),
    [("gt", 5, False), ("gte", 5, True), ("lt", 4, True), ("lte", 6, False)],
)
def test_comparisons(op, value, fires):
    assert AlertEvaluator()._compare(value, 5, op) is fires


def test_alert_fires_once_and_then_resolves(capsys):
    value = {"v": 9.0}
    ev = AlertEvaluator()
    ev.add_rule(rule("too_high", value))
    assert [a.rule_name for a in ev.evaluate()] == ["too_high"]
    assert [a.rule_name for a in ev.evaluate()] == ["too_high"]
    assert capsys.readouterr().out.count("ALERT FIRING") == 1
    value["v"] = 1.0
    assert ev.evaluate() == []
    assert "too_high" not in ev.fired_alerts
    assert "ALERT RESOLVED: too_high" in capsys.readouterr().out


def test_failing_evaluator_is_skipped():
    ev = AlertEvaluator()
    ev.add_rule(AlertRule("broken", "d", "low", "m", 1.0, "gt", 60, lambda: 1 / 0))
    assert ev.evaluate() == []
