"""A deterministic stand-in for the OpenAI client, used when NEXOMA_LAB_MODE is not "live".

It answers the lab's test inputs with fixed replies. Input that reaches it with an
injection already removed gets a refusal. The JWT answer includes a hard-coded signing
secret, the kind of thing a model really does write into example code, so the output
sanitizer has something to redact.
"""

from types import SimpleNamespace

REPLIES = {
    "capital of Germany": "The capital of Germany is Berlin.",
    "TCP and UDP": (
        "TCP is connection-oriented and guarantees ordered, reliable delivery; UDP is "
        "connectionless and faster, with no delivery guarantee."
    ),
    "Fibonacci": (
        "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n"
        "    return a"
    ),
    "JWT authentication": (
        "Use the PyJWT library. Sign tokens with a secret and verify them on each request:\n"
        "secret_key = 'my-signing-secret-2026'\n"
        "token = jwt.encode({'sub': user_id}, secret_key, algorithm='HS256')"
    ),
}
REFUSAL = (
    "I can't change my role, ignore my guidelines or reveal my configuration, but I'm "
    "happy to help with something else."
)


def reply(user_input: str) -> str:
    if "[INJECTION ATTEMPT REMOVED]" in user_input:
        return REFUSAL
    for key, text in REPLIES.items():
        if key.lower() in user_input.lower():
            return text
    return "I don't have a scripted answer for that; run in live mode to ask the model."


class _Completions:
    def create(self, *, messages, **_settings):
        user = next(m["content"] for m in messages if m["role"] == "user")
        message = SimpleNamespace(content=reply(user))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class StandInClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=_Completions())
