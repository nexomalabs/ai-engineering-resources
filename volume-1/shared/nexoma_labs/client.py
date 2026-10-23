"""A minimal, provider-agnostic chat client for labs that call a model.

Labs 8, 9 and 10 all need the same three things: send messages, get back text
plus a token count, and work identically whether NEXOMA_LAB_MODE is fixture,
record, or live (LAB_PROJECT_STANDARD.md section 6). This module is that
common layer, so each lab's own code is the experiment, not API plumbing.

The live path imports the OpenAI SDK lazily, inside complete(), so that
fixture-mode CI never needs it installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .fixtures import FixtureStore, lab_mode


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class Completion:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LabClient:
    """Wraps FixtureStore so a lab's model calls replay in CI and run for real
    with a key. `fixtures_dir` should sit inside the lab directory so each
    lab's recordings are self-contained.
    """

    def __init__(self, fixtures_dir: str | Path, model: str):
        self.store = FixtureStore(fixtures_dir)
        self.model = model

    def complete(
        self,
        messages: list[Message],
        temperature: float | None = 0.0,
        max_completion_tokens: int = 500,
        seed: int | None = None,
    ) -> Completion:
        request = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "max_completion_tokens": max_completion_tokens,
        }
        if temperature is not None:
            # None leaves temperature out: reasoning models such as gpt-6-luna
            # accept only their default and reject the request otherwise.
            request["temperature"] = temperature
        if seed is not None:
            # A distinct fixture per (prompt, temperature, seed) draw, so five
            # independent samples at one temperature don't collide on one key.
            request["seed"] = seed

        def call_live(req: dict) -> dict:
            from openai import OpenAI  # imported here: not a fixture-mode dependency

            client = OpenAI()
            sent = ("model", "messages", "temperature", "max_completion_tokens")
            resp = client.chat.completions.create(**{k: req[k] for k in sent if k in req})
            return {
                "content": resp.choices[0].message.content.strip(),
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }

        response = self.store.call(request, call_live)
        return Completion(**response)

    def ask(self, prompt: str, **kwargs) -> Completion:
        """Convenience for a single user-role message."""
        return self.complete([Message("user", prompt)], **kwargs)


def mode_banner(client_label: str = "model") -> str:
    mode = lab_mode()
    if mode == "fixture":
        return f"[{client_label}: replaying recorded fixtures, no API key needed]"
    if mode == "record":
        return f"[{client_label}: calling the live API and recording responses]"
    return f"[{client_label}: calling the live API]"
