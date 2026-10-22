# Volume II · Chapter 17 — Lab: Build a Three-Pattern Prompt Framework

## What You Will Build

A small prompt framework library with three frameworks, a Task Dispatcher (Template pattern), a Quality Gate (Evaluation pattern) and an Error Recovery framework (Role pattern), wired into one workflow that classifies a request, checks a draft reply, and asks clarifying questions when the classification is not confident enough.

## Learning Outcomes

- Implement `TaskDispatcherFramework` using the Template Pattern with Jinja2.
- Implement `QualityGateFramework` using the Evaluation Pattern with a three-dimension rubric.
- Implement `ErrorRecoveryFramework` using the Role Pattern with a defined uncertainty protocol.
- Register all three frameworks in a `FrameworkLibrary`.
- Apply the full workflow to three test business inputs.

## Prerequisites

- Python 3.15
- Chapter 17, read through its hands-on lab
- `jinja2`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (a deterministic mock model stands in for the LLM)

## Setup

```bash
cd volume-2/chapter-17      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but the quality gate trusts the model's own arithmetic (TODO 1), and an ambiguous request is never sent to error recovery (TODO 2), so test case 3 goes to the quality gate instead. Complete both TODOs and test case 3 ends in **[Stage 3 – Recovery Triggered]**.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
[Library] Registered: task-dispatcher@1.0.0
[Library] Registered: quality-gate@1.0.0
[Library] Registered: error-recovery@1.0.0

============================================================
TEST CASE 1: Billing Dispute

[Stage 1 – Dispatch]
{
  "category": "billing_dispute",
  "priority": "high",
  "confidence": 0.91,
  "routing_queue": "billing_team",
  "flags": []
}

[Stage 2 – Quality Gate]
{
  "scores": {
    "accuracy": {
      "score": 4,
      "justification": "Response addresses the billing discrepancy correctly."
    },
    "clarity": {
      "score": 5,
      "justification": "Clear and concise language used throughout."
    },
    "completeness": {
      "score": 3,
      "justification": "Missing information about refund timeline."
    }
  },
  "weighted_total": 0.8,
  "pass": true,
  "top_improvement": "Include expected refund processing time in the response."
}

============================================================
TEST CASE 2: Shipment Tracking

[Stage 1 – Dispatch]
{
  "category": "shipment_tracking",
  "priority": "high",
  "confidence": 0.88,
  "routing_queue": "logistics_team",
  "flags": [
    "sla_breach"
  ]
}

[Stage 2 – Quality Gate]
{
  "scores": {
    "accuracy": {
      "score": 5,
      "justification": "Gives the current location and a delivery estimate."
    },
    "clarity": {
      "score": 5,
      "justification": "Short and specific."
    },
    "completeness": {
      "score": 2,
      "justification": "Does not say what happens if today's delivery is missed."
    }
  },
  "weighted_total": 0.82,
  "pass": true,
  "top_improvement": "State the next step if the package does not arrive today."
}

============================================================
TEST CASE 3: Ambiguous Input

[Stage 1 – Dispatch]
{
  "category": "general_inquiry",
  "priority": "low",
  "confidence": 0.42,
  "routing_queue": "general_queue",
  "flags": [
    "ambiguous_request"
  ]
}

[Stage 3 – Recovery Triggered]
{
  "recovery_action": "request_clarification",
  "clarifying_questions": [
    "Which part of your account is affected: billing, deliveries, or sign-in?",
    "What happened, and when did you first notice it?"
  ],
  "confidence_after_clarification": 0.85
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
| `ModuleNotFoundError: No module named 'jinja2'` | Dependencies are not installed | Run `uv sync` in this folder |

## Going Further

- Add a fourth framework using the Pipeline Pattern that chains Dispatcher → Quality Gate → Error Recovery automatically.
- Implement a `FrameworkLibrary.search_by_tag()` method and demonstrate it finding all frameworks tagged `"logistics"`.
- Upgrade `TaskDispatcherFramework` to version `1.1.0` adding a new optional `"sla_hours"` output field. Register both versions and verify that existing applications pinned to `1.0.0` are unaffected.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with two TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
