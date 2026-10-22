# Applied AI Engineering, Volume III, Chapter 1
# Hands-on Lab: Build a Context Pipeline in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# context_pipeline.py
from dataclasses import dataclass, field
from typing import List, Optional
import tiktoken

@dataclass
class ContextBlock:
    """A single named block of context content."""
    name: str
    content: str
    priority: int          # Lower number = higher priority (1 = highest)
    layer: str             # 'system', 'user', 'knowledge', 'history', 'request'
    token_count: int = 0

    def __post_init__(self):
        encoder = tiktoken.get_encoding("cl100k_base")
        self.token_count = len(encoder.encode(self.content))
