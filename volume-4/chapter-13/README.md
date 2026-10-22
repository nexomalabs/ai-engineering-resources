# Volume IV · Chapter 13 — Lab: Instrumenting an AI Service with Prometheus Metrics

## What You Will Build

A FastAPI service that simulates model calls and exposes Prometheus metrics at `/metrics`: request counts by status, a latency histogram, in-flight requests, tokens by model, a quality-score histogram, errors by type and safety-filter triggers. A load generator sends it traffic, and an alert evaluator reads the metrics every 30 seconds and reports alerts as they fire and resolve.

## Learning Outcomes

- Choose the right metric type: counter, gauge or histogram.
- Instrument both the success and the failure path of a request.
- Keep a gauge correct when a request fails, with `try`/`finally`.
- Evaluate alert rules against scraped metrics, and resolve them when they clear.
- Explain why cumulative counters need `rate()` over a window in a production alert.

## Prerequisites

- Python 3.15
- Chapter 13, read through its hands-on lab
- Dependencies: `fastapi`, `uvicorn`, `prometheus-client`, `httpx`, installed by `uv sync`
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
| `httpx.ConnectError` from the load generator or alert evaluator | The service is not running | Start `ai_service_monitored.py` first, in its own terminal |
| `ai_active_requests` keeps growing | The gauge is not decremented on every path | Complete TODO 2 |
| `UnicodeEncodeError` printing `🔴` or `✅` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Alert when the mean quality score (the histogram's `_sum` divided by its `_count`) drops below 0.70 (Lab Exercise 4).
- Write `drift_detector.py` to compute the PSI of quality scores between the first 50 requests and the next 50 (Lab Exercise 5).
- Point a real Prometheus server at `/metrics`, and rewrite the error-rate rule with `rate()` over five minutes.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `ai_service_monitored.py`, `load_generator.py`, `alert_evaluator.py`; runs, with 3 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
