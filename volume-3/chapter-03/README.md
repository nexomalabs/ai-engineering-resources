# Volume III · Chapter 3 — Lab: Three-Type Memory System

## What You Will Build

A memory system with three stores: working memory (the last few conversation turns), episodic memory (past assistant responses, recalled by recency-weighted similarity), and semantic memory (facts, recalled by cosine similarity and deduplicated on write). A single `recall()` call gathers what is relevant to a new query from all three. Every memory belongs to a user, and every query names one, so a user recalls only their own memories and the facts marked as shared: the fix for the leak in the chapter's opening story, where one customer was greeted with another's delivery instructions.

## Learning Outcomes

- Bound working memory so it keeps only the most recent turns.
- Score episodic memories by similarity and recency together.
- Deduplicate semantic memory on write, so a fact is stored once.
- Retrieve from all three stores with one call, and read the scores.
- Scope every memory to its user, filtering before scoring, so one user's memories never reach another.
- Explain what a hashed bag-of-words embedding can and cannot match.

## Prerequisites

- Python 3.15
- Chapter 3, read through its hands-on lab
- Dependencies: `numpy`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (a deterministic hashed embedding stands in for an embedding model)

## Setup

```bash
cd volume-3/chapter-03      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but working memory keeps every turn (TODO 1), so it prints six turns where the reference prints five, and every user can see every memory (TODO 4), so the second user, `sam`, is shown Alex's past answers and the fact that Alex prefers Python. TODO 2 and TODO 3 do not change this demo's output; the tests check them.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
=== MEMORY RECALL FOR USER 'alex' ===
'What Python library handles JWT and how do I verify a token?'

--- WORKING MEMORY (recent conversation) ---
ASSISTANT: JWT authentication uses signed tokens. The server issues a JWT containing user claims, signed with a secret key. The client stores the token and sends it in the Authorization header. The server verifies the signature without needing session state.
USER: What library should I use in Python for JWT?
ASSISTANT: For Python, I recommend the `python-jose` or `PyJWT` library. PyJWT is widely used and straightforward: `import jwt; token = jwt.encode(payload, secret, algorithm='HS256')`.
USER: How do I refresh tokens?
ASSISTANT: Issue a short-lived access token (15 minutes) and a long-lived refresh token (7 days). When the access token expires, the client calls /auth/refresh with the refresh token to get a new access token.

--- EPISODIC MEMORY (past responses) ---
  [0.33] For Python, I recommend the `python-jose` or `PyJWT` library. PyJWT is widely used and straightforwa...
  [0.252] Issue a short-lived access token (15 minutes) and a long-lived refresh token (7 days). When the acce...

--- SEMANTIC MEMORY (facts) ---
  [0.272] [user] Alex prefers Python over JavaScript for server-side code
  [0.258] [kb] JWT tokens consist of three base64-encoded parts separated by dots
  [0.167] [kb] Python uses indentation to define code blocks

=== MEMORY RECALL FOR USER 'sam' ===
'What Python library handles JWT and how do I verify a token?'

--- WORKING MEMORY (recent conversation) ---
  (none)

--- EPISODIC MEMORY (past responses) ---
  (none)

--- SEMANTIC MEMORY (facts) ---
  [0.258] [kb] JWT tokens consist of three base64-encoded parts separated by dots
  [0.167] [kb] Python uses indentation to define code blocks
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. With the four TODOs left in place, six of the fourteen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| A fact you expect is not recalled | The hashed embedding matches shared words only | Reword the query to use the fact's words, or lower `threshold` in `retrieve()` |
| `sam` is shown Alex's answers or facts | TODO 4: `visible_to()` still returns True | Return True only when the owner is the user or `SHARED` |

## Going Further

- Replace `mock_embed` with a real embedding model and compare which facts are recalled for paraphrased queries.
- Add a time-to-live to episodic memory, so episodes older than a set age are forgotten.
- Persist semantic memory to a JSON file and reload it at start-up.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 4 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 14 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
