# Applied AI Engineering, Volume III, Chapter 12
# Section 12.6, Plan Validation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def validate_plan(tasks: list[Task], available_tools: set[str]) -> list[str]:
    errors = []
    task_ids = {t.id for t in tasks}

    # Check for duplicate IDs
    if len(task_ids) != len(tasks):
        errors.append("Duplicate task IDs detected.")

    for task in tasks:
        # Check dependency references
        for dep in task.depends_on:
            if dep not in task_ids:
                errors.append(f"Task '{task.id}' depends on unknown task '{dep}'.")

        # Check tool availability
        tool = task.tool
        if tool and tool not in available_tools:
            errors.append(f"Task '{task.id}' references unknown tool '{tool}'.")

    # Check for circular dependencies using DFS
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def has_cycle(task_id: str) -> bool:
        visited.add(task_id)
        rec_stack.add(task_id)
        task = next((t for t in tasks if t.id == task_id), None)
        if task:
            for dep in task.depends_on:
                if dep not in visited and has_cycle(dep):
                    return True
                elif dep in rec_stack:
                    return True
        rec_stack.discard(task_id)
        return False

    for task in tasks:
        if task.id not in visited:
            if has_cycle(task.id):
                errors.append("Circular dependency detected in task graph.")
                break

    return errors
