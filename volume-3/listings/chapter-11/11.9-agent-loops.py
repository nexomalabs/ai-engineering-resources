# Applied AI Engineering, Volume III, Chapter 11
# Section 11.9, Agent Loops
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def agent_loop(goal: str, tools: dict, max_steps: int = 10) -> str:
    history = []
    for step in range(max_steps):
        context = build_context(goal, history)
        response = llm_call(context)
        action = parse_action(response)

        if action["type"] == "finish":
            return action["answer"]

        observation = tools[action["tool"]](action["args"])
        history.append({
            "thought": response["thought"],
            "action": action,
            "observation": observation
        })

    return "Max steps reached without completion."
