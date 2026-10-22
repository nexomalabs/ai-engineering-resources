# Applied AI Engineering, Volume IV, Chapter 3
# Section 3.6, Real-Time Processing
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def stream_analysis(document_text: str) -> None:
    """Stream an AI analysis response, yielding tokens as they arrive."""
    stream = await client.chat.completions.create(
        model="gpt-6.1-sol",
        messages=[
            {"role": "system", "content": "Analyze the following document."},
            {"role": "user", "content": document_text}
        ],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
    print()  # newline after stream completes
