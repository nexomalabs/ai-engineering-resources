# Applied AI Engineering, Volume IV, Chapter 1
# Section 1.3, Reliability
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import random
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> T:
    """Retry an async function with exponential backoff and jitter."""
    last_exception = None
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as exc:
            last_exception = exc
            if attempt == max_attempts - 1:
                break
            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            await asyncio.sleep(delay)
    raise last_exception
