"""Tests for Lab 4. Run against solution/ in CI."""

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402

REAL_SLEEP = asyncio.sleep


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    lab.action_log.clear()
    published, waits = [], []

    async def publish(event_type, payload):
        published.append((event_type, payload))

    async def sleep(seconds):
        waits.append(seconds)
        await REAL_SLEEP(0)

    monkeypatch.setattr(lab.bus, "publish", publish)
    monkeypatch.setattr(lab.asyncio, "sleep", sleep)
    return published, waits


def flaky(failures, result):
    calls = {"n": 0}

    async def classify(text, fail_probability=0.2):
        calls["n"] += 1
        if calls["n"] <= failures:
            raise ConnectionError("transient")
        return result

    return classify, calls


def classify_file(tmp_path, monkeypatch, classifier):
    path = tmp_path / "doc.txt"
    path.write_text("Invoice from vendor", encoding="utf-8")
    monkeypatch.setattr(lab, "classify_document", classifier)
    asyncio.run(lab.on_classify_document({"file_id": "f-1", "filepath": str(path)}))


def actions():
    return [e["action"] for e in lab.action_log]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("This Software License Agreement is between...", "contract"),
        ("Invoice #00123 — Vendor: TechSupply LLC — $4,500", "invoice"),
        ("Q3 Operations Report — Revenue up 12% YoY...", "report"),
        ("Hi team, following up on the open action items...", "correspondence"),
        ("XYZ 9182 beta gamma delta epsilon zeta theta", "unknown"),
    ],
)
def test_classifier_reads_the_text(text, expected):
    out = asyncio.run(lab.classify_document(text, fail_probability=0.0))
    assert out["type"] == expected


def test_retry_succeeds_after_transient_failures(tmp_path, monkeypatch, fresh_state):
    published, waits = fresh_state
    classifier, calls = flaky(2, {"type": "invoice", "confidence": 0.99})
    classify_file(tmp_path, monkeypatch, classifier)
    assert calls["n"] == 3
    assert waits == [2, 4]
    assert [e for e, _ in published] == ["route_document"]


def test_exhausted_retries_go_to_the_dead_letter_path(tmp_path, monkeypatch, fresh_state):
    published, waits = fresh_state
    classifier, calls = flaky(99, None)
    classify_file(tmp_path, monkeypatch, classifier)
    assert calls["n"] == 3
    assert waits == [2, 4]
    assert actions() == ["classification_failed"]
    assert published == [("routing_failed", {"file_id": "f-1", "reason": "transient"})]


def route(doc_type, confidence):
    payload = {
        "file_id": "f-2",
        "filepath": "x.txt",
        "classification": {"type": doc_type, "confidence": confidence},
    }
    asyncio.run(lab.on_route_document(payload))


def test_confident_classification_goes_to_its_handler():
    route("invoice", 0.99)
    assert actions() == ["routed", "invoice_processed", "pipeline_complete"]


def test_low_confidence_goes_to_review():
    route("invoice", 0.6)
    assert actions() == ["routed", "routed_to_review", "pipeline_complete"]


def test_dead_letter_is_logged():
    asyncio.run(lab.on_routing_failed({"file_id": "f-3", "reason": "down"}))
    assert lab.action_log[-1]["action"] == "dead_letter"


def test_audit_entries_have_utc_timestamps():
    lab.log_action("f-4", "file_received", "a.txt")
    assert lab.action_log[-1]["timestamp"].endswith("+00:00")
