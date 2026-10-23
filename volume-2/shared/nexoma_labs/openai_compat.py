"""A stand-in for `openai.OpenAI` that records and replays model responses.

Volume II's lab listings call the OpenAI SDK directly. The companion versions change
one line, the import, so the rest of each lab matches the book while it still runs in
CI with no API key (LAB_PROJECT_STANDARD.md section 6).

    NEXOMA_LAB_MODE=fixture   replay from the lab's fixtures/ folder (the default)
    NEXOMA_LAB_MODE=record    call the real API and save every response
    NEXOMA_LAB_MODE=live      call the real API, save nothing

Only the two endpoints the labs use are supported: chat.completions.create and
embeddings.create. The OpenAI SDK is imported only when a real call is made.
"""

from __future__ import annotations

import inspect
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from .fixtures import FixtureStore


def _to_namespace(value):
    """Turn recorded JSON back into objects, so response.choices[0].message.content works."""
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _to_namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_to_namespace(v) for v in value]
    return value


class _Endpoint:
    def __init__(self, client: "OpenAI", kind: str):
        self._client = client
        self._kind = kind

    def create(self, **params):
        return self._client._request(self._kind, params)


class OpenAI:
    """Accepts the same constructor arguments as the SDK client it replaces."""

    def __init__(
        self, api_key: str | None = None, fixtures_dir: str | Path | None = None, **kwargs
    ):
        if fixtures_dir is None:
            # A lab's code lives in <lab>/solution/ or <lab>/src/; its recordings in <lab>/fixtures/.
            caller = Path(inspect.stack()[1].filename).resolve()
            fixtures_dir = caller.parent.parent / "fixtures"
        self._store = FixtureStore(fixtures_dir)
        self._api_key = api_key
        self._kwargs = kwargs
        self._occurrences: Counter[str] = Counter()
        self.chat = SimpleNamespace(completions=_Endpoint(self, "chat.completions"))
        self.embeddings = _Endpoint(self, "embeddings")

    def _request(self, kind: str, params: dict):
        request = {"endpoint": kind, **params}
        base = FixtureStore.key(request)
        self._occurrences[base] += 1
        # The same request made twice (five samples at temperature 0.9, say) is recorded
        # twice, so replay reproduces the variation instead of repeating one answer.
        request["occurrence"] = self._occurrences[base]

        def call_live(req: dict) -> dict:
            from openai import OpenAI as SDKClient  # only needed for record and live modes

            client = SDKClient(api_key=self._api_key, **self._kwargs)
            endpoint = client.chat.completions if kind == "chat.completions" else client.embeddings
            args = {k: v for k, v in req.items() if k not in ("endpoint", "occurrence")}
            return endpoint.create(**args).model_dump(mode="json")

        return _to_namespace(self._store.call(request, call_live))
