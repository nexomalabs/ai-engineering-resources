# Inference benchmark harness — Volume IV, Chapter 6 lab (reference solution)
#
# The harness from Section 6.10, extended as the lab's steps ask:
#   Step 3  run without the cache (use_cache=False)
#   Step 4  run a mixed set of unique and repeated prompts with the cache
#   Step 5  count tokens from the response's usage field, priced as gpt-6-luna
#   Step 6  sweep concurrency and watch the tail latency
# One fix the lab adds: identical prompts already in flight share one request
# (single-flight), so concurrent duplicates hit the cache instead of all missing.
#
#   NEXOMA_LAB_MODE=fixture  (default) a simulated API: repeatable latencies, no key, no cost
#   NEXOMA_LAB_MODE=live     calls gpt-6-luna; needs OPENAI_API_KEY and `--group live`

import asyncio
import hashlib
import os
import time
from dataclasses import dataclass, field

import numpy as np

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    import openai

    client = openai.AsyncOpenAI()  # reads OPENAI_API_KEY from environment
else:
    from stand_in import StandInAsyncClient

    client = StandInAsyncClient()

# gpt-6-luna list prices per 1,000 tokens (Chapter 15's pricing table: $0.10 / $0.50 per million)
INPUT_PER_1K = 0.0001
OUTPUT_PER_1K = 0.0005

# --- Exact-match cache, with single-flight for requests already in progress ---
_cache: dict[str, tuple[str, int, int]] = {}
_in_flight: dict[str, asyncio.Future] = {}


def _cache_key(prompt: str, model: str) -> str:
    return hashlib.sha256(f"{model}::{prompt}".encode()).hexdigest()


async def _call_model(prompt: str, model: str, max_tokens: int) -> tuple[str, int, int]:
    response = await client.chat.completions.create(
        model=model,
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
    )
    usage = response.usage
    return response.choices[0].message.content or "", usage.prompt_tokens, usage.completion_tokens


MISS, FROM_CACHE, SHARED = "miss", "cache", "shared"


async def cached_complete(
    prompt: str, model: str = "gpt-6-luna", max_tokens: int = 100, use_cache: bool = True
) -> tuple[str, str, int, int]:
    """Return (response_text, how_served, prompt_tokens, completion_tokens).

    how_served is MISS (a model call), FROM_CACHE (stored answer) or SHARED (waited for
    an identical request already in flight). Only a miss costs tokens."""
    if not use_cache:
        text, prompt_tokens, completion_tokens = await _call_model(prompt, model, max_tokens)
        return text, MISS, prompt_tokens, completion_tokens
    key = _cache_key(prompt, model)
    if key in _cache:
        return _cache[key][0], FROM_CACHE, 0, 0
    if key in _in_flight:  # the same prompt is already being answered: wait for it
        text, _, _ = await _in_flight[key]
        return text, SHARED, 0, 0
    future = asyncio.get_running_loop().create_future()
    _in_flight[key] = future
    try:
        result = await _call_model(prompt, model, max_tokens)
        future.set_result(result)
    except Exception as exc:
        future.set_exception(exc)
        raise
    finally:
        del _in_flight[key]
    _cache[key] = result
    return result[0], MISS, result[1], result[2]


@dataclass
class BenchmarkResult:
    label: str = ""
    latencies_ms: list[float] = field(default_factory=list)
    cache_latencies_ms: list[float] = field(default_factory=list)
    cache_hits: int = 0
    shared_requests: int = 0
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    elapsed_s: float = 0.0

    def percentile(self, q: float) -> float:
        return float(np.percentile(np.array(self.latencies_ms), q))

    def report(self) -> None:
        rps = self.total_requests / self.elapsed_s if self.elapsed_s else 0
        tps = self.total_tokens / self.elapsed_s if self.elapsed_s else 0
        cost_per_1k = (self.total_cost_usd / self.total_tokens * 1000) if self.total_tokens else 0
        print(f"\n=== {self.label} ===")
        print(f"Requests      : {self.total_requests}")
        saved = self.cache_hits + self.shared_requests
        print(
            f"Served without a model call: {saved} ({100 * saved / max(self.total_requests, 1):.1f}%)"
            f" | from cache {self.cache_hits}, shared in flight {self.shared_requests}"
        )
        print(f"Throughput    : {rps:.2f} req/s | {tps:.1f} tok/s")
        print(f"Latency p50   : {self.percentile(50):.0f} ms")
        print(f"Latency p95   : {self.percentile(95):.0f} ms")
        print(f"Latency p99   : {self.percentile(99):.0f} ms")
        if self.cache_latencies_ms:
            print(f"From-cache p99: {float(np.percentile(self.cache_latencies_ms, 99)):.2f} ms")
        print(f"Cost/1K tokens: ${cost_per_1k:.5f}")


async def run_benchmark(
    prompts: list[str],
    model: str = "gpt-6-luna",
    max_tokens: int = 100,
    concurrency: int = 5,
    use_cache: bool = True,
    label: str = "Benchmark",
) -> BenchmarkResult:
    result = BenchmarkResult(label=label)
    semaphore = asyncio.Semaphore(concurrency)

    async def single_request(prompt: str) -> None:
        async with semaphore:
            t0 = time.perf_counter()
            text, served, prompt_tokens, completion_tokens = await cached_complete(
                prompt, model, max_tokens, use_cache
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            result.latencies_ms.append(latency_ms)
            result.total_requests += 1
            result.total_tokens += prompt_tokens + completion_tokens
            result.total_cost_usd += (
                prompt_tokens * INPUT_PER_1K + completion_tokens * OUTPUT_PER_1K
            ) / 1000
            if served == FROM_CACHE:
                result.cache_hits += 1
                result.cache_latencies_ms.append(latency_ms)
            elif served == SHARED:
                result.shared_requests += 1

    t_start = time.perf_counter()
    await asyncio.gather(*[single_request(p) for p in prompts])
    result.elapsed_s = time.perf_counter() - t_start
    return result


UNIQUE = [
    f"Question {i}: explain {topic} in one sentence."
    for i, topic in enumerate(
        [
            "caching",
            "load balancing",
            "quantization",
            "distillation",
            "batching",
            "rate limiting",
            "embeddings",
            "vector search",
            "tokenization",
            "streaming",
            "retries",
            "timeouts",
            "autoscaling",
            "observability",
            "canary releases",
            "feature flags",
            "sharding",
            "replication",
            "backpressure",
            "idempotency",
        ]
    )
]
# 40 prompts, 20 unique. The first ten repeats arrive side by side with their original,
# while it is still in flight; the last ten arrive after their original has finished.
MIXED = [p for p in UNIQUE[:10] for _ in (0, 1)] + UNIQUE[10:] + UNIQUE[10:]


async def main() -> None:
    _cache.clear()
    no_cache = await run_benchmark(
        UNIQUE, use_cache=False, label="Step 3: 20 unique prompts, no cache"
    )
    no_cache.report()

    _cache.clear()
    with_cache = await run_benchmark(
        MIXED, label="Step 4: 40 prompts (20 unique, 20 repeats), cache on"
    )
    with_cache.report()

    print("\n=== Step 6: p99 latency by concurrency (40 unique prompts, no cache) ===")
    sweep = [f"{p} (variant {v})" for p in UNIQUE for v in (1, 2)]
    for concurrency in (1, 5, 10, 20):
        r = await run_benchmark(sweep, concurrency=concurrency, use_cache=False)
        print(
            f"concurrency {concurrency:>2}: p50 {r.percentile(50):5.0f} ms | "
            f"p99 {r.percentile(99):5.0f} ms | {r.total_requests / r.elapsed_s:5.2f} req/s"
        )


if __name__ == "__main__":
    asyncio.run(main())
