# Volume IV · Chapter 14 — Lab: LLM-as-Judge Evaluation Pipeline

## What You Will Build

An evaluation pipeline in which a judge scores each answer on accuracy, helpfulness, safety and conciseness, validated by a Pydantic schema, then combines the scores with weights, aggregates them into a report and flags anything below 0.60. The lab completes two of the chapter's exercises: a regression check that compares two runs on the same questions, and a loader that evaluates question-and-answer pairs from a CSV file.

## Learning Outcomes

- Define a judge's output as a validated schema, so a malformed score fails loudly.
- Combine dimension scores with explicit weights.
- Aggregate a run, and flag the items that need a human to look at them.
- Detect a regression: a dimension that drops by more than a tolerance between two versions.
- Explain what a mock judge can and cannot tell you, and when to switch to a real one.

## Prerequisites

- Python 3.15
- Chapter 14, read through its hands-on lab
- Dependencies: `pydantic`, `tabulate`, installed by `uv sync`
- Default mode: the mock judge, no key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` as the judge

## Setup

```bash
cd volume-4/chapter-14      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/evaluation_runner.py          # your work
uv run python solution/evaluation_runner.py     # reference
```

On Windows, if the report's bars and warning sign print as `?`, run `$env:PYTHONIOENCODING = "utf-8"` first.

By default the mock judge scores each answer (`mock_judge` in `evaluation_runner.py`). It is deterministic: accuracy is the share of the reference answer's key terms that appear in the response, a refusal or a wrong answer is scored as unhelpful, and a small fixed variation per item stands in for a judge's noise. With `NEXOMA_LAB_MODE=live` the chapter's `real_judge` asks `gpt-6-luna` instead.

`src/` runs as supplied, but its overall score is a plain average that ignores the weights (TODO 1), and its regression check never reports anything (TODO 2). Complete both.

## Expected Result

The reference prints a report for the five sample items, then the two exercises (full output in `expected/output.txt`):

```text
  ⚠️  2 items scored below 0.60:
  - q003: 0.522 — Disagrees with the reference answer.
  - q005: 0.411 — Refused a reasonable request.

============================================================
  Exercise 3: regression check
============================================================
...
  REGRESSION  accuracy     dropped by 0.112
  REGRESSION  helpfulness  dropped by 0.080
  REGRESSION  overall      dropped by 0.067
```

The two flagged items are the ones the sample set plants: "2 + 2 = 5", and a refusal to give a cake recipe. The regression check re-runs the same five questions with one answer made worse ("I'm not sure. Try contacting someone." for the password question) and names the three dimensions that fell by more than 0.05. The CSV run flags the wrong planet (Venus for Mercury) and another refusal.

The mock judge only matches words. It would pass a fluent answer that happens to repeat the reference's terms while getting the substance wrong; a real judge reads the meaning, at the cost of calls and some noise of its own. That trade is what the chapter's first exercise asks you to measure.

## Verifying Your Work

```bash
uv run pytest
```

Eight tests: the weights, schema validation, the judge prompt with and without a reference, the mock judge's determinism, the two flagged sample items, regression detection with a tolerance, CSV loading with an empty reference, and the bundled CSV's two flagged items. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With both TODOs left in place, four tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| The flagged items differ from the reference | TODO 1: the overall score ignores the weights | Multiply each score by its weight and add them |
| The regression check never fires | TODO 2 still returns an empty dict | Report each dimension whose drop exceeds the tolerance |
| `ValidationError` in live mode | The judge returned a score above 1 or missed a field | Keep `response_format={"type": "json_object"}` and the schema in the system prompt; retry once |
| `UnicodeEncodeError` on Windows | The console's code page cannot print the report's symbols | Set `PYTHONIOENCODING=utf-8` |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |

## Going Further

- Run the real judge on the same items, twice, and measure how much its scores move between runs.
- Add a `consistency` dimension: does the response contradict itself?
- Ask the judge for its reasoning before its scores, and check whether its accuracy against your own labels improves.

## Files

| Path | Purpose |
|---|---|
| `src/llm_judge.py`, `src/evaluation_runner.py` | Your starting point; runs, with 2 TODOs |
| `solution/llm_judge.py` | Step 1: the schema and the judge prompt |
| `solution/evaluation_runner.py` | Step 2 with the mode switch, plus exercises 3 and 4 |
| `solution/sample_qa.csv` | Five question-and-answer pairs for exercise 4 |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
