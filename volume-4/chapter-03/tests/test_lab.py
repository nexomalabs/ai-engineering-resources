"""Tests for Lab 3. Run against solution/ in CI."""

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import lab  # noqa: E402
from lab import (  # noqa: E402
    DocState,
    Document,
    DocumentWorkflowEngine,
    NotificationService,
)

SLA = 0.2 / 60  # minutes; the monitors multiply by 60


class RecordingNotifier(NotificationService):
    def __init__(self):
        self.sent = []

    async def notify(self, to, subject, body):
        self.sent.append((to, subject))


@pytest.fixture(autouse=True)
def fast_ai_review(monkeypatch):
    async def review(doc):
        doc.ai_summary, doc.ai_risk_score = "ok", 0.1

    monkeypatch.setattr(lab, "ai_review_document", review)


def run(coro):
    return asyncio.run(coro)


def test_states_print_as_their_values():
    assert f"{DocState.PENDING_REVIEW}" == "pending_review"


def test_illegal_transition_is_refused():
    doc = Document(title="t")
    with pytest.raises(ValueError, match="Illegal transition"):
        doc.transition(DocState.APPROVED, actor="mallory", role="submitter")
    assert doc.state == DocState.DRAFT


def test_terminal_states_allow_nothing():
    assert lab.ALLOWED_TRANSITIONS[DocState.APPROVED] == set()
    assert lab.ALLOWED_TRANSITIONS[DocState.REJECTED] == set()


def test_transition_is_recorded_with_actor_and_utc_time():
    doc = Document(title="t")
    doc.transition(DocState.SUBMITTED, actor="alice", role="submitter", comments="v1")
    (event,) = doc.history
    assert (event.from_state, event.to_state) == (DocState.DRAFT, DocState.SUBMITTED)
    assert (event.actor, event.role, event.comments) == ("alice", "submitter", "v1")
    assert event.timestamp.utcoffset().total_seconds() == 0


async def _happy_path():
    notifier = RecordingNotifier()
    engine = DocumentWorkflowEngine(notifier, review_sla_min=1, approval_sla_min=1)
    doc = Document(title="Budget")
    await engine.submit(doc, "alice")
    await asyncio.sleep(0.05)
    engine.reviewer_decision(doc.doc_id, "reviewer-001", approve=True)
    await asyncio.sleep(0.05)
    engine.approver_decision(doc.doc_id, "approver-001", approve=True)
    await asyncio.sleep(0.05)
    return doc, notifier


def test_happy_path_reaches_approved_and_notifies_each_party():
    doc, notifier = run(_happy_path())
    assert doc.state == DocState.APPROVED
    assert [s.value for s in (e.to_state for e in doc.history)] == [
        "submitted",
        "ai_reviewing",
        "pending_review",
        "pending_approval",
        "approved",
    ]
    assert [to for to, _ in notifier.sent] == ["alice", "reviewer-001", "approver-001", "alice"]


async def _reviewer_rejects():
    notifier = RecordingNotifier()
    engine = DocumentWorkflowEngine(notifier, review_sla_min=1)
    doc = Document(title="Budget")
    await engine.submit(doc, "alice")
    await asyncio.sleep(0.05)
    engine.reviewer_decision(doc.doc_id, "reviewer-001", approve=False, comments="No")
    await asyncio.sleep(0.05)
    return doc, notifier


def test_reviewer_rejection_ends_the_workflow():
    doc, notifier = run(_reviewer_rejects())
    assert doc.state == DocState.REJECTED
    assert notifier.sent[-1] == ("alice", "Document Rejected")


async def _review_times_out():
    notifier = RecordingNotifier()
    engine = DocumentWorkflowEngine(notifier, review_sla_min=SLA, approval_sla_min=1)
    doc = Document(title="Budget")
    await engine.submit(doc, "alice")
    await asyncio.sleep(0.5)
    return doc, notifier


def test_missed_review_sla_escalates_to_the_backup_reviewer():
    doc, notifier = run(_review_times_out())
    assert doc.state == DocState.ESCALATED
    assert doc.assigned_reviewer == "reviewer-002"
    assert doc.history[-1].actor == "sla-monitor"
    assert notifier.sent[-1] == ("reviewer-002", "ESCALATED: Review Required")


async def _approval_times_out():
    notifier = RecordingNotifier()
    engine = DocumentWorkflowEngine(notifier, review_sla_min=1, approval_sla_min=SLA)
    doc = Document(title="Budget")
    await engine.submit(doc, "alice")
    await asyncio.sleep(0.05)
    engine.reviewer_decision(doc.doc_id, "reviewer-001", approve=True)
    await asyncio.sleep(0.5)
    return doc, notifier


def test_missed_approval_sla_escalates_to_the_manager():
    doc, notifier = run(_approval_times_out())
    assert doc.state == DocState.ESCALATED
    assert doc.assigned_approver == "manager-001"
    assert notifier.sent[-1] == ("manager-001", "ESCALATED: Approval Required")
