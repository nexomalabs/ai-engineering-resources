"""Steps 1, 3 and 4: time each query through the two-level cache and analyse the results."""

import statistics
import time

from queries import QUERIES
from semantic_cache import SemanticCache, client


def timed_get(cache: SemanticCache, query: str, model: str = "gpt-6-luna") -> dict:
    t0 = time.perf_counter()
    exact_hits_before = cache.stats["exact_hits"]
    cached = cache.lookup(query)
    if cached:
        source = (
            "exact_cache" if cache.stats["exact_hits"] > exact_hits_before else "semantic_cache"
        )
        return {
            "response": cached,
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "source": source,
        }
    # Cache miss — call LLM
    resp = client.chat.completions.create(
        model=model,
        reasoning_effort="none",
        messages=[{"role": "user", "content": query}],
        max_completion_tokens=80,
    )
    text = resp.choices[0].message.content or ""
    cache.store(query, text)
    return {"response": text, "latency_ms": (time.perf_counter() - t0) * 1000, "source": "llm"}


def run(threshold: float = 0.93) -> tuple[SemanticCache, list[dict]]:
    cache = SemanticCache(similarity_threshold=threshold)
    return cache, [dict(timed_get(cache, q), query=q) for q in QUERIES]


def p50(results: list[dict], source: str) -> float:
    values = [r["latency_ms"] for r in results if r["source"] == source]
    return statistics.median(values) if values else float("nan")


def analyse(cache: SemanticCache, results: list[dict]) -> None:
    cache.report()
    print("\nSemantic hits (paraphrase -> answer reused):")
    for r in results:
        if r["source"] == "semantic_cache":
            print(f"  {r['query']}")
    llm = p50(results, "llm")
    semantic = p50(results, "semantic_cache")
    print(f"\nExact-cache p50    : {p50(results, 'exact_cache'):.3f} ms")
    print(f"Semantic-cache p50 : {semantic:.1f} ms  ({llm / semantic:.0f}x faster than the LLM)")
    print(f"LLM p50            : {llm:.1f} ms")


if __name__ == "__main__":
    analyse(*run())
