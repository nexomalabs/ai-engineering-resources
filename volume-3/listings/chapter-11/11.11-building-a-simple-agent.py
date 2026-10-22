# Applied AI Engineering, Volume III, Chapter 11
# Section 11.11, Building a Simple Agent
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json
import math
from datetime import date
from typing import Any

# ─── Tool definitions ──────────────────────────────────────────────────────────

def web_search(query: str) -> str:
    """Mock web search returning canned results for demonstration."""
    results = {
        "france gdp 2024": "France GDP (2024): approximately $3.16 trillion USD (World Bank).",
        "population of japan": "Japan population (2024): approximately 124.0 million people (World Bank).",
        "python creator": "Python was created by Guido van Rossum, first released in 1991.",
        "eiffel tower height": "The Eiffel Tower is 330 meters tall including the broadcast antenna.",
    }
    key = query.lower().strip()
    for k, v in results.items():
        if k in key or key in k:
            return v
    return f"No results found for: {query}"


def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    allowed = set("0123456789+-*/().,e E")
    if not all(c in allowed for c in expression.replace("**", "").replace("//", "")):
        return "Error: expression contains invalid characters."
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def get_current_date(_args: str = "") -> str:
    """Return today's date."""
    return str(date.today())


TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "get_current_date": get_current_date,
}

TOOL_DESCRIPTIONS = """
Available tools:
- web_search(query: str): Search the web for factual information.
- calculator(expression: str): Evaluate a Python arithmetic expression. E.g. "3.16e12 * 0.15"
- get_current_date(): Return today's date in YYYY-MM-DD format.
- finish(answer: str): Return the final answer and stop.
"""

# ─── LLM stub (replace with real API call) ────────────────────────────────────

def llm_call(prompt: str) -> str:
    """
    In production, replace this with an actual API call, e.g.:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-6.1-sol",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    """
    # Simulated response for demonstration. The stub reads only the history, and
    # checks the furthest step first: the tool descriptions contain an example
    # expression, so matching on the whole prompt would repeat the same step forever.
    history = prompt.split("History so far:")[-1]
    if "474000000000" in history:
        return json.dumps({
            "thought": "The calculation is complete.",
            "action": "finish",
            "args": "15% of France's 2024 GDP is approximately $474 billion USD."
        })
    if "3.16 trillion" in history:
        return json.dumps({
            "thought": "I have the GDP. Now I will calculate 15%.",
            "action": "calculator",
            "args": "3.16e12 * 0.15"
        })
    if "GDP of France" in prompt:
        return json.dumps({
            "thought": "I need to find France's GDP first.",
            "action": "web_search",
            "args": "france gdp 2024"
        })
    return json.dumps({
        "thought": "I will search for this information.",
        "action": "web_search",
        "args": prompt.split("Goal:")[-1].strip().split("\n")[0]
    })


# ─── Agent core ───────────────────────────────────────────────────────────────

def build_prompt(goal: str, history: list[dict]) -> str:
    lines = [
        "You are a ReAct agent. Reason step by step, then take an action.",
        TOOL_DESCRIPTIONS,
        f"\nGoal: {goal}\n",
        "Respond with a JSON object containing:",
        '  {"thought": "<your reasoning>", "action": "<tool_name>", "args": "<arguments>"}',
        "\nHistory so far:",
    ]
    for i, step in enumerate(history):
        lines.append(f"\nStep {i + 1}:")
        lines.append(f"  Thought: {step['thought']}")
        lines.append(f"  Action: {step['action']}({step['args']})")
        lines.append(f"  Observation: {step['observation']}")
    lines.append("\nNext step:")
    return "\n".join(lines)


def parse_response(raw: str) -> dict:
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"thought": "Parse error", "action": "finish", "args": "Unable to parse model response."}


def run_agent(goal: str, max_steps: int = 10) -> str:
    history: list[dict] = []
    print(f"\n{'='*60}\nAgent Goal: {goal}\n{'='*60}")

    for step_num in range(1, max_steps + 1):
        prompt = build_prompt(goal, history)
        raw_response = llm_call(prompt)
        parsed = parse_response(raw_response)

        thought = parsed.get("thought", "")
        action = parsed.get("action", "finish")
        args = parsed.get("args", "")

        print(f"\nStep {step_num}:")
        print(f"  Thought: {thought}")
        print(f"  Action: {action}({args!r})")

        if action == "finish":
            print(f"\nFinal Answer: {args}")
            return args

        tool_fn = TOOLS.get(action)
        if tool_fn is None:
            observation = f"Error: unknown tool '{action}'."
        else:
            try:
                observation = tool_fn(args)
            except Exception as e:
                observation = f"Tool error: {e}"

        print(f"  Observation: {observation}")
        history.append({
            "thought": thought,
            "action": action,
            "args": args,
            "observation": observation
        })

    return "Agent stopped: maximum steps reached."


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_agent("What is 15% of the GDP of France in 2024?")
    print(f"\nResult: {result}")
