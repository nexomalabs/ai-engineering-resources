# Applied AI Engineering, Volume IV, Chapter 5
# Hands-on Lab: Containerized AI API Service
# Copied from the book by scripts/export_listings.py. Report errors as errata.

"""
AI API Service — FastAPI Application
Volume IV, Chapter 5 Lab — Production Systems
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI, APIError, RateLimitError

from .config import Settings, get_settings
from .models import AnalyzeRequest, AnalyzeResponse, HealthResponse

logger = logging.getLogger("ai-api-service")

# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting AI API Service v%s [%s] model=%s",
        settings.service_version, settings.environment, settings.model_name,
    )
    # Verify API key is present (not valid — that's too expensive at startup)
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    yield
    logger.info("Shutting down AI API Service")

# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI API Service",
    description="Production AI analysis service",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Tighten in production
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness probe — returns 200 if service is running."""
    return HealthResponse(
        status="healthy",
        version=settings.service_version,
        environment=settings.environment,
        model=settings.model_name,
    )

@app.get("/ready", tags=["ops"])
async def readiness() -> dict:
    """Readiness probe — returns 200 when ready to serve traffic."""
    return {"status": "ready"}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["ai"])
async def analyze(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
) -> AnalyzeResponse:
    """Analyze text using the configured LLM."""
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.request_timeout,
    )

    task_prompts = {
        "summarize": "Summarize the following text in 2-3 sentences.",
        "classify": "Classify the document type of the following text. Return only the type.",
        "extract_entities": "Extract named entities from the text as a JSON list.",
    }
    system_prompt = task_prompts.get(request.task, task_prompts["summarize"])

    start = time.monotonic()
    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.text},
            ],
            max_completion_tokens=settings.max_tokens,
        )
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="LLM rate limit exceeded. Retry after 60 seconds.",
            headers={"Retry-After": "60"},
        )
    except APIError as exc:
        logger.error("LLM API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI service error",
        )

    latency_ms = (time.monotonic() - start) * 1000
    return AnalyzeResponse(
        result=response.choices[0].message.content,
        model_used=response.model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        latency_ms=round(latency_ms, 1),
    )
