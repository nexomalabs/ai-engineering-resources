"""Step 5: recall on comparable labels."""

# Presidio and the regex fallback name the same things differently; compare one set.
LABELS = {"EMAIL_ADDRESS": "EMAIL", "PHONE_NUMBER": "PHONE", "US_SSN": "SSN"}


def detection_score(detected: list, expected_labels: list[str]) -> float:
    """Recall: fraction of expected labels that were detected.

    `detected` is Presidio's list of dicts or the fallback's list of label strings."""
    detected_labels = {
        LABELS.get(e["entity"], e["entity"]) if isinstance(e, dict) else e for e in detected
    }
    hits = sum(1 for label in expected_labels if label in detected_labels)
    return hits / len(expected_labels) if expected_labels else 1.0
