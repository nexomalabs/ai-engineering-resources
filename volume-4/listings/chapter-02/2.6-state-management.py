# Applied AI Engineering, Volume IV, Chapter 2
# Section 2.6, State Management
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from enum import Enum
from typing import Optional
from datetime import datetime, timezone

class JobState(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"
    RETRYING = "retrying"

# Legal transitions: a mapping from current state to allowed next states
TRANSITIONS = {
    JobState.QUEUED:     {JobState.PARSING, JobState.FAILED},
    JobState.PARSING:    {JobState.ANALYZING, JobState.FAILED},
    JobState.ANALYZING:  {JobState.VALIDATING, JobState.RETRYING, JobState.FAILED},
    JobState.VALIDATING: {JobState.COMPLETE, JobState.RETRYING, JobState.FAILED},
    JobState.RETRYING:   {JobState.ANALYZING, JobState.FAILED},
    JobState.COMPLETE:   set(),   # terminal
    JobState.FAILED:     set(),   # terminal
}

class DocumentAnalysisJob:
    def __init__(self, job_id: str, document_id: str):
        self.job_id = job_id
        self.document_id = document_id
        self.state = JobState.QUEUED
        self.retry_count = 0
        self.max_retries = 3
        self.created_at = datetime.now(timezone.utc)
        self.state_history: list[tuple[JobState, datetime]] = [
            (JobState.QUEUED, self.created_at)
        ]

    def transition(self, new_state: JobState) -> None:
        allowed = TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Illegal transition: {self.state} → {new_state}. "
                f"Allowed: {allowed}"
            )
        self.state = new_state
        self.state_history.append((new_state, datetime.now(timezone.utc)))

    def mark_retry(self) -> bool:
        if self.retry_count >= self.max_retries:
            self.transition(JobState.FAILED)
            return False
        self.retry_count += 1
        self.transition(JobState.RETRYING)
        return True
