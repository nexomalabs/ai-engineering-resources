# Volume III · Chapter 18 — Lab: Agent Security Layer

## What You Will Build

A security layer around an agent, in three parts. An input validator truncates over-long input and finds prompt-injection patterns, replacing each with a marker before the model sees it. An output sanitizer redacts secrets (API keys, passwords, bearer tokens, private keys, social security numbers) from what the model returns. A tamper-evident audit log chains every entry to the one before it with SHA-256 hashes, so editing any entry afterwards is detectable. A ten-input test suite exercises all three.

## Learning Outcomes

- Detect known prompt-injection phrasings with patterns, and neutralise them before they reach the model.
- Redact sensitive data from model output before it reaches a user or another system.
- Build an append-only log in which each entry's hash covers the previous entry's hash.
- Verify the chain and locate exactly which entries were altered.
- Explain why pattern matching is one layer of a defence, not the whole of it.

## Prerequisites

- Python 3.15
- Chapter 18, read through its hands-on lab
- Default mode: the standard library only, no API key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (ten short calls)

## Setup

```bash
cd volume-3/chapter-18      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/security_layer.py          # your work
uv run python solution/security_layer.py     # reference
```

Both write `audit_log.json` in the current folder. By default a stand-in answers instead of the model (`stand_in.py`): a fixed reply for each safe question and a refusal for any input whose injection was removed. Its JWT answer includes a hard-coded signing secret, the kind of thing models really do write into example code, so the output sanitizer has something to catch.

`src/security_layer.py` runs as supplied, but it detects no injections (TODO 1), redacts nothing (TODO 2) and never reports tampering (TODO 3); its suite ends with `Test Results: 4/10 passed`. Complete all three.

For live mode:

```bash
uv sync --group live
NEXOMA_LAB_MODE=live OPENAI_API_KEY=... uv run python solution/security_layer.py
```

## Expected Result

The reference solution blocks all six injection attempts, processes the four safe inputs, and ends with the following (full output in `expected/output.txt`; session IDs, times and hashes differ on every run):

```text
--- TAMPER DETECTION TEST ---
Chain integrity before tampering: VALID
Chain integrity after tampering: INVALID — tampered at indices [0, 1]

Test Results: 10/10 passed

Audit log exported to audit_log.json (21 entries)
```

The JWT question is a safe input, but the answer to it carries a secret: the sanitizer redacts it, raises a critical event and adds a `security_alert` entry, which is why the log has 21 entries for 10 inputs. The tamper test edits entry 0, and the check reports index 1 as well, because entry 1's stored link no longer matches. That is the chain doing its job.

The pattern list is deliberately simple. It catches the phrasings it anticipates and nothing else: rephrase an attack ("Pretend your rules don't apply") and it passes. Chapter 18 explains why a filter like this is one layer among several.

## Verifying Your Work

```bash
uv run pytest
```

Fifteen tests: each of the six injections is detected and removed, three safe inputs pass unchanged, over-long input is truncated, secrets are redacted, the chain verifies and pinpoints an edited entry, a broken link flags two entries, the agent redacts its own JWT answer, and the whole suite passes 10 of 10. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `Test Results: 4/10 passed` | TODO 1: no injection is detected | Search with every compiled pattern and replace each match |
| The JWT answer shows the secret | TODO 2: the sanitizer redacts nothing | Replace each sensitive match with `[REDACTED]` |
| "after tampering" still says VALID | TODO 3: the chain is never checked | Compare each `previous_hash` and recomputed hash |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |
| Live mode fails with an auth error | No `OPENAI_API_KEY` in this terminal | Set it, or stay in the default mode |

## Going Further

- Add `validate_tool_output()`: scan what tools return for injection patterns before it goes back to the agent (indirect injection).
- Add a `ToolCallFilter` that allows only the tools whitelisted for each task type.
- Rate-limit a session that triggers more than three security events in sixty seconds.

## Files

| Path | Purpose |
|---|---|
| `src/security_layer.py` | Your starting point; runs, with 3 TODOs |
| `src/stand_in.py`, `solution/stand_in.py` | The stand-in for the model |
| `solution/security_layer.py` | Reference implementation: the chapter's code, with the mode switch where the client is created |
| `tests/test_lab.py` | 15 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
