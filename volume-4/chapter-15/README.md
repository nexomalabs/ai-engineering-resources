# Volume IV · Chapter 15 — Lab: Cost Tracking and Optimization Dashboard

## What You Will Build

A cost dashboard in two modules: `cost_tracker.py` prices each request from its token counts and a per-model price table, and generates a day of sample traffic; `cost_analyzer.py` breaks the cost down by feature and model, projects the monthly bill, and simulates three optimizations: prompt compression, routing to a cheaper model, and semantic caching.

## Learning Outcomes

- Price a request from its input and output tokens, priced separately.
- Attribute spend to features and models, to see where the money goes.
- Project a monthly bill from a sample period.
- Estimate the savings of compression, routing and caching, and explain why they differ.
- Recognize that compressing the prompt does not shrink the output bill.

## Prerequisites

- Python 3.15
- Chapter 15, read through its hands-on lab
- Dependencies: `tabulate`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (the traffic is simulated)

## Setup

```bash
cd volume-4/chapter-15      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/cost_analyzer.py          # your work
uv run python solution/cost_analyzer.py     # reference
```

`src/cost_analyzer.py` runs as supplied, but its monthly projection equals one day's cost (TODO 2), and it reports 25% savings from 25% prompt compression (TODO 3), because it shrinks the output bill too. TODO 1 is in `src/cost_tracker.py`; it does not change this demo's output, and the tests check it.

A fixed random seed makes the figures reproducible. They come from simulated traffic, and the price table holds October 2026 list prices: check current pricing before relying on it.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Generating 1,000 sample requests (representing 1 day of traffic)...

============================================================
  COST ANALYSIS REPORT
  Requests analyzed: 1,000
  Sample period:     1.0 day(s)
  Total cost:        $3.3307
  Avg per request:   $0.003331
  Monthly projection: $99.92
============================================================

Cost by Feature:
Feature           Cost     % Total
----------------  -------  ---------
customer_support  $1.1832  35.5%
document_summary  $0.8838  26.5%
code_review       $0.7583  22.8%
email_draft       $0.3846  11.5%
faq_lookup        $0.1208  3.6%

Cost by Model:
Model        Cost     % Total
-----------  -------  ---------
gpt-6.1-sol  $3.2683  98.1%
gpt-6-luna   $0.0624  1.9%

=================================================================
  OPTIMIZATION SIMULATION REPORT
  Baseline sample cost: $3.3307
  Baseline monthly projection: $99.92
=================================================================

Strategy                         Monthly Est.    Monthly Savings    Savings %
-------------------------------  --------------  -----------------  -----------
Baseline (no optimization)       $99.92          $0.00              0.0%
Prompt compression (25%)         $91.08          $8.84              8.8%
Model routing (60% to Luna)      $44.47          $55.45             55.5%
Semantic caching (35% hit rate)  $62.92          $37.00             37.0%
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `ModuleNotFoundError: No module named 'cost_tracker'` | Python cannot see the other module | Run the script by its path, `python src/cost_analyzer.py`, so its folder is on the path |
| Figures differ from the expected output | The random seed was changed or removed | Keep `random.seed(42)` at the start of the `__main__` block |

## Going Further

- Apply all three strategies together and compute the combined saving; explain why it is less than the sum (Lab Exercise 1).
- Deduplicate identical requests from the same user within five minutes (Lab Exercise 2).
- Raise an alert when the monthly projection exceeds a budget (Lab Exercise 3).
- Report cost per request and per token by feature, and name the two features with the most to gain (Lab Exercise 4).

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `cost_tracker.py`, `cost_analyzer.py`; runs, with 3 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
