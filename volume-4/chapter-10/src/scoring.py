"""Step 5: recall on comparable labels."""

# The two detectors name entities differently; compare one set of labels.
LABELS = {"EMAIL_ADDRESS": "EMAIL", "PHONE_NUMBER": "PHONE", "US_SSN": "SSN"}


def detection_score(detected: list, expected_labels: list[str]) -> float:
    """Recall: fraction of expected labels that were detected.

    `detected` is Presidio's list of dicts or the fallback's labels."""
    # TODO 2: map Presidio's labels (dicts with an "entity" key) through LABELS, so that
    # both detectors' results use PERSON, EMAIL, PHONE and SSN.
    detected_labels = {e["entity"] if isinstance(e, dict) else e for e in detected}
    hits = sum(1 for label in expected_labels if label in detected_labels)
    return hits / len(expected_labels) if expected_labels else 1.0
