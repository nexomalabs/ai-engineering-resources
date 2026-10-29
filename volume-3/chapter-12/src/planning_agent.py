"""Lab 12 — Task Planning Agent (starter).

This file RUNS as supplied. Validation finds the plan's error but nothing fixes it, tasks
never see the results they depend on, a transient failure triggers a full replan instead
of a retry, and a plan that refunds a claim before checking its receipt passes validation.
Complete the four TODOs.

    python src/planning_agent.py
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Optional

# ─── Part 1: the task data model (Section 12.4) ───────────────────────────────


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: str
    description: str
    tool: Optional[str] = None  # the one tool this task uses; checked by validate_plan
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 2

    def is_ready(self, completed_ids: set[str]) -> bool:
        """A task is ready to execute when all its dependencies are complete."""
        return all(dep in completed_ids for dep in self.depends_on)

    def mark_completed(self, result: str) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.value
        return data


# ─── Part 2: the planner (Section 12.5) ───────────────────────────────────────

AVAILABLE_TOOLS = {"web_search", "read_file", "write_file", "calculator", "get_current_date"}

# The claims agent from the chapter's opening story: its real tools, and the order rule
# finance insists on. Each pair (earlier, later) means a task using the later tool must
# depend, directly or through other tasks, on a task using the earlier one.
CLAIM_TOOLS = {
    "get_claim",
    "check_photos",
    "calculator",
    "verify_receipt",
    "issue_refund",
    "notify_customer",
}
CLAIM_ORDER = [("verify_receipt", "issue_refund")]

PLANNING_PROMPT = """
You are a planning agent. Given a high-level goal, decompose it into a list of concrete subtasks.

Goal: {goal}

Available tools: {tools}

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

# The stub's first plan contains one deliberate error, an unavailable "summarize" tool, so
# that validation has something to find (Part 3).
STUB_PLAN = {
    "plan_summary": "Gather sources on transformers, then write a structured summary.",
    "tasks": [
        {
            "id": "t1",
            "description": "Find the original transformer paper and its key ideas",
            "tool": "web_search",
            "depends_on": [],
        },
        {
            "id": "t2",
            "description": "Find recent work on efficient attention",
            "tool": "web_search",
            "depends_on": [],
        },
        {
            "id": "t3",
            "description": "Read the team's notes on attention mechanisms",
            "tool": "read_file",
            "depends_on": [],
        },
        {
            "id": "t4",
            "description": "Summarize the findings into a research summary",
            "tool": "summarize",
            "depends_on": ["t1", "t2", "t3"],
        },
    ],
}

# The seven-step plan from the chapter's story: it refunds at step 4, verifies the receipt
# at step 6, and phones the customer with a tool that does not exist.
STUB_CLAIM_PLAN = {
    "plan_summary": "Check the claim, refund it, and keep the customer informed.",
    "tasks": [
        {"id": "c1", "description": "Load claim C-311 and its order", "tool": "get_claim"},
        {
            "id": "c2",
            "description": "Review the damage photos",
            "tool": "check_photos",
            "depends_on": ["c1"],
        },
        {
            "id": "c3",
            "description": "Compare the claimed amount with the order total",
            "tool": "calculator",
            "depends_on": ["c1"],
        },
        {
            "id": "c4",
            "description": "Issue the refund for the claimed amount",
            "tool": "issue_refund",
            "depends_on": ["c2", "c3"],
        },
        {
            "id": "c5",
            "description": "Phone the customer to confirm the refund",
            "tool": "phone_customer",
            "depends_on": ["c4"],
        },
        {
            "id": "c6",
            "description": "Verify the purchase receipt",
            "tool": "verify_receipt",
            "depends_on": ["c1"],
        },
        {
            "id": "c7",
            "description": "Email the customer a summary of the decision",
            "tool": "notify_customer",
            "depends_on": ["c4", "c6"],
        },
    ],
}

STUB_CLAIM_REVISED = {
    "plan_summary": "Check the claim and the receipt, then refund it and tell the customer.",
    "tasks": [
        {"id": "c1", "description": "Load claim C-311 and its order", "tool": "get_claim"},
        {
            "id": "c2",
            "description": "Review the damage photos",
            "tool": "check_photos",
            "depends_on": ["c1"],
        },
        {
            "id": "c3",
            "description": "Compare the claimed amount with the order total",
            "tool": "calculator",
            "depends_on": ["c1"],
        },
        {
            "id": "c4",
            "description": "Verify the purchase receipt",
            "tool": "verify_receipt",
            "depends_on": ["c1"],
        },
        {
            "id": "c5",
            "description": "Issue the refund for the claimed amount",
            "tool": "issue_refund",
            "depends_on": ["c2", "c3", "c4"],
        },
        {
            "id": "c6",
            "description": "Email the customer that the refund is on its way",
            "tool": "notify_customer",
            "depends_on": ["c5"],
        },
    ],
}

STUB_REPLAN = {
    "plan_summary": "Skip the missing notes and write the summary from the search results.",
    "tasks": [
        {
            "id": "r1",
            "description": "Write the research summary from the search results",
            "tool": "write_file",
            "depends_on": ["t1", "t2"],
        },
    ],
}


def llm_call(prompt: str) -> str:
    """Scripted stand-in for the model. Replace with a real API call in production."""
    if "has encountered a failure" in prompt:
        return json.dumps(STUB_REPLAN)
    if "Revise this task" in prompt:
        return json.dumps(
            {"description": "Read the team's notes from notes/attention.md", "tool": "read_file"}
        )
    if "failed validation" in prompt:
        return json.dumps(STUB_CLAIM_REVISED)
    if "Claim C-311" in prompt:
        return json.dumps(STUB_CLAIM_PLAN)
    return json.dumps(STUB_PLAN)


def parse_plan(raw: str) -> list[Task]:
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


def plan_goal(
    goal: str, llm: Callable[[str], str] = llm_call, tools: set[str] = AVAILABLE_TOOLS
) -> list[Task]:
    return parse_plan(llm(PLANNING_PROMPT.format(goal=goal, tools=", ".join(sorted(tools)))))


# ─── Part 3: plan validation (Section 12.6) ───────────────────────────────────


def validate_plan(
    tasks: list[Task],
    available_tools: set[str],
    must_precede: list[tuple[str, str]] = (),
) -> list[str]:
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

    # Check required order: a task using the later tool must depend, directly or
    # through other tasks, on a task using the earlier one
    by_id = {t.id: t for t in tasks}

    def ancestors(task: Task) -> set[str]:
        seen: set[str] = set()
        stack = list(task.depends_on)
        while stack:
            dep = stack.pop()
            if dep in by_id and dep not in seen:
                seen.add(dep)
                stack.extend(by_id[dep].depends_on)
        return seen

    for earlier, later in must_precede:
        # TODO 4: For each task that uses the `later` tool, unless one of ancestors(task)
        #   uses the `earlier` tool, add "Task '<id>' uses '<later>' before any '<earlier>'
        #   task." As supplied, a plan that refunds before it checks the receipt passes.
        pass

    return errors


def revise_plan(
    goal: str, tasks: list[Task], errors: list[str], llm: Callable[[str], str] = llm_call
) -> list[Task]:
    """Send a rejected plan back to the model with the validator's errors."""
    plan = json.dumps([t.to_dict() for t in tasks])
    problems = "\n".join(f"- {e}" for e in errors)
    prompt = (
        f'This plan for goal "{goal}" failed validation:\n{problems}\n\n'
        f"Plan: {plan}\n\nReturn a corrected plan in the same JSON format."
    )
    return parse_plan(llm(prompt))


def fix_unknown_tools(tasks: list[Task], available_tools: set[str], fallback: str) -> list[str]:
    """Replace each unavailable tool with `fallback`, and return what was changed."""
    # TODO 1: For each task whose tool is not in available_tools, record
    #   "<id>: '<old tool>' -> '<fallback>'" and set task.tool to fallback.
    return []


# ─── Part 5 helpers: failure classification and replanning (12.7, 12.8) ───────


def classify_failure(error: str) -> str:
    error_lower = error.lower()
    if "timeout" in error_lower or "rate limit" in error_lower:
        return "transient"
    if "invalid" in error_lower or "parse" in error_lower:
        return "argument_error"
    if "not found" in error_lower or "no results" in error_lower:
        return "missing_data"
    return "logic_error"


def replan(
    original_goal: str,
    completed_tasks: list[Task],
    failed_task: Task,
    remaining_tasks: list[Task],
    llm: Callable[[str], str] = llm_call,
) -> list[Task]:
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
    return parse_plan(llm(prompt))


# ─── Simulated tools ──────────────────────────────────────────────────────────


def simulated_tool(tool: str, task: Task, context: dict[str, str]) -> str:
    """Stand-in tools. `context` holds the results of the task's dependencies."""
    if tool == "web_search":
        return f"Search results for: {task.description}"
    if tool == "read_file":
        if "notes/attention.md" not in task.description:
            raise ValueError("Invalid path: no file name given")
        return "Notes: attention cost grows with the square of sequence length"
    if tool == "write_file":
        return f"Wrote summary.md from {len(context)} source(s)"
    return f"{tool} completed"


# ─── Parts 4 and 5: the executor ──────────────────────────────────────────────


class PlanExecutor:
    def __init__(
        self,
        goal: str,
        tool_fn=simulated_tool,
        llm: Callable[[str], str] = llm_call,
        failures: Optional[dict[str, list[str]]] = None,
    ):
        self.goal = goal
        self.tool_fn = tool_fn
        self.llm = llm
        # Injected failures for testing: task id -> errors to raise, one per attempt
        self.failures = {k: list(v) for k, v in (failures or {}).items()}
        self.actions: list[str] = []
        self.replans = 0

    def _run(self, task: Task, results: dict[str, str]) -> str:
        if self.failures.get(task.id):
            raise RuntimeError(self.failures[task.id].pop(0))
        # TODO 2: Give the task the results of the tasks it depends on, as a dict
        #   mapping each dependency's id to its result.
        context = {}
        return self.tool_fn(task.tool, task, context)

    def execute_plan(self, tasks: list[Task]) -> dict:
        results: dict[str, str] = {}
        pending = list(tasks)
        while pending:
            completed_ids = set(results)
            ready = [t for t in pending if t.is_ready(completed_ids)]
            if not ready:
                for t in pending:
                    t.status = TaskStatus.SKIPPED
                self.actions.append(f"skipped {[t.id for t in pending]}: dependencies unmet")
                break
            task = ready[0]
            task.status = TaskStatus.IN_PROGRESS
            try:
                task.mark_completed(self._run(task, results))
                results[task.id] = task.result
                pending.remove(task)
            except Exception as e:
                task.mark_failed(str(e))
                done = [t for t in tasks if t.status == TaskStatus.COMPLETED]
                remaining = [t for t in pending if t is not task]
                new_tasks = self.recover(task, done, remaining)
                if new_tasks is not None:
                    # The new plan replaces the rest of the old one; the failed task stays FAILED
                    for t in remaining:
                        t.status = TaskStatus.SKIPPED
                    tasks.extend(new_tasks)
                    pending = list(new_tasks)
        return {
            "results": results,
            "actions": self.actions,
            "metrics": evaluate_plan_execution(tasks),
            "replans": self.replans,
        }

    def recover(
        self, failed_task: Task, completed_tasks: list[Task], remaining_tasks: list[Task]
    ) -> Optional[list[Task]]:
        """Fix the failed task in place, or return a new plan to replace what remains."""
        kind = classify_failure(failed_task.error)
        # TODO 3: A transient failure (a timeout or rate limit) will probably succeed if
        #   tried again. While retries < max_retries, count a retry, set the task back to
        #   PENDING, record "<id>: retry <n> after '<error>'", and return None.
        if kind == "argument_error" and failed_task.retries < failed_task.max_retries:
            failed_task.retries += 1
            revised = json.loads(
                self.llm(
                    f"Revise this task so it can succeed.\nTask: {failed_task.description}\n"
                    f"Error: {failed_task.error}"
                )
            )
            failed_task.description = revised["description"]
            failed_task.tool = revised.get("tool", failed_task.tool)
            failed_task.status = TaskStatus.PENDING
            self.actions.append(f"{failed_task.id}: revised after '{failed_task.error}'")
            return None
        self.replans += 1
        self.actions.append(f"{failed_task.id}: replanned after '{failed_task.error}' ({kind})")
        return replan(self.goal, completed_tasks, failed_task, remaining_tasks, self.llm)


# ─── Planning evaluation (Section 12.10) ──────────────────────────────────────


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


# ─── Deliverable: plan, validate, execute, summarize ─────────────────────────


def run(goal: str, failures: Optional[dict[str, list[str]]] = None) -> dict:
    print(f"Goal: {goal}\n")
    tasks = plan_goal(goal)
    for t in tasks:
        print(f"  {t.id} [{t.tool}] {t.description}  depends on {t.depends_on or '-'}")

    errors = validate_plan(tasks, AVAILABLE_TOOLS)
    print(f"\nValidation: {errors or 'no errors'}")
    if errors:
        for fix in fix_unknown_tools(tasks, AVAILABLE_TOOLS, fallback="write_file"):
            print(f"  fixed {fix}")
        print(f"Revalidation: {validate_plan(tasks, AVAILABLE_TOOLS) or 'no errors'}")

    outcome = PlanExecutor(goal, failures=failures).execute_plan(tasks)
    print("\nRecovery actions:")
    for action in outcome["actions"] or ["none"]:
        print(f"  {action}")
    print("\nTask status:")
    for t in tasks:
        print(f"  {t.id:3} {t.status.value:10} {t.result or t.error or ''}")
    m = outcome["metrics"]
    print(
        f"\nCompleted {m['completed']}/{m['total_tasks']} tasks, "
        f"{m['total_retries']} retries, {outcome['replans']} replan(s)"
    )
    return outcome


def run_claim(goal: str) -> dict:
    """The story's claim: a plan that is rejected before its first step, then revised."""
    print(f"Goal: {goal}\n")
    tasks = plan_goal(goal, tools=CLAIM_TOOLS)
    for t in tasks:
        print(f"  {t.id} [{t.tool}] {t.description}  depends on {t.depends_on or '-'}")

    errors = validate_plan(tasks, CLAIM_TOOLS, must_precede=CLAIM_ORDER)
    print("\nValidation:")
    for error in errors or ["no errors"]:
        print(f"  {error}")
    if errors:
        print("Rejected before the first step; asking the model for a plan within the rules.\n")
        tasks = revise_plan(goal, tasks, errors)
        for t in tasks:
            print(f"  {t.id} [{t.tool}] {t.description}  depends on {t.depends_on or '-'}")
        errors = validate_plan(tasks, CLAIM_TOOLS, must_precede=CLAIM_ORDER)
        print(f"\nRevalidation: {errors or 'no errors'}")

    outcome = PlanExecutor(goal).execute_plan(tasks)
    m = outcome["metrics"]
    order = [t.id for t in tasks if t.status == TaskStatus.COMPLETED]
    print(f"\nCompleted {m['completed']}/{m['total_tasks']} tasks, in the order {order}")
    return outcome


if __name__ == "__main__":
    goal = "Write a research summary on transformer architectures."
    # Run 1: t2 times out once (transient, so it is retried), and t3's first description
    # has no file name (an argument error, so it is revised).
    run(goal, failures={"t2": ["Search timeout after 30 s"]})
    # Run 2: t3 fails in a way no retry or revision can fix (a logic error), so the rest
    # of the plan is replaced.
    print("\n" + "=" * 60 + "\n")
    run(goal, failures={"t3": ["The notes repository is empty"]})
    # Run 3: the high-value claim from the chapter's opening story.
    print("\n" + "=" * 60 + "\n")
    run_claim("Decide Claim C-311, a high-value claim for a damaged monitor, and settle it.")
