# Applied AI Engineering, Volume II, Chapter 10
# Section 10.4, Tree of Thoughts
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Simplified ToT implementation
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment


def generate_thoughts(current_state: str, problem: str, n: int = 3) -> list[str]:
    """Generate N candidate next thoughts."""
    response = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=[{
            "role": "user",
            "content": f"""Problem: {problem}

Current reasoning state:
{current_state}

Generate {n} different possible next reasoning steps. Number them 1, 2, 3.
Each should be a substantively different approach to advancing the solution."""
        }],
        temperature=0.8,
        max_completion_tokens=400
    )
    # Parse numbered thoughts
    return [t.strip() for t in response.choices[0].message.content.split("\n") if t.strip()]

def evaluate_thought(thought: str, problem: str) -> float:
    """Evaluate a thought's promise. Returns score 1-10."""
    response = client.chat.completions.create(
        model="gpt-6-sol",
        reasoning_effort="none",
        messages=[{
            "role": "user",
            "content": f"""Rate this reasoning step for solving the problem on a scale 1-10.
Problem: {problem}
Reasoning step: {thought}

Consider: Is this step logically valid? Does it advance toward the solution?
Is it building on correct premises?

Respond with only a number from 1 to 10."""
        }],
        temperature=0,
        max_completion_tokens=5
    )
    try:
        return float(response.choices[0].message.content.strip())
    except:
        return 5.0
