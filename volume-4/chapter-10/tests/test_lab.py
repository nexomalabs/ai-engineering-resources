"""Tests for Lab 10. Run against solution/ in CI with the regex fallback and the stand-in model.
The Presidio tests run only when the optional `presidio` group is installed."""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solution"))

import lab10_pipeline as lab  # noqa: E402
from dataset import DATASET  # noqa: E402
from pii_regex import redact_with_regex_fallback  # noqa: E402
from scoring import detection_score  # noqa: E402


@pytest.mark.parametrize(
    "text, redacted",
    [
        ("Call me back on (415) 555-0132 after 5pm.", "Call me back on [PHONE] after 5pm."),
        ("Reach me at +1 312 555 0145 today", "Reach me at [PHONE] today"),
        ("Mail jo@example.com", "Mail [EMAIL]"),
        ("SSN 987-65-4325", "SSN [SSN]"),
        ("Card 4111-1111-1111-1111", "Card [CREDIT_CARD]"),
    ],
)
def test_regex_fallback_redacts_whole_values(text, redacted):
    assert redact_with_regex_fallback(text)[0] == redacted


def test_regex_fallback_leaves_names_and_plain_text_alone():
    text = "James O'Brien asked about pricing."
    assert redact_with_regex_fallback(text) == (text, [])


def test_scoring_maps_presidio_labels():
    presidio_style = [{"entity": "EMAIL_ADDRESS"}, {"entity": "US_SSN"}, {"entity": "PERSON"}]
    assert detection_score(presidio_style, ["EMAIL", "SSN", "PERSON"]) == 1.0
    assert detection_score(["EMAIL"], ["EMAIL", "PHONE"]) == 0.5
    assert detection_score([], []) == 1.0


def test_regex_recall_matches_the_chapter():
    labels = {"PERSON": [], "EMAIL": [], "PHONE": [], "SSN": []}
    for text, expected in DATASET:
        found = redact_with_regex_fallback(text)[1]
        for label in expected:
            labels[label].append(detection_score(found, [label]))
    assert all(sum(v) == len(v) for k, v in labels.items() if k != "PERSON")
    assert sum(labels["PERSON"]) == 0


def test_model_sees_only_redacted_input_and_output_is_redacted_too():
    result = lab.safe_llm_call("My SSN is 987-65-4325.", lab.client)
    assert "987-65-4325" not in result["redacted_input"]
    assert "support@example.com" in result["raw_output"]
    assert "support@example.com" not in result["redacted_output"]


def test_presidio_detects_names_too():
    pytest.importorskip("presidio_analyzer")
    from pii_presidio import redact_pii

    redacted, entities = redact_pii("This is David Chen; reach me at david.chen@example.org.")
    assert {e["entity"] for e in entities} >= {"PERSON", "EMAIL_ADDRESS"}
    assert "David Chen" not in redacted
