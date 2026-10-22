# Applied AI Engineering, Volume II, Chapter 10
# Hands-on Lab: Reasoning Strategies: Comparative Implementation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
import re
from collections import Counter
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PROBLEMS = [
    {
        "question": "A school has 3 grade levels. Grade 1 has 120 students, Grade 2 has 15% more than Grade 1, and Grade 3 has 20% fewer than Grade 2. If each student needs 3 notebooks and notebooks come in packs of 10, how many packs does the school need?",
        "answer": 42,
        "type": "compositional_math"
    },
    {
        "question": "If all Zorbels are Morbles, and some Morbles are Flurbs, can we conclude that some Zorbels are Flurbs?",
        "answer": "no",
        "type": "logical_inference"
    }
]

def run_cot(question: str) -> str:
    r = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": f"{question}\n\nLet's think step by step."}],
        temperature=0, max_tokens=400
    )
    return r.choices[0].message.content

def run_self_consistency(question: str, n: int = 5) -> str:
    answers = []
    for _ in range(n):
        r = client.chat.completions.create(
            model="gpt-6-luna",
            messages=[{"role": "user", "content": f"{question}\n\nThink step by step and provide a final answer."}],
            temperature=0.7, max_tokens=300
        )
        text = r.choices[0].message.content
        # Extract answer (last sentence)
        sentences = text.split(".")
        answers.append(sentences[-2].strip() if len(sentences) > 1 else text[-50:])

    # Return majority
    counts = Counter(answers)
    return f"Majority answer (from {n} samples): {counts.most_common(1)[0][0]}"

def run_least_to_most(question: str) -> str:
    # Phase 1: Decompose
    decomp_r = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{
            "role": "user",
            "content": f"""To answer this question, identify 3-4 simpler sub-questions that must be answered first:

Question: {question}

List the sub-questions in order from simplest to most complex."""
        }],
        temperature=0, max_tokens=200
    )
    sub_questions = decomp_r.choices[0].message.content

    # Phase 2: Solve sequentially
    solve_r = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{
            "role": "user",
            "content": f"""Sub-problems identified:
{sub_questions}

Now solve each sub-problem in order, using previous answers to solve later ones.
Finally, combine all answers to solve the original question:

{question}"""
        }],
        temperature=0, max_tokens=400
    )
    return solve_r.choices[0].message.content

# Run comparison
for prob in PROBLEMS:
    print(f"\n{'='*60}")
    print(f"PROBLEM: {prob['question'][:80]}...")
    print(f"Type: {prob['type']} | Expected: {prob['answer']}")

    print("\n--- Chain-of-Thought ---")
    cot = run_cot(prob["question"])
    print(cot[-200:])  # Last 200 chars

    print("\n--- Least-to-Most ---")
    ltm = run_least_to_most(prob["question"])
    print(ltm[-200:])

    print("\n--- Self-Consistency (3 samples) ---")
    sc = run_self_consistency(prob["question"], n=3)
    print(sc)
