# Volume IV · Chapter 13 — Lab: Instrumenting an AI Service with Prometheus Metrics

## What You Will Build

A FastAPI service that simulates model calls and exposes Prometheus metrics at `/metrics`: request counts by status, a latency histogram, in-flight requests, tokens by model, a quality-score histogram, errors by type and safety-filter triggers. A load generator sends it traffic, and an alert evaluator reads the metrics every 30 seconds and reports alerts as they fire and resolve. A fourth script, `quality_drift.py`, replays the chapter's opening story: answer quality drifting down for six days while the provider rolls a new model out behind Wren's alias, a long-window alert that catches it, and the query, quality by model version, that shows why.

## Learning Outcomes

- Choose the right metric type: counter, gauge or histogram.
- Instrument both the success and the failure path of a request.
- Keep a gauge correct when a request fails, with `try`/`finally`.
- Evaluate alert rules against scraped metrics, and resolve them when they clear.
- Explain why cumulative counters need `rate()` over a window in a production alert.
- Catch a slow quality drift with a long-window alert, and find its cause by grouping quality by model version.

## Prerequisites

- Python 3.15
- Chapter 13, read through its hands-on lab
- Dependencies: `fastapi`, `uvicorn`, `prometheus-client`, `httpx` and `httpx2` (which FastAPI's test client now uses), installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (model calls are simulated)

## Setup

```bash
cd volume-4/chapter-13      # from the repository root
uv sync
```

## Running It

```bash
# Terminal 1: the service; metrics at http://127.0.0.1:8000/metrics
uv run python src/ai_service_monitored.py
# Terminal 2: send 100 requests
uv run python src/load_generator.py
# Terminal 3: evaluate the alert rules every 30 seconds (Ctrl+C to stop)
uv run python src/alert_evaluator.py
```

Use `solution/` in place of `src/` to run the reference.

The simulated model call takes up to eight seconds, so 100 requests at ten at a time take a minute or two. Open http://127.0.0.1:8000/metrics in a browser to watch the counters change.

## Expected Result

Latency, errors and safety triggers are random, so your numbers will differ. The load
generator prints the count of each status code, for example:

```text
{200: 98, 503: 2}
```

About 2% of requests fail with 503 (the simulated upstream timeout), so the 5% error-rate
alert usually stays quiet; the safety-filter alert fires once 10 or more triggers have
accumulated, which takes a few hundred requests at the simulated 3% rate. Run the load
generator several times to see it fire.

In `/metrics`, look for lines such as:

```text
ai_requests_total{endpoint="complete",status="success"} 98.0
ai_tokens_input_total{model="gpt-6.1-sol"} 13246.0
ai_active_requests 0.0
```

## A Slow Drift

```bash
uv run python src/quality_drift.py          # your work
uv run python solution/quality_drift.py     # reference
```

The log is simulated from a fixed seed, so the output repeats. The reference prints (also saved in `expected/quality_drift.txt`):

```text
day  quality  words  note
  1     0.82    118  
  2     0.82    119  
  3     0.82    119  
  4     0.82    118  
  5     0.82    116  
  6     0.82    119  
  7     0.82    119  
  8     0.80    127  provider starts moving the alias
  9     0.77    136  
 10     0.76    145  
 11     0.74    155  
 12     0.71    164  
 13     0.70    172  long-window alert fires
 14     0.70    173  
 15     0.82    119  old version pinned
 16     0.82    118  

Quality by the model version recorded with each response:
  gpt-6.1-sol-2026-11-04   quality 0.82, 118 words, 4596 answers
  gpt-6.1-sol-2026-12-08   quality 0.70, 173 words, 1804 answers
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy Four more test the drift: no single day falls far enough to look alarming, the long-window alert fires on the sixth day, grouping by version shows each version steady and the new one worse, and pinning the old version restores quality. With the four TODOs left in place, four of the fourteen tests fail.
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `httpx.ConnectError` from the load generator or alert evaluator | The service is not running | Start `ai_service_monitored.py` first, in its own terminal |
| `ai_active_requests` keeps growing | The gauge is not decremented on every path | Complete TODO 2 |
| Quality by model version shows one group, "all versions" | TODO 4: the records are not grouped by version | Group by `record["model_version"]` |

## Going Further

- Alert when the mean quality score (the histogram's `_sum` divided by its `_count`) drops below 0.70 (Lab Exercise 4).
- Write `drift_detector.py` to compute the PSI of quality scores between the first 50 requests and the next 50 (Lab Exercise 5).
- Point a real Prometheus server at `/metrics`, and rewrite the error-rate rule with `rate()` over five minutes.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `ai_service_monitored.py`, `load_generator.py`, `alert_evaluator.py`; runs, with 3 TODOs; `quality_drift.py` has TODO 4 |
| `solution/quality_drift.py` | The quality drift from the chapter's story |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 14 tests, run against `solution/` |
| `expected/quality_drift.txt` | Captured output of `quality_drift.py` |
