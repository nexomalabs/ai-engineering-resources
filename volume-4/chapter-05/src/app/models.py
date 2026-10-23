"""Request and response models."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    # TODO 3: reject empty or over-long text (1 to 10,000 characters) and any task other
    # than summarize, classify or extract_entities, so bad input gets a 422.
    text: str
    task: str = "summarize"


class AnalyzeResponse(BaseModel):
    result: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    model: str
