"""Security middleware for the Chapter 9 lab: Sections 9.3, 9.8, 9.9 and 9.10 in one module.

NEXOMA_LAB_MODE=fixture  (default) moderation is simulated; no key
NEXOMA_LAB_MODE=live     moderation calls OpenAI; needs OPENAI_API_KEY and `--group live`
"""

import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from stand_in import stand_in_moderation

LAB_MODE = os.environ.get("NEXOMA_LAB_MODE", "fixture")


# ── Section 9.3: injection detection ────────────────────────────────────────

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
    # TODO 1: search the text with every compiled pattern; return the first matched text,
    # or None if nothing matches.
    return None


# ── Section 9.8: JWT authentication ─────────────────────────────────────────

# In production, load a long random secret from a secret store, never from source code.
SECRET_KEY = os.environ.get("JWT_SECRET", "lab-only-secret-change-me-0123456789abcdef")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

bearer_scheme = HTTPBearer()


def create_access_token(subject: str, scopes: list[str]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "scopes": scopes,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Decode and validate a Bearer JWT. Raises 401 on failure."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        subject: Optional[str] = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
            )
        return payload
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {exc}",
        ) from exc


def require_scope(required_scope: str):
    """Returns a dependency that checks for a specific scope."""

    def check(token_data: dict = Depends(verify_token)) -> dict:
        # TODO 2: a valid token is not enough. If required_scope is not in the token's
        # "scopes" claim, raise HTTPException 403 "Insufficient scope".
        return token_data

    return check


# ── Section 9.9: token-bucket rate limiting ─────────────────────────────────


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, capacity: float, refill_rate: float):
        """
        capacity    : maximum tokens in bucket
        refill_rate : tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        """Return True if tokens were consumed (request allowed), False if rate-limited."""
        # TODO 3: under the lock, refill the bucket, then take `tokens` from it if there are
        # enough and return True; otherwise return False. As written, nothing is limited.
        return True


# Per-user rate limiter registry
_limiters: dict[str, TokenBucket] = {}
_limiters_lock = threading.Lock()


def get_limiter(user_id: str, capacity: float = 10, rate: float = 1.0) -> TokenBucket:
    with _limiters_lock:
        if user_id not in _limiters:
            _limiters[user_id] = TokenBucket(capacity=capacity, refill_rate=rate)
        return _limiters[user_id]


# ── Section 9.10: output moderation ─────────────────────────────────────────


def moderate_output(text: str) -> dict:
    """Run OpenAI moderation API on model output. Returns moderation result.

    Outside live mode, the stand-in in stand_in.py answers instead (no key, no call)."""
    if LAB_MODE != "live":
        return stand_in_moderation(text)
    import openai  # imported here so the default mode needs no package

    result = openai.OpenAI().moderations.create(model="omni-moderation-latest", input=text)
    flagged = result.results[0].flagged
    categories = {k: v for k, v in result.results[0].categories.model_dump().items() if v}
    return {"flagged": flagged, "categories": categories}
