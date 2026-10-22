# Volume II · Chapter 19 — Lab: Review Board vs. Single-Prompt Review

## What You Will Build

A three-reviewer Review Board that reviews a short module with three planted defects, a synthesis step that merges findings without averaging them, a comparison with a single "act as three experts" prompt, and a three-role Critique Board that records verdicts without taking a vote.

## Learning Outcomes

- Implement three reviewer charters with a shared JSON output contract.
- Run each reviewer in its own context and synthesize the findings without averaging them.
- Measure each reviewer, the whole board, and the single prompt against the planted defects.
- Run a Critique Board and record verdicts, conditions, evidence, and assumptions separately.

## Prerequisites

- Python 3.15
- Chapter 19, read through its hands-on lab
- Fixture mode (default): standard library only, no API key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (seven short calls)

## Setup

```bash
cd volume-2/chapter-19      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but synthesis lists every finding separately instead of merging them by line (TODO 1), and the Critique Board takes a majority vote (TODO 2), which hides the Risk Manager's dissent. Complete both TODOs.

For live mode:

```bash
uv sync --group live
NEXOMA_LAB_MODE=live OPENAI_API_KEY=... uv run python solution/lab.py
```

The fixture responses are illustrative examples written for this lab, not measurements. Live mode shows what your model actually finds.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Mode: fixture

=== REVIEW BOARD: ranked findings ===
  1. line 2 [critical] SQL injection through customer_email
     raised by: security=critical, red_team=critical
  2. line 6 [major] Division by zero when orders is empty
     raised by: engineer=major, red_team=minor  <- severity disputed
  3. line 3 [minor] SELECT * returns every column, including any added later
     raised by: red_team=minor  <- one reviewer only
  4. line 9 [minor] percent is not validated
     raised by: engineer=minor  <- one reviewer only

=== Recall against the planted defects ===
  engineer       found 2/3 planted defects  missed lines: [2]  unplanted findings on lines: -
  security       found 1/3 planted defects  missed lines: [6, 9]  unplanted findings on lines: -
  red_team       found 2/3 planted defects  missed lines: [9]  unplanted findings on lines: [3]
  board (all 3)  found 3/3 planted defects  missed lines: -  unplanted findings on lines: [3]
  single prompt  found 2/3 planted defects  missed lines: [9]  unplanted findings on lines: -

  Model calls: review board = 3, single prompt = 1, critique board = 3

=== CRITIQUE BOARD: should the discount feature exist? ===
  customer_representative  BUILD WITH CONDITIONS
      condition:  The customer sees and accepts the offer; nothing is applied silently
      assumption: Unhappy customers value an instant discount
  financial_analyst        BUILD WITH CONDITIONS
      condition:  Cap discounts at 15%
      condition:  Set a daily budget per customer
      evidence:   apply_discount() has no upper bound (line 9)
      assumption: A discount costs less than losing the customer
  risk_manager             DO NOT BUILD
      evidence:   The chatbot decides who is unhappy from text the customer writes
      assumption: Customers will learn to sound unhappy once word spreads
  Board record: no majority vote is taken.
  Verdicts differ: BUILD WITH CONDITIONS (customer_representative, financial_analyst); DO NOT BUILD (risk_manager)
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
| `KeyError: 'OPENAI_API_KEY'` | Live mode is on without a key | Set `OPENAI_API_KEY`, or unset `NEXOMA_LAB_MODE` to use fixtures |
| Live results differ between runs | Models vary even at temperature 0 | Expected; run it three times and record the differences |

## Going Further

- Replace the code-based `synthesize()` with a model call whose charter forbids adding or dropping findings. Compare its output with the code version.
- Run the three reviewers on models from two different providers and compare their findings.
- Add a fourth reviewer from Table 19.1, give it a charter that overlaps with none of the existing three, and check whether it finds anything new.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with two TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 8 tests, run against `solution/` in fixture mode |
| `expected/output.txt` | Captured output of the reference in fixture mode |
| `.env.example` | The variables live mode needs; never commit a real key |
