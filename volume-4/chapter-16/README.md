# Volume IV · Chapter 16 — Lab: Request Queue Simulation with Autoscaling

## What You Will Build

Two simulations of serving AI requests at scale. `queue_simulation.py` runs a request queue in real time for about 40 seconds: worker threads take requests whose latency grows with their token counts, traffic triples for five seconds, and an autoscaler adds workers when the queue grows and removes idle ones when it drains, with a cooldown between changes. `load_balancer.py` compares round-robin, least-connections and complexity-weighted routing across four workers.

## Learning Outcomes

- Scale a worker pool on queue depth, with thresholds and a cooldown that prevents flapping.
- Scale down without killing a worker that is mid-request.
- Measure queue wait separately from processing time, and report p95 as well as the mean.
- Route requests of uneven cost by in-flight work rather than by request count.
- Avoid a check-then-act race between a dispatcher and its worker threads.

## Prerequisites

- Python 3.15
- Chapter 16, read through its hands-on lab
- Dependencies: `rich`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (inference latency is simulated)

## Setup

```bash
cd volume-4/chapter-16      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/queue_simulation.py          # your work
uv run python solution/queue_simulation.py     # reference
```

The queue simulation runs in real time for about 40 seconds and uses threads, so its numbers differ on every run; the result below is one run of the reference. Run `python solution/load_balancer.py` for the routing comparison.

`src/queue_simulation.py` runs as supplied, but without a cooldown (TODO 1) the autoscaler scales on consecutive ticks, so you will usually see more scale events. TODO 2 and TODO 3 (in `src/load_balancer.py`) rarely show in a run; the tests check all three.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

Starting simulation: 35.0s, 2.0 req/s, initial workers: 2
  ↑ Scale UP: 2 → 4 workers (queue_depth=6)
  ↑ Scale UP: 4 → 6 workers (queue_depth=6)
  ↓ Scale DOWN: 6 → 5 workers (queue_depth=0)

Simulation Complete
Requests completed:  83
Queue remaining:     0
Peak workers:        6
Workers at end:      5
Avg processing:      1.56s
p95 latency:         2.53s
Avg queue wait:      0.78s
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| The simulation seems to hang | It runs in real time for about 40 seconds | Wait for "Simulation Complete", or shorten `duration_seconds` in `__main__` |
| `UnicodeEncodeError` printing `↑` or `█` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Run with `arrival_rate=5.0` and watch the autoscaler during the spike (Lab Exercise 1).
- Scale up on p95 latency instead of queue depth (Lab Exercise 2).
- Serve `priority=1` requests before `priority=2` with a priority queue (Lab Exercise 3).
- Move requests that have waited more than 30 seconds to a dead-letter queue (Lab Exercise 4).

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `queue_simulation.py`, `load_balancer.py`; runs, with 3 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 9 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
