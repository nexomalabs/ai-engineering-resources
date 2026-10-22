# Applied AI Engineering, Volume IV, Chapter 2
# Hands-on Lab: System Design Document for an AI Document Analysis Service
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import asyncio
from datetime import datetime, timezone

app = FastAPI(title="AI Document Analysis Service", version="1.0.0")

# In-memory job store (replace with PostgreSQL in production)
jobs: dict[str, dict] = {}

class AnalysisRequest(BaseModel):
    document_id: str
    analysis_types: List[str] = ["classification", "entities", "summary"]
    webhook_url: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None

@app.post("/documents", status_code=202)
async def upload_document(file: UploadFile) -> dict:
    """Accept a document upload and return a document_id."""
    if file.content_type not in ["application/pdf",
                                  "application/vnd.openxmlformats-officedocument"
                                  ".wordprocessingml.document"]:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    doc_id = str(uuid.uuid4())
    # In production: validate size, store to S3, run virus scan
    return {"document_id": doc_id, "status": "uploaded"}

@app.post("/analyses", status_code=202)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> dict:
    """Queue a document analysis job."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "document_id": request.document_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    background_tasks.add_task(process_analysis, job_id, request)
    return {"job_id": job_id, "status": "queued"}

@app.get("/analyses/{job_id}", response_model=JobStatusResponse)
async def get_analysis(job_id: str) -> JobStatusResponse:
    """Retrieve the status and result of an analysis job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**jobs[job_id])

async def process_analysis(job_id: str, request: AnalysisRequest) -> None:
    """Simulate background AI analysis processing."""
    jobs[job_id]["status"] = "analyzing"
    await asyncio.sleep(2)  # Simulate LLM call
    jobs[job_id]["status"] = "complete"
    jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    jobs[job_id]["result"] = {
        "document_type": "contract",
        "type_confidence": 0.94,
        "entities": [{"text": "Acme Corp", "type": "ORG", "confidence": 0.99}],
        "summary": "A service agreement between Acme Corp and the client.",
        "model_used": "gpt-6.1-sol",
        "prompt_version": "v1.2.0",
    }
