# Applied AI Engineering, Volume III, Chapter 14
# Section 14.6, Communication Protocols
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""           # "" means broadcast
    message_type: str = ""           # "task", "result", "query", "response", "error", "status"
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # Links responses to requests
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    priority: int = 5                # 1 (highest) to 10 (lowest)
    ttl: int = 300                   # Time-to-live in seconds; 0 = no expiry
