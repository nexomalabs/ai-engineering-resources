# Applied AI Engineering, Volume II, Chapter 9
# Section 9.7, Output Validation Pipeline
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
from pydantic import BaseModel, ValidationError
from typing import Optional

class SentimentResult(BaseModel):
    sentiment: str  # Will validate against enum in practice
    confidence: float
    key_phrases: list[str]
    reasoning: str

def validated_extraction(raw_output: str, max_retries: int = 2) -> Optional[SentimentResult]:
    for attempt in range(max_retries + 1):
        try:
            data = json.loads(raw_output)
            result = SentimentResult(**data)
            return result
        except json.JSONDecodeError as e:
            print(f"Attempt {attempt+1}: JSON parse error: {e}")
        except ValidationError as e:
            print(f"Attempt {attempt+1}: Schema validation error: {e}")

        if attempt < max_retries:
            # Retry logic would call the LLM again with reinforced format prompt
            pass

    return None
