# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.3, Approval Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

@dataclass
class ApprovalStep:
    step_id: str
    role_required: str
    approver_id: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision_time: Optional[datetime] = None
    comments: Optional[str] = None

@dataclass
class ApprovalWorkflow:
    workflow_id: str
    item_id: str
    steps: list[ApprovalStep] = field(default_factory=list)
    current_step_index: int = 0
    overall_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=utcnow)

    def current_step(self) -> Optional[ApprovalStep]:
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def record_decision(
        self,
        approver_id: str,
        decision: ApprovalStatus,
        comments: Optional[str] = None
    ) -> None:
        step = self.current_step()
        if step is None:
            raise ValueError("No pending approval step")
        step.approver_id = approver_id
        step.status = decision
        step.decision_time = utcnow()
        step.comments = comments

        if decision == ApprovalStatus.REJECTED:
            self.overall_status = ApprovalStatus.REJECTED
        elif decision == ApprovalStatus.CHANGES_REQUESTED:
            self.overall_status = ApprovalStatus.CHANGES_REQUESTED
        elif decision == ApprovalStatus.APPROVED:
            self.current_step_index += 1
            if self.current_step_index >= len(self.steps):
                self.overall_status = ApprovalStatus.APPROVED
            # else: next step is now pending
