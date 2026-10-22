# Volume IV · Chapter 4 — Lab: Event-Driven Document Automation Pipeline

## What You Will Build

An event-driven pipeline on an in-process event bus: a directory watcher publishes each new file, a classifier stage labels it with a simulated model call that sometimes fails, a router sends it to a handler (or to human review when confidence is low), and every action lands in an audit log. Transient failures are retried with exponential backoff; a file that still fails goes to a dead-letter path rather than disappearing.

## Learning Outcomes

- Decouple pipeline stages with publish/subscribe events.
- Retry transient failures with exponential backoff, and bound the attempts.
- Send work that cannot be completed to a dead-letter path, so nothing is lost silently.
- Route low-confidence classifications to a person.
- Keep an audit log of every action a pipeline takes on a file.

## Prerequisites

- Python 3.15
- Chapter 4, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (the classifier is simulated)

## Setup

```bash
cd volume-4/chapter-04      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

The demo runs for about ten seconds. `src/lab.py` runs as supplied, but it does not retry (TODO 1), so with the demo's random seed some files fail once and never reach `pipeline_complete`: compare the action counts. TODO 2 and TODO 3 do not show in this demo; the tests check them.

The output includes times and random file IDs, so yours will differ in those details.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

=== ACTION LOG ===
  06:41:05 | 6963b4bc | file_received                  | agreement_2024.txt
  06:41:05 | dfd762e7 | file_received                  | invoice_00123.txt
  06:41:05 | d4ea3b57 | file_received                  | q3_report.txt
  06:41:05 | d4ea3b57 | classified                     | type=report confidence=0.99
  06:41:05 | dfd762e7 | classified                     | type=invoice confidence=0.99
  06:41:05 | d4ea3b57 | routed                         | → report handler
  06:41:05 | dfd762e7 | routed                         | → invoice handler
  06:41:05 | dfd762e7 | invoice_processed              | Created payment record. Confidence: 0.99
  06:41:05 | dfd762e7 | pipeline_complete              | type=invoice
  06:41:06 | d4ea3b57 | report_archived                | Archived to reports store. Confidence: 0.99
  06:41:06 | d4ea3b57 | pipeline_complete              | type=report
  06:41:06 | 7ebcba0a | file_received                  | email_thread.txt
  06:41:06 | bca369b9 | file_received                  | unknown_doc.txt
  06:41:07 | 6963b4bc | classified                     | type=contract confidence=0.9
  06:41:07 | 6963b4bc | routed                         | → contract handler
  06:41:07 | 6963b4bc | contract_processed             | Extracted terms. Confidence: 0.9
  06:41:07 | 6963b4bc | pipeline_complete              | type=contract
  06:41:09 | bca369b9 | classified                     | type=unknown confidence=0.5
  06:41:09 | bca369b9 | routed                         | → unknown handler
  06:41:09 | bca369b9 | routed_to_review               | Low confidence or unknown type: 0.5
  06:41:09 | bca369b9 | pipeline_complete              | type=unknown
  06:41:12 | 7ebcba0a | classified                     | type=correspondence confidence=0.9
  06:41:12 | 7ebcba0a | routed                         | → correspondence handler
  06:41:12 | 7ebcba0a | routed_to_review               | Low confidence or unknown type: 0.9
  06:41:12 | 7ebcba0a | pipeline_complete              | type=correspondence

Total actions logged: 25
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
| A file is missing from the action log | Its classification failed and was not retried or dead-lettered | Complete TODO 1 and TODO 2 |
| `UnicodeEncodeError` printing `→` or `—` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Add a `KillSwitch` that the pipeline checks before each file, and show that setting it pauses processing (Extension Exercise 1).
- Cap processing at ten documents a minute, queueing the excess (Extension Exercise 2).
- Alert when more than 30% of files in a 60-second window are classified `unknown` (Extension Exercise 3).
- Add random jitter to the backoff, so many failing files do not retry in lockstep.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 3 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
