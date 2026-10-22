# Applied AI Engineering, Volume III, Chapter 12
# Section 12.4, Task Trees
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    id: str
    description: str
    tool: Optional[str] = None  # the one tool this task uses; checked by validate_plan
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 2

    def is_ready(self, completed_ids: set[str]) -> bool:
        """A task is ready to execute when all its dependencies are complete."""
        return all(dep in completed_ids for dep in self.depends_on)

    def mark_completed(self, result: str) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error
