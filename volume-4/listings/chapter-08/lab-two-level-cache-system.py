# Applied AI Engineering, Volume IV, Chapter 8
# Hands-on Lab: Two-Level Cache System
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import time

def timed_get(cache: SemanticCache, query: str, model: str = "gpt-6-luna") -> dict:
    t0 = time.perf_counter()
    cached = cache.lookup(query)
    if cached:
        return {"response": cached, "latency_ms": (time.perf_counter()-t0)*1000, "source": "cache"}
    # Cache miss — call LLM
    resp = client.chat.completions.create(
        model=model,
        reasoning_effort="none",
        messages=[{"role": "user", "content": query}],
        max_completion_tokens=80,
    )
    text = resp.choices[0].message.content or ""
    cache.store(query, text)
    return {"response": text, "latency_ms": (time.perf_counter()-t0)*1000, "source": "llm"}
