# Volume III · Chapter 14 — Lab: Two-Agent Research Pipeline

## What You Will Build

A multi-agent pipeline: an orchestrator splits a goal into research tasks for a Researcher agent and a writing task for a Writer agent. Both workers run as daemon threads pulling from one shared priority queue, take only the tasks addressed to them, write their output to a shared result store, and reply to the orchestrator, which matches each reply to its task by correlation ID.

## Learning Outcomes

- Exchange structured messages with sender, recipient, type and correlation ID.
- Distribute work through a thread-safe priority queue.
- Pass large results through a shared store and small references through messages.
- Match replies to requests by correlation ID, with a timeout.
- Report a worker's failure as a message rather than letting the thread die silently.

## Prerequisites

- Python 3.15
- Chapter 14, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (search results are canned; no model is called)

## Setup

```bash
cd volume-3/chapter-14      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/multi_agent_pipeline.py          # your work
uv run python solution/multi_agent_pipeline.py     # reference
```

`src/multi_agent_pipeline.py` runs as supplied, but the Writer ignores its sources (TODO 1), so the report has a title and nothing under it. TODO 2 does not show in a normal run; the tests check it.

Both workers pull from the same queue, and a worker that takes a task addressed to the other puts it back. The order in which research results return can therefore differ from run to run; the report itself does not, because the Writer lists sources in the order the orchestrator gives them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Goal: Write a brief report on AI advances in 2024.

orchestrator -> researcher: task 1 {'query': 'EU AI Act'}
orchestrator -> researcher: task 2 {'query': 'Nobel physics 2024'}
orchestrator -> researcher: task 3 {'query': 'Nobel chemistry 2024'}
researcher -> orchestrator: result for task 1
researcher -> orchestrator: result for task 2
researcher -> orchestrator: result for task 3
orchestrator -> writer: task 4 write 'AI advances in 2024' from the results of tasks 1-3
writer -> orchestrator: result for task 4

=== REPORT ===
AI advances in 2024

- The EU AI Act, the first comprehensive AI law, entered into force on 1 August 2024.
- The 2024 Nobel Prize in Physics went to John Hopfield and Geoffrey Hinton for foundational work that enables machine learning with artificial neural networks.
- The 2024 Nobel Prize in Chemistry went to David Baker for computational protein design, and to Demis Hassabis and John Jumper for protein structure prediction.
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/multi_agent_pipeline.py` there with your `src/multi_agent_pipeline.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `TypeError: '<' not supported between instances of 'AgentMessage'` | Two queued messages tied on priority and timestamp, and the queue has no tie-breaker | Keep the `next(self._seq)` counter in `TaskQueue.enqueue`; Windows clocks tie often |
| `TimeoutError: 1 task(s) did not reply` | A worker thread died on an exception | Complete TODO 2; the error then reaches the orchestrator |

## Going Further

- Run two Researcher threads and measure how much faster the research phase completes.
- Give each worker its own queue, and compare with the shared queue and requeueing.
- Drop messages whose `ttl` has expired before a worker handles them.
- Replace the template Writer with a model call that synthesizes the findings.

## Files

| Path | Purpose |
|---|---|
| `src/multi_agent_pipeline.py` | Your starting point: runs, with 2 TODOs |
| `solution/multi_agent_pipeline.py` | Reference implementation |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
