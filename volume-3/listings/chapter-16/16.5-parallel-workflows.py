# Applied AI Engineering, Volume III, Chapter 16
# Section 16.5, Parallel Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import time
from dataclasses import dataclass
from openai import AsyncOpenAI

async_client = AsyncOpenAI()


@dataclass
class AnalysisResult:
    analyzer: str
    output: dict
    duration: float
    error: Optional[str] = None


async def analyze_sentiment(text: str) -> AnalysisResult:
    start = time.perf_counter()
    try:
        response = await async_client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": "You are a sentiment analyst. Return JSON: {sentiment, score, key_phrases}"},
                {"role": "user", "content": f"Analyze sentiment:\n{text}"},
            ],
            temperature=0.0,
            max_completion_tokens=200,
        )
        import json, re
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"sentiment": "neutral", "score": 0.5}
        return AnalysisResult("sentiment", result, time.perf_counter() - start)
    except Exception as e:
        return AnalysisResult("sentiment", {}, time.perf_counter() - start, str(e))


async def extract_entities(text: str) -> AnalysisResult:
    start = time.perf_counter()
    try:
        response = await async_client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": "Extract named entities. Return JSON: {people, organizations, locations, dates}"},
                {"role": "user", "content": f"Extract entities:\n{text}"},
            ],
            temperature=0.0,
            max_completion_tokens=300,
        )
        import json, re
        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {}
        return AnalysisResult("entities", result, time.perf_counter() - start)
    except Exception as e:
        return AnalysisResult("entities", {}, time.perf_counter() - start, str(e))


async def run_parallel_analysis(document: str) -> dict:
    """Dispatch multiple analyzers concurrently and aggregate results."""
    start = time.perf_counter()

    results = await asyncio.gather(
        analyze_sentiment(document),
        extract_entities(document),
        return_exceptions=False,
    )

    total_time = time.perf_counter() - start
    aggregated = {r.analyzer: r.output for r in results if not r.error}
    errors = [{"analyzer": r.analyzer, "error": r.error} for r in results if r.error]

    return {
        "analyses": aggregated,
        "errors": errors,
        "total_duration": round(total_time, 3),
        "individual_durations": {r.analyzer: round(r.duration, 3) for r in results},
    }


if __name__ == "__main__":
    doc = "Quillmark Software reported record Q3 revenue of $4.2M, driven by its AI consulting division."
    output = asyncio.run(run_parallel_analysis(doc))
    import json
    print(json.dumps(output, indent=2))
