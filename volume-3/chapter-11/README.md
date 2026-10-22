# Volume III · Chapter 11 — Lab: Build a ReAct Agent with Three Tools

## What You Will Build

A ReAct agent: a loop in which the model states a thought, chooses an action, and reads the observation, until it finishes or reaches its step limit. `agent_tools.py` holds a mocked web search, a calculator that validates its input before evaluating it, and a date lookup; `react_agent.py` builds the prompt, parses the model's JSON, runs the loop, and turns tool errors into observations. A scripted stub plays the model.

## Learning Outcomes

- Implement the Thought, Action, Observation loop with a step limit.
- Format the goal and the history into the prompt for each step.
- Validate model-supplied input before a tool acts on it.
- Turn a tool failure into an observation the model can respond to.
- Fall back safely when the model's output is not valid JSON.

## Prerequisites

- Python 3.15
- Chapter 11, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (a scripted stub stands in for the model)

## Setup

```bash
cd volume-3/chapter-11      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/react_agent.py          # your work
uv run python solution/react_agent.py     # reference
```

`src/react_agent.py` runs as supplied and completes all three goals, because none of them sends the calculator a bad expression, makes a tool raise, or returns broken JSON. Those are the paths the three TODOs cover, and the tests exercise each one (Part 4 of the lab). The first goal prints today's date, so that line will differ from the output below.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

============================================================
Agent Goal: What is today's date?
============================================================

Step 1:
  Thought: I can read the date directly.
  Action: get_current_date('')
  Observation: 2026-10-14

Step 2:
  Thought: I have the date.
  Action: finish("Today's date is 2026-10-14.")

Final Answer: Today's date is 2026-10-14.

============================================================
Agent Goal: What is the population of Japan multiplied by 0.0001?
============================================================

Step 1:
  Thought: I need Japan's population first.
  Action: web_search('population of japan')
  Observation: Japan population (2024): approximately 124.0 million people (World Bank).

Step 2:
  Thought: Now multiply by 0.0001.
  Action: calculator('124.0e6 * 0.0001')
  Observation: 12400.0

Step 3:
  Thought: The calculation is complete.
  Action: finish("Japan's population (about 124.0 million) multiplied by 0.0001 is 12400.0.")

Final Answer: Japan's population (about 124.0 million) multiplied by 0.0001 is 12400.0.

============================================================
Agent Goal: Who created Python and in what year?
============================================================

Step 1:
  Thought: I will search for who created Python.
  Action: web_search('python creator')
  Observation: Python was created by Guido van Rossum, first released in 1991.

Step 2:
  Thought: The search answered both parts.
  Action: finish('Python was created by Guido van Rossum, first released in 1991.')

Final Answer: Python was created by Guido van Rossum, first released in 1991.
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `Agent stopped: maximum steps reached.` | The model repeated a step instead of finishing | Check that the stub reads only the history; with a real model, tighten the prompt |
| `ModuleNotFoundError: No module named 'agent_tools'` | Python cannot see the tools module | Run the script by its path, `python src/react_agent.py`, so its folder is on the path |

## Going Further

- Replace the stub with a real model call, and run the three goals again.
- Add a goal the canned search cannot answer, and make the agent say so instead of guessing.
- Stop the loop early if the model repeats the same action with the same arguments.
- Replace `eval` with a small parser using Python's `ast` module, which cannot run code.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `agent_tools.py`, `react_agent.py`; runs, with 3 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 9 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
