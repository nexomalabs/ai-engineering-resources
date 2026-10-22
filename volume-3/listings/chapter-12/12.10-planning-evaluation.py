# Applied AI Engineering, Volume III, Chapter 12
# Section 12.10, Planning Evaluation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def evaluate_plan_execution(tasks: list[Task]) -> dict:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    total_retries = sum(t.retries for t in tasks)

    return {
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "completion_rate": completed / total if total > 0 else 0.0,
        "total_retries": total_retries,
        "avg_retries_per_task": total_retries / total if total > 0 else 0.0,
    }
