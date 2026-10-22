# Applied AI Engineering, Volume IV, Chapter 5
# Section 5.6, API Gateway Patterns
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # PyJWT

SECRET_KEY = "loaded-from-secrets-manager"  # Never hardcode
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

app = FastAPI()

@app.post("/api/v1/analyze")
async def analyze(
    request: dict,
    claims: dict = Depends(verify_token),
) -> dict:
    user_id = claims.get("sub")
    # ... process request scoped to user_id
    return {"result": "analysis"}
