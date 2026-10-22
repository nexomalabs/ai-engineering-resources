# Applied AI Engineering, Volume IV, Chapter 5
# Hands-on Lab: Containerized AI API Service
# Copied from the book by scripts/export_listings.py. Report errors as errata.

"""Request and response models."""
from pydantic import BaseModel, Field
from typing import Optional

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    task: str = Field(
        default="summarize",
        pattern="^(summarize|classify|extract_entities)$"
    )

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
