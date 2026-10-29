"""Tests for Lab 5. Run against solution/ in CI, with the stand-in model (no key, no Docker)."""

import os
import sys
from pathlib import Path

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
os.environ.setdefault("SERVICE_VERSION", "test")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solution"))

from app import main  # noqa: E402
from app.canary import Canary  # noqa: E402
from app.stand_in import StandInAsyncClient  # noqa: E402


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def test_health_reports_version_and_model(client):
    body = client.get("/health").json()
    assert body == {
        "status": "healthy",
        "version": "test",
        "environment": "development",
        "model": "gpt-6-luna",
    }


def test_ready(client):
    assert client.get("/ready").json() == {"status": "ready"}


@pytest.mark.parametrize(
    "task, expected",
    [
        ("summarize", "Summary: Artificial intelligence is transforming enterprise operations."),
        ("classify", "article"),
    ],
)
def test_analyze_returns_result_and_usage(client, task, expected):
    text = "Artificial intelligence is transforming enterprise operations. It is fast."
    r = client.post("/api/v1/analyze", json={"text": text, "task": task})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == expected
    assert body["model_used"] == "stand-in"
    assert body["prompt_tokens"] > 0 and body["completion_tokens"] > 0


@pytest.mark.parametrize(
    "payload",
    [
        {"text": "", "task": "summarize"},
        {"text": "Test content", "task": "invalid_task_xyz"},
        {"text": "x" * 10001},
    ],
)
def test_invalid_input_is_rejected_with_422(client, payload):
    assert client.post("/api/v1/analyze", json=payload).status_code == 422


def _raise(error):
    async def create(**_kwargs):
        raise error

    return create


def _patch_client(monkeypatch, error):
    stand_in = StandInAsyncClient()
    stand_in.chat.completions.create = _raise(error)
    monkeypatch.setattr(main, "StandInAsyncClient", lambda **_: stand_in)


def test_rate_limit_maps_to_429_with_retry_after(client, monkeypatch):
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com"))
    _patch_client(monkeypatch, openai.RateLimitError("slow down", response=response, body=None))
    r = client.post("/api/v1/analyze", json={"text": "hello"})
    assert r.status_code == 429 and r.headers["retry-after"] == "60"


def test_upstream_error_maps_to_502_without_details(client, monkeypatch):
    request = httpx.Request("POST", "https://api.openai.com")
    _patch_client(monkeypatch, openai.APIError("secret internal detail", request, body=None))
    r = client.post("/api/v1/analyze", json={"text": "hello"})
    assert r.status_code == 502
    assert r.json() == {"detail": "Upstream AI service error"}


def test_live_mode_refuses_to_start_without_a_key(monkeypatch):
    monkeypatch.setenv("NEXOMA_LAB_MODE", "live")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        with TestClient(main.app):
            pass


def test_the_canary_gets_its_share_of_traffic():
    canary = Canary("stable-model", "canary-model", 5, seed=1)
    tracks = [canary.route()[0] for _ in range(4000)]
    assert 0.04 < tracks.count("canary") / len(tracks) < 0.06


def test_a_canary_costing_nearly_twice_as_much_is_rolled_back():
    canary = Canary("stable-model", "canary-model", 5, seed=1)
    for _ in range(100):
        canary.record("stable", prompt_tokens=60, completion_tokens=20)
    reasons = [canary.record("canary", prompt_tokens=60, completion_tokens=50) for _ in range(20)]
    assert reasons[-1].startswith("cost per request is 1.9x")
    assert canary.percent == 0 and canary.route()[0] == "stable"


def test_a_canary_within_its_limits_keeps_its_traffic():
    canary = Canary("stable-model", "canary-model", 5, seed=1)
    for _ in range(100):
        canary.record("stable", prompt_tokens=60, completion_tokens=20)
    for _ in range(40):
        assert canary.record("canary", prompt_tokens=60, completion_tokens=24) == ""
    assert canary.percent == 5


def test_a_failing_canary_is_rolled_back():
    canary = Canary("stable-model", "canary-model", 5, seed=1)
    for _ in range(100):
        canary.record("stable", prompt_tokens=60, completion_tokens=20)
    for i in range(20):
        canary.record("canary", error=i % 4 == 0)
    assert canary.rollback_reason.startswith("error rate 25.0%")


def test_the_service_rolls_back_a_canary_that_writes_longer_replies(monkeypatch):
    monkeypatch.setenv("CANARY_MODEL", "wren-model-next")
    monkeypatch.setenv("CANARY_PERCENT", "50")
    monkeypatch.setenv("CANARY_SEED", "3")
    with TestClient(main.app) as c:
        for _ in range(60):
            assert (
                c.post("/api/v1/analyze", json={"text": "Where is my parcel?"}).status_code == 200
            )
        status = c.get("/canary").json()
    assert status["rolled_back"] and status["canary_percent"] == 0
    assert status["rollback_reason"].startswith("cost per request")


def test_without_a_canary_all_traffic_is_stable(client):
    client.post("/api/v1/analyze", json={"text": "Where is my parcel?"})
    status = client.get("/canary").json()
    assert status["canary_model"] == "" and status["canary_percent"] == 0
    assert status["stable"]["requests"] == 1 and status["canary"]["requests"] == 0
