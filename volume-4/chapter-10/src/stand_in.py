"""A stand-in for the model, used when NEXOMA_LAB_MODE is not "live".

It answers every message the same way, and its answer contains PII of its own (a
support address), as a real assistant's often does, so the pipeline's output redaction
has something to find.
"""

from types import SimpleNamespace

REPLY = (
    'Thanks for your message: "{message}". I have passed it to our team, who will reply '
    "from support@example.com within one business day."
)


class _Completions:
    def create(self, *, messages, **_settings):
        content = REPLY.format(message=messages[-1]["content"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class StandInClient:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_Completions())
