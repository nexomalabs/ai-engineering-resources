# Applied AI Engineering, Volume IV, Chapter 9
# Hands-on Lab: Security Middleware for FastAPI
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from security_middleware import detect_injection, get_limiter, moderate_output, verify_token

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(
    request: ChatRequest,
    token_data: dict = Depends(verify_token),
):
    user_id = token_data["sub"]
    # Rate limit check
    limiter = get_limiter(user_id, capacity=5, rate=0.5)
    if not limiter.consume():
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    # Input validation
    injection = detect_injection(request.message)
    if injection:
        raise HTTPException(status_code=400, detail=f"Injection pattern detected: {injection}")
    # LLM call (mocked for the lab)
    response_text = f"Echo: {request.message}"
    # Output validation
    mod_result = moderate_output(response_text)
    if mod_result["flagged"]:
        raise HTTPException(status_code=422, detail="Output policy violation")
    return {"response": response_text}
