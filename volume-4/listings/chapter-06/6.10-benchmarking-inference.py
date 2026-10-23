# Applied AI Engineering, Volume IV, Chapter 6
# Section 6.10, Benchmarking Inference
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Inference benchmark harness
# Requires: pip install openai numpy

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import openai

client = openai.AsyncOpenAI()  # reads OPENAI_API_KEY from environment

# --- Simple in-memory exact-match cache ---
_cache: dict[str, str] = {}

def _cache_key(prompt: str, model: str) -> str:
    return hashlib.sha256(f"{model}::{prompt}".encode()).hexdigest()

async def cached_complete(prompt: str, model: str = "gpt-6-luna", max_tokens: int = 100) -> tuple[str, bool]:
    """Return (response_text, cache_hit)."""
    key = _cache_key(prompt, model)
    if key in _cache:
        return _cache[key], True
    response = await client.chat.completions.create(
        model=model,
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
    )
    text = response.choices[0].message.content or ""
    _cache[key] = text
    return text, False

@dataclass
class BenchmarkResult:
    latencies_ms: list[float] = field(default_factory=list)
    cache_hits: int = 0
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    elapsed_s: float = 0.0

    def report(self) -> None:
        arr = np.array(self.latencies_ms)
        rps = self.total_requests / self.elapsed_s if self.elapsed_s else 0
        tps = self.total_tokens / self.elapsed_s if self.elapsed_s else 0
        cost_per_1k = (self.total_cost_usd / self.total_tokens * 1000) if self.total_tokens else 0
        print(f"\n=== Benchmark Report ===")
        print(f"Requests      : {self.total_requests}")
        print(f"Cache hits    : {self.cache_hits} ({100*self.cache_hits/max(self.total_requests,1):.1f}%)")
        print(f"Throughput    : {rps:.2f} req/s | {tps:.1f} tok/s")
        print(f"Latency p50   : {np.percentile(arr,50):.0f} ms")
        print(f"Latency p95   : {np.percentile(arr,95):.0f} ms")
        print(f"Latency p99   : {np.percentile(arr,99):.0f} ms")
        print(f"Cost/1K tokens: ${cost_per_1k:.4f}")

async def run_benchmark(
    prompts: list[str],
    model: str = "gpt-6-luna",
    max_tokens: int = 100,
    concurrency: int = 5,
    cost_per_1k_tokens: float = 0.0005,  # gpt-6-luna output price, Chapter 15
) -> BenchmarkResult:
    result = BenchmarkResult()
    semaphore = asyncio.Semaphore(concurrency)

    async def single_request(prompt: str) -> None:
        async with semaphore:
            t0 = time.perf_counter()
            text, hit = await cached_complete(prompt, model, max_tokens)
            latency_ms = (time.perf_counter() - t0) * 1000
            token_count = len(text.split())  # approximation
            result.latencies_ms.append(latency_ms)
            result.total_requests += 1
            result.total_tokens += token_count
            result.total_cost_usd += token_count * cost_per_1k_tokens / 1000
            if hit:
                result.cache_hits += 1

    t_start = time.perf_counter()
    await asyncio.gather(*[single_request(p) for p in prompts])
    result.elapsed_s = time.perf_counter() - t_start
    return result

if __name__ == "__main__":
    # Mix of unique and repeated prompts to demonstrate cache benefit
    test_prompts = [
        "What is the capital of France?",
        "Summarize the concept of machine learning in one sentence.",
        "What is the capital of France?",  # repeat — cache hit
        "List three benefits of cloud computing.",
        "What is the capital of France?",  # repeat — cache hit
        "Explain REST API in one sentence.",
        "Summarize the concept of machine learning in one sentence.",  # repeat
    ]

    result = asyncio.run(run_benchmark(test_prompts, concurrency=3))
    result.report()
