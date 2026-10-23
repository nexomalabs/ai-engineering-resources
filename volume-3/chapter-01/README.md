# Volume III · Chapter 1 — Lab: Build a Context Pipeline in Python

## What You Will Build

A context pipeline for a customer support assistant. It takes named blocks of context (system instructions, retrieved knowledge articles, the user's account profile, the conversation so far, and the current request), counts each block's tokens, orders the blocks by layer and priority, and assembles them into a message list that fits a token budget. The system and request layers are always kept; the others are dropped, in order, when the budget runs out.

## Learning Outcomes

- Represent each piece of context as a block with a layer, a priority and a token count.
- Order context by layer first and by priority within a layer.
- Reserve part of the budget for the model's response.
- Keep mandatory layers regardless of budget, and drop optional ones in a predictable order.
- Read a token utilization report and explain which blocks were excluded and why.

## Prerequisites

- Python 3.15
- Chapter 1, read through its hands-on lab
- `tiktoken`, installed by `uv sync`. It downloads its token encoding (about 1.7 MB) on first use.
- No API key. **Estimated API cost: $0.00.** The pipeline assembles context; it does not call a model.

## Setup

```bash
cd volume-3/chapter-01      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/context_pipeline.py          # your work
uv run python solution/context_pipeline.py     # reference
```

`src/context_pipeline.py` runs as supplied, and at the default 4,096-token budget its output looks the same as the reference: everything fits. The two TODOs only show at a small budget. TODO 1 sorts the blocks by layer and priority; TODO 2 enforces the budget for the optional layers. Try `build_customer_support_context(query, token_budget=800)` before and after.

## Expected Result

The reference solution prints six messages and this report (full output in `expected/output.txt`):

```text
=== TOKEN UTILIZATION REPORT ===
{
  "token_budget": 4096,
  "tokens_used": 370,
  "tokens_available": 3726,
  "blocks_included": 7,
  "blocks_excluded": 0,
  "excluded_blocks": []
}
```

Seven blocks become six messages because the two system blocks are joined into one system message. At a budget of 800 tokens, 512 are reserved for the response and 288 remain: both knowledge articles still fit, but the user profile and the conversation history are excluded, because the knowledge layer comes first in `LAYER_ORDER`.

## Verifying Your Work

```bash
uv run pytest
```

Six tests: token counting, layer-then-priority ordering, the six-message assembly, the 800-token exclusions, mandatory layers at a one-token budget, and the report's arithmetic. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/context_pipeline.py` over the one in `solution/` there, and run `uv run pytest`. With both TODOs left in place, three tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| A network error on the first run | `tiktoken` downloads its encoding once | Run it once with a connection; after that it is cached |
| Nothing is excluded at a small budget | TODO 2 still includes every block | Compare `tokens_used + block.token_count` with `available` |
| The wrong blocks are excluded | TODO 1 still returns the blocks unsorted | Sort by `LAYER_ORDER` position, then by priority |

## Going Further

- Change `LAYER_ORDER` so that conversation history outranks knowledge, and see which blocks survive at 800 tokens.
- Report the tokens left after the response reserve, not just `budget - used`.
- Truncate the lowest-priority block to fit, instead of dropping it whole.

## Files

| Path | Purpose |
|---|---|
| `src/context_pipeline.py` | Your starting point; runs, with 2 TODOs |
| `solution/context_pipeline.py` | Reference implementation, as printed in the chapter |
| `tests/test_lab.py` | 6 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
