"""Steps 1, 3, 4 and 5: redact around a model call, then compare the two detectors.

Uses Presidio when it is installed (`uv sync --group presidio`), and the regex fallback
otherwise; the comparison in Step 4 needs both.

    NEXOMA_LAB_MODE=fixture  (default) a stand-in plays the model; no key
    NEXOMA_LAB_MODE=live     calls gpt-6-luna; needs OPENAI_API_KEY and `--group live`
"""

import os

from dataset import DATASET
from pii_regex import redact_with_regex_fallback
from scoring import detection_score

try:
    from pii_presidio import redact_pii

    HAVE_PRESIDIO = True
except ImportError:  # presidio or its spaCy model is not installed
    HAVE_PRESIDIO = False

    def redact_pii(text: str) -> tuple[str, list]:
        return redact_with_regex_fallback(text)


if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    from openai import OpenAI

    client = OpenAI()
else:
    from stand_in import StandInClient

    client = StandInClient()


def safe_llm_call(user_input: str, client) -> dict:
    # Redact input
    redacted_input, input_entities = redact_pii(user_input)
    # LLM call with redacted input
    resp = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": redacted_input}],
        max_completion_tokens=150,
    )
    raw_output = resp.choices[0].message.content or ""
    # Redact output
    redacted_output, output_entities = redact_pii(raw_output)
    return {
        "redacted_input": redacted_input,
        "input_entities": input_entities,
        "raw_output": raw_output,
        "redacted_output": redacted_output,
        "output_entities": output_entities,
    }


def compare_detectors() -> None:
    """Step 4 and 5: recall of each detector, overall and per label."""
    detectors = {"regex fallback": redact_with_regex_fallback}
    if HAVE_PRESIDIO:
        detectors = {"Presidio": redact_pii} | detectors
    labels = ["PERSON", "EMAIL", "PHONE", "SSN"]
    print(f"\n{'Detector':<16}{'recall':>8}" + "".join(f"{label:>8}" for label in labels))
    for name, detect in detectors.items():
        per_input = [(detect(text)[1], expected) for text, expected in DATASET]
        overall = [detection_score(found, expected) for found, expected in per_input if expected]
        row = f"{name:<16}{sum(overall) / len(overall):>8.0%}"
        for label in labels:
            relevant = [(found, [label]) for found, expected in per_input if label in expected]
            row += f"{sum(detection_score(f, e) for f, e in relevant) / len(relevant):>8.0%}"
        print(row)


if __name__ == "__main__":
    print(f"Detector: {'Presidio' if HAVE_PRESIDIO else 'regex fallback (Presidio not installed)'}")
    for text, _ in DATASET:  # Step 3
        result = safe_llm_call(text, client)
        print(f"\nOriginal : {text}")
        print(f"Redacted : {result['redacted_input']}")
        print(f"Detected : {result['input_entities']}")
        print(f"Output   : {result['redacted_output']}")
    compare_detectors()
