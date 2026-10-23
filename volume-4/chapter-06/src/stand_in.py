"""A simulated AsyncOpenAI client, used when NEXOMA_LAB_MODE is not "live".

It behaves like a remote API for benchmarking purposes, with no key and no cost:

- each prompt has a fixed latency between 300 and 800 ms, derived from a hash of the
  prompt, so runs are repeatable;
- the provider serves at most PROVIDER_CONCURRENCY requests at once, so a client that
  sends more than that queues, and its tail latency grows, as with a real rate limit;
- the response carries usage counts, estimated at four characters a token.

The numbers are a model of an API, not measurements of one. Set NEXOMA_LATENCY_SCALE
(default 1.0) to speed everything up, as the tests do.
"""

import asyncio
import hashlib
import os
from types import SimpleNamespace

PROVIDER_CONCURRENCY = 10
_slots_by_loop: dict[int, asyncio.Semaphore] = {}


def latency_s(prompt: str) -> float:
    fraction = hashlib.sha256(prompt.encode()).digest()[0] / 255
    return (0.300 + 0.500 * fraction) * float(os.environ.get("NEXOMA_LATENCY_SCALE", "1.0"))


def _slots() -> asyncio.Semaphore:
    """The provider's capacity: one semaphore per event loop."""
    loop_id = id(asyncio.get_running_loop())
    return _slots_by_loop.setdefault(loop_id, asyncio.Semaphore(PROVIDER_CONCURRENCY))


class _Completions:
    async def create(self, *, model, messages, max_completion_tokens=100, **_settings):
        prompt = messages[-1]["content"]
        async with _slots():
            await asyncio.sleep(latency_s(prompt))
        words = f"A simulated answer to: {prompt}".split()
        text = " ".join(words[: max(1, max_completion_tokens // 2)])
        usage = SimpleNamespace(
            prompt_tokens=max(1, len(prompt) // 4), completion_tokens=max(1, len(text) // 4)
        )
        return SimpleNamespace(
            model="stand-in",
            usage=usage,
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        )


class StandInAsyncClient:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_Completions())
