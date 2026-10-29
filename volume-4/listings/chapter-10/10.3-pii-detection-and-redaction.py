# Applied AI Engineering, Volume IV, Chapter 10
# Section 10.3, PII Detection and Redaction
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# PII detection and redaction pipeline
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
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "US_SSN", "CREDIT_CARD", "LOCATION",
            "IP_ADDRESS", "US_PASSPORT", "US_DRIVER_LICENSE",
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


def redact_with_regex_fallback(text: str) -> tuple[str, list[str]]:
    """
    Regex-only PII redaction for environments without Presidio.
    Handles email, US phone, SSN, credit card and passport numbers, and dates.
    """
    import re

    patterns = {
        "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        # (?<!\w), not \b: a number can start with "(" or "+", where \b never matches.
        "PHONE": r"(?<!\w)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        # A nine-digit number, the form of UK and US passport numbers
        "PASSPORT": r"\b\d{9}\b",
        # A full date, such as a date of birth
        "DATE": r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{4}\b",
    }

    detected_types = []
    for label, pattern in patterns.items():
        compiled = re.compile(pattern)
        if compiled.search(text):
            detected_types.append(label)
            text = compiled.sub(f"[{label}]", text)

    return text, detected_types


# Example usage
if __name__ == "__main__":
    sample_texts = [
        "My name is Alice Johnson and my email is alice.johnson@example.com. Call me at 555-867-5309.",
        # 987-65-4325 is in a range the Social Security Administration reserves for
        # advertising, so it belongs to no one. Presidio rejects well-known invalid
        # examples such as 123-45-6789, so they make poor test data.
        "Patient SSN: 987-65-4325. Please bill card 4111-1111-1111-1111.",
        "Send the report to Bob Smith at 742 Evergreen Terrace, Springfield.",
    ]

    print("=== Presidio Redaction ===")
    for text in sample_texts:
        redacted, entities = redact_pii(text)
        print(f"Original : {text}")
        print(f"Redacted : {redacted}")
        print(f"Detected : {entities}")
        print()
