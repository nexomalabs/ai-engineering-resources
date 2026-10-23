import sys
from pathlib import Path

# Find the volume's shared/ folder, which holds the recording client.
sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in Path(__file__).resolve().parents
            if (p / "shared" / "nexoma_labs").is_dir()
        )
    ),
)

import os

from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# THREE PROMPTS WITH EMBEDDED ANTI-PATTERNS
# ============================================================

PROMPTS_TO_FIX = [
    {
        "name": "Customer Support Bot (Multiple Anti-Patterns)",
        "original": """You are an AI assistant. Help customers with their questions.
        Be helpful and nice. Don't be rude. Don't be too long. Don't use technical words.
        Don't be confusing. Be clear. Always answer the question. Don't say I don't know.
        Be friendly but professional. Don't use bullet points too much. Be accurate.
        Don't make mistakes. Be helpful.""",
        "test_input": "I've been charged $49.99 twice for the same subscription. What do I do?",
        "anti_patterns": [
            "Vague Role",
            "Over-Instruction",
            "Negation Abuse",
            "Conflicting Persona",
        ],
        "refactored": """You are a customer success specialist at a SaaS company. Your goal
is to resolve billing and account issues efficiently.

Rules:
1. For billing issues: first acknowledge the problem, then provide specific resolution steps
2. Always include a timeline for resolution
3. If resolution requires action from the customer, list steps 1, 2, 3
4. Use plain language (no billing system terminology)
5. Close with a direct contact for follow-up""",
    },
    {
        "name": "Content Strategy Assistant (Missing Context + Sycophancy)",
        "original": """You are a content marketing expert. Evaluate my content strategy
and tell me if it's good. Give me detailed feedback.""",
        "test_input": "My strategy is to post 10 blog posts per day covering every possible topic in my niche.",
        "anti_patterns": ["Missing Context", "Sycophancy Trap", "Ambiguous Task"],
        "refactored": """You are a content marketing strategist with expertise in B2B SaaS content.

Evaluate the content strategy described below with honest, evidence-based analysis.

Your evaluation must include:
1. What works (if anything, with specific reasoning)
2. Specific risks and challenges with this approach
3. Industry benchmark context (what strategies typically work)
4. A clear recommendation: Proceed / Significantly Revise / Start Over — with justification

Be direct. If the strategy has fundamental problems, say so clearly.
Validation without substance is not helpful feedback.

Strategy to evaluate: """,
    },
]


def test_prompt(prompt_system: str, user_input: str) -> str:
    r = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": user_input},
        ],
        temperature=0.2,
        max_completion_tokens=400,
    )
    return r.choices[0].message.content


for p in PROMPTS_TO_FIX:
    print(f"\n{'=' * 60}")
    print(f"PROMPT: {p['name']}")
    print(f"Anti-patterns present: {', '.join(p['anti_patterns'])}")

    print("\n--- ORIGINAL PROMPT OUTPUT ---")
    orig_output = test_prompt(p["original"], p["test_input"])
    print(orig_output[:400])

    print("\n--- REFACTORED PROMPT OUTPUT ---")
    ref_output = test_prompt(p["refactored"], p["test_input"])
    print(ref_output[:400])

    print()

# ============================================================
# ANTI-PATTERN SCANNER
# ============================================================


def scan_for_antipatterns(prompt: str) -> list[str]:
    """Simple heuristic scanner for common anti-patterns."""
    found = []
    text = prompt.lower()

    # Vague role check
    vague_roles = [
        "you are an ai",
        "you are a helpful",
        "you are an assistant",
        "you are an expert",
    ]
    if any(v in text for v in vague_roles):
        found.append("⚠ Vague Role")

    # Negation abuse check
    negations = (
        text.count("don't") + text.count("do not") + text.count("never") + text.count("avoid")
    )
    positives = (
        text.count("return") + text.count("provide") + text.count("write") + text.count("use")
    )
    if negations > positives:
        found.append("⚠ Negation Abuse")

    # Over-instruction check
    if text.count("\n") > 20 or len(prompt) > 1500:
        found.append("⚠ Possible Over-Instruction or Prompt Bloat")

    # Missing context check
    specific_refs = ["this project", "our company", "the document", "this report", "our product"]
    if any(ref in text for ref in specific_refs) and "<" not in text:
        found.append("⚠ Possible Missing Context (specific reference without context block)")

    return found if found else ["✓ No obvious anti-patterns detected"]


print("\n\nANTI-PATTERN SCANNER")
print("=" * 60)
for p in PROMPTS_TO_FIX:
    print(f"\n{p['name']}:")
    for finding in scan_for_antipatterns(p["original"]):
        print(f"  {finding}")
