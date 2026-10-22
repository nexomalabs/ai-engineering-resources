# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.4, Scheduled Automation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from datetime import datetime, time, timezone
from typing import Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class DailyScheduler:
    """Execute an async task once per day at a specified time."""

    def __init__(
        self,
        task: Callable[[], Awaitable[None]],
        run_at: time = time(2, 0),   # 02:00 UTC default
        name: str = "scheduled-task",
    ):
        self.task = task
        self.run_at = run_at
        self.name = name
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Scheduler '%s' started. Daily at %s UTC", self.name, self.run_at)
        while self._running:
            now = datetime.now(timezone.utc)
            target = now.replace(
                hour=self.run_at.hour,
                minute=self.run_at.minute,
                second=0, microsecond=0
            )
            if target <= now:
                # Next run is tomorrow
                from datetime import timedelta
                target = target + timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            logger.info("Next run of '%s' in %.0f seconds", self.name, wait_seconds)
            await asyncio.sleep(wait_seconds)
            if self._running:
                logger.info("Running scheduled task: %s", self.name)
                try:
                    await self.task()
                except Exception as exc:
                    logger.error("Scheduled task '%s' failed: %s", self.name, exc)

    def stop(self) -> None:
        self._running = False
