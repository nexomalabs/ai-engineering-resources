# Volume II · Chapter 20 — Lab: Customer Support AI Prompt Engineering Workflow (Capstone)

## What You Will Build

A complete prompt engineering workflow for StreamNest, a fictional video streaming service: output schemas, a ticket classifier, two response-generator variants, an evaluator whose score is recomputed rather than trusted, a pipeline that routes risky or unclear tickets to a human, nine test cases across three tiers, a baseline run, and an A/B comparison.

## Learning Outcomes

- Complete a requirements analysis (quality targets, constraints, functional requirements).
- Design the prompt architecture (component map, output schemas for all components).
- Implement the three core prompts (classifier, response generator, evaluator) using the provided starter code.
- Build and run the evaluation pipeline on the provided test cases.
- Design two prompt variants (A and B) for the response generator and run an A/B comparison.
- Produce a written Architecture Document and an Evaluation Report (minimum one page each).
- Run a three-role Review Board (Chapter 19) on your Architecture Document, and record the findings, any disagreement between reviewers, and what you changed.

## Prerequisites

- Python 3.15
- Chapter 20, read through its hands-on lab
- Standard library only
- No API key. **Estimated API cost: $0.00** (a deterministic, rule-based mock model stands in for the LLM)

## Setup

```bash
cd volume-2/chapter-20      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` is the starter printed in Chapter 20. It runs, but prints only the two section headings until you complete its six TODOs. `solution/lab.py` is one way to complete them; your schemas, prompts and test cases may differ. The mock model's scores illustrate the method and are not measurements of a real model.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
StreamNest Support AI — Capstone Baseline
  T001 standard     subscription_billing   -> human_review
  T002 standard     streaming_quality      -> human_review
  T003 standard     content_questions      -> human_review
  T004 edge         subscription_billing   -> human
  T005 edge         subscription_billing   -> human_review
  T006 edge         escalate_to_human      -> human
  T007 adversarial  escalate_to_human      -> human
  T008 adversarial  escalate_to_human      -> human
  T009 adversarial  escalate_to_human      -> human
{
  "classification_accuracy": 1.0,
  "avg_quality_score": 0.69,
  "escalation_rate": 0.556
}

A/B Test: Response Generator Variant Comparison
{
  "variants": {
    "A": {
      "cases": 4,
      "mean_quality": 0.69,
      "mean_brand_voice": 2.0
    },
    "B": {
      "cases": 4,
      "mean_quality": 0.93,
      "mean_brand_voice": 5.0
    }
  },
  "winner": "B",
  "difference": 0.24,
  "caveat": "4 cases, mock judge: illustrative, not statistically significant (Section 13.5)"
}
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
| Your pipeline returns `None` | A TODO method still ends in `pass` | Implement `classify`, `generate_response`, `evaluate` and `run` |

## Going Further

- Add a fourth component to the pipeline: a **Personalization Layer** that adjusts the response tone based on the customer's tier (free, standard, premium). Demonstrate that the quality score improves for premium customers.
- Implement a **Retry Loop**: if the evaluation score is between 0.65 and 0.78 (below threshold but not catastrophic), regenerate the response once with the `top_improvement` feedback injected into the response generator prompt. Measure whether the retry succeeds more than 70% of the time.
- Design a **Drift Detection System**: run the evaluation pipeline once per week on the same fixed test set and alert if any dimension score drops by more than 0.3 from the established baseline. Implement the comparison logic in Python.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | The starter from the chapter: runs, with six TODOs |
| `solution/lab.py` | Reference solution |
| `tests/test_lab.py` | 16 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
