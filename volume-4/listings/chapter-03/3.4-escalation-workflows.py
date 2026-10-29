# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.4, Escalation Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import datetime, timedelta, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class EscalationLevel:
    level: int
    assignee_id: str
    sla_minutes: int
    notify_fn: Callable[[str, str], None]

@dataclass
class EscalationTask:
    task_id: str
    item_id: str
    levels: list[EscalationLevel]
    current_level: int = 0
    resolved: bool = False
    created_at: datetime = field(default_factory=utcnow)

class EscalationEngine:
    def __init__(self):
        self.tasks: dict[str, EscalationTask] = {}
        self._timers: dict[str, asyncio.Task] = {}

    def register(self, task: EscalationTask) -> None:
        self.tasks[task.task_id] = task
        # Keep a reference: the event loop holds tasks only weakly, so an
        # unreferenced task can be garbage-collected before it finishes.
        self._timers[task.task_id] = asyncio.create_task(self._schedule_escalation(task))

    async def _schedule_escalation(self, task: EscalationTask) -> None:
        while task.current_level < len(task.levels) and not task.resolved:
            level = task.levels[task.current_level]
            level.notify_fn(task.item_id, level.assignee_id)
            try:
                await asyncio.wait_for(
                    self._wait_for_resolution(task.task_id),
                    timeout=level.sla_minutes * 60
                )
                return  # Resolved within SLA
            except asyncio.TimeoutError:
                task.current_level += 1
                if task.current_level >= len(task.levels):
                    self._handle_sla_breach(task)

    async def _wait_for_resolution(self, task_id: str) -> None:
        while not self.tasks[task_id].resolved:
            await asyncio.sleep(5)

    def resolve(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].resolved = True

    def _handle_sla_breach(self, task: EscalationTask) -> None:
        print(f"[SLA BREACH] Task {task.task_id} for item {task.item_id} "
              f"breached all escalation levels. Manual intervention required.")
