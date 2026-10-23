# Volume IV · Chapter 9 — Lab: Security Middleware for FastAPI

## What You Will Build

A security layer for an AI endpoint, assembled from four sections of Chapter 9: injection detection on the way in (9.3), JWT authentication with scopes (9.8), per-user token-bucket rate limiting (9.9), and moderation of the model's output on the way out (9.10). A `/chat` endpoint uses all four, and an attack simulation sends it six requests, each of which one layer should stop, and checks the status code it gets back.

## Learning Outcomes

- Authenticate with signed, expiring JWTs, and authorise with scopes.
- Tell 401 (who are you?) from 403 (you may not), and send the `WWW-Authenticate` challenge.
- Rate-limit each user with a token bucket that refills over time.
- Refuse known injection phrasings before they reach the model.
- Check the model's output as well as the user's input.

## Prerequisites

- Python 3.15
- Chapter 9, read through Sections 9.3 and 9.8–9.10 and the hands-on lab
- Dependencies: `fastapi`, `uvicorn`, `pyjwt`, `httpx`, `httpx2`, installed by `uv sync`
- Default mode: moderation is simulated, no key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. OpenAI's moderation endpoint has no charge at the time of writing.

## Setup

```bash
cd volume-4/chapter-09      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/attack_simulation.py          # your work
uv run python solution/attack_simulation.py     # reference
```

The simulation runs in-process, with no server. To attack a running server instead, start one from `solution/` (`uv run --project .. uvicorn app:app`) and pass its URL: `uv run python solution/attack_simulation.py http://127.0.0.1:8000`.

`security_middleware.py` combines the chapter's four sections as printed, with the JWT code on PyJWT. By default moderation is simulated (`stand_in.py`): it flags a few unmistakable phrases by category. The real endpoint is a trained classifier. `app.py` is the lab's Step 2 endpoint; it depends on `require_scope("inference:run")`, not on `verify_token` alone, because a valid token without the right scope must still be refused.

`src/` runs as supplied, but nothing detects injections (TODO 1), any valid token is accepted whatever its scopes (TODO 2), and the rate limiter never refuses (TODO 3). Its simulation passes 3 of 6. Complete all three.

## Expected Result

The reference prints the following (also saved in `expected/output.txt`):

```text
Test                       Expected   Got
--------------------------------------------
No token                        401   401  PASS
Valid token                     200   200  PASS
Injection attempt               400   400  PASS
Rate limit: 6th request         429   429  PASS
Wrong scope                     403   403  PASS
Harmful output                  422   422  PASS
--------------------------------------------
6/6 passed
```

A missing token gets 401 with a `WWW-Authenticate: Bearer` header; older FastAPI releases answered 403 here, which is why some guides still show that. The rate-limit case sends six requests at a bucket of five, so the sixth is refused. "Harmful output" is an addition to the chapter's five cases: the endpoint echoes the message, so the echo trips the output check, which is the layer that stops a model saying what it should not.

## Verifying Your Work

```bash
uv run pytest
```

Twelve tests: four injection phrasings are detected and ordinary text is not; a token round-trips and a tampered one fails; an expired token gets 401; the bucket allows its capacity, refuses, then refills; a missing token gets 401 with its challenge; a wrong scope gets 403; harmful output gets 422; and the whole simulation passes. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With all three TODOs left in place, seven tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| "Wrong scope" gets 200 | TODO 2: scopes are not checked, or the endpoint depends on `verify_token` | Check the scope in `require_scope`, and depend on it |
| "Rate limit" gets 200 | TODO 3: `consume()` always returns True | Refill, then take a token if one is there |
| "No token" gets 403, not 401 | An older FastAPI | Run `uv sync` to install the version this lab pins a floor for, or expect 403 |
| `jwt.exceptions.DecodeError` with a hand-written token | The token was not signed with `SECRET_KEY` | Create tokens with `create_access_token()` |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |

## Going Further

- Detect indirect injection: scan retrieved documents with the same patterns before they enter the prompt.
- Keep the rate limiter's buckets in Redis, so that several server processes share one limit.
- Add a refresh-token flow, with short-lived access tokens and a revocation list.

## Files

| Path | Purpose |
|---|---|
| `src/security_middleware.py` | Your starting point; runs, with 3 TODOs |
| `solution/security_middleware.py` | Sections 9.3, 9.8, 9.9 and 9.10 combined, with the mode switch |
| `solution/app.py` | Step 2: the `/chat` endpoint |
| `solution/attack_simulation.py` | Steps 3 and 4: the six attacks and the report |
| `solution/stand_in.py` | Simulated moderation |
| `tests/test_lab.py` | 12 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
