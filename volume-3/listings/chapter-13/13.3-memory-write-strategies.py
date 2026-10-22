# Applied AI Engineering, Volume III, Chapter 13
# Section 13.3, Memory Write Strategies
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def should_write_to_memory(observation: str, thought: str) -> bool:
    """
    Simple rule-based significance classifier.
    In production, replace with an LLM-based classifier.
    """
    significance_signals = [
        "user preference",
        "user name",
        "confirmed",
        "important",
        "remember",
        "always",
        "never",
        "decided",
        "resolved",
        "learned",
    ]
    combined = (observation + " " + thought).lower()
    return any(signal in combined for signal in significance_signals)
