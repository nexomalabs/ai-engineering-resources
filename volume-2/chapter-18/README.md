# Volume II · Chapter 18 — Lab: Design and Implement a Prompt Library

## What You Will Build

A prompt library for a legal AI team: five production prompts with metadata, tags and test cases, plus a `PromptLibrary` class that registers, retrieves, versions, searches, deprecates, and logs every change.

## Learning Outcomes

- Implement a `Prompt` dataclass with full metadata.
- Implement a `PromptLibrary` class with CRUD, tag search, version listing, and deprecation.
- Populate the library with five prompts covering legal document classification, clause extraction, risk scoring, summarization, and plain-language translation.
- Demonstrate retrieval by tag and by version.
- Demonstrate the deprecation workflow.

## Prerequisites

- Python 3.15
- Chapter 18, read through its hands-on lab
- Standard library only
- No API key. **Estimated API cost: $0.00** (a deterministic mock model stands in for the LLM)

## Setup

```bash
cd volume-2/chapter-18      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but versions are compared as text (TODO 1), so `1.10.0` would sort before `1.9.0`; search ignores tags and task type (TODO 2); and a deprecated version is returned without a warning (TODO 3). Complete the three TODOs.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
[Library] Registered: legal/document-classification@1.2.0
[Library] Registered: legal/clause-extraction@1.0.3
[Library] Registered: legal/risk-scoring@2.0.1
[Library] Registered: legal/document-summarization@1.1.0
[Library] Registered: legal/plain-language-translation@1.0.0

============================================================
ALL PROMPTS IN LIBRARY:
  legal/document-classification@1.2.0 — Legal Document Type Classifier
  legal/clause-extraction@1.0.3 — Legal Clause Extractor
  legal/risk-scoring@2.0.1 — Contract Risk Scorer
  legal/document-summarization@1.1.0 — Legal Document Summarizer
  legal/plain-language-translation@1.0.0 — Legal Plain Language Translator

============================================================
SEARCH: tag='domain:legal', task_type='classification'
  Found: legal/document-classification — Legal Document Type Classifier

============================================================
EXECUTE: document-classification
  Result: {
  "document_type": "service_agreement",
  "parties": [
    "Acme Corp",
    "TechVendor Ltd"
  ],
  "governing_law": "New York",
  "confidence": 0.93
}

============================================================
SCHEMA TEST: document-classification
  Test passed: True

============================================================
VERSION LISTING: legal/document-classification
[Library] Updated: legal/document-classification@1.3.0
  1.2.0 — stable (updated: 2026-10-14)
  1.3.0 — stable (updated: 2026-10-14)

============================================================
DEPRECATION: document-classification@1.2.0
[Library] Deprecated: legal/document-classification@1.2.0
Attempting to get deprecated version:
[Library] WARNING: 'legal/document-classification@1.2.0' is deprecated. Sunset: 2027-06-01. Replaced by: legal/document-classification@1.3.0

============================================================
CHANGELOG: legal/document-classification
  [REGISTER] v1.2.0 by legal-ai-team: Initial registration: Legal Document Type Classifier
  [UPDATE] v1.3.0 by legal-ai-team: MINOR: Added partnership_agreement document type.
  [DEPRECATE] v1.2.0 by governance: Deprecated. Sunset: 2027-06-01. Replaced by: legal/document-classification@1.3.0
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| The version dates in your output differ from the ones below | Each version records the time it was created | Expected; compare everything except the dates |

## Going Further

- Add a `bulk_test()` method that runs all test cases for all prompts and produces a coverage report.
- Implement a `PromptLibrary.export_catalog()` method that serializes the full catalog to JSON for compliance auditing.
- Add a `PromptLibrary.diff(prompt_id, version_a, version_b)` method that shows the textual differences between two versions of a prompt template.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with three TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
