"""Section 10.3: the regex-only fallback, for environments without Presidio."""


def redact_with_regex_fallback(text: str) -> tuple[str, list[str]]:
    """
    Regex-only PII redaction for environments without Presidio.
    Handles email, US phone, SSN, credit card numbers.
    """
    import re

    patterns = {
        "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        # (?<!\w), not \b: a number can start with "(" or "+", where \b never matches.
        "PHONE": r"(?<!\w)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }

    detected_types = []
    for label, pattern in patterns.items():
        compiled = re.compile(pattern)
        if compiled.search(text):
            detected_types.append(label)
            text = compiled.sub(f"[{label}]", text)

    return text, detected_types
