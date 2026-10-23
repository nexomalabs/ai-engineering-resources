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
    monkeypatch.setattr(main, "StandInAsyncClient", lambda: stand_in)


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
