# Applied AI Engineering, Volume IV, Chapter 1
# Section 1.5, Observability
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class AIRequestLog:
    request_id: str
    timestamp_iso: str
    user_id: str
    endpoint: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    cache_hit: bool
    fallback_used: bool
    validation_passed: bool
    error: Optional[str] = None

def log_ai_request(log: AIRequestLog) -> None:
    """Emit a structured JSON log line for an AI request."""
    print(json.dumps(asdict(log)))

# Usage
log_ai_request(AIRequestLog(
    request_id=str(uuid.uuid4()),
    timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    user_id="user-123",
    endpoint="/api/v1/analyze",
    model="gpt-6.1-sol",
    input_tokens=1420,
    output_tokens=312,
    latency_ms=1834.5,
    cost_usd=0.0021,
    cache_hit=False,
    fallback_used=False,
    validation_passed=True,
))
