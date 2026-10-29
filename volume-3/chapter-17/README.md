# Volume III · Chapter 17 — Lab: Agent Evaluation Suite

## What You Will Build

An evaluation harness for a ReAct agent, run on two suites. Ten easy cases are one-step lookups, like the claims Noor's first suite in the chapter was built from. Four claims are the kind that caused trouble in real traffic: a clear case, a used item, damage reported days after delivery, and a missing receipt. Each case names a task, the answer expected, the tool calls that should produce it and the optimal number of steps. The harness runs the agent on each case, records an execution trace (every step, every tool call, the final answer), scores three metrics (task completion, tool-use accuracy and step efficiency), and aggregates them into a report that scores each suite separately, counts from the traces how often each tool was called, and names the failing cases.

## Learning Outcomes

- Define agent test cases with expected answers, expected tool calls and an optimal step count.
- Capture an execution trace that records what the agent did, not just what it answered.
- Score task completion, tool-use accuracy and step efficiency separately.
- Aggregate per-case scores into a report that names the failing and inefficient cases.
- Explain why an agent can answer correctly and still score badly on efficiency.
- Show how an evaluation built only from easy cases overstates an agent, and use trace counts to find out why it fails on the hard ones.

## Prerequisites

- Python 3.15
- Chapter 17, read through its hands-on lab
- Default mode: the standard library only, no API key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (about thirty-five short calls)

## Setup

```bash
cd volume-3/chapter-17      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/agent_eval.py          # your work
uv run python solution/agent_eval.py     # reference
```

By default a scripted stand-in plays the agent's model (`stand_in.py`). It exposes the one method the lab calls, `client.chat.completions.create(...)`, so the agent loop is exactly the chapter's code. Eight tasks take the optimal path. Two do not, so the evaluation has something to find. On "2 to the power of 10" the agent first sends `2^10`, which the calculator cannot parse, then recovers with `2 ** 10`. On "the highest mountain" it searches for "tallest peak on Earth", finds nothing and gives up. On the four claims it repeats what the chapter's story found in the traces: it checks the photos twice on every claim and never reads the carrier's handling log, so it approves a dent that was signed for as undamaged, and a claim with no receipt.

`src/agent_eval.py` runs as supplied, but it never parses an action (TODO 1), so no tool is ever called and every lookup fails; and its tool-accuracy and step-efficiency scores always return 100% (TODOs 2 and 3). Complete all three.

For live mode, set your key and the mode, and add `--group live`, which installs the OpenAI
SDK that the default mode does not need.

macOS or Linux:

```bash
export OPENAI_API_KEY=sk-...
NEXOMA_LAB_MODE=live uv run --group live python solution/agent_eval.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:NEXOMA_LAB_MODE = "live"
uv run --group live python solution/agent_eval.py
Remove-Item Env:NEXOMA_LAB_MODE     # back to the stand-in
```

## Expected Result

The reference solution prints the following summary (full output in `expected/output.txt`):

```text
{
  "total_test_cases": 14,
  "task_completion_rate": 78.6,
  "avg_tool_use_accuracy": 82.1,
  "avg_step_efficiency": 91.7,
  "avg_duration_seconds": 0.0
}

BY SUITE:
  easy    10 cases | completion  90.0% | tool accuracy  90.0% | step efficiency  96.7%
  claims   4 cases | completion  50.0% | tool accuracy  62.5% | step efficiency  79.2%

TOOL CALLS PER CASE (from the traces):
  easy    search 0.5 | calculator 0.4 | get_weather 0.2
  claims  check_photos 2.0 | get_receipt 0.5 | get_handling_log 0.0
```

On the easy suite alone the agent looks ready: 90% completion and 90% tool accuracy. The claims suite halves its completion rate, and the trace counts say why: two photo checks per claim, and the handling log never read. TC13 even scores 100% step efficiency, because it stops early with the wrong answer, which is why no single metric is enough. TC04 completes, but in three steps instead of two, so its step efficiency is 67%: a correct answer reached inefficiently. In live mode, the model's choices decide the scores, and durations are real.

## Verifying Your Work

```bash
uv run pytest
```

Nine tests: action and answer parsing, tool accuracy (right tool, wrong tool, wrong argument), step efficiency (including the cap and zero steps), case-insensitive completion, the report's headline numbers over all fourteen cases, the per-suite scores, the tool counts from the traces, and the failure analysis. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With all three TODOs left in place, seven tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| Every task shows `NO ANSWER` or 0% completion | TODO 1: no action is parsed, so the agent loops without tools | Match `Action: name({...})` and parse the JSON |
| Tool accuracy is 100% even for TC09 | TODO 2 still returns 1.0 | Compare each expected tool and argument with the trace |
| Step efficiency is 100% for TC04 | TODO 3 still returns 1.0 | Divide the optimal steps by the actual steps, capped at 1.0 |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |
| Live mode fails with an auth error | No `OPENAI_API_KEY` in this terminal | Set it, or stay in the default mode |

## Going Further

- Add a reasoning-quality metric: a second model call that scores each completed trace's reasoning on a 1–5 rubric.
- Run every case three times and report the mean and standard deviation of each metric.
- Pre-load a memory store with relevant facts and test whether the agent uses them.

## Files

| Path | Purpose |
|---|---|
| `src/agent_eval.py` | Your starting point; runs, with 3 TODOs |
| `src/stand_in.py`, `solution/stand_in.py` | The scripted stand-in for the model |
| `solution/agent_eval.py` | Reference implementation: the chapter's code, with the mode switch where the client is created |
| `tests/test_lab.py` | 9 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
