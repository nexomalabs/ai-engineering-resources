# Applied AI Engineering, Volume III, Chapter 16
# Section 16.10, Monitoring Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
import uuid
import hashlib
from datetime import datetime, timezone


def structured_log(
    workflow_id: str,
    step: str,
    status: str,
    duration: float,
    input_text: str = "",
    output_text: str = "",
    metadata: dict = None,
) -> None:
    """Emit a structured JSON log entry for workflow monitoring."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow_id": workflow_id,
        "step": step,
        "status": status,
        "duration_seconds": round(duration, 4),
        "input_hash": hashlib.sha256(input_text.encode()).hexdigest()[:12],
        "output_hash": hashlib.sha256(output_text.encode()).hexdigest()[:12],
        "output_length": len(output_text),
        **(metadata or {}),
    }
    # In production: ship to log aggregator (Datadog, CloudWatch, etc.)
    print(json.dumps(entry))
