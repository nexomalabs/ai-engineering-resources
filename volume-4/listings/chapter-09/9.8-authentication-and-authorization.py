# Applied AI Engineering, Volume IV, Chapter 9
# Section 9.8, Authentication and Authorization
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# JWT authentication middleware for FastAPI
# Requires: pip install fastapi python-jose[cryptography] passlib

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

SECRET_KEY = "change-this-to-a-256-bit-random-secret-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {exc}",
        ) from exc

def require_scope(required_scope: str):
    """Returns a dependency that checks for a specific scope."""
    def check(token_data: dict = Depends(verify_token)) -> dict:
        scopes = token_data.get("scopes", [])
        if required_scope not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return token_data
    return check

@app.post("/inference")
async def run_inference(
    prompt: str,
    token_data: dict = Depends(require_scope("inference:run")),
) -> dict:
    user = token_data["sub"]
    # ... call LLM ...
    return {"user": user, "response": "..."}
