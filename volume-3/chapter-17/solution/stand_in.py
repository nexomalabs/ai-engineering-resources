"""A deterministic stand-in for the OpenAI client, used when NEXOMA_LAB_MODE is not "live".

It exposes the one method the lab calls, client.chat.completions.create(...), and plays
a ReAct agent from a script: each test case's task maps to the actions it takes. Most
tasks take the optimal path. Two do not, so the evaluation has something to find:
"2 to the power of 10" first sends an expression the calculator cannot parse and then
recovers, and "the highest mountain" searches for the wrong words and gives up.

On the four claims it repeats the habits the chapter's story found in the traces: it
checks the photos twice on every claim and never reads the carrier's handling log, so
it approves the late-reported dent and the claim with no receipt.
"""

import json
from types import SimpleNamespace

# task -> list of (thought, tool, args); the agent answers after the last observation.
SCRIPTS = {
    "What is the capital of France?": [
        ("I should search for this.", "search", {"query": "capital of France"})
    ],
    "Calculate 15 times 8.": [("This is arithmetic.", "calculator", {"expression": "15 * 8"})],
    "What is the population of Tokyo?": [
        ("I should search for this.", "search", {"query": "population of Tokyo"})
    ],
    "What is 2 to the power of 10?": [
        ("This is arithmetic.", "calculator", {"expression": "2^10"}),
        ("The calculator needs Python syntax for powers.", "calculator", {"expression": "2 ** 10"}),
    ],
    "What is the current weather in London?": [
        ("I need the weather tool.", "get_weather", {"city": "London"})
    ],
    "What is the speed of light in meters per second?": [
        ("I should search for this.", "search", {"query": "speed of light"})
    ],
    "What is 100 divided by 4?": [("This is arithmetic.", "calculator", {"expression": "100 / 4"})],
    "When was Python first released?": [
        ("I should search for this.", "search", {"query": "Python release year"})
    ],
    "What is the highest mountain and its height?": [
        ("I should search for this.", "search", {"query": "tallest peak on Earth"})
    ],
    "What is the weather in Tokyo?": [
        ("I need the weather tool.", "get_weather", {"city": "Tokyo"})
    ],
    "Claim C-201: a laptop arrived with a cracked hinge. Approve, reject or escalate?": [
        ("I should look at the photos.", "check_photos", {"claim_id": "C-201"}),
        ("Let me check the photos again.", "check_photos", {"claim_id": "C-201"}),
        ("Now the receipt.", "get_receipt", {"claim_id": "C-201"}),
    ],
    "Claim C-202: headphones reported faulty. Approve, reject or escalate?": [
        ("I should look at the photos.", "check_photos", {"claim_id": "C-202"}),
        ("Let me check the photos again.", "check_photos", {"claim_id": "C-202"}),
        ("Now the receipt.", "get_receipt", {"claim_id": "C-202"}),
    ],
    "Claim C-203: a dented speaker, reported days after delivery. Approve, reject or escalate?": [
        ("I should look at the photos.", "check_photos", {"claim_id": "C-203"}),
        ("Let me check the photos again.", "check_photos", {"claim_id": "C-203"}),
    ],
    "Claim C-204: a cracked phone screen, no receipt attached. Approve, reject or escalate?": [
        ("I should look at the photos.", "check_photos", {"claim_id": "C-204"}),
        ("Let me check the photos again.", "check_photos", {"claim_id": "C-204"}),
    ],
}

# The claims' final answers; the lookups answer with their last observation.
ANSWERS = {
    "C-201": "Approve: the photos show a cracked hinge and the receipt matches.",
    "C-202": "Reject: the photos show months of wear on a pair bought 9 months ago.",
    "C-203": "Approve: the photos show a dented casing.",
    "C-204": "Approve: the photo shows a cracked screen.",
}

NO_RESULT = ("No results found", "Cannot compute", "unavailable")


def reply(messages: list) -> str:
    task = next(m["content"] for m in messages if m["role"] == "user")
    observations = [m["content"] for m in messages[2:] if m["role"] == "user"]
    script = SCRIPTS.get(task, [])
    step = len(observations)
    if step < len(script):
        thought, tool, args = script[step]
        return f"Thought: {thought}\nAction: {tool}({json.dumps(args)})"
    claim = next((cid for cid in ANSWERS if task.startswith(f"Claim {cid}")), None)
    if claim:
        return f"Thought: I have what I need.\nAnswer: {ANSWERS[claim]}"
    last = observations[-1].removeprefix("Observation: ") if observations else ""
    if not last or any(marker in last for marker in NO_RESULT):
        return "Thought: The tools did not give me the answer.\nAnswer: I could not find that."
    return f"Thought: The observation answers the question.\nAnswer: {last}"


class _Completions:
    def create(self, *, messages, **_settings):
        content = reply(messages)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class StandInClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=_Completions())
