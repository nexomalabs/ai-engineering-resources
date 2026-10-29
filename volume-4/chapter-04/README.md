# Volume IV · Chapter 4 — Lab: Event-Driven Document Automation Pipeline

## What You Will Build

An event-driven pipeline on an in-process event bus: a directory watcher publishes each new file, a classifier stage labels it with a simulated model call that sometimes fails, a router sends it to a handler (or to human review when confidence is low), and every action lands in an audit log. Transient failures are retried with exponential backoff; a file that still fails goes to a dead-letter path rather than disappearing. Around the pipeline stand the governance controls of Section 4.9: a kill switch, a dry-run mode, an approval gate that holds payment records for a person, and an anomaly monitor. The demo ends by replaying the chapter's customs incident, in which a shipper's new invoice layout makes the extractor read euros as dollars: the monitor pulls the kill switch, the action log names the affected filings, a dry run tests the fix, and every filing waits for a broker's approval.

## Learning Outcomes

- Pause an automation with a kill switch, test a fix with a dry run, and hold financial actions at an approval gate.
- Use an anomaly monitor to stop a pipeline, and an action log to find what it affected.
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

The demo runs for about ten seconds. `src/lab.py` runs as supplied, but it does not retry (TODO 1), so with the demo's random seed some files fail once and never reach `pipeline_complete`: compare the action counts. TODO 4 shows in the customs incident at the end: with nothing to stop it, the starter files INV-103 and INV-104 in dollars and reports no affected filings. TODO 2 and TODO 3 do not show in this demo; the tests check them.

The output includes times and random file IDs, so yours will differ in those details.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

=== ACTION LOG ===
  12:55:26 | 5e119c5d | file_received                  | agreement_2024.txt
  12:55:26 | f529189d | file_received                  | invoice_00123.txt
  12:55:26 | 95f54951 | file_received                  | q3_report.txt
  12:55:26 | 95f54951 | classified                     | type=report confidence=0.99
  12:55:26 | 95f54951 | routed                         | → report handler
  12:55:26 | f529189d | classified                     | type=invoice confidence=0.99
  12:55:26 | f529189d | routed                         | → invoice handler
  12:55:26 | f529189d | awaiting_approval              | a invoice action needs a person's approval
  12:55:26 | f529189d | pipeline_complete              | type=invoice
  12:55:27 | 95f54951 | report_archived                | Archived to reports store. Confidence: 0.99
  12:55:27 | 95f54951 | pipeline_complete              | type=report
  12:55:27 | 319ead2e | file_received                  | email_thread.txt
  12:55:27 | 42aea04b | file_received                  | unknown_doc.txt
  12:55:28 | 5e119c5d | classified                     | type=contract confidence=0.9
  12:55:28 | 5e119c5d | routed                         | → contract handler
  12:55:28 | 5e119c5d | contract_processed             | Extracted terms. Confidence: 0.9
  12:55:28 | 5e119c5d | pipeline_complete              | type=contract
  12:55:30 | 42aea04b | classified                     | type=unknown confidence=0.5
  12:55:30 | 42aea04b | routed                         | → unknown handler
  12:55:30 | 42aea04b | routed_to_review               | Low confidence or unknown type: 0.5
  12:55:30 | 42aea04b | pipeline_complete              | type=unknown
  12:55:33 | 319ead2e | classified                     | type=correspondence confidence=0.9
  12:55:33 | 319ead2e | routed                         | → correspondence handler
  12:55:33 | 319ead2e | routed_to_review               | Low confidence or unknown type: 0.9
  12:55:33 | 319ead2e | pipeline_complete              | type=correspondence

Total actions logged: 25

=== THE CUSTOMS INCIDENT ===
  INV-101   | filing_prepared        | 12,400 EUR, awaiting a broker
  INV-102   | filing_prepared        | 9,850 EUR, awaiting a broker
  pipeline  | kill_switch_engaged    | Hallbeck GmbH declared in USD; its filings are in EUR
  INV-103   | held_by_kill_switch    | Hallbeck GmbH declared in USD; its filings are in EUR
  INV-104   | held_by_kill_switch    | Hallbeck GmbH declared in USD; its filings are in EUR
  INV-103   | dry_run                | would file 11,200 EUR
  INV-104   | dry_run                | would file 7,300 EUR
  pipeline  | kill_switch_released   | 2 held item(s)
  INV-103   | filing_prepared        | 11,200 EUR, awaiting a broker
  INV-104   | filing_prepared        | 7,300 EUR, awaiting a broker

Affected filings, found in the action log: INV-103, INV-104
Filings awaiting a broker's approval, none yet submitted: INV-101, INV-102, INV-103, INV-104
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. With the four TODOs left in place, four of the seventeen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| A file is missing from the action log | Its classification failed and was not retried or dead-lettered | Complete TODO 1 and TODO 2 |
| The customs incident files INV-103 in USD | TODO 4: nothing holds an invoice or reacts to the monitor | Hold invoices while `governance.paused`, and pull the kill switch when `monitor.is_anomalous()` |
| `UnicodeEncodeError` printing `→` or `—` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Add a `KillSwitch` that the pipeline checks before each file, and show that setting it pauses processing (Extension Exercise 1).
- Cap processing at ten documents a minute, queueing the excess (Extension Exercise 2).
- Alert when more than 30% of files in a 60-second window are classified `unknown` (Extension Exercise 3).
- Add random jitter to the backoff, so many failing files do not retry in lockstep.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 4 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 17 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
