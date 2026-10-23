# Applied AI Engineering, Volume III, Chapter 16
# Section 16.4, Sequential Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI()


@dataclass
class WorkflowContext:
    """Accumulates state across workflow steps."""
    document: str
    extracted_text: Optional[str] = None
    classification: Optional[dict] = None
    summary: Optional[str] = None
    errors: list = field(default_factory=list)
    step_timings: dict = field(default_factory=dict)


def llm_call(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """Single LLM inference call with error handling."""
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_completion_tokens=512,
    )
    return response.choices[0].message.content.strip()


def step_extract(ctx: WorkflowContext) -> WorkflowContext:
    """Step 1: Extract and clean text from raw document."""
    start = time.perf_counter()
    logger.info("Step 1: Extraction")

    prompt = (
        f"Clean and extract the main body text from the following document. "
        f"Remove headers, footers, and formatting artifacts. "
        f"Return only the cleaned text.\n\nDocument:\n{ctx.document}"
    )
    ctx.extracted_text = llm_call(prompt)
    ctx.step_timings["extract"] = round(time.perf_counter() - start, 3)
    logger.info("Extraction complete in %.3fs", ctx.step_timings["extract"])
    return ctx


def step_classify(ctx: WorkflowContext) -> WorkflowContext:
    """Step 2: Classify the document type and topic."""
    start = time.perf_counter()
    logger.info("Step 2: Classification")

    prompt = (
        f"Classify the following text. Return a JSON object with keys: "
        f"'type' (one of: report, article, email, memo, contract), "
        f"'topic' (short phrase), 'confidence' (0.0-1.0).\n\n"
        f"Text:\n{ctx.extracted_text}"
    )
    import json, re
    raw = llm_call(prompt)
    # Extract JSON from response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        ctx.classification = json.loads(match.group())
    else:
        ctx.classification = {"type": "unknown", "topic": "unknown", "confidence": 0.0}
    ctx.step_timings["classify"] = round(time.perf_counter() - start, 3)
    logger.info("Classification: %s (%.0f%% confidence)",
                ctx.classification.get("type"), ctx.classification.get("confidence", 0) * 100)
    return ctx


def step_summarize(ctx: WorkflowContext) -> WorkflowContext:
    """Step 3: Summarize the document with type-aware instructions."""
    start = time.perf_counter()
    logger.info("Step 3: Summarization")

    doc_type = ctx.classification.get("type", "document") if ctx.classification else "document"
    prompt = (
        f"Summarize this {doc_type} in 3-5 sentences. "
        f"Focus on the key facts, decisions, or findings.\n\n"
        f"Text:\n{ctx.extracted_text}"
    )
    ctx.summary = llm_call(prompt)
    ctx.step_timings["summarize"] = round(time.perf_counter() - start, 3)
    logger.info("Summarization complete in %.3fs", ctx.step_timings["summarize"])
    return ctx


def run_sequential_workflow(document: str) -> WorkflowContext:
    """Execute the three-step sequential workflow."""
    ctx = WorkflowContext(document=document)
    steps = [step_extract, step_classify, step_summarize]

    for step in steps:
        try:
            ctx = step(ctx)
        except Exception as exc:
            logger.error("Step %s failed: %s", step.__name__, exc)
            ctx.errors.append({"step": step.__name__, "error": str(exc)})
            break  # Sequential: failure stops the pipeline

    return ctx


if __name__ == "__main__":
    sample_doc = """
    QUARTERLY FINANCIAL REPORT - Q3 2025
    Nexoma Labs LLC | Confidential

    Revenue for Q3 2025 reached $4.2M, representing a 23% increase over Q3 2024.
    Operating expenses totaled $2.8M. Net profit margin stood at 33%.
    The growth was driven primarily by the AI consulting division (+41%)
    and the SaaS platform subscriptions (+18%).
    Headcount increased from 47 to 63 full-time employees.
    """
    result = run_sequential_workflow(sample_doc)
    print("\n=== WORKFLOW RESULTS ===")
    print(f"Type: {result.classification}")
    print(f"Summary: {result.summary}")
    print(f"Timings: {result.step_timings}")
    if result.errors:
        print(f"Errors: {result.errors}")
