"""
Lab 17: Agent Evaluation Suite
Evaluates a ReAct agent on 10 test cases across three metrics.

    NEXOMA_LAB_MODE=fixture  (default) a scripted stand-in plays the agent's model; no key
    NEXOMA_LAB_MODE=live     calls gpt-6-luna; needs OPENAI_API_KEY and `--group live`
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

if os.environ.get("NEXOMA_LAB_MODE", "fixture") == "live":
    from openai import OpenAI

    client = OpenAI()
else:
    from stand_in import StandInClient

    client = StandInClient()

# ── Mock Tools ─────────────────────────────────────────────────────────────────

MOCK_TOOL_REGISTRY = {
    "search": {
        "description": "Search for factual information. Args: {query: str}",
        "responses": {
            "capital of France": "Paris is the capital of France.",
            "population of Tokyo": "Tokyo has a population of approximately 13.96 million.",
            "speed of light": "The speed of light is 299,792,458 meters per second.",
            "Python release year": "Python was first released in 1991.",
            "highest mountain": "Mount Everest is the highest mountain, at 8,849 meters.",
        },
        "default": "No results found for that query.",
    },
    "calculator": {
        "description": "Perform arithmetic. Args: {expression: str}",
        "responses": {
            "15 * 8": "120",
            "100 / 4": "25.0",
            "2 ** 10": "1024",
            "sqrt(144)": "12.0",
            "42 + 58": "100",
        },
        "default": "Cannot compute that expression.",
    },
    "get_weather": {
        "description": "Get current weather for a city. Args: {city: str}",
        "responses": {
            "London": "London: 18°C, partly cloudy.",
            "New York": "New York: 24°C, sunny.",
            "Tokyo": "Tokyo: 29°C, humid.",
        },
        "default": "Weather data unavailable for that city.",
    },
}


def call_mock_tool(tool_name: str, args: dict) -> str:
    """Execute a mock tool call with deterministic responses."""
    if tool_name not in MOCK_TOOL_REGISTRY:
        return f"Error: Unknown tool '{tool_name}'."
    tool = MOCK_TOOL_REGISTRY[tool_name]
    # Check each arg value against known responses
    for key, value in args.items():
        for known_input, response in tool["responses"].items():
            if known_input.lower() in str(value).lower():
                return response
    return tool["default"]


# ── Test Case Library ──────────────────────────────────────────────────────────


@dataclass
class TestCase:
    id: str
    task: str
    expected_answer: str
    expected_tools: list  # list of (tool_name, key_arg) tuples
    optimal_steps: int


TEST_CASES = [
    TestCase(
        "TC01", "What is the capital of France?", "Paris", [("search", "capital of France")], 2
    ),
    TestCase("TC02", "Calculate 15 times 8.", "120", [("calculator", "15 * 8")], 2),
    TestCase(
        "TC03",
        "What is the population of Tokyo?",
        "13.96 million",
        [("search", "population of Tokyo")],
        2,
    ),
    TestCase("TC04", "What is 2 to the power of 10?", "1024", [("calculator", "2 ** 10")], 2),
    TestCase(
        "TC05", "What is the current weather in London?", "18°C", [("get_weather", "London")], 2
    ),
    TestCase(
        "TC06",
        "What is the speed of light in meters per second?",
        "299,792,458",
        [("search", "speed of light")],
        2,
    ),
    TestCase("TC07", "What is 100 divided by 4?", "25", [("calculator", "100 / 4")], 2),
    TestCase(
        "TC08", "When was Python first released?", "1991", [("search", "Python release year")], 2
    ),
    TestCase(
        "TC09",
        "What is the highest mountain and its height?",
        "Everest",
        [("search", "highest mountain")],
        2,
    ),
    TestCase("TC10", "What is the weather in Tokyo?", "29°C", [("get_weather", "Tokyo")], 2),
]


# ── Execution Trace ────────────────────────────────────────────────────────────


@dataclass
class ToolCall:
    tool: str
    args: dict
    result: str
    correct_tool: bool = False
    correct_args: bool = False


@dataclass
class ExecutionTrace:
    test_case_id: str
    task: str
    steps: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    final_answer: str = ""
    completed: bool = False
    duration: float = 0.0


# ── ReAct Agent ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a ReAct agent. You answer questions using available tools.

Available tools:
- search(query): Search for factual information.
- calculator(expression): Perform arithmetic calculations.
- get_weather(city): Get current weather for a city.

Format your response strictly as:
Thought: [your reasoning]
Action: tool_name({"key": "value"})
Observation: [you will receive the tool result here]
... (repeat Thought/Action/Observation as needed)
Answer: [your final answer]

Use the minimum number of steps necessary."""


def parse_action(text: str) -> Optional[tuple]:
    """Extract tool name and args from Action line."""
    match = re.search(r"Action:\s*(\w+)\((\{[^}]+\})\)", text)
    if not match:
        return None
    tool_name = match.group(1)
    try:
        args = json.loads(match.group(2))
        return tool_name, args
    except json.JSONDecodeError:
        return None


def parse_answer(text: str) -> Optional[str]:
    """Extract final answer from Answer line."""
    match = re.search(r"Answer:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    return match.group(1).strip() if match else None


def run_react_agent(task: str, max_steps: int = 8) -> ExecutionTrace:
    """Run a simple ReAct agent loop with mock tools."""
    trace = ExecutionTrace(test_case_id="", task=task)
    start = time.perf_counter()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-6-luna",
            reasoning_effort="none",
            messages=messages,
            temperature=0.0,
            max_completion_tokens=512,
        )
        # Current models reject a `stop` parameter, so cut the turn at "Observation:"
        # here: the observation must come from the tool, never from the model.
        assistant_text = response.choices[0].message.content.split("Observation:")[0].strip()
        trace.steps.append(assistant_text)
        messages.append({"role": "assistant", "content": assistant_text})

        # Check for final answer
        answer = parse_answer(assistant_text)
        if answer:
            trace.final_answer = answer
            trace.completed = True
            break

        # Parse and execute tool call
        action = parse_action(assistant_text)
        if action:
            tool_name, args = action
            tool_result = call_mock_tool(tool_name, args)
            tc = ToolCall(tool=tool_name, args=args, result=tool_result)
            trace.tool_calls.append(tc)
            observation = f"Observation: {tool_result}"
            messages.append({"role": "user", "content": observation})
        else:
            # No action and no answer — agent is stuck
            messages.append(
                {"role": "user", "content": "Observation: Please provide an Action or Answer."}
            )

    trace.duration = round(time.perf_counter() - start, 3)
    return trace


# ── Metric Computation ─────────────────────────────────────────────────────────


def score_task_completion(trace: ExecutionTrace, test_case: TestCase) -> float:
    """1.0 if expected answer substring found in final answer, else 0.0."""
    if not trace.completed or not trace.final_answer:
        return 0.0
    answer_lower = trace.final_answer.lower()
    expected_lower = test_case.expected_answer.lower()
    return 1.0 if expected_lower in answer_lower else 0.0


def score_tool_use_accuracy(trace: ExecutionTrace, test_case: TestCase) -> float:
    """Fraction of expected tool calls that were made correctly."""
    if not test_case.expected_tools:
        return 1.0
    hits = 0
    for expected_tool, expected_arg_substring in test_case.expected_tools:
        for tc in trace.tool_calls:
            if tc.tool == expected_tool:
                args_str = json.dumps(tc.args).lower()
                if expected_arg_substring.lower() in args_str:
                    hits += 1
                    break
    return hits / len(test_case.expected_tools)


def score_step_efficiency(trace: ExecutionTrace, test_case: TestCase) -> float:
    """optimal_steps / actual_steps, capped at 1.0."""
    actual = len(trace.steps)
    if actual == 0:
        return 0.0
    return min(1.0, test_case.optimal_steps / actual)


@dataclass
class TestResult:
    test_case_id: str
    task: str
    completed: float
    tool_accuracy: float
    step_efficiency: float
    actual_steps: int
    optimal_steps: int
    final_answer: str
    duration: float


def evaluate_agent(test_cases: list) -> list:
    """Run all test cases and return scored results."""
    results = []
    for tc in test_cases:
        print(f"  Running {tc.id}: {tc.task[:50]}...")
        trace = run_react_agent(tc.task)
        trace.test_case_id = tc.id

        result = TestResult(
            test_case_id=tc.id,
            task=tc.task,
            completed=score_task_completion(trace, tc),
            tool_accuracy=score_tool_use_accuracy(trace, tc),
            step_efficiency=score_step_efficiency(trace, tc),
            actual_steps=len(trace.steps),
            optimal_steps=tc.optimal_steps,
            final_answer=trace.final_answer,
            duration=trace.duration,
        )
        results.append(result)
    return results


# ── Report Generator ───────────────────────────────────────────────────────────


def generate_report(results: list) -> dict:
    """Aggregate results into a structured evaluation report."""
    n = len(results)
    tcr = sum(r.completed for r in results) / n * 100
    avg_tua = sum(r.tool_accuracy for r in results) / n * 100
    avg_eff = sum(r.step_efficiency for r in results) / n * 100
    avg_duration = sum(r.duration for r in results) / n

    report = {
        "summary": {
            "total_test_cases": n,
            "task_completion_rate": round(tcr, 1),
            "avg_tool_use_accuracy": round(avg_tua, 1),
            "avg_step_efficiency": round(avg_eff, 1),
            "avg_duration_seconds": round(avg_duration, 3),
        },
        "per_case": [
            {
                "id": r.test_case_id,
                "task": r.task,
                "completed": bool(r.completed),
                "tool_accuracy": f"{r.tool_accuracy:.0%}",
                "step_efficiency": f"{r.step_efficiency:.0%}",
                "steps": f"{r.actual_steps}/{r.optimal_steps}",
                "answer": r.final_answer[:80] if r.final_answer else "NO ANSWER",
                "duration_s": r.duration,
            }
            for r in results
        ],
        "failure_analysis": {
            "incomplete_tasks": [r.test_case_id for r in results if not r.completed],
            "inefficient_tasks": [r.test_case_id for r in results if r.step_efficiency < 0.5],
            "wrong_tools": [r.test_case_id for r in results if r.tool_accuracy < 1.0],
        },
    }
    return report


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AGENT EVALUATION SUITE — LAB 17")
    print("=" * 60)
    print(f"Running {len(TEST_CASES)} test cases...\n")

    results = evaluate_agent(TEST_CASES)
    report = generate_report(results)

    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    print(json.dumps(report["summary"], indent=2))

    print("\nPER-CASE RESULTS:")
    print("-" * 60)
    for case in report["per_case"]:
        status = "✓" if case["completed"] else "✗"
        print(f"{status} {case['id']}: {case['task'][:45]}")
        print(
            f"    Tool accuracy: {case['tool_accuracy']} | "
            f"Step efficiency: {case['step_efficiency']} | "
            f"Steps: {case['steps']} | "
            f"Time: {case['duration_s']}s"
        )
        print(f"    Answer: {case['answer']}")

    print("\nFAILURE ANALYSIS:")
    print(json.dumps(report["failure_analysis"], indent=2))
