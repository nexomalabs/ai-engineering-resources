"""Step 5: the transparency control from the chapter's opening story, run on every deployment.

The EU AI Act's Article 50 requires that people interacting with an AI system be told so,
unless it is obvious. Wren's greeting said "Hi, I'm Wren!" and nothing else, and some
customers believed they were talking to a person. The team's greeting now says that Wren
is an AI assistant and how to reach a person, and this control checks it at every release.
The disclosure is the legal requirement; the route to a person is the team's own standard.

    python solution/transparency.py
"""

import re

from compliance_runner import AISystemProfile, ComplianceControl, ControlSeverity, ControlStatus

DISCLOSES_AI = re.compile(
    r"\b(AI|artificial intelligence|virtual assistant|automated assistant|chatbot)\b"
)
OFFERS_A_PERSON = re.compile(r"\b(person|human|agent|colleague)\b", re.IGNORECASE)


def evaluate_greeting(profile: AISystemProfile) -> ControlStatus:
    """COMPLIANT: discloses the AI and offers a person. PARTIAL: only discloses."""
    if profile.greeting is None:
        return ControlStatus.NOT_APPLICABLE  # not a chatbot
    if not DISCLOSES_AI.search(profile.greeting):
        return ControlStatus.NON_COMPLIANT
    if not OFFERS_A_PERSON.search(profile.greeting):
        return ControlStatus.PARTIAL
    return ControlStatus.COMPLIANT


CHATBOT_DISCLOSURE = ComplianceControl(
    control_id="EU-50.1",
    framework="EU AI Act",
    category="TRANSPARENCY",
    title="Chatbot tells users it is an AI",
    description=(
        "A system that talks to people says, at the start, that it is an AI system, "
        "and how to reach a person."
    ),
    severity=ControlSeverity.HIGH,
    evaluator=evaluate_greeting,
)

GREETINGS = {
    "before the mapping": "Hi, I'm Wren!",
    "a first fix": "Hi, I'm Wren, Wrenfield's AI assistant. How can I help?",
    "after the mapping": (
        "Hi, I'm Wren, Wrenfield's AI assistant. To talk to a person instead, "
        "type 'agent' at any time."
    ),
}


def main() -> None:
    print(f"{CHATBOT_DISCLOSURE.control_id} {CHATBOT_DISCLOSURE.title}\n")
    for label, greeting in GREETINGS.items():
        profile = AISystemProfile("Wren", "4.2.0", "2026-12-01", greeting=greeting)
        result = CHATBOT_DISCLOSURE.evaluate(profile)
        print(f"  {result.status.value:<14} {label:<19} {greeting}")
    other = CHATBOT_DISCLOSURE.evaluate(AISystemProfile("Customs pipeline", "1.3.0", "2026-12-01"))
    print(f"  {other.status.value:<14} {'customs pipeline':<19} (no chat, so no greeting)")


if __name__ == "__main__":
    main()
