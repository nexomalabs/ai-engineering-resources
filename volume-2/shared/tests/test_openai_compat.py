"""Tests for nexoma_labs.openai_compat. Standard library only; no network, no key."""

import os
import sys
import tempfile
import types
import unittest

from nexoma_labs.fixtures import FixtureMissing
from nexoma_labs.openai_compat import OpenAI


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, mode="json"):
        return self.payload


class _FakeSDK:
    """Stands in for the real openai.OpenAI during record-mode tests."""

    calls = []

    def __init__(self, api_key=None, **kwargs):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._chat))
        self.embeddings = types.SimpleNamespace(create=self._embed)

    def _chat(self, **params):
        _FakeSDK.calls.append(params)
        n = len(_FakeSDK.calls)
        return _FakeResponse(
            {
                "choices": [{"message": {"content": f"answer {n}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
            }
        )

    def _embed(self, **params):
        _FakeSDK.calls.append(params)
        return _FakeResponse({"data": [{"embedding": [0.1, 0.2]}]})


class TestOpenAICompat(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        _FakeSDK.calls = []
        sys.modules["openai"] = types.SimpleNamespace(OpenAI=_FakeSDK)
        self.messages = [{"role": "user", "content": "hi"}]

    def tearDown(self):
        os.environ.pop("NEXOMA_LAB_MODE", None)
        sys.modules.pop("openai", None)
        self.tmp.cleanup()

    def chat(self, client):
        return client.chat.completions.create(
            model="m", messages=self.messages, temperature=0.9, max_tokens=5
        )

    def test_record_then_replay(self):
        os.environ["NEXOMA_LAB_MODE"] = "record"
        recorded = self.chat(OpenAI(fixtures_dir=self.tmp.name)).choices[0].message.content
        os.environ["NEXOMA_LAB_MODE"] = "fixture"
        replayed = self.chat(OpenAI(fixtures_dir=self.tmp.name)).choices[0].message.content
        self.assertEqual(recorded, replayed)
        self.assertEqual(len(_FakeSDK.calls), 1)

    def test_repeated_requests_are_recorded_separately(self):
        os.environ["NEXOMA_LAB_MODE"] = "record"
        client = OpenAI(fixtures_dir=self.tmp.name)
        first, second = self.chat(client), self.chat(client)
        self.assertNotEqual(first.choices[0].message.content, second.choices[0].message.content)
        os.environ["NEXOMA_LAB_MODE"] = "fixture"
        replay = OpenAI(fixtures_dir=self.tmp.name)
        self.assertEqual(self.chat(replay).choices[0].message.content, "answer 1")
        self.assertEqual(self.chat(replay).choices[0].message.content, "answer 2")

    def test_usage_and_embeddings_replay(self):
        os.environ["NEXOMA_LAB_MODE"] = "record"
        client = OpenAI(fixtures_dir=self.tmp.name)
        self.assertEqual(self.chat(client).usage.prompt_tokens, 10)
        vector = client.embeddings.create(model="e", input="x").data[0].embedding
        self.assertEqual(vector, [0.1, 0.2])

    def test_missing_fixture_fails_loudly(self):
        os.environ["NEXOMA_LAB_MODE"] = "fixture"
        with self.assertRaises(FixtureMissing):
            self.chat(OpenAI(fixtures_dir=self.tmp.name))

    def test_live_mode_saves_nothing(self):
        os.environ["NEXOMA_LAB_MODE"] = "live"
        self.chat(OpenAI(fixtures_dir=self.tmp.name))
        self.assertEqual(os.listdir(self.tmp.name), [])


if __name__ == "__main__":
    unittest.main()
