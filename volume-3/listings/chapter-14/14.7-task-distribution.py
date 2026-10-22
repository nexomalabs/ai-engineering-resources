# Applied AI Engineering, Volume III, Chapter 14
# Section 14.7, Task Distribution
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import itertools
import queue
import threading
from typing import Optional

class TaskQueue:
    """Thread-safe task distribution queue."""

    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._in_flight: dict[str, AgentMessage] = {}
        self._lock = threading.Lock()
        # Tie-breaker: two messages with the same priority and timestamp would
        # otherwise make the queue compare AgentMessage objects, which raises TypeError
        self._seq = itertools.count()

    def enqueue(self, msg: AgentMessage) -> None:
        self._queue.put((msg.priority, msg.timestamp, next(self._seq), msg))

    def dequeue(self, timeout: float = 1.0) -> Optional[AgentMessage]:
        try:
            *_, msg = self._queue.get(timeout=timeout)
            with self._lock:
                self._in_flight[msg.message_id] = msg
            return msg
        except queue.Empty:
            return None

    def acknowledge(self, message_id: str) -> None:
        with self._lock:
            self._in_flight.pop(message_id, None)

    def requeue_in_flight(self) -> int:
        """Requeue all in-flight messages (e.g., after a worker crash)."""
        with self._lock:
            count = len(self._in_flight)
            for msg in self._in_flight.values():
                self._queue.put((msg.priority, msg.timestamp, next(self._seq), msg))
            self._in_flight.clear()
        return count

    def size(self) -> int:
        return self._queue.qsize()
