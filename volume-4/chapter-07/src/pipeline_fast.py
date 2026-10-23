"""Step 3: the same pipeline with the profile's findings fixed (the "after").

- The three calls for a document run concurrently (asyncio.gather), and so do the
  documents, up to MAX_IN_FLIGHT requests at a time.
- The report is built with one "".join over a list, in memory; nothing goes to disk.

    NEXOMA_LAB_MODE=fixture  (default) a simulated API; no key
    NEXOMA_LAB_MODE=live     calls gpt-6-luna; needs OPENAI_API_KEY and `--group live`
"""

import asyncio
import os

from documents import DOCUMENTS

MAX_IN_FLIGHT = 10  # stay within the provider's concurrency limit

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
else:
    from stand_in import StandInAsyncClient

    client = StandInAsyncClient()


async def _ask(prompt: str, max_tokens: int, limit: asyncio.Semaphore) -> str:
    # TODO 3: hold `limit` around the call, so no more than MAX_IN_FLIGHT requests run
    # at once once TODOs 1 and 2 make them concurrent.
    resp = await client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


async def process_document(text: str, limit: asyncio.Semaphore) -> dict:
    # TODO 1: the three calls do not depend on each other. Run them together with
    # asyncio.gather instead of awaiting them one by one.
    sentiment = await _ask(f"Classify as POSITIVE/NEGATIVE/NEUTRAL: {text}", 10, limit)
    summary = await _ask(f"Summarize in one sentence: {text}", 60, limit)
    keywords = await _ask(f"List top 3 keywords, comma-separated: {text}", 30, limit)
    return {"sentiment": sentiment, "summary": summary, "keywords": keywords}


def build_report(results: list[dict]) -> str:
    return "".join(
        f"Document {i}\n  Sentiment: {r['sentiment']}\n  Summary:   {r['summary']}\n"
        f"  Keywords:  {r['keywords']}\n"
        for i, r in enumerate(results, 1)
    )


async def process_all_documents_async(docs: list[str]) -> str:
    limit = asyncio.Semaphore(MAX_IN_FLIGHT)
    # TODO 2: process the documents concurrently too (asyncio.gather over all of them).
    results = [await process_document(text, limit) for text in docs]
    return build_report(results)


def process_all_documents(docs: list[str]) -> str:
    return asyncio.run(process_all_documents_async(docs))


if __name__ == "__main__":
    print(process_all_documents(DOCUMENTS))
