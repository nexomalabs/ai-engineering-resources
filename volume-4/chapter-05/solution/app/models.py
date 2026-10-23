"""Request and response models."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    task: str = Field(default="summarize", pattern="^(summarize|classify|extract_entities)$")


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
