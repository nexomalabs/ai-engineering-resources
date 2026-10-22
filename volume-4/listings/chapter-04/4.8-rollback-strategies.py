# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.8, Rollback Strategies
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import json

@dataclass
class AutomatedAction:
    action_id: str
    pipeline_id: str
    action_type: str          # "route", "notify", "update", "create", "delete"
    target_resource: str      # e.g., "document:uuid-123"
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    executed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    is_rolled_back: bool = False

class ActionLog:
    def __init__(self):
        self._actions: list[AutomatedAction] = []

    def record(self, action: AutomatedAction) -> None:
        action.executed_at = datetime.now(timezone.utc)
        self._actions.append(action)

    def rollback_all(self, since: datetime) -> list[str]:
        """Return rollback instructions for all actions since a timestamp."""
        instructions = []
        for action in reversed(self._actions):
            if (action.executed_at and action.executed_at >= since
                    and not action.is_rolled_back):
                instructions.append(
                    f"ROLLBACK: {action.action_type} on {action.target_resource} — "
                    f"restore to: {json.dumps(action.before_state)}"
                )
                action.is_rolled_back = True
                action.rolled_back_at = datetime.now(timezone.utc)
        return instructions
