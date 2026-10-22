# Applied AI Engineering, Volume III, Chapter 13
# Section 13.5, Episodic Memory for Agents
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class EpisodicRecord:
    id: Optional[int]
    timestamp: datetime
    session_id: str
    agent_id: str
    event_type: str            # "observation", "action", "decision", "error"
    content: str               # The actual content of the event
    importance: float = 0.5    # 0.0 (trivial) to 1.0 (critical)
    tags: list[str] = field(default_factory=list)
