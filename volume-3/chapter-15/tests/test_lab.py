"""Tests for Lab 15. Run against solution/ in CI."""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import async_agents as aa  # noqa: E402
from async_agents import AgentBus, MessageEnvelope, MessageLog, main  # noqa: E402


def test_envelope_round_trips_through_json():
    msg = MessageEnvelope(
        sender_id="a",
        recipient_id="b",
        message_type="task",
        payload={"args": {"query": "x"}},
        correlation_id="c1",
    )
    assert MessageEnvelope.from_json(msg.to_json()) == msg


def test_expiry():
    old = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    assert MessageEnvelope(timestamp=old, ttl_seconds=5).is_expired()
    assert not MessageEnvelope(timestamp=old, ttl_seconds=0).is_expired()


def test_log_summary_handles_messages_without_correlation():
    log = MessageLog()
    log.record(MessageEnvelope(sender_id="a", recipient_id="b", message_type="status"))
    assert "corr=-" in log.summary()


def test_demo_completes_with_retries_and_reassignment(capsys):
    orch = asyncio.run(main(seed=8))
    assert orch.results["S"].startswith("Python was created by Guido van Rossum")
    assert orch.results["C"].startswith("The Eiffel Tower")
    assert orch.reassigned == ["A", "C"]
    assert orch.retries == 2


def test_no_loss_means_no_retries(capsys):
    orch = asyncio.run(main(seed=1, drop_rate=0.0))
    assert orch.retries == 0
    assert orch.reassigned == ["C"]  # alpha still crashes after its first task


def test_failure_is_reported_once(capsys):
    asyncio.run(main(seed=8))
    assert capsys.readouterr().out.count("[MONITOR] alpha appears to have failed") == 1


async def _one_task(bus, msg, calls_before):
    agent = asyncio.create_task(aa.run_agent("beta", "analyst", bus))
    await bus.send(msg)
    await bus.send(msg)  # the same task, resent
    replies = [await asyncio.wait_for(bus.inbox("orchestrator").get(), 2) for _ in range(2)]
    agent.cancel()
    return replies


def test_resent_task_runs_once(monkeypatch, capsys):
    calls = []
    real = aa.perform
    monkeypatch.setattr(aa, "perform", lambda args: calls.append(args) or real(args))
    bus = AgentBus(rng=random.Random(0))
    for name in ("beta", "orchestrator", "monitor"):
        bus.register(name)
    msg = MessageEnvelope(
        sender_id="orchestrator",
        recipient_id="beta",
        reply_to="orchestrator",
        message_type="task",
        correlation_id="X",
        payload={"args": {"expression": "2 + 2"}},
    )
    replies = asyncio.run(_one_task(bus, msg, calls))
    assert [r.payload["result"] for r in replies] == ["4", "4"]
    assert len(calls) == 1


async def _expired(bus, msg):
    agent = asyncio.create_task(aa.run_agent("beta", "analyst", bus))
    await bus.send(msg)
    await asyncio.sleep(0.5)
    agent.cancel()
    return bus.inbox("orchestrator").qsize()


def test_expired_task_is_skipped(capsys):
    bus = AgentBus()
    for name in ("beta", "orchestrator", "monitor"):
        bus.register(name)
    old = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    msg = MessageEnvelope(
        sender_id="orchestrator",
        recipient_id="beta",
        reply_to="orchestrator",
        message_type="task",
        correlation_id="old",
        timestamp=old,
        ttl_seconds=30,
        payload={"args": {"expression": "1"}},
    )
    assert asyncio.run(_expired(bus, msg)) == 0
    assert "skipped expired old" in capsys.readouterr().out
