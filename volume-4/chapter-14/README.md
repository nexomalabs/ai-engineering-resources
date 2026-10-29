# Volume IV · Chapter 14 — Lab: LLM-as-Judge Evaluation Pipeline

## What You Will Build

An evaluation pipeline in which a judge scores each answer on accuracy, helpfulness, safety and conciseness, validated by a Pydantic schema, then combines the scores with weights, aggregates them into a report and flags anything below 0.60. The lab completes two of the chapter's exercises: a regression check that compares two runs on the same questions, and a loader that evaluates question-and-answer pairs from a CSV file. A second script, `quality_gate.py`, replays the chapter's opening story: a release gate that compares the mean score of every slice of a refund evaluation suite, each language and each customer tier, and blocks Dev's new prompt, which raises the average but answers Portuguese questions in English.

## Learning Outcomes

- Define a judge's output as a validated schema, so a malformed score fails loudly.
- Combine dimension scores with explicit weights.
- Aggregate a run, and flag the items that need a human to look at them.
- Detect a regression: a dimension that drops by more than a tolerance between two versions.
- Explain what a mock judge can and cannot tell you, and when to switch to a real one.
- Gate a release on every slice of the evaluation suite, so that a regression in one language cannot hide inside a better average.

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

`src/` runs as supplied, but its overall score is a plain average that ignores the weights (TODO 1), and its regression check never reports anything (TODO 2). Complete both. The release gate has TODO 3, below.

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

## The Release Gate

```bash
uv run python src/quality_gate.py          # your work
uv run python solution/quality_gate.py     # reference
```

Three CSV files hold three versions of Wren's refund prompt answering the same twelve questions, six in English, three in Spanish and three in Portuguese, from personal and business customers. Their `language` and `tier` columns become each item's slices. Version 1 is in production, version 2 is Dev's new prompt, and version 3 is version 2 with its Portuguese replies fixed. The gate compares versions 2 and 3 with version 1 and blocks a change if the whole suite or any slice falls by more than 0.05. As supplied, it compares only the whole suite (TODO 3), and so it passes version 2. The reference prints (also saved in `expected/quality_gate.txt`):

```text
Refund prompt v2 against v1, tolerance 0.05
  slice           items     v1     v2  change
  all                12  0.678  0.817  +0.139
  language=en         6  0.679  0.912  +0.233
  language=es         3  0.685  0.872  +0.187
  language=pt         3  0.669  0.572  -0.097  BLOCK
  tier=business       5  0.717  0.815  +0.099
  tier=personal       7  0.651  0.819  +0.168
  Gate: blocked by language=pt

Refund prompt v3 against v1, tolerance 0.05
  slice           items     v1     v3  change
  all                12  0.678  0.888  +0.210
  language=en         6  0.679  0.912  +0.233
  language=es         3  0.685  0.872  +0.187
  language=pt         3  0.669  0.855  +0.185
  tier=business       5  0.717  0.882  +0.165
  tier=personal       7  0.651  0.892  +0.242
  Gate: passed
```

The mock judge scores accuracy by the reference answer's key terms, so an English reply to a Portuguese question scores low; the real judge's rubric asks for an answer in the language the user wrote in. A fixed tolerance suits the mock judge, which gives the same scores on every run; a real judge's tolerance should come from repeated runs of the unchanged prompt.

## Verifying Your Work

```bash
uv run pytest
```

Twelve tests. Eight cover the pipeline: the weights, schema validation, the judge prompt with and without a reference, the mock judge's determinism, the two flagged sample items, regression detection with a tolerance, CSV loading with an empty reference, and the bundled CSV's two flagged items. Four more test the release gate: extra CSV columns become slices, a slice that falls too far blocks a change that raised the average, the story's prompt is blocked on the Portuguese slice alone, and the fixed prompt passes every language and tier. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With the three TODOs left in place, seven of the twelve tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| The flagged items differ from the reference | TODO 1: the overall score ignores the weights | Multiply each score by its weight and add them |
| The regression check never fires | TODO 2 still returns an empty dict | Report each dimension whose drop exceeds the tolerance |
| The gate passes version 2 and shows only the `all` row | TODO 3: the gate compares only the average over the whole suite | Add a row for each value of every slice key, from `slice_means()` on both runs |
| `ValidationError` in live mode | The judge returned a score above 1 or missed a field | Keep `response_format={"type": "json_object"}` and the schema in the system prompt; retry once |
| `UnicodeEncodeError` on Windows | The console's code page cannot print the report's symbols | Set `PYTHONIOENCODING=utf-8` |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |

## Going Further

- Run the real judge on the same items, twice, and measure how much its scores move between runs.
- Add a `consistency` dimension: does the response contradict itself?
- Run the real judge five times on version 1 of the refund suite, and set the gate's tolerance from how far each slice's mean moves between runs.
- Ask the judge for its reasoning before its scores, and check whether its accuracy against your own labels improves.

## Files

| Path | Purpose |
|---|---|
| `src/llm_judge.py`, `src/evaluation_runner.py`, `src/quality_gate.py` | Your starting point; runs, with 3 TODOs |
| `solution/llm_judge.py` | Step 1: the schema and the judge prompt |
| `solution/evaluation_runner.py` | Step 2 with the mode switch, plus exercises 3 and 4 |
| `solution/sample_qa.csv` | Five question-and-answer pairs for exercise 4 |
| `solution/quality_gate.py` | Step 3: the release gate from the chapter's story, checked slice by slice |
| `solution/refund_v1.csv`, `refund_v2.csv`, `refund_v3.csv` | Three refund prompts' answers to the same twelve questions, with each item's language and tier |
| `tests/test_lab.py` | 12 tests, run against `solution/` |
| `expected/output.txt` | Captured output of `evaluation_runner.py` |
| `expected/quality_gate.txt` | Captured output of `quality_gate.py` |
