# Applied AI Engineering, Volume IV, Chapter 5
# Hands-on Lab: Containerized AI API Service
# Copied from the book by scripts/export_listings.py. Report errors as errata.

"""Application configuration loaded from environment variables."""
import os
from dataclasses import dataclass

@dataclass
class Settings:
    openai_api_key: str
    model_name: str
    max_tokens: int
    request_timeout: float
    environment: str
    log_level: str
    service_version: str

def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.environ["OPENAI_API_KEY"],  # Required
        model_name=os.environ.get("MODEL_NAME", "gpt-6-luna"),
        max_tokens=int(os.environ.get("MAX_TOKENS", "512")),
        request_timeout=float(os.environ.get("REQUEST_TIMEOUT_S", "30")),
        environment=os.environ.get("ENVIRONMENT", "development"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        service_version=os.environ.get("SERVICE_VERSION", "unknown"),
    )
