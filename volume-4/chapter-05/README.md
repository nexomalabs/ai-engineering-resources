# Volume IV · Chapter 5 — Lab: Containerized AI API Service

## What You Will Build

A FastAPI service that analyses text with a model (summarize, classify or extract entities), packaged for production: configuration from environment variables, validated requests, liveness and readiness probes, rate-limit and upstream errors mapped to the right HTTP status codes, a multi-stage Docker image that runs as a non-root user, a Compose file with health checks and resource limits, and a smoke-test script that decides whether a deployment may be promoted.

## Learning Outcomes

- Load all configuration from environment variables, with the secret never in the image.
- Validate requests at the boundary so bad input gets a 422 before it costs a model call.
- Map a provider's rate limit to 429 with `Retry-After`, and its failures to 502 without leaking details.
- Build a small, non-root, health-checked image in two stages.
- Gate a deployment on a smoke test of health, readiness, a real request and two validation cases.

## Prerequisites

- Python 3.15
- Chapter 5, read through its hands-on lab
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `openai`, and `httpx2` for FastAPI's test client, installed by `uv sync`
- Docker, only for the container steps. The tests and the smoke test run without it.
- Default mode: no API key. **Estimated API cost: $0.00** (a stand-in answers instead of the model)
- Live mode (optional): `OPENAI_API_KEY`. **Estimated API cost: under $0.01** for the smoke test with `gpt-6-luna`

## Setup

```bash
cd volume-4/chapter-05      # from the repository root
uv sync
```

## Running It

`src/` and `solution/` each hold the whole project from the chapter: `app/`, `Dockerfile`, `docker-compose.yml`, `requirements.txt` and `scripts/smoke_test.sh`. Run the service from either folder:

```bash
cd src                       # or: cd solution
uv run --project .. python -m uvicorn app.main:app --port 8000
# in a second terminal, from the same folder:
bash scripts/smoke_test.sh http://localhost:8000
```

To run it in a container instead (from `solution/`, with Docker):

```bash
docker compose up --build -d
docker compose ps                       # wait for "healthy"
bash scripts/smoke_test.sh http://localhost:8000
docker compose down
```

By default a stand-in answers instead of the model (`app/stand_in.py`), and Compose sets `NEXOMA_LAB_MODE=fixture` unless you set it, so the container needs no key either. The service is the chapter's code with three additions: `config.py` reads the mode, `main.py` uses the stand-in unless the mode is `live`, and the start-up key check applies in live mode only. For live mode, export `OPENAI_API_KEY` and `NEXOMA_LAB_MODE=live` before starting the service or running `docker compose up`.

`src/` runs as supplied, but a rate limit or an upstream error escapes as a 500 (TODOs 1 and 2), and requests are not validated, so empty text or an unknown task reaches the model (TODO 3). Complete all three.

## Expected Result

The smoke test against the reference prints the following (also saved in `expected/output.txt`):

```text
=== AI API Service Smoke Tests ===
Target: http://localhost:8765

1. Health endpoint
  [PASS] GET /health → 200
2. Readiness endpoint
  [PASS] GET /ready → 200
3. Analysis endpoint (valid request)
  [PASS] POST /api/v1/analyze → 200 with result
4. Input validation (empty text)
  [PASS] Empty text → 422 Unprocessable Entity
5. Input validation (invalid task)
  [PASS] Invalid task → 422 Unprocessable Entity

=== Results: 5 passed, 0 failed ===
SMOKE TEST PASSED — Safe to promote
```

Against `src/`, tests 4 and 5 fail and the script ends `SMOKE TEST FAILED — DO NOT PROMOTE THIS VERSION` with exit code 1, which is what should stop a pipeline from promoting the build.

## Verifying Your Work

```bash
uv run pytest
```

Ten tests, using FastAPI's test client, so no server or container is needed: health and readiness, two analysis tasks with token usage, three kinds of invalid input, a rate limit mapped to 429 with `Retry-After`, an upstream error mapped to 502 with no details leaked, and the start-up check that refuses to run in live mode without a key. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, replace `solution/` there with your `src/`, and run `uv run pytest`. With all three TODOs left in place, five tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | uvicorn was started from the wrong folder | Start it from `src/` or `solution/`, the folder that contains `app/` |
| A rate limit gives 500, not 429 | TODO 1 re-raises the provider's error | Raise `HTTPException(429, ..., headers={"Retry-After": "60"})` |
| Empty text gets 200 | TODO 3: the request model has no constraints | Add `Field(..., min_length=1, max_length=10000)` and the task pattern |
| `docker compose ps` never shows "healthy" | The app failed at start-up | Run `docker compose logs ai-api`; in live mode, check that `OPENAI_API_KEY` was exported |
| `RuntimeError: OPENAI_API_KEY is required` | Live mode without a key | Export the key, or leave `NEXOMA_LAB_MODE` unset |

## Going Further

- Add `POST /api/v2/analyze`, which takes a `document_id`, fetches the text from a simulated store and analyses it.
- Add Redis-based rate limiting: 100 requests per hour per client IP.
- Write the smoke test's five checks, plus three edge cases, as a `pytest` suite that runs against the container with `httpx`.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: the whole project, runnable, with 3 TODOs |
| `solution/` | Reference: the chapter's project with the mode switch |
| `solution/app/stand_in.py` | The stand-in for the model, used unless `NEXOMA_LAB_MODE=live` |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
| `expected/output.txt` | The smoke test's output against the reference |
