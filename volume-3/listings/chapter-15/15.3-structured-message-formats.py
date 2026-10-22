# Applied AI Engineering, Volume III, Chapter 15
# Section 15.3, Structured Message Formats
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

@dataclass
class MessageEnvelope:
    """Standard message envelope for all inter-agent communication."""
    # Routing
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""        # "" = broadcast
    reply_to: Optional[str] = None  # Queue/channel for replies

    # Classification
    message_type: str = ""        # task | result | query | response | error | heartbeat
    schema_version: str = "1.0"

    # Content
    payload: dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None  # Groups related messages
    priority: int = 5              # 1 = highest, 10 = lowest
    ttl_seconds: int = 300         # 0 = no expiry

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str) -> "MessageEnvelope":
        return cls(**json.loads(data))

    def is_expired(self) -> bool:
        if self.ttl_seconds == 0:
            return False
        sent_at = datetime.fromisoformat(self.timestamp)
        age = (datetime.now(timezone.utc) - sent_at).total_seconds()
        return age > self.ttl_seconds


def make_task_message(sender: str, recipient: str, task_desc: str,
                      args: dict, correlation_id: str | None = None) -> MessageEnvelope:
    return MessageEnvelope(
        sender_id=sender,
        recipient_id=recipient,
        message_type="task",
        payload={"description": task_desc, "args": args},
        correlation_id=correlation_id or str(uuid.uuid4()),
    )

def make_result_message(sender: str, recipient: str, result: Any,
                        correlation_id: str) -> MessageEnvelope:
    return MessageEnvelope(
        sender_id=sender,
        recipient_id=recipient,
        message_type="result",
        payload={"result": result},
        correlation_id=correlation_id,
    )

def make_error_message(sender: str, recipient: str, error: str,
                       correlation_id: str) -> MessageEnvelope:
    return MessageEnvelope(
        sender_id=sender,
        recipient_id=recipient,
        message_type="error",
        payload={"error": error},
        correlation_id=correlation_id,
    )
