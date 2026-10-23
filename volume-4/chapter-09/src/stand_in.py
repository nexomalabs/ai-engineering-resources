"""A stand-in for OpenAI's moderation endpoint, used when NEXOMA_LAB_MODE is not "live".

It flags text that contains a few unmistakable phrases, by category, so the lab's
output-moderation path can be exercised with no key. The real endpoint is a trained
classifier and catches far more than a word list.
"""

FLAGGED_PHRASES = {
    "violence": ["kill them", "hurt someone", "build a bomb"],
    "self_harm": ["hurt myself"],
    "illicit": ["steal a car", "make a weapon"],
}


def stand_in_moderation(text: str) -> dict:
    lowered = text.lower()
    categories = {
        category: True
        for category, phrases in FLAGGED_PHRASES.items()
        if any(phrase in lowered for phrase in phrases)
    }
    return {"flagged": bool(categories), "categories": categories}
