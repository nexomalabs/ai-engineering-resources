# Volume III · Chapter 8 — Lab: Tool-Calling System

## What You Will Build

A tool-calling system with four tools (`get_weather`, `search_database`, `calculate_cost`, and `get_shipment_status`, the rewritten tool from the chapter's opening story), their JSON schemas, a registry, and an orchestrator that validates every call's arguments against the schema before the tool runs and returns every failure to the model as a structured error. Five scenarios execute tool calls directly; the sixth runs the full loop, in which a scripted model asks for a tool, the tool runs and its result goes back to the model. No API key is needed.

## Learning Outcomes

- Write JSON schemas that tell a model what each tool does and accepts.
- Dispatch tool calls through a registry, by name.
- Validate arguments against the schema, including a pattern, before a tool runs.
- Run the model-tool loop: tool calls out, tool results back, until the model answers.
- Return an unknown tool, or a tool that raises, as a structured error the model can act on.
- Run independent tool calls in one turn, as parallel tool calling does.
- Keep tool results honest: an empty search returns no results, not invented ones.

## Prerequisites

- Python 3.15
- Chapter 8, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (a mock model issues the tool calls)

## Setup

```bash
cd volume-3/chapter-08      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but it ignores `units` (TODO 1), so New York in Scenario 2 reports 20 degrees Fahrenheit. It also skips the tracking-number pattern (TODO 4), so in Scenario 6 the customer's postcode reaches `get_shipment_status`, as postcodes reached the tool in the story; the reference rejects it before the tool runs. TODO 2 and TODO 3 do not change this demo's output, because every call names a real tool; the tests check them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

============================================================
SCENARIO: Weather Query — Paris
============================================================

→ Tool Call: get_weather({'city': 'Paris'})
← Result:    {
  "temp": 18,
  "condition": "Partly cloudy",
  "humidity": 65,
  "units": "celsius",
  "city": "Paris"
}

============================================================
SCENARIO: Parallel Weather Comparison
============================================================

→ Tool Call: get_weather({'city': 'London', 'units': 'celsius'})
← Result:    {
  "temp": 14,
  "condition": "Overcast",
  "humidity": 82,
  "units": "celsius",
  "city": "London"
}

→ Tool Call: get_weather({'city': 'Tokyo', 'units': 'celsius'})
← Result:    {
  "temp": 24,
  "condition": "Clear",
  "humidity": 55,
  "units": "celsius",
  "city": "Tokyo"
}

→ Tool Call: get_weather({'city': 'New York', 'units': 'fahrenheit'})
← Result:    {
  "temp": 68.0,
  "condition": "Sunny",
  "humidity": 48,
  "units": "fahrenheit",
  "city": "New York"
}

============================================================
SCENARIO: Database Search
============================================================

→ Tool Call: search_database({'query': 'neural network transformer', 'limit': 3})
← Result:    {
  "results": [
    {
      "id": 1,
      "name": "Neural Network Fundamentals",
      "type": "course",
      "rating": 4.8
    },
    {
      "id": 3,
      "name": "Transformer Architecture",
      "type": "article",
      "rating": 4.9
    }
  ],
  "total_found": 2,
  "query": "neural network transformer"
}

============================================================
SCENARIO: Cost Calculation
============================================================

→ Tool Call: calculate_cost({'items': [{'name': 'Pro License', 'quantity': 5, 'unit_price': 49.99}, {'name': 'Support Plan', 'quantity': 1, 'unit_price': 199.0}]})
← Result:    {
  "line_items": [
    {
      "name": "Pro License",
      "quantity": 5,
      "unit_price": 49.99,
      "total": 249.95
    },
    {
      "name": "Support Plan",
      "quantity": 1,
      "unit_price": 199.0,
      "total": 199.0
    }
  ],
  "subtotal": 448.95,
  "tax_8pct": 35.92,
  "grand_total": 484.87,
  "currency": "USD"
}

============================================================
SCENARIO: Error Handling — Unknown City
============================================================

→ Tool Call: get_weather({'city': 'Atlantis'})
← Result:    {
  "error": "City 'Atlantis' not found in weather database."
}

============================================================
SCENARIO: The model–tool loop — Where is my parcel?
============================================================

User: Where is my parcel? The tracking number is WF-2291.
  → get_shipment_status({"tracking_number": "WF-2291"})
  ← {"tracking_number": "WF-2291", "status": "in transit", "last_scan": "Leeds depot", "expected": "Thursday"}
Assistant: Your parcel WF-2291 is in transit, last scanned at the Leeds depot, expected Thursday.

User: Where is my parcel? I live at SW1A 1AA.
  → get_shipment_status({"tracking_number": "SW1A 1AA"})
  ← {"error": "Invalid arguments: 'tracking_number' does not match the pattern ^WF-[0-9]{4}$"}
Assistant: I can look that up with your tracking number: WF- and four digits, such as WF-2291. Could you send it?

✓ All tool calling scenarios completed successfully.
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. With the four TODOs left in place, six of the fifteen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `UnicodeEncodeError` printing `→` or `✓` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |
| The postcode reaches `get_shipment_status` in Scenario 6 | TODO 4: the pattern is not checked | Add an error when `re.search(spec["pattern"], value)` finds no match |

## Going Further

- Run the three calls in Scenario 2 concurrently with `asyncio.gather` and measure the time saved (Lab Question 1).
- Add a `convert_currency(amount, from_currency, to_currency)` tool with its schema (Lab Question 2).
- Validate each call's arguments against its schema before executing it, and return the validation error to the model.
- Write every tool invocation to a JSON Lines audit log (Lab Question 5).

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 4 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 15 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
