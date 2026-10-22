# Applied AI Engineering, Volume IV, Chapter 2
# Section 2.4, Interface Design
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    REPORT = "report"
    CORRESPONDENCE = "correspondence"
    UNKNOWN = "unknown"

class Entity(BaseModel):
    text: str = Field(..., description="The entity surface form")
    type: str = Field(..., description="Entity type: PERSON, ORG, DATE, MONEY, etc.")
    start_char: int = Field(..., description="Character offset in source document")
    confidence: float = Field(..., ge=0.0, le=1.0)

class AnalysisRequest(BaseModel):
    document_id: str = Field(..., description="UUID of previously uploaded document")
    analysis_types: List[str] = Field(
        default=["classification", "entities", "summary"],
        description="Which analyses to perform"
    )
    webhook_url: Optional[str] = Field(
        None,
        description="If provided, POST results here when complete"
    )

class AnalysisResult(BaseModel):
    document_id: str
    document_type: DocumentType
    type_confidence: float = Field(..., ge=0.0, le=1.0)
    entities: List[Entity]
    summary: str = Field(..., max_length=500)
    model_used: str
    prompt_version: str
    processing_time_ms: int
    created_at: str  # ISO 8601

class AnalysisResponse(BaseModel):
    job_id: str
    status: str = Field(..., description="queued | processing | complete | failed")
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
