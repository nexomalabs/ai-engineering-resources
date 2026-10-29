"""Tests for Lab 17. Run against solution/ in CI, with the stand-in model."""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("NEXOMA_LAB_MODE", "fixture")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import agent_eval as ev  # noqa: E402


def trace_with(tool_calls=(), steps=2, answer="", completed=True):
    trace = ev.ExecutionTrace(test_case_id="T", task="t", final_answer=answer, completed=completed)
    trace.steps = ["s"] * steps
    trace.tool_calls = [ev.ToolCall(tool=t, args=a, result="") for t, a in tool_calls]
    return trace


def test_parse_action_reads_tool_and_json_args():
    assert ev.parse_action('Thought: x\nAction: search({"query": "speed of light"})') == (
        "search",
        {"query": "speed of light"},
    )
    assert ev.parse_action("Action: search({not json})") is None
    assert ev.parse_action("Thought: no action here") is None


def test_parse_answer_takes_the_answer_line():
    assert ev.parse_answer("Thought: done\nAnswer: Paris") == "Paris"
    assert ev.parse_answer("Thought: still working") is None


def test_tool_accuracy_needs_the_right_tool_and_argument():
    case = ev.TEST_CASES[4]  # weather in London
    assert (
        ev.score_tool_use_accuracy(trace_with([("get_weather", {"city": "London"})]), case) == 1.0
    )
    assert ev.score_tool_use_accuracy(trace_with([("search", {"query": "London"})]), case) == 0.0
    assert ev.score_tool_use_accuracy(trace_with([("get_weather", {"city": "Paris"})]), case) == 0.0


def test_step_efficiency_is_capped_and_handles_no_steps():
    case = ev.TEST_CASES[0]  # optimal_steps == 2
    assert ev.score_step_efficiency(trace_with(steps=4), case) == 0.5
    assert ev.score_step_efficiency(trace_with(steps=1), case) == 1.0
    assert ev.score_step_efficiency(trace_with(steps=0), case) == 0.0


def test_completion_is_a_case_insensitive_substring_match():
    case = ev.TEST_CASES[0]
    assert ev.score_task_completion(trace_with(answer="PARIS is the capital."), case) == 1.0
    assert ev.score_task_completion(trace_with(answer="Lyon"), case) == 0.0
    assert ev.score_task_completion(trace_with(answer="Paris", completed=False), case) == 0.0


@pytest.fixture(scope="module")
def report():
    return ev.generate_report(ev.evaluate_agent(ev.TEST_CASES))


def test_report_summarizes_all_fourteen_cases(report):
    summary = report["summary"]
    assert summary["total_test_cases"] == 14
    assert summary["task_completion_rate"] == pytest.approx(78.6)
    assert summary["avg_tool_use_accuracy"] == pytest.approx(82.1)
    assert summary["avg_step_efficiency"] == pytest.approx(91.7)


def test_the_easy_suite_flatters_the_agent_and_the_claims_suite_does_not(report):
    easy, claims = report["by_suite"]["easy"], report["by_suite"]["claims"]
    assert (easy["test_cases"], claims["test_cases"]) == (10, 4)
    assert easy["task_completion_rate"] == 90.0 and claims["task_completion_rate"] == 50.0
    assert easy["avg_tool_use_accuracy"] == 90.0 and claims["avg_tool_use_accuracy"] == 62.5


def test_traces_show_photos_checked_twice_and_the_handling_log_never(report):
    assert report["tool_calls_per_case"]["claims"] == {
        "check_photos": 2.0,
        "get_receipt": 0.5,
        "get_handling_log": 0.0,
    }


def test_report_names_the_scripted_failures(report):
    assert report["failure_analysis"]["incomplete_tasks"] == ["TC09", "TC13", "TC14"]
    assert report["failure_analysis"]["wrong_tools"] == ["TC09", "TC13", "TC14"]
    tc04 = next(c for c in report["per_case"] if c["id"] == "TC04")
    assert tc04["steps"] == "3/2" and tc04["completed"]
    tc11 = next(c for c in report["per_case"] if c["id"] == "TC11")
    assert tc11["steps"] == "4/3" and tc11["completed"]
