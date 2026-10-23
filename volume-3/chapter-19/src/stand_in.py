"""A deterministic stand-in for the OpenAI client, used when NEXOMA_LAB_MODE is not "live".

It provides the two methods the capstone calls:

- embeddings.create(...): a hashed bag-of-words vector, so retrieval and memory recall
  work offline and give the same ranking every time. It is far cruder than a real
  embedding model; it matches words, not meaning.
- chat.completions.create(...): a rule-based ReAct agent. Arithmetic goes to the
  calculator, "tell me more about" goes to web search, a question about how two things
  relate reads the top document, and anything else is answered from the top retrieved
  passage. After a tool's observation it answers from what it observed.
"""

import hashlib
import json
import re
from types import SimpleNamespace

DIMENSIONS = 256
STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "in",
    "is",
    "are",
    "what",
    "how",
    "does",
    "do",
    "can",
    "you",
    "me",
    "about",
    "more",
    "tell",
    "which",
    "use",
    "for",
    "by",
}
WEB_TOPICS = {
    "transformer": "transformer",
    "prompt": "prompt engineering",
    "rag": "rag retrieval",
    "security": "agent security",
}


def embed(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS:
            continue
        digest = hashlib.md5(word.encode()).digest()
        vector[digest[0] % DIMENSIONS] += 1.0 if digest[1] % 2 else -1.0
    return vector


def _passages(system_prompt: str) -> list[tuple[str, str]]:
    """(doc_id, text) for each retrieved passage in the system prompt, best first."""
    knowledge = system_prompt.split("## Retrieved Knowledge", 1)[-1].split(
        "## Past Research Memory"
    )[0]
    return re.findall(r"\[(doc_\d+) \|[^\]]*\]\n([^\n]+)", knowledge)


def _first_sentences(text: str, n: int) -> str:
    return " ".join(re.split(r"(?<=[.!?])\s+", text.strip())[:n])


def _plan(query: str, passages: list[tuple[str, str]]) -> tuple[str, str, dict] | None:
    q = query.lower()
    power = re.search(r"(\d+)\s*(?:to the power of|\*\*|\^)\s*(\d+)", q)
    times = re.search(r"(\d+)\s*(?:times|multiplied by|\*)\s*(\d+)", q)
    root = re.search(r"square root of (\d+)", q)
    if power:
        return "This is arithmetic.", "calculator", {"expression": f"{power[1]} ** {power[2]}"}
    if times:
        return "This is arithmetic.", "calculator", {"expression": f"{times[1]} * {times[2]}"}
    if root:
        return "This is arithmetic.", "calculator", {"expression": f"sqrt({root[1]})"}
    if "more about" in q:
        topic = next((t for k, t in WEB_TOPICS.items() if k in q), q)
        return "I will look for more on this.", "web_search", {"query": topic}
    if "relate" in q and passages:
        return "I need the full document.", "read_document", {"doc_id": passages[0][0]}
    return None


def reply(messages: list) -> str:
    system = messages[0]["content"]
    query = messages[1]["content"]
    observations = [
        m["content"].removeprefix("Observation: ") for m in messages[2:] if m["role"] == "user"
    ]
    passages = _passages(system)
    plan = _plan(query, passages)

    if plan and not observations:
        thought, tool, args = plan
        return f"Thought: {thought}\nAction: {tool}({json.dumps(args)})"
    if plan:
        observed = observations[-1]
        if plan[1] == "calculator":
            return f"Thought: I have the result.\nAnswer: The result is {observed}."
        if plan[1] == "read_document":
            return f"Thought: The document answers it.\nAnswer: {_first_sentences(observed.split(chr(10), 1)[-1], 4)}"
        grounded = _first_sentences(passages[0][1], 2) if passages else ""
        return f"Thought: I can combine the knowledge base and the search.\nAnswer: {grounded} {observed}".strip()
    if passages:
        return f"Thought: The retrieved knowledge answers this.\nAnswer: {_first_sentences(passages[0][1], 2)}"
    return "Thought: I have nothing to ground an answer in.\nAnswer: That information is not available."


class _Completions:
    def create(self, *, messages, **_settings):
        message = SimpleNamespace(content=reply(messages))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _Embeddings:
    def create(self, *, input, **_settings):
        return SimpleNamespace(data=[SimpleNamespace(embedding=embed(input))])


class StandInClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=_Completions())
        self.embeddings = _Embeddings()
