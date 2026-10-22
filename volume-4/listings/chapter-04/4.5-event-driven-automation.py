# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.5, Event-Driven Automation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from collections import defaultdict
from typing import Callable, Awaitable, Any
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]

class EventBus:
    """Simple in-process async event bus for automation pipelines."""

    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, payload: dict) -> None:
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            logger.debug("No subscribers for event: %s", event_type)
            return
        await asyncio.gather(
            *[self._safe_call(h, payload) for h in handlers],
            return_exceptions=True,
        )

    async def _safe_call(self, handler: EventHandler, payload: dict) -> None:
        try:
            await handler(payload)
        except Exception as exc:
            logger.error("Event handler %s failed: %s", handler.__name__, exc)
