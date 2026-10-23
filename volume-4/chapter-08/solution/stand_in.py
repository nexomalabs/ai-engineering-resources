"""A simulated OpenAI client, used when NEXOMA_LAB_MODE is not "live".

- embeddings.create(...) returns a hashed bag-of-words vector after dropping question
  words and filler, with plurals folded to the singular. Two phrasings that use the same
  content words score close to 1.0; a rewording with different words scores much lower.
  Real embeddings capture meaning, not just shared words, so they score paraphrases
  higher than this does. Each call waits 60-120 ms, like a hosted embedding API.
- chat.completions.create(...) returns a short fixed answer after 300-1,500 ms.

Latencies come from a hash of the text, so runs repeat. Set NEXOMA_LATENCY_SCALE
(default 1.0) to speed everything up, as the tests do.
"""

import hashlib
import os
import re
import time
from types import SimpleNamespace

DIMENSIONS = 512
FILLER = {
    "what",
    "whats",
    "how",
    "why",
    "when",
    "which",
    "who",
    "is",
    "are",
    "was",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "would",
    "you",
    "me",
    "i",
    "we",
    "please",
    "explain",
    "tell",
    "describe",
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "and",
    "or",
    "it",
    "be",
    "help",
    "simple",
    "terms",
    "s",
    "with",
    "about",
}


def _scale() -> float:
    return float(os.environ.get("NEXOMA_LATENCY_SCALE", "1.0"))


def _fraction(text: str) -> float:
    return hashlib.sha256(text.encode()).digest()[0] / 255


def _words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("'", ""))
    return [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in FILLER]


def embed(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for word in _words(text):
        digest = hashlib.md5(word.encode()).digest()
        vector[int.from_bytes(digest[:2], "big") % DIMENSIONS] += 1.0
    return vector


class _Embeddings:
    def create(self, *, input, **_settings):
        time.sleep((0.060 + 0.060 * _fraction(input)) * _scale())
        return SimpleNamespace(data=[SimpleNamespace(embedding=embed(input))])


class _Completions:
    def create(self, *, messages, **_settings):
        prompt = messages[-1]["content"]
        time.sleep((0.300 + 1.200 * _fraction(prompt)) * _scale())
        message = SimpleNamespace(content=f"(simulated answer) {prompt}")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class StandInClient:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_Completions())
        self.embeddings = _Embeddings()
