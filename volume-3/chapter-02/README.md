# Volume III · Chapter 2 — Lab: Context Window Manager

## What You Will Build

A context window manager that takes content blocks with priorities, counts their tokens with tiktoken, keeps every required block, and fills the rest of a token budget with optional blocks in priority order. It reports which blocks were left out, and assembles the survivors into chat messages.

## Learning Outcomes

- Count tokens exactly with the tokenizer the model uses, rather than estimating.
- Enforce a token budget that leaves room for the model's answer.
- Apply priority-based truncation that never drops a required block.
- Refuse to build a context whose required blocks alone exceed the budget.
- Read a utilization report to see what was excluded and why.

## Prerequisites

- Python 3.15
- Chapter 2, read through its hands-on lab
- Dependencies: `tiktoken`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (nothing calls a model; tokens are counted locally)

The first run needs an internet connection: tiktoken downloads the `cl100k_base` encoding once and caches it.

## Setup

```bash
cd volume-3/chapter-02      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but it estimates tokens as one per four characters (TODO 1), so its report shows different counts: compare `tokens_used` with the reference. TODO 2 and TODO 3 do not change this demo's output; the tests check them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
=== TOKEN UTILIZATION REPORT ===
{
  "model": "gpt-6.1-sol",
  "token_budget": 200,
  "tokens_used": 184,
  "utilization_pct": 92.0,
  "blocks_total": 6,
  "blocks_included": 5,
  "blocks_excluded": 1,
  "excluded": [
    {
      "name": "retrieved_doc_2",
      "tokens": 66,
      "priority": 4
    }
  ]
}

=== FINAL MESSAGES ===

[SYSTEM]
## SYSTEM ROLE
You are a senior financial analyst. Answer all questions with data-driven precision.

## COMPLIANCE RULES
COMPLIANCE RULES:
1. Do not provide specific investment advice.
2. Always recommend consulting a licensed advisor.
3. Cite sources when providing market data.

## RETRIEVED DOC 1
MARKET REPORT (Q2): The Northwind 500 index closed the quarter at 5,480. Year-to-date return: 12.4%....

[USER]
What is the current policy interest rate and how does it affect bond yields?
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
| `ConnectionError` or SSL error on the first run | tiktoken could not download its encoding | Connect to the internet once; behind a proxy, set `HTTPS_PROXY` |
| `ValueError: Required blocks alone ...` | The required blocks do not fit the budget | Raise `token_budget`, or shorten a required block |

## Going Further

- Add a strict mode that stops at the first optional block that does not fit, and compare the two reports.
- Reserve an output budget: subtract a `max_output_tokens` value from the window before computing the input budget.
- Truncate an oversized optional block to fit, instead of dropping it whole, and mark it as truncated in the report.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 3 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
