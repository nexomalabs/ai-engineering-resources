# Volume III · Chapter 16 — Lab: Document Processing Workflow

## What You Will Build

A three-stage document workflow: extraction cleans the raw text, classification returns a validated JSON label with a confidence, and summarization writes a summary shaped by the document's type. Every stage runs under a retry with exponential backoff, a stage that fails stops the pipeline, and a context object carries the results, the errors and the timing of each stage from one stage to the next.

## Learning Outcomes

- Pass state between stages in a single context object.
- Wrap an unreliable call in a retry with exponential backoff, and know when to give up.
- Validate a model's JSON before the next stage relies on it.
- Stop a pipeline at the first failed stage, and record where and why it stopped.
- Choose stage instructions from an earlier stage's output (type-aware summaries).

## Prerequisites

- Python 3.15
- Chapter 16, read through its hands-on lab
- Default mode: the standard library only, no API key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (six short calls, more if a stage retries)

## Setup

```bash
cd volume-3/chapter-16      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/document_workflow.py          # your work
uv run python solution/document_workflow.py     # reference
```

By default a stand-in plays the model (`stand_in.py`): it answers the three kinds of prompt from the document's own text, so every run gives the same result with no key. It also returns prose instead of JSON the first time it classifies a report, so you can watch the retry recover. The workflow itself is the chapter's code; only `call_llm()` checks the mode.

`src/document_workflow.py` runs as supplied, but it has no retry (TODO 1), so the report fails at classification; it does not validate the classification (TODO 2); and a failed stage does not stop the pipeline (TODO 3), so summarization runs on missing data. Complete all three.

For live mode:

```bash
uv sync --group live
NEXOMA_LAB_MODE=live OPENAI_API_KEY=... uv run python solution/document_workflow.py
```

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`). The log lines go to the terminal's error stream, so they are not in the saved output; they show the retry: `Attempt 1 failed: No JSON in classification response ... Retrying in 1.0s...`.

```text
DOCUMENT 1
============================================================
Type:    memo (94%)
Topic:   Remote Work Policy Update
Summary: Main point: Effective August 1, 2026, all employees may work remotely up to three days per week. Directive: Please update your schedules in the HR portal by July 31.
Timings: {'extract': 0.0, 'classify': 0.001, 'summarize': 0.0}

DOCUMENT 2
============================================================
Type:    report (91%)
Topic:   Q2 2026 Sales Report
Summary: Key findings: Total Revenue: $6.1M (up 31% YoY); ... Recommendation: Increase SDR headcount by 4 to address pipeline volume.
Timings: {'extract': 0.001, 'classify': 1.001, 'summarize': 0.002}
```

The timings change on every run. The report's classification takes about a second because of the retry's one-second wait. In live mode the wording, topics and confidences come from the model and will differ.

## Verifying Your Work

```bash
uv run pytest
```

Six tests: the retry recovers and waits 1 s then 2 s with a backoff of 2, the retry gives up after its last attempt, the memo runs all three stages, the report recovers from the malformed classification, an out-of-range confidence is rejected, and a failed extraction stops the pipeline. The tests replace `time.sleep`, so they do not wait. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With all three TODOs left in place, four tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `FAILED: [{'stage': 'classify', ...}]` for the report | TODO 1: no retry, so the first malformed answer is final | Retry with backoff, as the docstring describes |
| The report's summary reads "Summarize the key points" | TODO 3: the pipeline went on after a failure | Stop at the first failed stage |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |
| Live mode fails with an auth error | No `OPENAI_API_KEY` in this terminal | Set it, or stay in the default mode |
| `400 Unsupported value: 'temperature'` in live mode | `reasoning_effort="none"` was removed from `call_llm()` | Put it back: gpt-6-luna accepts a temperature only with reasoning off |

## Going Further

- Add a fourth stage, `store_to_database()`, that writes the result to SQLite.
- Skip summarization and flag the document for human review when confidence is below 0.7.
- Add a `WorkflowMonitor` that aggregates timings and failures across many runs.

## Files

| Path | Purpose |
|---|---|
| `src/document_workflow.py` | Your starting point; runs, with 3 TODOs |
| `src/stand_in.py`, `solution/stand_in.py` | The deterministic stand-in for the model |
| `solution/document_workflow.py` | Reference implementation: the chapter's code, with the mode switch in `call_llm()` |
| `tests/test_lab.py` | 6 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
