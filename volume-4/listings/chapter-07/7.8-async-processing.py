# Applied AI Engineering, Volume IV, Chapter 7
# Section 7.8, Async Processing
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Async AI pipeline with parallel API calls
# Requires: pip install openai aiohttp

import asyncio
import time
import openai

client = openai.AsyncOpenAI()

async def classify(text: str) -> str:
    """Classify document sentiment."""
    resp = await client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": f"Classify as POSITIVE/NEGATIVE/NEUTRAL: {text}"}],
        max_tokens=10,
    )
    return resp.choices[0].message.content or "UNKNOWN"

async def summarize(text: str) -> str:
    """Summarize document in one sentence."""
    resp = await client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": f"Summarize in one sentence: {text}"}],
        max_tokens=60,
    )
    return resp.choices[0].message.content or ""

async def extract_keywords(text: str) -> str:
    """Extract top-3 keywords."""
    resp = await client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": f"List top 3 keywords, comma-separated: {text}"}],
        max_tokens=30,
    )
    return resp.choices[0].message.content or ""

async def process_document(text: str) -> dict:
    """Run all three analyses in parallel."""
    t0 = time.perf_counter()
    sentiment, summary, keywords = await asyncio.gather(
        classify(text),
        summarize(text),
        extract_keywords(text),
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "sentiment": sentiment.strip(),
        "summary": summary.strip(),
        "keywords": keywords.strip(),
        "elapsed_ms": round(elapsed, 1),
    }

async def process_sequential(text: str) -> dict:
    """Run analyses sequentially for comparison."""
    t0 = time.perf_counter()
    sentiment = await classify(text)
    summary = await summarize(text)
    keywords = await extract_keywords(text)
    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "sentiment": sentiment.strip(),
        "summary": summary.strip(),
        "keywords": keywords.strip(),
        "elapsed_ms": round(elapsed, 1),
    }

if __name__ == "__main__":
    sample = (
        "The new framework dramatically simplifies deployment of large language models "
        "while reducing infrastructure costs by 40 percent in early benchmarks."
    )

    print("=== Sequential ===")
    seq_result = asyncio.run(process_sequential(sample))
    print(seq_result)

    print("\n=== Parallel ===")
    par_result = asyncio.run(process_document(sample))
    print(par_result)

    speedup = seq_result["elapsed_ms"] / par_result["elapsed_ms"]
    print(f"\nSpeedup: {speedup:.2f}x")
