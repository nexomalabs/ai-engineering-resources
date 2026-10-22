# Applied AI Engineering, Volume III, Chapter 12
# Section 12.7, Dynamic Replanning
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def replan(original_goal: str, completed_tasks: list[Task],
           failed_task: Task, remaining_tasks: list[Task]) -> list[Task]:
    completed_summary = "\n".join(
        f"- {t.id}: {t.description} → {t.result[:200]}" for t in completed_tasks
    )
    prompt = f"""
The following plan for goal "{original_goal}" has encountered a failure.

Completed tasks:
{completed_summary}

Failed task: {failed_task.description}
Failure reason: {failed_task.error}

Remaining tasks that are now invalid:
{[t.description for t in remaining_tasks]}

Please generate a revised plan for completing the goal, taking into account what has
already been completed and the nature of the failure. Return the same JSON format as before.
"""
    raw = llm_call(prompt)
    return parse_plan(raw)
