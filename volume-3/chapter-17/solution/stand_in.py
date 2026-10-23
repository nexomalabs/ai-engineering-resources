"""A deterministic stand-in for the OpenAI client, used when NEXOMA_LAB_MODE is not "live".

It exposes the one method the lab calls, client.chat.completions.create(...), and plays
a ReAct agent from a script: each test case's task maps to the actions it takes. Most
tasks take the optimal path. Two do not, so the evaluation has something to find:
"2 to the power of 10" first sends an expression the calculator cannot parse and then
recovers, and "the highest mountain" searches for the wrong words and gives up.
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
