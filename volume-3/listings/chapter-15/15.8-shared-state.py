# Applied AI Engineering, Volume III, Chapter 15
# Section 15.8, Shared State
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from typing import Any

class SharedStateStore:
    """Thread-safe shared state with optimistic locking for agents."""

    def __init__(self):
        self._state: dict[str, tuple[int, Any]] = {}  # key → (version, value)
        self._lock = asyncio.Lock()

    async def read(self, key: str) -> tuple[int, Any]:
        """Returns (version, value). Version is used for optimistic locking."""
        async with self._lock:
            if key not in self._state:
                return 0, None
            return self._state[key]

    async def write(self, key: str, value: Any,
                    expected_version: int = 0) -> bool:
        """
        Write only if current version matches expected_version.
        Returns True on success, False on conflict (stale data).
        """
        async with self._lock:
            current_version, _ = self._state.get(key, (0, None))
            if current_version != expected_version:
                return False  # Conflict: another agent has written since our read
            self._state[key] = (current_version + 1, value)
            return True

    async def force_write(self, key: str, value: Any) -> int:
        """Unconditional write. Returns new version number."""
        async with self._lock:
            current_version, _ = self._state.get(key, (0, None))
            new_version = current_version + 1
            self._state[key] = (new_version, value)
            return new_version
