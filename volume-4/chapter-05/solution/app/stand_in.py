"""A stand-in for AsyncOpenAI, used when NEXOMA_LAB_MODE is not "live".

It answers each of the three tasks from the request text, with token counts estimated
at four characters a token, so the service, its tests and the smoke test run with no
API key.
"""

import json
import re
from types import SimpleNamespace

MODEL = "stand-in"


def _answer(system: str, text: str) -> str:
    if system.startswith("Classify"):
        lowered = text.lower()
        for kind in ("invoice", "contract", "email", "report", "memo"):
            if kind in lowered:
                return kind
        return "article"
    if system.startswith("Extract named entities"):
        names = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*", text)
        return json.dumps(sorted(set(names)))
    first = re.split(r"(?<=[.!?])\s+", text.strip())[0]
    return f"Summary: {first}"


class _Completions:
    async def create(self, *, model, messages, **_settings):
        system = next(m["content"] for m in messages if m["role"] == "system")
        text = next(m["content"] for m in messages if m["role"] == "user")
        result = _answer(system, text)
        usage = SimpleNamespace(
            prompt_tokens=(len(system) + len(text)) // 4, completion_tokens=max(1, len(result) // 4)
        )
        return SimpleNamespace(
            model=MODEL,
            usage=usage,
            choices=[SimpleNamespace(message=SimpleNamespace(content=result))],
        )


class StandInAsyncClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=_Completions())
