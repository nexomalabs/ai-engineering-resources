# Applied AI Engineering, Volume III, Chapter 15
# Section 15.10, Communication Security
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+a",
    r"disregard\s+your\s+system\s+prompt",
    r"act\s+as\s+if\s+you\s+are",
    r"<\s*/?script",
    r"system:\s*",
]

def sanitize_external_content(content: str) -> str:
    """
    Remove known prompt injection patterns from externally sourced content.
    This is a defense-in-depth measure, not a complete solution.
    """
    for pattern in INJECTION_PATTERNS:
        content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)
    return content
