# Volume IV · Chapter 3 — Lab: Enterprise Document Review Workflow

## What You Will Build

A document review workflow on asyncio: a state machine that only allows legal transitions, three roles (submitter, reviewer, approver), a simulated AI review step, SLA monitors that escalate a document when a reviewer or approver does not act in time, notifications on each significant change, and an audit history of every transition.

## Learning Outcomes

- Encode a workflow as a state machine with an explicit table of allowed transitions.
- Record every transition with actor, role, timestamp and comments.
- Enforce an SLA with `asyncio.wait_for` and escalate when it expires.
- Signal a human decision to a waiting task with `asyncio.Event`.
- Use timezone-aware UTC timestamps rather than the deprecated `datetime.utcnow()`.

## Prerequisites

- Python 3.15
- Chapter 3, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (the AI review step is simulated)

## Setup

```bash
cd volume-4/chapter-03      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but it records no history (TODO 2), so its Transition History is empty. TODO 1 and TODO 3 do not change this demo's output, because every transition is legal and every decision arrives within its SLA; the tests check them, with SLAs of a fraction of a second.

The history times are in UTC, so yours will differ from those below.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
=== Enterprise Document Review Workflow Demo ===

[TRANSITION] draft → submitted | actor=alice@company.com role=submitter
[NOTIFY] → alice@company.com    | Document Submitted
[TRANSITION] submitted → ai_reviewing | actor=ai-system role=system
[TRANSITION] ai_reviewing → pending_review | actor=ai-system role=system
[NOTIFY] → reviewer-001         | Review Required
[TRANSITION] pending_review → pending_approval | actor=reviewer-001 role=reviewer
[NOTIFY] → approver-001         | Approval Required
[TRANSITION] pending_approval → approved | actor=approver-001 role=approver
[NOTIFY] → alice@company.com    | Document Approved

=== Final State: APPROVED ===
AI Summary: Document 'Q3 Budget Amendment — Engineering' analyzed. Content is 73 characters. Identified as standard operational document with low regulatory risk.
Risk Score: 0.12

Transition History:
  06:38:04 | draft                → submitted            | alice@company.com (submitter)
  06:38:04 | submitted            → ai_reviewing         | ai-system (system)
  06:38:04 | ai_reviewing         → pending_review       | ai-system (system)
  06:38:05 | pending_review       → pending_approval     | reviewer-001 (reviewer)
  06:38:05 | pending_approval     → approved             | approver-001 (approver)
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
| `ImportError: cannot import name 'StrEnum'` | Python is older than 3.11 | Use Python 3.15, which the lab's `.python-version` selects |
| `UnicodeEncodeError` printing `→` or `—` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Add a `CHANGES_REQUESTED` state that sends the document back to the submitter with feedback (Extension Exercise 1).
- After ten documents, report the share that met each SLA (Extension Exercise 2).
- Submit a batch of documents concurrently, at most five at a time, with `asyncio.Semaphore` (Extension Exercise 3).
- Keep a reference to every task `asyncio.create_task` returns, as the asyncio documentation advises, and cancel the monitors on shutdown.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 3 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
