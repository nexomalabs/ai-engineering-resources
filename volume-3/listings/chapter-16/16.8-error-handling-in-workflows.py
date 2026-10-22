# Applied AI Engineering, Volume III, Chapter 16
# Section 16.8, Error Handling in Workflows
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)
T = TypeVar("T")


class WorkflowError(Exception):
    """Base class for workflow errors."""
    pass


class TransientError(WorkflowError):
    """Retriable infrastructure failure."""
    pass


class SemanticError(WorkflowError):
    """AI output failed validation; may be retried with modified prompt."""
    pass


class FatalError(WorkflowError):
    """Non-retriable error; workflow must stop."""
    pass


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    retryable_exceptions: tuple = (TransientError,),
):
    """Decorator: retry a workflow step with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, exc
                        )
                        raise
                    wait = backoff_base ** (attempt - 1)
                    logger.warning(
                        "%s attempt %d/%d failed (%s). Retrying in %.1fs...",
                        func.__name__, attempt, max_attempts, exc, wait
                    )
                    time.sleep(wait)
                except FatalError:
                    logger.error("%s: fatal error, aborting.", func.__name__)
                    raise
            raise last_exception  # unreachable but satisfies type checker
        return wrapper
    return decorator


def validate_classification_output(output: dict) -> None:
    """Validate that classification output meets schema requirements."""
    required_keys = {"type", "topic", "confidence"}
    missing = required_keys - set(output.keys())
    if missing:
        raise SemanticError(f"Classification output missing keys: {missing}")
    if not (0.0 <= output["confidence"] <= 1.0):
        raise SemanticError(f"Invalid confidence value: {output['confidence']}")
    valid_types = {"report", "article", "email", "memo", "contract", "unknown"}
    if output["type"] not in valid_types:
        raise SemanticError(f"Invalid document type: {output['type']}")


@with_retry(max_attempts=3, retryable_exceptions=(TransientError, SemanticError))
def robust_classify(text: str) -> dict:
    """Classification step with retry and validation."""
    import json, re
    try:
        result_raw = llm_call(
            f"Classify this text. Return JSON with keys: type, topic, confidence.\n\n{text}"
        )
        match = re.search(r"\{.*\}", result_raw, re.DOTALL)
        if not match:
            raise SemanticError("No JSON object found in classification response.")
        result = json.loads(match.group())
        validate_classification_output(result)
        return result
    except json.JSONDecodeError as e:
        raise SemanticError(f"JSON parse failed: {e}") from e
    except Exception as e:
        if "rate limit" in str(e).lower() or "timeout" in str(e).lower():
            raise TransientError(str(e)) from e
        raise
