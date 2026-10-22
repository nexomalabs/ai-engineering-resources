# Applied AI Engineering, Volume IV, Chapter 9
# Section 9.9, Rate Limiting
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import time
import threading

class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, capacity: float, refill_rate: float):
        """
        capacity    : maximum tokens in bucket
        refill_rate : tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        """Return True if tokens were consumed (request allowed), False if rate-limited."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

# Per-user rate limiter registry
_limiters: dict[str, TokenBucket] = {}
_limiters_lock = threading.Lock()

def get_limiter(user_id: str, capacity: float = 10, rate: float = 1.0) -> TokenBucket:
    with _limiters_lock:
        if user_id not in _limiters:
            _limiters[user_id] = TokenBucket(capacity=capacity, refill_rate=rate)
        return _limiters[user_id]
