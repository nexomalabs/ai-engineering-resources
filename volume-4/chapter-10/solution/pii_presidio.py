"""Section 10.3: Presidio redaction. Needs the optional `presidio` dependency group."""

# Requires: pip install presidio-analyzer presidio-anonymizer spacy
#           python -m spacy download en_core_web_lg

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Initialize engines (load once at startup)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def redact_pii(text: str, language: str = "en") -> tuple[str, list[dict]]:
    """
    Detect and redact PII from text.
    Returns (redacted_text, list_of_detected_entities).
    """
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=[
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "US_SSN",
            "CREDIT_CARD",
            "LOCATION",
            "IP_ADDRESS",
            "US_PASSPORT",
            "US_DRIVER_LICENSE",
        ],
        # Structured recognizers such as PHONE_NUMBER start at 0.4 and rise only when a
        # context word ("phone", "call") is nearby; a higher threshold lets most
        # phone numbers through unredacted.
        score_threshold=0.4,
    )

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP_ADDRESS]"}),
        },
    )

    detected = [
        {"entity": r.entity_type, "start": r.start, "end": r.end, "score": round(r.score, 2)}
        for r in results
    ]
    return anonymized.text, detected
