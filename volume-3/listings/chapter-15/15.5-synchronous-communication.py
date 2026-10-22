# Applied AI Engineering, Volume III, Chapter 15
# Section 15.5, Synchronous Communication
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio

async def request_with_timeout(
    sender_queue: asyncio.Queue,
    target_agent: "AsyncAgent",
    message: MessageEnvelope,
    timeout: float = 30.0
) -> MessageEnvelope:
    """Send a message and wait synchronously for the correlated response."""
    await target_agent.inbox.put(message)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    # Replies for other requests are set aside and returned to the queue at the end.
    # Putting one straight back would spin: get() on a non-empty queue never yields,
    # so the agent being waited for would never run.
    held: list[MessageEnvelope] = []
    try:
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"No response for correlation_id={message.correlation_id}")
            try:
                response = await asyncio.wait_for(sender_queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"No response for correlation_id={message.correlation_id}") from None
            if response.correlation_id == message.correlation_id:
                return response
            held.append(response)
    finally:
        for other in held:
            sender_queue.put_nowait(other)
