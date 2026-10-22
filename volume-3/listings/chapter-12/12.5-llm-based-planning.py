# Applied AI Engineering, Volume III, Chapter 12
# Section 12.5, LLM-Based Planning
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import json

PLANNING_PROMPT = """
You are a planning agent. Given a high-level goal, decompose it into a list of concrete subtasks.

Goal: {goal}

Available tools: web_search, read_file, write_file, calculator, get_current_date

Return a JSON object with this structure:
{{
  "plan_summary": "one-sentence description of the approach",
  "tasks": [
    {{
      "id": "t1",
      "description": "clear description of what to do",
      "tool": "tool_name",
      "args_template": "description of arguments needed",
      "depends_on": []
    }},
    ...
  ]
}}

Rules:
- Each task must use exactly one tool.
- Specify dependencies using task IDs.
- Tasks without dependencies can run in parallel.
- The final task should synthesize all results.
"""


def parse_plan(raw: str) -> list[Task]:
    """Turn the model's JSON plan into Task objects (Task is defined in Section 12.4)."""
    data = json.loads(raw)
    return [
        Task(
            id=t["id"],
            description=t["description"],
            tool=t.get("tool"),
            depends_on=list(t.get("depends_on", [])),
        )
        for t in data["tasks"]
    ]
