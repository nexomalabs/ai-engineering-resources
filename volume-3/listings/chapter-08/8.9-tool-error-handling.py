# Applied AI Engineering, Volume III, Chapter 8
# Section 8.9, Tool Error Handling
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import time
from functools import wraps

def with_retry(max_retries: int = 3, backoff_factor: float = 1.5):
    """Decorator for automatic retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1.0
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError) as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator
