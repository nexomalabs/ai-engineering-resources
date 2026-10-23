# Applied AI Engineering, Volume III, Chapter 16
# Hands-on Lab: Document Processing Workflow
# Copied from the book by scripts/export_listings.py. Report errors as errata.

"""
Lab 16: Document Processing Workflow
A production-style sequential workflow with retry and validation.
"""

import json
import re
import time
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lab16")
client = OpenAI()


# ── Data Model ───────────────────────────────────────────────────────────────

@dataclass
class DocumentContext:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    raw_document: str = ""
    extracted_text: str = ""
    classification: dict = field(default_factory=dict)
    summary: str = ""
    errors: list = field(default_factory=list)
    timings: dict = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return len(self.errors) == 0


# ── Utilities ─────────────────────────────────────────────────────────────────

def call_llm(prompt: str, system: str = "You are a precise assistant.", max_tokens: int = 512) -> str:
    """LLM call with timeout handling."""
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.0,
        max_completion_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def retry(func, max_attempts: int = 3, backoff: float = 1.5):
    """Simple retry wrapper with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts:
                raise
            wait = backoff ** (attempt - 1)
            logger.warning("Attempt %d failed: %s. Retrying in %.1fs...", attempt, e, wait)
            time.sleep(wait)


# ── Workflow Steps ─────────────────────────────────────────────────────────────

def extract(ctx: DocumentContext) -> DocumentContext:
    """Stage 1: Extract and normalize text."""
    logger.info("[%s] Stage 1: Extraction", ctx.run_id)
    start = time.perf_counter()

    def _call():
        result = call_llm(
            f"Extract and clean the main text content. Remove formatting noise, "
            f"page numbers, and headers. Return only the clean body text.\n\n"
            f"Document:\n{ctx.raw_document}"
        )
        if len(result) < 20:
            raise ValueError("Extracted text too short; possible extraction failure.")
        return result

    ctx.extracted_text = retry(_call, max_attempts=3)
    ctx.timings["extract"] = round(time.perf_counter() - start, 3)
    logger.info("[%s] Extraction done in %.3fs (%d chars)", ctx.run_id,
                ctx.timings["extract"], len(ctx.extracted_text))
    return ctx


def classify(ctx: DocumentContext) -> DocumentContext:
    """Stage 2: Classify document type and topic."""
    logger.info("[%s] Stage 2: Classification", ctx.run_id)
    start = time.perf_counter()

    def _call():
        raw = call_llm(
            f"Classify the following document. Return ONLY a JSON object with keys:\n"
            f"- type: one of [report, article, email, memo, contract, other]\n"
            f"- topic: short descriptive phrase (max 8 words)\n"
            f"- confidence: float 0.0 to 1.0\n\n"
            f"Text:\n{ctx.extracted_text[:1500]}"
        )
        match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON in classification response: {raw[:100]}")
        parsed = json.loads(match.group())
        # Validate schema
        assert "type" in parsed and "topic" in parsed and "confidence" in parsed
        assert 0.0 <= float(parsed["confidence"]) <= 1.0
        return parsed

    ctx.classification = retry(_call, max_attempts=3)
    ctx.timings["classify"] = round(time.perf_counter() - start, 3)
    logger.info("[%s] Classified as '%s' (%.0f%% conf) in %.3fs",
                ctx.run_id, ctx.classification.get("type"),
                ctx.classification.get("confidence", 0) * 100,
                ctx.timings["classify"])
    return ctx


def summarize(ctx: DocumentContext) -> DocumentContext:
    """Stage 3: Generate type-aware summary."""
    logger.info("[%s] Stage 3: Summarization", ctx.run_id)
    start = time.perf_counter()
    doc_type = ctx.classification.get("type", "document")

    instructions = {
        "report": "Summarize the key findings, metrics, and recommendations.",
        "email": "Summarize the sender's intent and required action items.",
        "contract": "Summarize the parties, obligations, and key dates.",
        "memo": "Summarize the main point and any decisions or directives.",
    }.get(doc_type, "Summarize the key points in 3-5 sentences.")

    def _call():
        result = call_llm(
            f"{instructions}\n\nDocument ({doc_type}):\n{ctx.extracted_text[:2000]}",
            max_tokens=256
        )
        if len(result) < 30:
            raise ValueError("Summary too short.")
        return result

    ctx.summary = retry(_call, max_attempts=3)
    ctx.timings["summarize"] = round(time.perf_counter() - start, 3)
    logger.info("[%s] Summary done in %.3fs", ctx.run_id, ctx.timings["summarize"])
    return ctx


# ── Orchestrator ───────────────────────────────────────────────────────────────

def run_workflow(document: str) -> DocumentContext:
    """Execute the sequential document processing workflow."""
    ctx = DocumentContext(raw_document=document)
    pipeline = [extract, classify, summarize]

    logger.info("=== Workflow %s started ===", ctx.run_id)
    for stage in pipeline:
        try:
            ctx = stage(ctx)
        except Exception as exc:
            error_entry = {"stage": stage.__name__, "error": str(exc)}
            ctx.errors.append(error_entry)
            logger.error("[%s] Pipeline stopped at %s: %s", ctx.run_id, stage.__name__, exc)
            break

    total = sum(ctx.timings.values())
    logger.info("=== Workflow %s finished in %.3fs. Success: %s ===",
                ctx.run_id, total, ctx.succeeded)
    return ctx


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    documents = [
        """
        MEMORANDUM
        To: All Staff | From: CEO | Date: July 27, 2026
        Re: Remote Work Policy Update

        Effective August 1, 2026, all employees may work remotely up to three days per week.
        Departments requiring on-site presence will receive separate guidance from their directors.
        Please update your schedules in the HR portal by July 31.
        """,
        """
        Q2 2026 SALES REPORT — NEXOMA LABS LLC
        Total Revenue: $6.1M (up 31% YoY)
        New Customers: 142
        Churn Rate: 2.1%
        Top Product: Context Engineering Suite (43% of revenue)
        Pipeline: $18M qualified, close rate 28%
        Recommendation: Increase SDR headcount by 4 to address pipeline volume.
        """,
    ]

    for i, doc in enumerate(documents, 1):
        print(f"\n{'='*60}")
        print(f"DOCUMENT {i}")
        print("="*60)
        result = run_workflow(doc)
        if result.succeeded:
            print(f"Type:    {result.classification.get('type')} "
                  f"({result.classification.get('confidence', 0):.0%})")
            print(f"Topic:   {result.classification.get('topic')}")
            print(f"Summary: {result.summary}")
            print(f"Timings: {result.timings}")
        else:
            print(f"FAILED: {result.errors}")
