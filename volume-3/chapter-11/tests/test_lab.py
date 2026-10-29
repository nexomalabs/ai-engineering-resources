"""Tests for Lab 11. Run against solution/ in CI."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

import agent_tools  # noqa: E402
from agent_tools import calculator, validate_expression, web_search  # noqa: E402
from react_agent import build_prompt, parse_response, run_agent  # noqa: E402


def test_search_has_at_least_five_canned_queries():
    assert len(agent_tools.SEARCH_RESULTS) >= 5
    assert "Guido van Rossum" in web_search("Python creator")
    assert web_search("unknown topic").startswith("No results found")


def test_calculator_evaluates_arithmetic():
    assert calculator("3.16e12 * 0.15") == "474000000000.0"
    assert calculator("2 +* 3").startswith("Error:")


def test_validation_blocks_code_and_empty_input():
    assert validate_expression("(1 + 2) * 3e2")
    assert not validate_expression("__import__('os').getcwd()")
    assert not validate_expression("   ")
    assert calculator("__import__('os')") == "Error: expression contains invalid characters."


def test_prompt_contains_goal_tools_and_history():
    prompt = build_prompt(
        "Find X", [{"thought": "t", "action": "web_search", "args": "x", "observation": "obs"}]
    )
    assert "Goal: Find X" in prompt
    assert "calculator(expression: str)" in prompt
    assert "Observation: obs" in prompt


def test_unparseable_output_finishes_safely():
    assert parse_response("not json")["action"] == "finish"


def test_the_three_lab_goals_finish(capsys):
    assert run_agent("What is today's date?").startswith("Today's date is ")
    assert run_agent("What is the population of Japan multiplied by 0.0001?").endswith("12400.0.")
    assert "1991" in run_agent("Who created Python and in what year?")


def test_tool_exception_becomes_an_observation(monkeypatch, capsys):
    def broken(args):
        raise RuntimeError("search backend down")

    monkeypatch.setitem(agent_tools.TOOLS, "web_search", broken)
    answer = run_agent("Who created Python and in what year?")
    assert answer == "Tool error: search backend down"


def test_unknown_tool_is_reported():
    def model(prompt):
        if "Observation:" in prompt.split("History so far:")[-1]:
            return json.dumps({"thought": "", "action": "finish", "args": "done"})
        return json.dumps({"thought": "", "action": "teleport", "args": ""})

    assert run_agent("anything", model=model) == "done"


def test_step_limit_stops_a_looping_model():
    calls = []

    def model(prompt):  # a new calculation each time, so the repeat guard never fires
        calls.append(1)
        return json.dumps({"thought": "again", "action": "calculator", "args": f"{len(calls)} + 1"})

    assert run_agent("loop", max_steps=3, model=model) == "Agent stopped: maximum steps reached."


def test_repeating_an_unchanged_action_stops_the_agent(capsys):
    # The chapter's opening story: the shipment stays "in transit", so asking again is pointless
    answer = run_agent("Decide whether the damage claim on shipment WF-2291 should be paid.")
    assert answer == (
        "Agent stopped: web_search('shipment WF-2291 status') returned the same result as before."
    )
    assert capsys.readouterr().out.count("Step ") == 2


def test_the_same_action_with_a_new_result_is_allowed():
    results = iter(["in transit", "delivered"])
    calls = []

    def model(prompt):
        calls.append(1)
        if len(calls) == 3:
            return json.dumps({"thought": "", "action": "finish", "args": "delivered"})
        return json.dumps({"thought": "", "action": "web_search", "args": "status"})

    original = agent_tools.TOOLS["web_search"]
    agent_tools.TOOLS["web_search"] = lambda args: next(results)
    try:
        assert run_agent("status", model=model) == "delivered"
    finally:
        agent_tools.TOOLS["web_search"] = original
