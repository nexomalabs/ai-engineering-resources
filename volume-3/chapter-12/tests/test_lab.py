"""Tests for Lab 12. Run against solution/ in CI."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from planning_agent import (  # noqa: E402
    AVAILABLE_TOOLS,
    CLAIM_ORDER,
    CLAIM_TOOLS,
    PlanExecutor,
    Task,
    TaskStatus,
    classify_failure,
    fix_unknown_tools,
    plan_goal,
    revise_plan,
    run_claim,
    validate_plan,
)

GOAL = "Write a research summary on transformer architectures."
CLAIM_GOAL = "Decide Claim C-311, a high-value claim for a damaged monitor, and settle it."


def test_task_serializes():
    data = Task("t1", "d", tool="web_search").to_dict()
    assert data["status"] == "pending"
    assert json.dumps(data)


def test_plan_parses_into_tasks():
    tasks = plan_goal(GOAL)
    assert [t.id for t in tasks] == ["t1", "t2", "t3", "t4"]
    assert tasks[3].depends_on == ["t1", "t2", "t3"]


def test_validation_finds_each_kind_of_error():
    tasks = [
        Task("a", "d", tool="web_search", depends_on=["b"]),
        Task("b", "d", tool="teleport", depends_on=["a"]),
        Task("c", "d", depends_on=["zzz"]),
        Task("c", "d"),
    ]
    errors = validate_plan(tasks, AVAILABLE_TOOLS)
    assert "Duplicate task IDs detected." in errors
    assert "Task 'c' depends on unknown task 'zzz'." in errors
    assert "Task 'b' references unknown tool 'teleport'." in errors
    assert "Circular dependency detected in task graph." in errors


def test_order_rule_needs_the_check_somewhere_upstream():
    rule = [("verify_receipt", "issue_refund")]
    direct = [
        Task("r", "d", tool="verify_receipt"),
        Task("p", "d", tool="issue_refund", depends_on=["r"]),
    ]
    through = [
        Task("r", "d", tool="verify_receipt"),
        Task("x", "d", tool="calculator", depends_on=["r"]),
        Task("p", "d", tool="issue_refund", depends_on=["x"]),
    ]
    alongside = [
        Task("r", "d", tool="verify_receipt"),
        Task("p", "d", tool="issue_refund"),
    ]
    assert validate_plan(direct, CLAIM_TOOLS, must_precede=rule) == []
    assert validate_plan(through, CLAIM_TOOLS, must_precede=rule) == []
    assert validate_plan(alongside, CLAIM_TOOLS, must_precede=rule) == [
        "Task 'p' uses 'issue_refund' before any 'verify_receipt' task."
    ]


def test_the_story_plan_is_rejected_for_both_of_its_faults():
    tasks = plan_goal(CLAIM_GOAL, tools=CLAIM_TOOLS)
    assert len(tasks) == 7
    assert validate_plan(tasks, CLAIM_TOOLS, must_precede=CLAIM_ORDER) == [
        "Task 'c5' references unknown tool 'phone_customer'.",
        "Task 'c4' uses 'issue_refund' before any 'verify_receipt' task.",
    ]


def test_the_revised_claim_plan_passes_and_checks_the_receipt_before_refunding(capsys):
    tasks = plan_goal(CLAIM_GOAL, tools=CLAIM_TOOLS)
    errors = validate_plan(tasks, CLAIM_TOOLS, must_precede=CLAIM_ORDER)
    revised = revise_plan(CLAIM_GOAL, tasks, errors)
    assert validate_plan(revised, CLAIM_TOOLS, must_precede=CLAIM_ORDER) == []
    outcome = run_claim(CLAIM_GOAL)
    order = list(outcome["results"])
    assert order.index("c4") < order.index("c5")  # receipt (c4) before refund (c5)
    assert "Rejected before the first step" in capsys.readouterr().out


def test_unknown_tool_is_fixed_programmatically():
    tasks = plan_goal(GOAL)
    fixes = fix_unknown_tools(tasks, AVAILABLE_TOOLS, fallback="write_file")
    assert fixes == ["t4: 'summarize' -> 'write_file'"]
    assert validate_plan(tasks, AVAILABLE_TOOLS) == []


def test_failure_classes():
    assert classify_failure("Search timeout after 30 s") == "transient"
    assert classify_failure("Invalid path") == "argument_error"
    assert classify_failure("File not found") == "missing_data"
    assert classify_failure("The notes repository is empty") == "logic_error"


def valid_plan():
    tasks = plan_goal(GOAL)
    fix_unknown_tools(tasks, AVAILABLE_TOOLS, fallback="write_file")
    return tasks


def test_results_flow_to_dependent_tasks():
    tasks = valid_plan()
    out = PlanExecutor(GOAL).execute_plan(tasks)
    assert out["results"]["t4"] == "Wrote summary.md from 3 source(s)"


def test_dependencies_run_first():
    order = []

    def tool(name, task, context):
        order.append(task.id)
        assert set(context) == set(task.depends_on)
        return "ok"

    tasks = [
        Task("last", "d", tool="write_file", depends_on=["a", "b"]),
        Task("a", "d", tool="web_search"),
        Task("b", "d", tool="web_search"),
    ]
    PlanExecutor(GOAL, tool_fn=tool).execute_plan(tasks)
    assert order[-1] == "last"


def test_transient_failure_is_retried():
    tasks = valid_plan()
    ex = PlanExecutor(GOAL, failures={"t2": ["Search timeout after 30 s"]})
    out = ex.execute_plan(tasks)
    assert out["replans"] == 0
    assert tasks[1].status == TaskStatus.COMPLETED and tasks[1].retries == 1


def test_retries_are_capped_then_the_agent_replans():
    tasks = valid_plan()
    ex = PlanExecutor(GOAL, failures={"t1": ["timeout"] * 5})
    out = ex.execute_plan(tasks)
    assert tasks[0].retries == 2
    assert out["replans"] == 1


def test_argument_error_is_revised():
    tasks = valid_plan()
    out = PlanExecutor(GOAL).execute_plan(tasks)
    assert "notes/attention.md" in tasks[2].description
    assert any(a.startswith("t3: revised") for a in out["actions"])


def test_logic_error_replans_and_keeps_the_failure_visible():
    tasks = valid_plan()
    out = PlanExecutor(GOAL, failures={"t3": ["The notes repository is empty"]}).execute_plan(tasks)
    status = {t.id: t.status for t in tasks}
    assert status["t3"] == TaskStatus.FAILED
    assert status["t4"] == TaskStatus.SKIPPED
    assert status["r1"] == TaskStatus.COMPLETED
    assert out["results"]["r1"] == "Wrote summary.md from 2 source(s)"
