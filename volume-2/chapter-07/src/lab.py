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
import re
from collections import Counter

from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MATH_PROBLEMS = [
    {
        "question": "A car averages 32 miles per gallon on the highway. If gas costs $3.45 per gallon and a trip covers 280 miles, what is the total fuel cost?",
        "correct_answer": 30.19,
    },
    {
        "question": "A company has 240 employees. If 15% receive a promotion, and 8% of those promoted also get a salary increase, how many employees get both a promotion and a salary increase?",
        "correct_answer": 2.88,  # approximately 3 employees
    },
    {
        "question": "A rectangular garden is 12 meters long and 8 meters wide. A path 1.5 meters wide runs around the outside. What is the area of the path?",
        "correct_answer": 105.0,
    },
]

FEW_SHOT_COT_EXAMPLES = """
Q: A bakery makes 240 cookies per hour. If they operate for 6.5 hours and sell 80% of their output, how many cookies are sold?

A: Let's work through this step by step.
Step 1: Total cookies produced = 240 cookies/hour × 6.5 hours = 1,560 cookies
Step 2: Cookies sold = 1,560 × 0.80 = 1,248 cookies
Answer: 1,248 cookies are sold.

Q: A project team of 5 people can complete a task in 12 days. How long will it take 8 people to complete the same task, assuming equal productivity?

A: Let's work through this step by step.
Step 1: Total person-days required = 5 people × 12 days = 60 person-days
Step 2: Time for 8 people = 60 person-days ÷ 8 people = 7.5 days
Answer: 8 people will complete the task in 7.5 days.

"""


def run_standard(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": f"Solve this math problem: {question}\n\nAnswer:"}],
        temperature=0,
        max_completion_tokens=100,
    )
    return response.choices[0].message.content.strip()


def run_zero_shot_cot(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": f"{question}\n\nLet's think step by step."}],
        temperature=0,
        max_completion_tokens=300,
    )
    return response.choices[0].message.content.strip()


def run_few_shot_cot(question: str) -> str:
    prompt = FEW_SHOT_COT_EXAMPLES + f"Q: {question}\n\nA: Let's work through this step by step."
    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=300,
    )
    return response.choices[0].message.content.strip()


def run_self_consistency(question: str, n_samples: int = 5) -> str:
    """Generate multiple chains and return majority-vote answer."""
    answers = []
    for _ in range(n_samples):
        response = client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=[{"role": "user", "content": f"{question}\n\nLet's think step by step."}],
            temperature=0.7,
            max_completion_tokens=300,
        )
        text = response.choices[0].message.content
        # Extract numerical answers using regex
        numbers = re.findall(
            r"\$?(\d+(?:\.\d+)?)", text.split("Answer:")[-1] if "Answer:" in text else text[-100:]
        )
        if numbers:
            answers.append(numbers[-1])

    if not answers:
        return "Could not extract answer"

    vote_counts = Counter(answers)
    majority_answer = vote_counts.most_common(1)[0][0]
    return f"{majority_answer} (from {vote_counts.most_common(1)[0][1]}/{n_samples} chains)"


# Run comparison
print("CHAIN-OF-THOUGHT COMPARISON")
print("=" * 60)

for prob in MATH_PROBLEMS[:2]:  # Run first 2 for speed
    q = prob["question"]
    correct = prob["correct_answer"]

    print(f"\nPROBLEM: {q}")
    print(f"Correct answer: {correct}")
    print()

    std = run_standard(q)
    print(f"Standard prompt: {std[:100]}...")

    zs_cot = run_zero_shot_cot(q)
    print(f"Zero-shot CoT (last 100 chars): ...{zs_cot[-100:]}")

    fs_cot = run_few_shot_cot(q)
    print(f"Few-shot CoT (last 100 chars): ...{fs_cot[-100:]}")

    sc = run_self_consistency(q, n_samples=3)
    print(f"Self-consistency (3 samples): {sc}")
    print("-" * 40)

print("\nAll tests complete.")
