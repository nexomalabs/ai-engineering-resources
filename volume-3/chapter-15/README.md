# Volume III · Chapter 15 — Lab: Async Agent Communication System

## What You Will Build

Three asyncio agents (a researcher, an analyst and a synthesizer) exchange structured messages over a bus that drops 20% of them. The orchestrator runs research and calculation in parallel, collects the results by correlation ID, resends any task whose result does not arrive, and has the results synthesized. When the researcher crashes, a heartbeat monitor notices it has gone silent and the orchestrator reassigns its work. A message log records every delivered message.

## Learning Outcomes

- Exchange envelope-and-payload messages between asyncio agents.
- Match results to requests by correlation ID while several are in flight.
- Survive message loss with timeouts and resends, and make resends idempotent.
- Detect a failed agent from missing heartbeats and reassign its tasks.
- Skip messages whose time-to-live has expired.

## Prerequisites

- Python 3.15
- Chapter 15, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (tools are mocked; no model is called)

## Setup

```bash
cd volume-3/chapter-15      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/async_agents.py          # your work
uv run python solution/async_agents.py     # reference
```

The bus drops messages using a seeded random generator, so the run below is reproducible: with seed 8, alpha's first result is lost, alpha crashes before the resend, and its task is reassigned to beta; later, task C goes straight to beta. Change the seed in `main()` to see other patterns. Some seeds lose four sends in a row, and the orchestrator then gives up with a TimeoutError, as it should.

`src/async_agents.py` runs as supplied, but the monitor repeats its failure report every interval (TODO 3). TODO 1 and TODO 2 do not change this run's output; the tests check them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Parts 3-4: research and calculation in parallel, then synthesis
  alpha (researcher) received task A
  [SIMULATED DROP] result alpha → orchestrator corr=A
  beta (analyst) received task B
  [MONITOR] alpha appears to have failed
  orchestrator: alpha is down; reassigning A to beta
  orchestrator: no result for A; resending to beta (retry 1/3)
  [SIMULATED DROP] task orchestrator → beta corr=A
  orchestrator: no result for A; resending to beta (retry 2/3)
  beta (analyst) received task A
  gamma (synthesizer) received task S

Synthesis: Python was created by Guido van Rossum, first released in 1991. | Years since release: 33

Part 5: alpha has crashed; its next task must go elsewhere
  orchestrator: alpha is down; reassigning C to beta
  beta (analyst) received task C

Follow-up result: The Eiffel Tower is 330 meters tall including the broadcast antenna.

Retries: 2; reassigned: ['A', 'C']

=== MESSAGE LOG (delivered messages) ===
orchestrator → alpha | task | corr=A
orchestrator → beta | task | corr=B
beta → orchestrator | result | corr=B
orchestrator → beta | task | corr=A
beta → orchestrator | result | corr=A
orchestrator → gamma | task | corr=S
gamma → orchestrator | result | corr=S
orchestrator → beta | task | corr=C
beta → orchestrator | result | corr=C
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/async_agents.py` there with your `src/async_agents.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `TimeoutError: no result for S after 3 retries` | Four sends in a row were dropped | Expected occasionally at 20% loss; use another seed or raise `MAX_RETRIES` |
| `UnicodeEncodeError` printing `→` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Add exponential backoff between resends instead of a fixed timeout.
- Send an `error` message when a task fails, and let the orchestrator decide whether to resend or reassign.
- Restart a crashed agent and let the monitor mark it healthy when its heartbeats resume.
- Serialize every message with `to_json()` and parse it with `from_json()` at the receiving end, as a real network transport would.

## Files

| Path | Purpose |
|---|---|
| `src/async_agents.py` | Your starting point: runs, with 3 TODOs |
| `solution/async_agents.py` | Reference implementation |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
