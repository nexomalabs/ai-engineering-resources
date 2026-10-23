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
    lab_mode: str


def get_settings() -> Settings:
    return Settings(
        # Required in live mode; the default fixture mode uses a stand-in model.
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        model_name=os.environ.get("MODEL_NAME", "gpt-6-luna"),
        max_tokens=int(os.environ.get("MAX_TOKENS", "512")),
        request_timeout=float(os.environ.get("REQUEST_TIMEOUT_S", "30")),
        environment=os.environ.get("ENVIRONMENT", "development"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        service_version=os.environ.get("SERVICE_VERSION", "unknown"),
        lab_mode=os.environ.get("NEXOMA_LAB_MODE", "fixture"),
    )
