"""
AI API Service — FastAPI Application
Volume IV, Chapter 5 Lab — Production Systems
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import APIError, AsyncOpenAI, RateLimitError

from .canary import Canary
from .config import Settings, get_settings
from .models import AnalyzeRequest, AnalyzeResponse, HealthResponse
from .stand_in import StandInAsyncClient

logger = logging.getLogger("ai-api-service")

# Created at start-up from the settings; routes traffic and rolls a canary back.
canary = Canary("unconfigured")

# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting AI API Service v%s [%s] model=%s",
        settings.service_version,
        settings.environment,
        settings.model_name,
    )
    # Verify API key is present (not valid — that's too expensive at startup)
    if settings.lab_mode == "live" and not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    global canary
    canary = Canary(
        settings.model_name,
        settings.canary_model,
        settings.canary_percent,
        seed=settings.canary_seed,
    )
    if settings.canary_model:
        logger.info("Canary %s on %s%% of traffic", settings.canary_model, settings.canary_percent)
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


@app.get("/canary", tags=["ops"])
async def canary_status() -> dict:
    """The canary's share of traffic, each version's numbers, and any rollback."""
    return canary.status()


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["ai"])
async def analyze(
    request: AnalyzeRequest,
    settings: Settings = Depends(get_settings),
) -> AnalyzeResponse:
    """Analyze text using the configured LLM."""
    if settings.lab_mode == "live":
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout,
        )
    else:
        client = StandInAsyncClient(verbose_models={settings.canary_model})

    task_prompts = {
        "summarize": "Summarize the following text in 2-3 sentences.",
        "classify": "Classify the document type of the following text. Return only the type.",
        "extract_entities": "Extract named entities from the text as a JSON list.",
    }
    system_prompt = task_prompts.get(request.task, task_prompts["summarize"])

    track, model = canary.route()
    start = time.monotonic()
    try:
        response = await client.chat.completions.create(
            model=model,
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.text},
            ],
            max_completion_tokens=settings.max_tokens,
        )
    except RateLimitError:
        canary.record(track, error=True)
        # TODO 1: tell the caller to back off: raise HTTPException with status 429,
        # a clear detail message and a "Retry-After: 60" header.
        raise
    except APIError as exc:
        canary.record(track, error=True)
        # TODO 2: an upstream failure is not the caller's fault: log it and raise
        # HTTPException 502 "Upstream AI service error", without leaking the details.
        raise

    latency_ms = (time.monotonic() - start) * 1000
    reason = canary.record(track, response.usage.prompt_tokens, response.usage.completion_tokens)
    if reason:
        logger.warning("Canary %s rolled back: %s", canary.canary_model, reason)
    return AnalyzeResponse(
        result=response.choices[0].message.content,
        model_used=response.model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        latency_ms=round(latency_ms, 1),
    )
