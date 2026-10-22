# Volume III · Chapter 13 — Lab: Agent Memory System with SQLite

## What You Will Build

An agent memory system on SQLite, built on Section 13.10's `AgentMemoryStore`: episodic records from three sessions with a returning user, semantic facts about the user and a tool, a code-review procedure injected first into the agent's context, hybrid retrieval that blends keyword relevance with recency, and forgetting that removes old, unimportant records while keeping important ones.

## Learning Outcomes

- Store episodic, semantic and procedural memory in one SQLite schema.
- Import past events with their real timestamps.
- Blend relevance and recency in retrieval, and see how the weight changes what surfaces.
- Upsert facts, so a fact is updated rather than duplicated.
- Forget by age and importance together, keeping what matters.

## Prerequisites

- Python 3.15
- Chapter 13, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (no model is called)

## Setup

```bash
cd volume-3/chapter-13      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/memory_lab.py          # your work
uv run python solution/memory_lab.py     # reference
```

`src/memory_lab.py` runs as supplied, but each TODO shows in its output: with every record stamped "now" (TODO 1) and recency ignored (TODO 2), both recency weights return the same records in Part 5, and Part 6 deletes nothing; once records are backdated, forgetting by age alone (TODO 3) also deletes the important ones.

The run writes `memory_lab.db` to the folder you run it from; open it with `sqlite3 memory_lab.db` and `.tables` to see the schema (Part 1).

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Part 1 — Schema
  tables: ['episodic', 'procedural', 'semantic']

Part 2 — Episodic records
  sess-1: 3 records
  sess-2: 2 records
  sess-3: 2 records

Part 3 — Semantic facts
  user:bob prefers_language = Python
  user:bob project_type = REST API built with FastAPI
  user:bob experience_level = learning async programming
  user:bob prefers_explanations = short, with a code example
  tool:code_review capability = flags blocking calls in async code

Part 4 — Procedural memory
  PROCEDURE (code_review): 1. Read the code. 2. Check for blocking calls in async functions. 3. Check error handling. 4. Suggest improvements with examples.
  MEMORY: Bob asked for a code review of his endpoint.
  MEMORY: Reviewed the endpoint: a blocking database call stalls the event loop.

Part 5 — Hybrid retrieval: 'async Python FastAPI'
  recency_weight=0.3:
    [sess-2] Bob asked how to write async endpoints in FastAPI.
    [sess-2] Surfaced Session 1: Bob is learning async Python.
    [sess-1] Explained Python's async and await keywords with an asyncio example.
  recency_weight=0.8:
    [sess-3] Reviewed the endpoint: a blocking database call stalls the event loop.
    [sess-3] Bob asked for a code review of his endpoint.
    [sess-2] Bob asked how to write async endpoints in FastAPI.
  At 0.3, keyword relevance dominates, so the older sessions about async Python and
  FastAPI surface. At 0.8, recency dominates, so the recent code review surfaces
  although it shares no keywords with the query.

Part 6 — Forgetting
  deleted 4 record(s) older than 3 days with importance below 0.7
  kept [sess-2] importance 0.7: Bob asked how to write async endpoints in FastAPI.
  kept [sess-3] importance 0.6: Bob asked for a code review of his endpoint.
  kept [sess-3] importance 0.9: Reviewed the endpoint: a blocking database call stalls the event loop.

Database written to memory_lab.db
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
| `TypeError: can't compare offset-naive and offset-aware datetimes` | A timestamp was written without a time zone | Pass timezone-aware datetimes, such as `utcnow() - timedelta(days=7)` |
| Records appear twice | An old `memory_lab.db` was reused | `memory_lab.py` deletes the file at the start; if you changed that, delete it by hand |

## Going Further

- Replace keyword matching in `retrieve_relevant` with embedding similarity.
- Give semantic facts an expiry date and skip expired facts in `get_facts_about`.
- Raise a record's importance each time it is retrieved, so useful memories survive forgetting.
- Record whether each procedure use succeeded, and keep `success_rate` up to date.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `agent_memory_store.py`, `memory_lab.py`; runs, with 3 TODOs |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
