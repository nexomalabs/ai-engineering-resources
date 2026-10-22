"""Tests for Lab 14. Run against solution/ in CI."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import multi_agent_pipeline as mp  # noqa: E402
from multi_agent_pipeline import (  # noqa: E402
    AgentMessage,
    Orchestrator,
    ResearcherAgent,
    ResultStore,
    TaskQueue,
    WriterAgent,
    run_pipeline,
)


def test_queue_orders_by_priority():
    q = TaskQueue()
    q.enqueue(AgentMessage(payload={"n": "low"}, priority=9))
    q.enqueue(AgentMessage(payload={"n": "high"}, priority=1))
    assert q.dequeue().payload["n"] == "high"


def test_queue_survives_ties():
    q = TaskQueue()
    q.enqueue(AgentMessage(payload={"n": 1}, timestamp="same"))
    q.enqueue(AgentMessage(payload={"n": 2}, timestamp="same"))
    assert [q.dequeue().payload["n"], q.dequeue().payload["n"]] == [1, 2]


def test_requeue_in_flight_returns_unacknowledged_messages():
    q = TaskQueue()
    q.enqueue(AgentMessage())
    q.dequeue()
    assert q.size() == 0
    assert q.requeue_in_flight() == 1
    assert q.size() == 1


def test_result_store_round_trip():
    store = ResultStore()
    store.write("k", "v")
    assert store.read("k") == "v" and store.read("missing") is None


def test_pipeline_report_lists_every_finding(capsys):
    report = run_pipeline()
    lines = report.splitlines()
    assert lines[0] == "AI advances in 2024"
    assert [line[:20] for line in lines if line.startswith("- ")] == [
        "- The EU AI Act, the",
        "- The 2024 Nobel Pri",
        "- The 2024 Nobel Pri",
    ]


def test_writer_reads_sources_in_order():
    store = ResultStore()
    store.write("a", "first")
    store.write("b", "second")
    writer = WriterAgent("writer", TaskQueue(), TaskQueue(), store)
    out = writer.handle(AgentMessage(payload={"title": "T", "sources": ["b", "a"]}))
    assert out == "T\n\n- second\n- first"


def test_a_failing_task_is_reported_as_an_error(monkeypatch, capsys):
    def boom(query):
        raise RuntimeError("search backend down")

    monkeypatch.setattr(mp, "web_search", boom)
    tasks, inbox, store = TaskQueue(), TaskQueue(), ResultStore()
    worker = ResearcherAgent("researcher", tasks, inbox, store)
    worker.start()
    try:
        with pytest.raises(RuntimeError, match="search backend down"):
            Orchestrator(tasks, inbox, store).run("goal", ["EU AI Act"])
    finally:
        worker.stopped.set()
        worker.join(timeout=1)


def test_replies_are_matched_by_correlation_id(capsys):
    tasks, inbox, store = TaskQueue(), TaskQueue(), ResultStore()
    orch = Orchestrator(tasks, inbox, store)
    sent = orch.send("researcher", {"query": "x"})
    inbox.enqueue(
        AgentMessage(sender_id="researcher", message_type="result", correlation_id="unrelated")
    )
    inbox.enqueue(
        AgentMessage(sender_id="researcher", message_type="result", correlation_id=sent.message_id)
    )
    replies = orch.wait_for([sent], timeout=2)
    assert list(replies) == [sent.message_id]
