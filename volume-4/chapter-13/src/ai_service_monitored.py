"""Lab 13 — Prometheus-instrumented AI service (starter).

This file RUNS as supplied, but it records no token usage, and a failed request leaves the
in-flight gauge raised. In alert_evaluator.py, an alert never resolves. Complete the three
TODOs. Run from the lab folder:

    python src/ai_service_monitored.py
"""

import asyncio
import random
import time

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

app = FastAPI(title="Monitored AI Service")

# ── Prometheus metrics ──────────────────────────────────────────────────────
REQUEST_COUNTER = Counter(
    "ai_requests_total",
    "Total AI requests",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "ai_request_duration_seconds",
    "Request latency",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)
ACTIVE_REQUESTS = Gauge(
    "ai_active_requests",
    "Currently in-flight requests",
)
TOKENS_IN = Counter(
    "ai_tokens_input_total",
    "Total input tokens consumed",
    ["model"],
)
TOKENS_OUT = Counter(
    "ai_tokens_output_total",
    "Total output tokens generated",
    ["model"],
)
QUALITY_SCORE = Histogram(
    "ai_response_quality_score",
    "Automated quality score 0–1",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
ERROR_COUNTER = Counter(
    "ai_errors_total",
    "Total errors",
    ["error_type"],
)
SAFETY_FILTER = Counter(
    "ai_safety_filter_triggered_total",
    "Safety filter trigger events",
    ["action"],  # blocked, warned
)


def simulate_ai_call(prompt: str) -> dict:
    """Simulate calling an LLM with realistic metrics."""
    # Simulate variable latency (0.5s to 8s)
    latency = random.lognormvariate(0.5, 0.7)
    time.sleep(min(latency, 8.0))

    # Simulate token usage
    tokens_in = len(prompt.split()) * 1.3 + random.randint(50, 200)
    tokens_out = random.randint(50, 400)

    # Simulate quality score (skewed toward 0.7–0.9)
    quality = max(0.0, min(1.0, random.gauss(0.80, 0.15)))

    # Simulate occasional safety filter triggers
    safety_triggered = random.random() < 0.03  # 3% rate

    # Simulate occasional errors
    if random.random() < 0.02:  # 2% error rate
        raise ValueError("upstream_timeout")

    return {
        "response": f"AI response to: {prompt[:50]}...",
        "tokens_in": int(tokens_in),
        "tokens_out": int(tokens_out),
        "quality_score": round(quality, 3),
        "safety_triggered": safety_triggered,
        "latency": latency,
    }


@app.post("/v1/complete")
async def complete(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    model = body.get("model", "gpt-6.1-sol")
    endpoint = "complete"

    ACTIVE_REQUESTS.inc()
    start = time.time()

    try:
        # Run blocking call in thread pool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, simulate_ai_call, prompt)

        # Record metrics
        duration = time.time() - start
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        REQUEST_COUNTER.labels(endpoint=endpoint, status="success").inc()
        # TODO 1: Add the request's input and output tokens to TOKENS_IN and
        #   TOKENS_OUT, labelled by model. Token counts drive cost dashboards.
        QUALITY_SCORE.observe(result["quality_score"])

        if result["safety_triggered"]:
            SAFETY_FILTER.labels(action="warned").inc()

        return {
            "response": result["response"],
            "usage": {
                "tokens_in": result["tokens_in"],
                "tokens_out": result["tokens_out"],
            },
            "quality_score": result["quality_score"],
            "latency_ms": round(duration * 1000, 1),
        }

    except ValueError as e:
        error_type = str(e)
        REQUEST_COUNTER.labels(endpoint=endpoint, status="error").inc()
        ERROR_COUNTER.labels(error_type=error_type).inc()
        raise HTTPException(status_code=503, detail=f"AI service error: {error_type}")

    # TODO 2: Decrement ACTIVE_REQUESTS whether the request succeeds or fails. Here it
    #   is never decremented, so the gauge only grows.


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
