"""Lab 3 — Enterprise Document Review Workflow (reference solution).

A document state machine with three roles, SLA escalation and notifications, on asyncio.

    python solution/lab.py
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── State Machine ───────────────────────────────────────────────────────────


class DocState(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AI_REVIEWING = "ai_reviewing"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


ALLOWED_TRANSITIONS: dict[DocState, set[DocState]] = {
    DocState.DRAFT: {DocState.SUBMITTED},
    DocState.SUBMITTED: {DocState.AI_REVIEWING},
    DocState.AI_REVIEWING: {DocState.PENDING_REVIEW},
    DocState.PENDING_REVIEW: {DocState.PENDING_APPROVAL, DocState.REJECTED, DocState.ESCALATED},
    DocState.PENDING_APPROVAL: {DocState.APPROVED, DocState.REJECTED, DocState.ESCALATED},
    DocState.ESCALATED: {
        DocState.PENDING_REVIEW,
        DocState.PENDING_APPROVAL,
        DocState.APPROVED,
        DocState.REJECTED,
    },
    DocState.APPROVED: set(),
    DocState.REJECTED: set(),
}

# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class TransitionEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_state: Optional[DocState] = None
    to_state: DocState = DocState.DRAFT
    actor: str = "system"
    role: str = "system"
    timestamp: datetime = field(default_factory=utcnow)
    comments: Optional[str] = None


@dataclass
class Document:
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    submitter_id: str = ""
    state: DocState = DocState.DRAFT
    assigned_reviewer: Optional[str] = None
    assigned_approver: Optional[str] = None
    review_sla: Optional[datetime] = None
    approval_sla: Optional[datetime] = None
    ai_summary: Optional[str] = None
    ai_risk_score: Optional[float] = None
    history: list[TransitionEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def transition(self, to: DocState, actor: str, role: str, comments: str = "") -> None:
        allowed = ALLOWED_TRANSITIONS.get(self.state, set())
        if to not in allowed:
            raise ValueError(f"Illegal transition: {self.state} → {to}")
        event = TransitionEvent(
            from_state=self.state,
            to_state=to,
            actor=actor,
            role=role,
            comments=comments,
        )
        self.history.append(event)
        self.state = to
        self.updated_at = utcnow()
        print(f"[TRANSITION] {event.from_state} → {event.to_state} | actor={actor} role={role}")


# ─── Notification Service ─────────────────────────────────────────────────────


class NotificationService:
    async def notify(self, to: str, subject: str, body: str) -> None:
        """Simulate notification delivery (email/Slack/webhook)."""
        print(f"[NOTIFY] → {to:20s} | {subject}")


# ─── Simulated AI Review ─────────────────────────────────────────────────────


async def ai_review_document(doc: Document) -> None:
    """Simulate AI analysis of the document."""
    await asyncio.sleep(0.5)  # Simulate LLM call latency
    doc.ai_summary = (
        f"Document '{doc.title}' analyzed. Content is {len(doc.content)} characters. "
        "Identified as standard operational document with low regulatory risk."
    )
    doc.ai_risk_score = 0.12  # 0.0 = no risk, 1.0 = maximum risk


# ─── Workflow Engine ──────────────────────────────────────────────────────────


class DocumentWorkflowEngine:
    def __init__(
        self, notifier: NotificationService, review_sla_min: int = 30, approval_sla_min: int = 60
    ):
        self.notifier = notifier
        self.review_sla_min = review_sla_min
        self.approval_sla_min = approval_sla_min
        self.docs: dict[str, Document] = {}
        # Resolution events: doc_id → asyncio.Event
        self._review_events: dict[str, asyncio.Event] = {}
        self._approval_events: dict[str, asyncio.Event] = {}

    def register(self, doc: Document) -> None:
        self.docs[doc.doc_id] = doc
        self._review_events[doc.doc_id] = asyncio.Event()
        self._approval_events[doc.doc_id] = asyncio.Event()

    async def submit(self, doc: Document, submitter_id: str) -> None:
        self.register(doc)
        doc.submitter_id = submitter_id
        doc.transition(DocState.SUBMITTED, actor=submitter_id, role="submitter")
        await self.notifier.notify(
            submitter_id, "Document Submitted", f"'{doc.title}' submitted for review."
        )
        asyncio.create_task(self._run_ai_review(doc))

    async def _run_ai_review(self, doc: Document) -> None:
        doc.transition(DocState.AI_REVIEWING, actor="ai-system", role="system")
        await ai_review_document(doc)
        doc.transition(
            DocState.PENDING_REVIEW,
            actor="ai-system",
            role="system",
            comments=f"Risk score: {doc.ai_risk_score}",
        )
        reviewer = self._assign_reviewer(doc)
        doc.assigned_reviewer = reviewer
        doc.review_sla = utcnow() + timedelta(minutes=self.review_sla_min)
        await self.notifier.notify(
            reviewer,
            "Review Required",
            f"'{doc.title}' awaiting your review. SLA: {self.review_sla_min} min.",
        )
        asyncio.create_task(self._monitor_review_sla(doc))

    async def _monitor_review_sla(self, doc: Document) -> None:
        try:
            await asyncio.wait_for(
                self._wait_for_review(doc.doc_id),
                timeout=self.review_sla_min * 60,
            )
        except asyncio.TimeoutError:
            if doc.state == DocState.PENDING_REVIEW:
                backup = self._assign_backup_reviewer(doc)
                doc.transition(
                    DocState.ESCALATED,
                    actor="sla-monitor",
                    role="system",
                    comments=f"Review SLA exceeded. Escalating to {backup}.",
                )
                doc.assigned_reviewer = backup
                doc.review_sla = utcnow() + timedelta(minutes=self.review_sla_min)
                await self.notifier.notify(
                    backup,
                    "ESCALATED: Review Required",
                    f"'{doc.title}' escalated to you (SLA breach).",
                )

    async def _wait_for_review(self, doc_id: str) -> None:
        await self._review_events[doc_id].wait()

    def reviewer_decision(
        self, doc_id: str, reviewer_id: str, approve: bool, comments: str = ""
    ) -> None:
        doc = self.docs[doc_id]
        if approve:
            doc.transition(
                DocState.PENDING_APPROVAL, actor=reviewer_id, role="reviewer", comments=comments
            )
            approver = self._assign_approver(doc)
            doc.assigned_approver = approver
            doc.approval_sla = utcnow() + timedelta(minutes=self.approval_sla_min)
            asyncio.create_task(
                self.notifier.notify(
                    approver,
                    "Approval Required",
                    f"'{doc.title}' awaiting your approval. SLA: {self.approval_sla_min} min.",
                )
            )
            asyncio.create_task(self._monitor_approval_sla(doc))
        else:
            doc.transition(DocState.REJECTED, actor=reviewer_id, role="reviewer", comments=comments)
            asyncio.create_task(
                self.notifier.notify(
                    doc.submitter_id,
                    "Document Rejected",
                    f"'{doc.title}' was rejected. Reason: {comments}",
                )
            )
        self._review_events[doc_id].set()

    async def _monitor_approval_sla(self, doc: Document) -> None:
        try:
            await asyncio.wait_for(
                self._wait_for_approval(doc.doc_id),
                timeout=self.approval_sla_min * 60,
            )
        except asyncio.TimeoutError:
            if doc.state == DocState.PENDING_APPROVAL:
                manager = "manager-001"
                doc.transition(
                    DocState.ESCALATED,
                    actor="sla-monitor",
                    role="system",
                    comments=f"Approval SLA exceeded. Escalating to {manager}.",
                )
                doc.assigned_approver = manager
                await self.notifier.notify(
                    manager, "ESCALATED: Approval Required", f"'{doc.title}' escalated to you."
                )

    async def _wait_for_approval(self, doc_id: str) -> None:
        await self._approval_events[doc_id].wait()

    def approver_decision(
        self, doc_id: str, approver_id: str, approve: bool, comments: str = ""
    ) -> None:
        doc = self.docs[doc_id]
        final_state = DocState.APPROVED if approve else DocState.REJECTED
        doc.transition(final_state, actor=approver_id, role="approver", comments=comments)
        asyncio.create_task(
            self.notifier.notify(
                doc.submitter_id,
                f"Document {final_state.value.capitalize()}",
                f"'{doc.title}' was {final_state.value}. Comments: {comments}",
            )
        )
        self._approval_events[doc_id].set()

    def _assign_reviewer(self, doc: Document) -> str:
        return "reviewer-001"

    def _assign_backup_reviewer(self, doc: Document) -> str:
        return "reviewer-002"

    def _assign_approver(self, doc: Document) -> str:
        return "approver-001"


# ─── Demo Scenario ────────────────────────────────────────────────────────────


async def demo():
    notifier = NotificationService()
    engine = DocumentWorkflowEngine(
        notifier=notifier,
        review_sla_min=1,  # 1 minute for demo
        approval_sla_min=2,  # 2 minutes for demo
    )

    doc = Document(
        title="Q3 Budget Amendment — Engineering",
        content="This document proposes a $50,000 budget increase for AI infrastructure...",
    )

    print("=== Enterprise Document Review Workflow Demo ===\n")

    # Submitter submits the document
    await engine.submit(doc, submitter_id="alice@company.com")
    await asyncio.sleep(1)  # Allow AI review to complete

    # Reviewer approves
    engine.reviewer_decision(
        doc.doc_id,
        reviewer_id="reviewer-001",
        approve=True,
        comments="Content is accurate and well-justified.",
    )
    await asyncio.sleep(0.1)

    # Approver approves
    engine.approver_decision(
        doc.doc_id,
        approver_id="approver-001",
        approve=True,
        comments="Approved. Proceed with procurement.",
    )
    await asyncio.sleep(0.1)

    print(f"\n=== Final State: {doc.state.value.upper()} ===")
    print(f"AI Summary: {doc.ai_summary}")
    print(f"Risk Score: {doc.ai_risk_score}")
    print("\nTransition History:")
    for event in doc.history:
        print(
            f"  {event.timestamp.strftime('%H:%M:%S')} | "
            f"{str(event.from_state):20s} → {str(event.to_state):20s} | "
            f"{event.actor} ({event.role})"
        )


if __name__ == "__main__":
    asyncio.run(demo())
