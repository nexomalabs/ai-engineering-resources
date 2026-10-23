"""A deterministic stand-in for the model, used when NEXOMA_LAB_MODE is not "live".

It recognises the three prompts the workflow sends (extraction, classification and
summarization) and answers each from the document's own text, so the lab runs with no
API key and gives the same output every time. The first classification of a report
comes back as prose with no JSON, so the workflow's retry path runs once.
"""

import json
import re

_flaky_report_pending = True


def reset() -> None:
    """Make the next report classification fail once again (used by the tests)."""
    global _flaky_report_pending
    _flaky_report_pending = True


def _after(marker: str, prompt: str) -> str:
    return prompt.split(marker, 1)[1] if marker in prompt else prompt


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _extract(prompt: str) -> str:
    return "\n".join(_lines(_after("Document:\n", prompt)))


def _classify(prompt: str) -> str:
    global _flaky_report_pending
    text = _after("Text:\n", prompt)
    lines = _lines(text)
    if "MEMORANDUM" in text:
        topic = next((ln[3:].strip() for ln in lines if ln.startswith("Re:")), lines[0])
        return json.dumps({"type": "memo", "topic": topic, "confidence": 0.94})
    if "REPORT" in text:
        if _flaky_report_pending:
            _flaky_report_pending = False
            return "This document appears to be a quarterly sales report."
        topic = lines[0].split("—")[0].strip().title()
        return json.dumps({"type": "report", "topic": topic, "confidence": 0.91})
    return json.dumps(
        {"type": "other", "topic": " ".join(lines[0].split()[:8]), "confidence": 0.55}
    )


def _summarize(prompt: str) -> str:
    doc_type = re.search(r"Document \((\w+)\):", prompt)
    lines = _lines(_after("):\n", prompt))
    if doc_type and doc_type.group(1) == "memo":
        body = [ln for ln in lines if not re.match(r"^(MEMORANDUM|To:|Re:)", ln)]
        directive = next((ln for ln in body if ln.startswith("Please")), "")
        return f"Main point: {body[0]} Directive: {directive}".strip()
    if doc_type and doc_type.group(1) == "report":
        metrics = [ln for ln in lines[1:] if ":" in ln and not ln.startswith("Recommendation")]
        action = next((ln for ln in lines if ln.startswith("Recommendation")), "")
        return f"Key findings: {'; '.join(metrics)}. {action}"
    return " ".join(lines[:3])


def reply(prompt: str) -> str:
    if prompt.startswith("Extract and clean"):
        return _extract(prompt)
    if prompt.startswith("Classify the following document"):
        return _classify(prompt)
    return _summarize(prompt)
