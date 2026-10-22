# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.9, SLA Management
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class SLAMonitor:
    """Monitor workflow items for SLA compliance."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval = check_interval_seconds
        self._breach_handlers: list[Callable] = []

    def on_breach(self, handler: Callable) -> None:
        self._breach_handlers.append(handler)

    async def run(self, get_pending_items: Callable) -> None:
        """Continuously check for SLA breaches."""
        while True:
            items = await get_pending_items()
            now = utcnow()
            for item in items:
                if item.sla_deadline and now > item.sla_deadline:
                    minutes_overdue = int(
                        (now - item.sla_deadline).total_seconds() / 60
                    )
                    for handler in self._breach_handlers:
                        await handler(item, minutes_overdue)
            await asyncio.sleep(self.check_interval)
