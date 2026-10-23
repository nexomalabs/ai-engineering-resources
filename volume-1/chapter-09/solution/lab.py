"""Lab 9 — Comparing LLM vs. Reasoning Models (reference solution).

Runs three multi-step math problems under three conditions — a standard model
answering directly, the same model with chain-of-thought prompting, and a
reasoning model — and compares accuracy, tokens, and latency.

Calls replay through the shared LabClient (LAB_PROJECT_STANDARD.md section 6):
no API key needed by default. See "Recording Your Own Fixtures" in the README
to run this against a real account.

Models: MODEL_STANDARD is a standard model that accepts temperature=0.0.
MODEL_REASONING is gpt-6-luna, a reasoning model that accepts only its default
temperature, so call_reasoning sends none. Model names change between
releases; check the current list before recording real fixtures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from nexoma_labs.client import LabClient, Message, mode_banner  # noqa: E402

MODEL_STANDARD = "gpt-5.4-mini"
MODEL_REASONING = "gpt-6-luna"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "chapter-09"

PROBLEMS = [
    {
        "id": "P1",
        "description": "Train meeting problem",
        "problem": (
            "A train leaves Chicago at 9:00 AM traveling toward New York at 60 mph. "
            "A second train leaves New York at 10:00 AM traveling toward Chicago at "
            "80 mph. The cities are 790 miles apart. At what time do the two trains "
            "meet? Give your answer as a specific time (e.g., 3:13 PM)."
        ),
        "answer": "3:13 PM",
    },
    {
        "id": "P2",
        "description": "Compound probability",
        "problem": (
            "A bag contains 4 red balls and 6 blue balls. You draw two balls without "
            "replacement. What is the probability that both balls are red? Express "
            "your answer as a fraction in lowest terms."
        ),
        "answer": "2/15",
    },
    {
        "id": "P3",
        "description": "Work rate problem",
        "problem": (
            "Alice can complete a project in 12 days. Bob can complete the same "
            "project in 8 days. If they work together, how many days will it take "
            "to complete the project? Round to two decimal places."
        ),
        "answer": "4.80 days",
    },
]


def plain_fractions(text: str) -> str:
    r"""Rewrite LaTeX fractions such as \frac{2}{15} as 2/15. Current models
    often answer in LaTeX, and a keyword check would otherwise miss them."""
    return re.sub(r"\\[dt]?frac\{(\d+)\}\{(\d+)\}", r"\1/\2", text)


def check_accuracy(response: str, answer: str) -> bool:
    """Simple keyword match: do the answer's digits/punctuation appear in the response?"""
    text = plain_fractions(response).lower()
    key = "".join(c for c in answer if c.isdigit() or c in "./:")
    return key in text or answer.lower() in text


def call_standard(client: LabClient, problem: str, chain_of_thought: bool):
    suffix = (
        "\n\nThink step by step before giving your final answer."
        if chain_of_thought
        else "\n\nGive only the final answer with no explanation."
    )
    return client.complete(
        [Message("user", problem + suffix)], temperature=0.0, max_completion_tokens=500
    )


def call_reasoning(client: LabClient, problem: str) -> dict:
    """Reasoning-model call. Uses the fixture store directly rather than
    LabClient.complete, because reasoning APIs return an extra
    reasoning_tokens field that the generic Completion type does not model —
    and real reasoning endpoints typically reject a temperature parameter
    entirely, unlike the standard chat endpoint this lab otherwise uses.
    """
    request = {
        "model": MODEL_REASONING,
        "messages": [{"role": "user", "content": problem}],
    }

    def call_live(req: dict) -> dict:
        from openai import OpenAI

        oa = OpenAI()
        resp = oa.chat.completions.create(model=req["model"], messages=req["messages"])
        usage = resp.usage
        details = getattr(usage, "completion_tokens_details", None)
        return {
            "content": resp.choices[0].message.content.strip(),
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
            "total_tokens": usage.total_tokens,
        }

    return client.store.call(request, call_live)


def main() -> int:
    print(mode_banner("OpenAI"))
    print("=" * 72)
    print("Lab 9: Comparing Standard LLM vs. Reasoning Model")
    print("=" * 72)

    client = LabClient(FIXTURES_DIR, MODEL_STANDARD)
    tally = {"direct": 0, "cot": 0, "reasoning": 0}

    for prob in PROBLEMS:
        print(f"\n{'-' * 72}")
        print(f"Problem {prob['id']}: {prob['description']}")
        print(f"Expected answer contains: {prob['answer']}")
        print(f"{'-' * 72}")

        direct = call_standard(client, prob["problem"], chain_of_thought=False)
        ok = check_accuracy(direct.content, prob["answer"])
        tally["direct"] += ok
        print(f"\n[1] {MODEL_STANDARD} | direct answer")
        print(f"    {direct.content[:160]}")
        print(f"    correct={ok}  tokens={direct.total_tokens}")

        cot = call_standard(client, prob["problem"], chain_of_thought=True)
        ok = check_accuracy(cot.content, prob["answer"])
        tally["cot"] += ok
        print(f"\n[2] {MODEL_STANDARD} | chain-of-thought")
        print(f"    {cot.content[:160]}...")
        print(f"    correct={ok}  tokens={cot.total_tokens}")

        reasoning = call_reasoning(client, prob["problem"])
        ok = check_accuracy(reasoning["content"], prob["answer"])
        tally["reasoning"] += ok
        print(f"\n[3] {MODEL_REASONING} | reasoning")
        print(f"    {reasoning['content'][:160]}...")
        print(
            f"    correct={ok}  reasoning_tokens={reasoning['reasoning_tokens']}"
            f"  total_tokens={reasoning['total_tokens']}"
        )

    print(f"\n{'=' * 72}")
    print(f"Accuracy over {len(PROBLEMS)} problems:")
    for mode, correct in tally.items():
        print(f"  {mode:<10} {correct}/{len(PROBLEMS)}")
    print()
    print("The direct condition answers instantly and shows no work, so nothing")
    print("catches a wrong step: in the bundled run it misses the train problem,")
    print("the one that needs a head-start step before the arithmetic.")
    print("Chain-of-thought recovers it by making the model write out intermediate")
    print("steps. The reasoning model gets every problem right too, but it spends")
    print("hidden reasoning tokens first: you pay for them and never see them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
