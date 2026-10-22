# Applied AI Engineering, Volume IV, Chapter 9
# Section 9.3, Prompt Injection (Direct)
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import re
from typing import Optional

# Common direct injection patterns
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(your\s+)?(system\s+)?prompt",
    r"you\s+are\s+now\s+(?:dan|jailbroken|in\s+developer\s+mode)",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"repeat\s+(everything\s+)?above",
    r"act\s+as\s+(if\s+you\s+have\s+no\s+restrictions?|an?\s+unfiltered)",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

def detect_injection(text: str) -> Optional[str]:
    """Return the matched pattern string if injection detected, else None."""
    for pattern in _compiled:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None
