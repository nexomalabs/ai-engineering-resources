# Semantic cache implementation (Section 8.4)
#   NEXOMA_LAB_MODE=fixture  (default) a simulated API; no key
#   NEXOMA_LAB_MODE=live     calls the API; needs OPENAI_API_KEY and `--group live`

import hashlib
import os
from typing import Optional

import numpy as np

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    import openai

    client = openai.OpenAI()  # synchronous client
else:
    from stand_in import StandInClient

    client = StandInClient()


class SemanticCache:
    """Two-level cache: exact match (SHA-256) + semantic (cosine similarity)."""

    def __init__(self, similarity_threshold: float = 0.93):
        self.threshold = similarity_threshold
        # Level 1: exact match  {key: response_str}
        self._exact: dict[str, str] = {}
        # Level 2: semantic  list of {"embedding": np.ndarray, "response": str, "query": str}
        self._semantic: list[dict] = []
        self.stats = {"exact_hits": 0, "semantic_hits": 0, "misses": 0}

    def _exact_key(self, query: str) -> str:
        # TODO 1: normalise before hashing (strip surrounding spaces, lower-case), so that
        # "What is X?" and "  what is x?  " share one exact-match key.
        return hashlib.sha256(query.encode()).hexdigest()

    def _embed(self, text: str) -> np.ndarray:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text.strip(),
        )
        return np.array(resp.data[0].embedding, dtype=np.float32)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    def lookup(self, query: str) -> Optional[str]:
        """Return cached response or None."""
        # Level 1: exact match
        key = self._exact_key(query)
        if key in self._exact:
            self.stats["exact_hits"] += 1
            return self._exact[key]

        # Level 2: semantic match
        # TODO 2: embed the query, find the stored entry with the highest cosine similarity,
        # and return its response if the score reaches self.threshold (count a semantic hit).
        # TODO 3: on a semantic hit, also store the answer under this query's exact key, so
        # the same wording next time is an exact hit and needs no embedding call.

        self.stats["misses"] += 1
        return None

    def store(self, query: str, response: str) -> None:
        """Store a new query-response pair in both cache levels."""
        # Exact cache
        key = self._exact_key(query)
        self._exact[key] = response
        # Semantic cache
        embedding = self._embed(query)
        self._semantic.append({"embedding": embedding, "response": response, "query": query})

    def hit_rate(self) -> float:
        total = sum(self.stats.values())
        hits = self.stats["exact_hits"] + self.stats["semantic_hits"]
        return hits / total if total > 0 else 0.0

    def report(self) -> None:
        total = sum(self.stats.values())
        print("\n=== Cache Report ===")
        print(f"Total queries  : {total}")
        print(f"Exact hits     : {self.stats['exact_hits']}")
        print(f"Semantic hits  : {self.stats['semantic_hits']}")
        print(f"Misses         : {self.stats['misses']}")
        print(f"Hit rate       : {self.hit_rate() * 100:.1f}%")
