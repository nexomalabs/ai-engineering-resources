"""Simulated OpenAI clients, used when NEXOMA_LAB_MODE is not "live".

Each of the pipeline's three calls takes the latency Section 7.8 uses as its example
(classify 200 ms, summarize 300 ms, keywords 500 ms) and returns a short, fixed-shape
answer, so the profile has real waiting in it and no key is needed. The provider serves
at most ten requests at once. Set NEXOMA_LATENCY_SCALE (default 1.0) to speed it up.
"""

import asyncio
import os
import time
from types import SimpleNamespace

PROVIDER_CONCURRENCY = 10
LATENCY_S = {"Classify": 0.200, "Summarize": 0.300, "List top 3 keywords": 0.500}
_slots_by_loop: dict[int, asyncio.Semaphore] = {}


def _latency(prompt: str) -> float:
    scale = float(os.environ.get("NEXOMA_LATENCY_SCALE", "1.0"))
    return next((s for prefix, s in LATENCY_S.items() if prompt.startswith(prefix)), 0.3) * scale


def _answer(prompt: str) -> str:
    text = prompt.split(":", 1)[1].strip()
    words = [w.strip(".,").lower() for w in text.split()]
    if prompt.startswith("Classify"):
        return "NEGATIVE" if any(w in words for w in ("fails", "slow", "outage")) else "POSITIVE"
    if prompt.startswith("Summarize"):
        return text.split(".")[0] + "."
    long_words = sorted({w for w in words if len(w) > 7}, key=lambda w: (-len(w), w))
    return ", ".join(long_words[:3])


def _response(prompt: str) -> SimpleNamespace:
    message = SimpleNamespace(content=_answer(prompt))
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _Completions:
    def create(self, *, messages, **_settings):
        prompt = messages[-1]["content"]
        time.sleep(_latency(prompt))
        return _response(prompt)


class _AsyncCompletions:
    async def create(self, *, messages, **_settings):
        prompt = messages[-1]["content"]
        slots = _slots_by_loop.setdefault(
            id(asyncio.get_running_loop()), asyncio.Semaphore(PROVIDER_CONCURRENCY)
        )
        async with slots:
            await asyncio.sleep(_latency(prompt))
        return _response(prompt)


class StandInClient:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_Completions())


class StandInAsyncClient:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_AsyncCompletions())
