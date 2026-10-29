# Semantic cache implementation (Section 8.4)
#   NEXOMA_LAB_MODE=fixture  (default) a simulated API; no key
#   NEXOMA_LAB_MODE=live     calls the API; needs OPENAI_API_KEY and `--group live`

import hashlib
import os
import re
from typing import Callable, Optional

import numpy as np

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    import openai

    client = openai.OpenAI()  # synchronous client
else:
    from stand_in import StandInClient

    client = StandInClient()


# Destinations a shipping question can name. Their rules differ, so an answer about one
# must never answer a question about another, however similar the two questions look.
DESTINATIONS = {
    "australia", "brazil", "canada", "china", "france", "germany", "india", "ireland",
    "italy", "japan", "mexico", "netherlands", "poland", "spain", "uk", "usa",
}  # fmt: skip


def destinations(text: str) -> frozenset[str]:
    """The destination countries a question names."""
    return frozenset(set(re.findall(r"[a-z]+", text.lower())) & DESTINATIONS)


class SemanticCache:
    """
    Two-level cache: exact match (SHA-256) + semantic (cosine similarity). A semantic hit
    must also agree on `must_match(query)`, by default the destination countries the
    question names; pass must_match=None for a cache that compares similarity alone.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.93,
        must_match: Optional[Callable[[str], frozenset]] = destinations,
    ):
        self.threshold = similarity_threshold
        self.must_match = must_match
        # Level 1: exact match  {key: response_str}
        self._exact: dict[str, str] = {}
        # Level 2: semantic  list of {"embedding", "response", "query", "must_match"}
        self._semantic: list[dict] = []
        self.stats = {"exact_hits": 0, "semantic_hits": 0, "misses": 0}

    def _exact_key(self, query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()

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
        if self._semantic:
            query_vec = self._embed(query)
            required = self.must_match(query) if self.must_match else None
            best_score = 0.0
            best_response = None
            for entry in self._semantic:
                if entry["must_match"] != required:
                    continue  # e.g. a question about Canada never takes China's answer
                score = self._cosine_similarity(query_vec, entry["embedding"])
                if score > best_score:
                    best_score = score
                    best_response = entry["response"]
            if best_score >= self.threshold and best_response is not None:
                self.stats["semantic_hits"] += 1
                # Promote to exact cache to avoid recomputing embedding
                self._exact[key] = best_response
                return best_response

        self.stats["misses"] += 1
        return None

    def store(self, query: str, response: str) -> None:
        """Store a new query-response pair in both cache levels."""
        # Exact cache
        key = self._exact_key(query)
        self._exact[key] = response
        # Semantic cache
        embedding = self._embed(query)
        match_key = self.must_match(query) if self.must_match else None
        self._semantic.append(
            {"embedding": embedding, "response": response, "query": query, "must_match": match_key}
        )

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
