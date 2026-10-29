# Volume IV · Chapter 16 — Lab: Request Queue Simulation with Autoscaling

## What You Will Build

Three simulations of serving AI requests at scale. `queue_simulation.py` runs a request queue in real time for about 40 seconds: worker threads take requests whose latency grows with their token counts, traffic triples for five seconds, and an autoscaler adds workers when the queue grows and removes idle ones when it drains, with a cooldown between changes. `load_balancer.py` compares round-robin, least-connections and complexity-weighted routing across four workers. `scaling_signal.py` replays the chapter's opening story: a day of peak traffic, second by second, under an autoscaler that scales on CPU and never fires, one that scales on requests in flight and queue depth, and that one with rate-limited requests waiting in the queue instead of failing.

## Learning Outcomes

- Scale a worker pool on queue depth, with thresholds and a cooldown that prevents flapping.
- Scale down without killing a worker that is mid-request.
- Measure queue wait separately from processing time, and report p95 as well as the mean.
- Route requests of uneven cost by in-flight work rather than by request count.
- Avoid a check-then-act race between a dispatcher and its worker threads.
- Choose a scaling signal that tracks the real load of an I/O-bound service, and queue rate-limited requests instead of failing them.

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

`src/queue_simulation.py` runs as supplied, but without a cooldown (TODO 1) the autoscaler scales on consecutive ticks, so you will usually see more scale events. TODO 2 and TODO 3 (in `src/load_balancer.py`) rarely show in a run; the tests check all three. TODO 4 is in `src/scaling_signal.py`, below.

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

## The Scaling Signal

```bash
uv run python src/scaling_signal.py          # your work
uv run python solution/scaling_signal.py     # reference
```

Unlike the queue simulation, this one does not run in real time: it steps through twelve hours of traffic a second at a time, in about two seconds, and the random traffic comes from a fixed seed, so the output repeats. Each instance holds 50 provider connections; each request holds one for four seconds and uses 16 ms of CPU; a request that waits 30 seconds for a connection times out; and the provider accepts 50 requests a second. As supplied, B and C scale on CPU like A (TODO 4). The reference prints (also saved in `expected/scaling_signal.txt`):

```text
A: add an instance when CPU passes 70%, hour by hour
  hour  req/s in flight  queued  CPU instances  timeouts
  08:00    15        59       0  12%         2         0
  09:00    28       100     844  20%         2       486
  10:00    40       100   1,165  20%         2    31,479
  11:00    42       100   1,232  20%         2    57,260
  12:00    38       100   1,115  20%         2    54,012
  13:00    40       100   1,197  20%         2    51,221
  14:00    45       100   1,328  20%         2    62,911
  15:00    44       100   1,292  20%         2    69,756
  16:00    36       100   1,013  20%         2    54,327
  17:00    25       100     702  20%         2    20,363
  18:00    15        48       0  12%         2         0
  19:00    15        58       0  12%         2         0

Three ways through the day
  A  scale on CPU above 70%
  B  scale on requests in flight and queue depth
  C  B, with rate-limited requests waiting in the queue
                                  A          B          C
  requests answered         964,074  1,358,690  1,365,889
  timed out                 401,815          0          0
  failed on rate limit            0      7,199          0
  waited in the queue       760,384         43     10,647
  longest wait                 29 s        1 s        1 s
  most instances                  2          6          7
  highest CPU                   20%        18%        18%
```

CPU never passes 20%, because an instance's connections are all in use well before its processor is busy, so A never scales. The figures are illustrative.

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. Four of the
tests check the scaling signal: CPU stays near 20% so the CPU policy never scales, the load policy
sizes the pool correctly, scaling on load ends the timeouts but meets the provider's rate limit,
and with rate-limited requests waiting in the queue every request is answered. With the four TODOs
left in place, five of the thirteen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| The simulation seems to hang | It runs in real time for about 40 seconds | Wait for "Simulation Complete", or shorten `duration_seconds` in `__main__` |
| `UnicodeEncodeError` printing `↑` or `█` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |
| In `scaling_signal.py`, B and C never add an instance | TODO 4: every policy still scales on CPU | For policy `"load"`, use `desired_by_load(in_flight, queued)` |

## Going Further

- Run with `arrival_rate=5.0` and watch the autoscaler during the spike (Lab Exercise 1).
- Scale up on p95 latency instead of queue depth (Lab Exercise 2).
- Serve `priority=1` requests before `priority=2` with a priority queue (Lab Exercise 3).
- Move requests that have waited more than 30 seconds to a dead-letter queue (Lab Exercise 4).
- In `scaling_signal.py`, raise `BOOT` to five minutes and see how far ahead of the traffic a load-based autoscaler then has to look.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `queue_simulation.py`, `load_balancer.py`, `scaling_signal.py`; runs, with 4 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 13 tests, run against `solution/` |
| `expected/output.txt` | Captured output of `queue_simulation.py` (one run) |
| `expected/scaling_signal.txt` | Captured output of `scaling_signal.py` |
