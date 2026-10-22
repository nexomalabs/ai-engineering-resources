# Applied AI Engineering, Volume II, Chapter 12
# Hands-on Lab: Manual Optimization with OPRO-Style Meta-Prompting
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ============================================================
# TASK: Classify support ticket urgency
# ============================================================

LABELED_DATA = [
    ("My account was hacked and I'm being charged for things I didn't buy", "CRITICAL"),
    ("I can't log in to my account", "HIGH"),
    ("How do I update my billing address?", "LOW"),
    ("I was charged twice for the same order", "HIGH"),
    ("Can you recommend a good product for home use?", "LOW"),
    ("The service has been down for 3 hours and I'm losing business", "CRITICAL"),
    ("I'd like to cancel my subscription", "MEDIUM"),
    ("The app keeps crashing when I try to upload files", "HIGH"),
    ("Do you offer student discounts?", "LOW"),
    ("I need to update my password", "LOW"),
    ("I've been waiting 2 weeks for a refund and nobody responds", "HIGH"),
    ("Your service disrupted my hospital's operations", "CRITICAL"),
]

def evaluate_prompt(instruction: str, data: list) -> float:
    """Score a prompt instruction on the labeled dataset."""
    correct = 0
    for text, true_label in data:
        r = client.chat.completions.create(
            model="gpt-6-luna",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"Ticket: {text}\nUrgency:"}
            ],
            temperature=0,
            max_tokens=15
        )
        pred = r.choices[0].message.content.strip().upper()
        if true_label in pred:
            correct += 1
    return correct / len(data)

# ============================================================
# OPRO-STYLE OPTIMIZATION
# ============================================================

def opro_optimizer(initial_instruction: str, data: list, n_rounds: int = 4) -> str:
    """Optimize an instruction using OPRO-style meta-prompting."""

    history = [(initial_instruction, evaluate_prompt(initial_instruction, data))]
    print(f"Initial: Score={history[0][1]:.2f}\n  Instruction: {initial_instruction[:80]}...")

    for round_num in range(n_rounds):
        # Build history string
        history_str = "\n".join([
            f"Instruction: \"{inst[:100]}...\" → Score: {score:.2f}"
            for inst, score in sorted(history, key=lambda x: x[1])
        ])

        # Ask LLM to generate a better instruction
        r = client.chat.completions.create(
            model="gpt-6.1-sol",
            messages=[{
                "role": "user",
                "content": f"""You are optimizing a system prompt for a support ticket urgency classifier.
The classifier must output one of: CRITICAL, HIGH, MEDIUM, or LOW.

Past instructions and their accuracy scores (higher is better):
{history_str}

Analysis:
- CRITICAL: Security breaches, business operations affected, immediate safety issues
- HIGH: Account issues, billing problems, service failures
- MEDIUM: General requests that need resolution
- LOW: Informational queries, preference questions

Generate one new instruction that you predict will score higher than {max(s for _, s in history):.2f}.
Return ONLY the instruction text, no explanation."""
            }],
            temperature=0.7,
            max_tokens=150
        )
        new_instruction = r.choices[0].message.content.strip()
        new_score = evaluate_prompt(new_instruction, data)
        history.append((new_instruction, new_score))
        print(f"\nRound {round_num+1}: Score={new_score:.2f}")
        print(f"  Instruction: {new_instruction[:100]}...")

    best_instruction, best_score = max(history, key=lambda x: x[1])
    print(f"\n\nBest instruction (score={best_score:.2f}):")
    print(best_instruction)
    return best_instruction

# Run optimization
initial = "Classify the urgency of this support ticket as CRITICAL, HIGH, MEDIUM, or LOW."
best = opro_optimizer(initial, LABELED_DATA, n_rounds=4)
