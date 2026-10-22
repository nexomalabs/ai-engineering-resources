# Volume III · Chapter 12 — Lab: Task Planning Agent

## What You Will Build

A planning agent that turns a goal into a graph of tasks, validates the plan (unique IDs, known dependencies, no cycles, available tools), repairs what it can, and executes the tasks in dependency order with each task's inputs taken from the results it depends on. When a task fails, the agent classifies the failure and retries it, revises it, or replans the rest of the goal. A scripted stub stands in for the model.

## Learning Outcomes

- Represent a plan as tasks with explicit dependencies.
- Validate a model-generated plan before executing any of it.
- Execute tasks in dependency order, passing results forward.
- Match the recovery to the failure: retry, revise, or replan.
- Measure an execution: completion rate, retries and replans.

## Prerequisites

- Python 3.15
- Chapter 12, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (a scripted stub stands in for the model; tools are simulated)

## Setup

```bash
cd volume-3/chapter-12      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/planning_agent.py          # your work
uv run python solution/planning_agent.py     # reference
```

`src/planning_agent.py` runs as supplied, but each TODO shows in its output: the revalidation still reports the unknown tool (TODO 1), the summary is written from 0 sources (TODO 2), and in the first run t2's timeout causes a replan rather than a retry (TODO 3).

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Goal: Write a research summary on transformer architectures.

  t1 [web_search] Find the original transformer paper and its key ideas  depends on -
  t2 [web_search] Find recent work on efficient attention  depends on -
  t3 [read_file] Read the team's notes on attention mechanisms  depends on -
  t4 [summarize] Summarize the findings into a research summary  depends on ['t1', 't2', 't3']

Validation: ["Task 't4' references unknown tool 'summarize'."]
  fixed t4: 'summarize' -> 'write_file'
Revalidation: no errors

Recovery actions:
  t2: retry 1 after 'Search timeout after 30 s'
  t3: revised after 'Invalid path: no file name given'

Task status:
  t1  completed  Search results for: Find the original transformer paper and its key ideas
  t2  completed  Search results for: Find recent work on efficient attention
  t3  completed  Notes: attention cost grows with the square of sequence length
  t4  completed  Wrote summary.md from 3 source(s)

Completed 4/4 tasks, 2 retries, 0 replan(s)

============================================================

Goal: Write a research summary on transformer architectures.

  t1 [web_search] Find the original transformer paper and its key ideas  depends on -
  t2 [web_search] Find recent work on efficient attention  depends on -
  t3 [read_file] Read the team's notes on attention mechanisms  depends on -
  t4 [summarize] Summarize the findings into a research summary  depends on ['t1', 't2', 't3']

Validation: ["Task 't4' references unknown tool 'summarize'."]
  fixed t4: 'summarize' -> 'write_file'
Revalidation: no errors

Recovery actions:
  t3: replanned after 'The notes repository is empty' (logic_error)

Task status:
  t1  completed  Search results for: Find the original transformer paper and its key ideas
  t2  completed  Search results for: Find recent work on efficient attention
  t3  failed     The notes repository is empty
  t4  skipped    
  r1  completed  Wrote summary.md from 2 source(s)

Completed 3/5 tasks, 0 retries, 1 replan(s)
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/planning_agent.py` there with your `src/planning_agent.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| Every task is skipped with "dependencies unmet" | A dependency names a task that never completes | Run `validate_plan` first; it reports unknown dependencies and cycles |

## Going Further

- Replace the stub with a real model call, and validate whatever plan it returns.
- Run independent ready tasks concurrently with `asyncio.gather`.
- Handle the `missing_data` failure class by inserting a new data-gathering task (Section 12.8).
- Expand a high-level task into its own sub-plan only when it becomes ready (hierarchical planning, Section 12.9).

## Files

| Path | Purpose |
|---|---|
| `src/planning_agent.py` | Your starting point: runs, with 3 TODOs |
| `solution/planning_agent.py` | Reference implementation |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
