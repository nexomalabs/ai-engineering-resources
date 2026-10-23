"""Section 10.3: the regex-only fallback, for environments without Presidio."""


def redact_with_regex_fallback(text: str) -> tuple[str, list[str]]:
    """
    Regex-only PII redaction for environments without Presidio.
    Handles email, US phone, SSN, credit card numbers.
    """

    patterns = {
        "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        # (?<!\w), not \b: a number can start with "(" or "+", where \b never matches.
        "PHONE": r"(?<!\w)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }

    # TODO 1: for each label and pattern, if the pattern matches, record the label and
    # replace every match with "[LABEL]". As written, nothing is redacted.
    detected_types = []
    return text, detected_types
