"""Tests for Lab 7. Run against solution/ in CI, with the simulated API sped up 20x."""

import asyncio
import glob
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
os.environ["NEXOMA_LATENCY_SCALE"] = "0.05"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solution"))

import pipeline_fast  # noqa: E402
import pipeline_slow  # noqa: E402
from documents import DOCUMENTS  # noqa: E402


def timed(fn):
    t0 = time.perf_counter()
    result = fn(DOCUMENTS)
    return result, time.perf_counter() - t0


def test_both_pipelines_produce_the_same_report():
    assert pipeline_slow.process_all_documents(DOCUMENTS) == pipeline_fast.process_all_documents(
        DOCUMENTS
    )


def test_report_covers_every_document_and_reads_the_sentiment():
    report = pipeline_fast.process_all_documents(DOCUMENTS)
    assert report.count("Document ") == len(DOCUMENTS)
    assert "Document 2\n  Sentiment: NEGATIVE" in report


def test_slow_pipeline_leaves_no_temporary_file_behind():
    before = set(glob.glob(os.path.join(tempfile.gettempdir(), "*.txt")))
    pipeline_slow.process_all_documents(DOCUMENTS[:1])
    assert set(glob.glob(os.path.join(tempfile.gettempdir(), "*.txt"))) <= before


def test_fast_pipeline_cuts_wall_time_by_more_than_half():
    _, slow = timed(pipeline_slow.process_all_documents)
    _, fast = timed(pipeline_fast.process_all_documents)
    assert fast < 0.5 * slow


def test_fast_pipeline_respects_the_in_flight_limit(monkeypatch):
    state = {"active": 0, "peak": 0}
    original = pipeline_fast.client.chat.completions.create

    async def counting(**kwargs):
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        try:
            return await original(**kwargs)
        finally:
            state["active"] -= 1

    monkeypatch.setattr(pipeline_fast.client.chat.completions, "create", counting)
    monkeypatch.setattr(pipeline_fast, "MAX_IN_FLIGHT", 4)
    asyncio.run(pipeline_fast.process_all_documents_async(DOCUMENTS))
    assert state["peak"] == 4
