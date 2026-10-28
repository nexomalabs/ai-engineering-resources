"""Tests for Lab 16. Run against solution/ in CI, with the stand-in model."""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import document_workflow as wf  # noqa: E402
import stand_in  # noqa: E402

MEMO = """
MEMORANDUM
To: All Staff | From: CEO | Date: July 27, 2026
Re: Remote Work Policy Update
Effective August 1, 2026, all employees may work remotely up to three days per week.
Please update your schedules in the HR portal by July 31.
"""
REPORT = """
Q2 2026 SALES REPORT — NEXOMA LABS LLC
Total Revenue: $6.1M (up 31% YoY)
Churn Rate: 2.1%
Recommendation: Increase SDR headcount by 4 to address pipeline volume.
"""


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    sleeps = []
    monkeypatch.setattr(wf.time, "sleep", sleeps.append)
    stand_in.reset()
    return sleeps


def test_retry_recovers_after_failures(no_waiting):
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("not yet")
        return "done"

    assert wf.retry(flaky, max_attempts=3, backoff=2.0) == "done"
    assert len(calls) == 3
    assert no_waiting == [1.0, 2.0]


def test_retry_gives_up_after_max_attempts():
    def always_fails():
        raise ValueError("broken")

    with pytest.raises(ValueError, match="broken"):
        wf.retry(always_fails, max_attempts=2)


def test_memo_runs_all_three_stages():
    ctx = wf.run_workflow(MEMO)
    assert ctx.succeeded
    assert ctx.classification["type"] == "memo"
    assert ctx.summary.startswith("Main point:")
    assert set(ctx.timings) == {"extract", "classify", "summarize"}


def test_report_recovers_from_a_malformed_classification(no_waiting):
    ctx = wf.run_workflow(REPORT)
    assert ctx.succeeded
    assert ctx.classification["type"] == "report"
    assert no_waiting == [1.0]
    assert "Recommendation" in ctx.summary


def test_classification_rejects_an_out_of_range_confidence(monkeypatch):
    monkeypatch.setattr(
        wf, "call_llm", lambda *a, **k: '{"type": "memo", "topic": "x", "confidence": 1.7}'
    )
    ctx = wf.DocumentContext(extracted_text="some text")
    with pytest.raises(ValueError, match="Confidence out of range"):
        wf.classify(ctx)


def test_retry_does_not_retry_errors_a_second_attempt_cannot_fix(no_waiting):
    calls = []

    def bad_key():
        calls.append(1)
        raise PermissionError("invalid API key")

    with pytest.raises(PermissionError):
        wf.retry(bad_key, max_attempts=3)
    assert len(calls) == 1 and no_waiting == []


def test_a_failed_stage_stops_the_pipeline():
    ctx = wf.run_workflow("too short")
    assert not ctx.succeeded
    assert ctx.errors[0]["stage"] == "extract"
    assert ctx.classification == {} and ctx.summary == ""
