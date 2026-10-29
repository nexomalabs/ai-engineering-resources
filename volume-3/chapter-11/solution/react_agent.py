"""Lab 11 — ReAct agent with three tools (reference solution).

A Thought -> Action -> Observation loop over the tools in agent_tools.py. A scripted stub
stands in for the model, so the lab runs with no API key. Run from the lab folder:

    python solution/react_agent.py
"""

import json
import re

from agent_tools import TOOL_DESCRIPTIONS, TOOLS

# ─── LLM stub (replace with a real API call) ──────────────────────────────────


def step(thought: str, action: str, args: str) -> str:
    return json.dumps({"thought": thought, "action": action, "args": args})


def llm_call(prompt: str) -> str:
    """
    A scripted stand-in for the model. It reads the goal and the observations so far and
    returns the next step as JSON, as a real model prompted by build_prompt() would. It
    reads only the history section, never the tool descriptions, so the example
    expression there cannot trigger a step.

    In production, replace this with an API call, e.g.:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-6.1-sol",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    """
    goal = prompt.split("Goal:")[1].split("\n")[0].strip()
    history = prompt.split("History so far:")[-1]
    observations = re.findall(r"Observation: (.*)", history)
    last = observations[-1] if observations else None
    lowered = goal.lower()

    if "date" in lowered:
        if last is None:
            return step("I can read the date directly.", "get_current_date", "")
        return step("I have the date.", "finish", f"Today's date is {last}.")

    if "japan" in lowered:
        if last is None:
            return step("I need Japan's population first.", "web_search", "population of japan")
        match = re.search(r"([\d.]+) million", last)
        if match and len(observations) == 1:
            return step("Now multiply by 0.0001.", "calculator", f"{match.group(1)}e6 * 0.0001")
        return step(
            "The calculation is complete.",
            "finish",
            f"Japan's population (about 124.0 million) multiplied by 0.0001 is {last}.",
        )

    if "python" in lowered:
        if last is None:
            return step("I will search for who created Python.", "web_search", "python creator")
        return step("The search answered both parts.", "finish", last)

    if "shipment" in lowered:
        # The chapter's opening story: the parcel shows as in transit, so the model keeps
        # checking it, with impeccable reasoning, every time.
        return step(
            "The parcel shows as in transit. I should confirm delivery before deciding.",
            "web_search",
            "shipment WF-2291 status",
        )

    if last is None:
        return step("I will search for this information.", "web_search", goal)
    return step("I will report what I found.", "finish", last)


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
    for i, past in enumerate(history):
        lines.append(f"\nStep {i + 1}:")
        lines.append(f"  Thought: {past['thought']}")
        lines.append(f"  Action: {past['action']}({past['args']})")
        lines.append(f"  Observation: {past['observation']}")
    lines.append("\nNext step:")
    return "\n".join(lines)


def parse_response(raw: str) -> dict:
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "thought": "Parse error",
            "action": "finish",
            "args": "Unable to parse model response.",
        }


def run_agent(goal: str, max_steps: int = 10, model=llm_call) -> str:
    history: list[dict] = []
    print(f"\n{'=' * 60}\nAgent Goal: {goal}\n{'=' * 60}")

    for step_num in range(1, max_steps + 1):
        parsed = parse_response(model(build_prompt(goal, history)))
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

        # An action that returns exactly what it returned before has told the agent
        # nothing new, so repeating it cannot change the decision: stop instead.
        if any(
            (past["action"], past["args"], past["observation"]) == (action, args, observation)
            for past in history
        ):
            message = f"Agent stopped: {action}({args!r}) returned the same result as before."
            print(f"\n{message}")
            return message

        history.append(
            {"thought": thought, "action": action, "args": args, "observation": observation}
        )

    return "Agent stopped: maximum steps reached."


if __name__ == "__main__":
    for goal in [
        "What is today's date?",
        "What is the population of Japan multiplied by 0.0001?",
        "Who created Python and in what year?",
        "Decide whether the damage claim on shipment WF-2291 should be paid.",
    ]:
        run_agent(goal)
