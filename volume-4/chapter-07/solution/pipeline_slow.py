"""Step 1: a deliberately slow, synchronous document pipeline (the "before").

For each of ten documents it calls classify, summarize and extract_keywords one after
another, then builds a report by repeated string concatenation, writes it to a temporary
file and reads it back. Profile it to see where the time goes.

    NEXOMA_LAB_MODE=fixture  (default) a simulated API; no key
    NEXOMA_LAB_MODE=live     calls gpt-6-luna; needs OPENAI_API_KEY and `--group live`
"""

import os
import tempfile

from documents import DOCUMENTS

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    from openai import OpenAI

    client = OpenAI()
else:
    from stand_in import StandInClient

    client = StandInClient()


def _ask(prompt: str, max_tokens: int) -> str:
    resp = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def classify(text: str) -> str:
    return _ask(f"Classify as POSITIVE/NEGATIVE/NEUTRAL: {text}", 10)


def summarize(text: str) -> str:
    return _ask(f"Summarize in one sentence: {text}", 60)


def extract_keywords(text: str) -> str:
    return _ask(f"List top 3 keywords, comma-separated: {text}", 30)


def build_report(results: list[dict]) -> str:
    report = ""
    for i, r in enumerate(results, 1):
        report += f"Document {i}\n"
        report += f"  Sentiment: {r['sentiment']}\n"
        report += f"  Summary:   {r['summary']}\n"
        report += f"  Keywords:  {r['keywords']}\n"
    return report


def round_trip_through_disk(report: str) -> str:
    """Write the report to a temporary file and read it back: work that adds nothing."""
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(report)
        path = f.name
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.remove(path)


def process_all_documents(docs: list[str]) -> str:
    results = []
    for text in docs:
        results.append(
            {
                "sentiment": classify(text),
                "summary": summarize(text),
                "keywords": extract_keywords(text),
            }
        )
    return round_trip_through_disk(build_report(results))


if __name__ == "__main__":
    print(process_all_documents(DOCUMENTS))
