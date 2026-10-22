"""Lab 3 — Three-Type Memory System (starter).

This file RUNS as supplied. Working memory never forgets, semantic memory stores
duplicates, and episodic recall ignores recency. Complete the three TODOs.

    python src/lab.py
"""

# memory_system.py
import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "do",
    "does",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "to",
    "what",
    "with",
    "you",
}


def mock_embed(text: str, dims: int = 256) -> np.ndarray:
    """
    Deterministic stand-in for an embedding model, using the "hashing trick":
    each word is hashed into one of `dims` buckets, so texts that share words
    get similar vectors. It captures shared vocabulary, not meaning ("car" and
    "automobile" share nothing). For production, use a real embedding model.
    """
    vec = np.zeros(dims, dtype=np.float32)
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]  # crude plural folding: "tokens" matches "token"
        bucket = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % dims
        vec[bucket] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class WorkingMemory:
    """
    In-context memory: a simple ordered list of recent conversation turns.
    Maintains the last max_turns turns.
    """

    max_turns: int = 10
    turns: List[Dict] = field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append({"role": role, "content": content, "timestamp": time.time()})
        # TODO 1: Keep only the last `max_turns` turns, dropping the oldest first.
        #   Without a bound, working memory grows until it no longer fits the window.

    def get_context(self) -> str:
        if not self.turns:
            return ""
        lines = []
        for t in self.turns:
            lines.append(f"{t['role'].upper()}: {t['content']}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.turns.clear()


@dataclass
class Episode:
    episode_id: str
    content: str
    timestamp: float
    tags: List[str]
    outcome: str
    embedding: np.ndarray = field(repr=False)


class EpisodicMemory:
    """
    Stores discrete past events. Retrieval uses recency-weighted cosine similarity.
    """

    def __init__(self, recency_weight: float = 0.3):
        self.episodes: List[Episode] = []
        self.recency_weight = recency_weight

    def store(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        outcome: str = "",
        timestamp: Optional[float] = None,
    ) -> Episode:
        ts = time.time() if timestamp is None else timestamp
        ep = Episode(
            episode_id=hashlib.md5(f"{content}{ts}".encode()).hexdigest()[:8],
            content=content,
            timestamp=ts,
            tags=tags or [],
            outcome=outcome,
            embedding=mock_embed(content),
        )
        self.episodes.append(ep)
        return ep

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Episode, float]]:
        if not self.episodes:
            return []

        query_emb = mock_embed(query)
        now = time.time()
        oldest = min(e.timestamp for e in self.episodes)
        time_range = max(now - oldest, 1.0)

        scored = []
        for ep in self.episodes:
            semantic_score = cosine_similarity(query_emb, ep.embedding)
            recency_score = (ep.timestamp - oldest) / time_range
            # TODO 3: Blend similarity and recency, weighting recency by
            #   `self.recency_weight`, so that of two equally similar episodes the
            #   newer one ranks first.
            combined = semantic_score
            scored.append((ep, combined))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


@dataclass
class Fact:
    fact_id: str
    content: str
    source: str
    created_at: float
    embedding: np.ndarray = field(repr=False)


class SemanticMemory:
    """
    Stores general facts as vector-indexed knowledge.
    Retrieval uses cosine similarity.
    """

    def __init__(self):
        self.facts: List[Fact] = []

    def store_fact(self, content: str, source: str = "user") -> Fact:
        # Deduplication: skip if near-identical fact exists
        new_emb = mock_embed(content)
        # TODO 2: If a stored fact is a near-duplicate (cosine similarity above
        #   0.98), return it instead of storing the new one.

        fact = Fact(
            fact_id=hashlib.md5(f"{content}".encode()).hexdigest()[:8],
            content=content,
            source=source,
            created_at=time.time(),
            embedding=new_emb,
        )
        self.facts.append(fact)
        return fact

    def retrieve(
        self, query: str, top_k: int = 3, threshold: float = 0.1
    ) -> List[Tuple[Fact, float]]:
        if not self.facts:
            return []

        query_emb = mock_embed(query)
        scored = []
        for fact in self.facts:
            score = cosine_similarity(query_emb, fact.embedding)
            if score >= threshold:
                scored.append((fact, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class MemorySystem:
    """
    Unified memory system combining working, episodic, and semantic memory.
    """

    def __init__(self):
        self.working = WorkingMemory(max_turns=5)
        self.episodic = EpisodicMemory(recency_weight=0.3)
        self.semantic = SemanticMemory()

    def record_turn(self, role: str, content: str) -> None:
        """Record a conversation turn into working and episodic memory."""
        self.working.add_turn(role, content)
        if role == "assistant":
            self.episodic.store(content=content, tags=["response"], outcome="delivered")

    def learn_fact(self, fact: str, source: str = "user") -> None:
        """Store a general fact in semantic memory."""
        self.semantic.store_fact(fact, source)

    def recall(self, query: str) -> dict:
        """Retrieve relevant memories across all three types for a given query."""
        working_ctx = self.working.get_context()
        episodic_results = self.episodic.retrieve(query, top_k=2)
        semantic_results = self.semantic.retrieve(query, top_k=3)

        return {
            "working_memory": working_ctx,
            "episodic_memories": [
                {
                    "content": ep.content[:100],
                    "score": round(sc, 3),
                    "tags": ep.tags,
                    "outcome": ep.outcome,
                }
                for ep, sc in episodic_results
            ],
            "semantic_memories": [
                {"content": fact.content, "score": round(sc, 3), "source": fact.source}
                for fact, sc in semantic_results
            ],
        }


def run_demo():
    ms = MemorySystem()

    # Seed semantic memory with domain facts
    ms.learn_fact("Python uses indentation to define code blocks", source="kb")
    ms.learn_fact("REST APIs communicate using HTTP methods: GET, POST, PUT, DELETE", source="kb")
    ms.learn_fact("JWT tokens consist of three base64-encoded parts separated by dots", source="kb")
    ms.learn_fact("The user's name is Alex and they are a backend developer", source="user")
    ms.learn_fact("Alex prefers Python over JavaScript for server-side code", source="user")

    # Simulate a conversation being recorded
    turns = [
        ("user", "Can you explain how JWT authentication works?"),
        (
            "assistant",
            "JWT authentication uses signed tokens. The server issues a JWT containing user claims, signed with a secret key. The client stores the token and sends it in the Authorization header. The server verifies the signature without needing session state.",
        ),
        ("user", "What library should I use in Python for JWT?"),
        (
            "assistant",
            "For Python, I recommend the `python-jose` or `PyJWT` library. PyJWT is widely used and straightforward: `import jwt; token = jwt.encode(payload, secret, algorithm='HS256')`.",
        ),
        ("user", "How do I refresh tokens?"),
        (
            "assistant",
            "Issue a short-lived access token (15 minutes) and a long-lived refresh token (7 days). When the access token expires, the client calls /auth/refresh with the refresh token to get a new access token.",
        ),
    ]

    for role, content in turns:
        ms.record_turn(role, content)

    # New query: retrieve relevant memories
    new_query = "What Python library handles JWT and how do I verify a token?"
    memories = ms.recall(new_query)

    print(f"=== MEMORY RECALL FOR QUERY ===\n'{new_query}'\n")

    print("--- WORKING MEMORY (recent conversation) ---")
    print(memories["working_memory"])

    print("\n--- EPISODIC MEMORY (past responses) ---")
    for m in memories["episodic_memories"]:
        print(f"  [{m['score']}] {m['content']}...")

    print("\n--- SEMANTIC MEMORY (facts) ---")
    for m in memories["semantic_memories"]:
        print(f"  [{m['score']}] [{m['source']}] {m['content']}")


if __name__ == "__main__":
    run_demo()
