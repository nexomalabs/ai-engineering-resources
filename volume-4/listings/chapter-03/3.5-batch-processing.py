# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.5, Batch Processing
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from typing import AsyncIterator, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

async def process_batch(
    items: list[T],
    processor: Callable[[T], R],
    batch_size: int = 50,
    concurrency: int = 10,
    on_error: Callable[[T, Exception], None] = None,
) -> list[R | None]:
    """
    Process a list of items in parallel with controlled concurrency.
    Returns results in the same order as input items.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: list[R | None] = [None] * len(items)

    async def process_one(index: int, item: T) -> None:
        async with semaphore:
            try:
                results[index] = await asyncio.coroutine(processor)(item) \
                    if asyncio.iscoroutinefunction(processor) \
                    else processor(item)
            except Exception as exc:
                if on_error:
                    on_error(item, exc)

    tasks = [process_one(i, item) for i, item in enumerate(items)]
    await asyncio.gather(*tasks)
    return results
