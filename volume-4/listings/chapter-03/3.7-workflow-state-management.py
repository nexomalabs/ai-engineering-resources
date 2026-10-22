# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.7, Workflow State Management
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AI_PROCESSING = "ai_processing"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETE = "complete"
    ARCHIVED = "archived"

class WorkflowEvent(BaseModel):
    event_id: str
    workflow_id: str
    timestamp: datetime
    from_state: WorkflowStatus
    to_state: WorkflowStatus
    actor_id: str
    actor_role: str
    comments: Optional[str] = None

class WorkflowRecord(BaseModel):
    workflow_id: str
    item_id: str
    item_type: str
    current_status: WorkflowStatus
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    events: List[WorkflowEvent] = []
    ai_output: Optional[dict] = None
    final_decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime
