# Applied AI Engineering, Volume II, Chapter 14
# Section 14.4, Prompt Logging for Production Debugging
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from dataclasses import dataclass


@dataclass
class PromptExecutionLog:
    log_id: str
    timestamp: str
    prompt_id: str
    prompt_version: str
    model: str
    model_params: dict
    input_hash: str          # Hash of input for privacy
    input_length_tokens: int
    output_raw: str
    output_length_tokens: int
    parse_success: bool
    validation_success: bool
    latency_ms: int
    error_type: str | None
    error_detail: str | None
    retry_count: int = 0
