# Volume I · Chapter 10 — Lab: Writing Your First Professional Prompts

**Volume I capstone.**

## What You Will Build

Five exercises. Each pairs a WEAK prompt against a STRONG one on the identical task, and
each demonstrates one specific failure mode from the taxonomy in §10.9: ambiguity,
format, hallucination, constraint violation, and missing structure. You will write a
checker for each exercise that proves — rather than just asserts — that the strong prompt
actually fixed what the weak one broke.

## Learning Outcomes

- Apply the prompt anatomy from §10.3 to remove ambiguity from a task.
- Force a structured, parseable output format and verify it parses.
- Ground a model in a provided document and detect when it is not grounded.
- Enforce a hard constraint (a word limit) and verify compliance.
- Extract a full schema from unstructured text and verify every field arrived.
- Recognise that a "weak" prompt is not a bad prompt — it is an underspecified one.

## Prerequisites

- Python 3.15
- Chapter 10 read through §10.9
- **No API key required by default.** This lab replays recorded model responses.
  Estimated API cost to complete: **$0.00**.

## Setup

```bash
cd volume-1/chapter-10      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py
```

`src/lab.py` runs as supplied against the fixtures, but all five `check_exN` functions are
stubs returning `False`, so every exercise reports **0/5**. Complete the five TODOs — one
check function per exercise.

Reference implementation:

```bash
uv run python solution/lab.py
```

## Expected Result

Full output is in `expected/output.txt`. Summary: **5/5**.

| Exercise | Failure mode | Weak result | Strong result |
|---|---|---|---|
| 1 — Summarization | Ambiguity | 3 sentences in an order the model chose for itself | Exactly 3 sentences, each figure in its assigned slot |
| 2 — Intent classification | Format | `Intent: Correct the billing address on an invoice.` — prose, not parseable | `{"intent":"request","confidence":"high","topic":"Correcting the address on an invoice"}` |
| 3 — Document Q&A | Hallucination | Guesses the question is about OpenAI and describes ChatGPT plans | Correctly reports "Professional, $20 per month" from the document |
| 4 — Product description | Constraint violation | 73 words, with a headline it was never asked for | 26 words, no headline, ends on the call to action |
| 5 — Meeting notes | Missing structure | A bulleted list of the three action items — not JSON, no attendees or decisions | Valid JSON, all 3 attendees, all 3 decisions, all 3 action items |

**Exercise 3 is the one to read closely.** "Nexoma Cloud Storage" is fictional — invented
for this exercise — so there is no real answer for an ungrounded model to recall. Given
nothing to ground it, gpt-6-luna did not admit it lacked the information. It guessed what
you probably meant ("If you mean OpenAI...") and answered a question about a different
product. A newer model fails more politely than an older one, but it still fills the gap
with its own assumptions. The strong prompt removes the gap by supplying the document and
saying what to do when the answer is not in it.

**Exercise 1 looks like a draw, and that is the point.** The weak summary is reasonable:
three sentences with the right figures. But its structure is the model's choice, and a
different run may choose differently. The strong prompt fixes which figure goes in which
sentence, so every run is checkable against the same specification. The check accepts
`$4.2M` or `$4.2 million`, since the strong prompt did not specify a number format.

**Why gpt-6-luna, and why 2,000 tokens.** gpt-6-luna is a reasoning model: it accepts only
its default temperature, so `call()` sends none, and its hidden reasoning tokens count
against `max_completion_tokens`. A limit of a few hundred tokens can be used up by
reasoning before any visible answer is written, so the lab allows 2,000.

**Exercise 1 also taught something during authoring.** A naive sentence counter that
splits on every `.` character counts **8** sentences in the strong response, not 3 —
because the text contains `$4.2M`, `$1.1M`, `$1.8M`, and `$3.1M`, each with a period the
splitter mistook for a sentence break. `sentence_count()` splits only on a
period/question mark/exclamation point that is followed by whitespace and a capital
letter, which fixes it. `TestSentenceCount.test_dollar_figures_do_not_create_false_sentence_breaks`
pins this so it cannot regress.

## Verifying Your Work

```bash
uv run pytest
```

Nineteen tests. `TestExerciseChecks` verifies each check function against hand-built
weak/strong strings, independent of the fixtures — so a future fixture change cannot
silently break the checker itself. `TestAllFiveExercisesDemonstrateTheirFix` is the
end-to-end claim: all five, against the bundled recordings.

## Running It Against the Real API

The bundled fixtures are real responses, recorded from gpt-6-luna on 22 October 2026.
With an `OPENAI_API_KEY` you can run the lab yourself. A full run is ten requests and costs
well under $0.05.

**Use `live` mode for your first run.** It calls the API and saves nothing, so your
clone stays exactly as shipped and `uv run pytest` keeps passing.

macOS or Linux:

```bash
export OPENAI_API_KEY=sk-...
NEXOMA_LAB_MODE=live uv run --group live python solution/lab.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:NEXOMA_LAB_MODE = "live"
uv run --group live python solution/lab.py
Remove-Item Env:NEXOMA_LAB_MODE     # back to replaying fixtures
```

`--group live` installs the OpenAI SDK, which fixture mode does not need. The banner on
the first line of output tells you which mode ran. Expect your numbers to differ from
*Expected Result*: these are fresh samples from the model.

**`record` mode overwrites the bundled fixtures.** Fixtures are keyed by a hash of the
request, and the solution sends the same requests the bundled files were saved under, so
`NEXOMA_LAB_MODE=record` replaces them with your responses. Tests that check exact values
may then fail. Restore the originals with `git checkout -- fixtures/`.

## If It Does Not Work

| Symptom | Cause | Fix |
|---------|-------|-----|
| Every exercise reports "fail" | All five `check_exN` are still stubs | Complete the five TODOs |
| Exercise 1 sentence count looks wrong | Splitting on every `.`, breaking on `$4.2M` | Use `sentence_count()`, not `text.split(".")` |
| Exercise 2/5 "fix demonstrated" is `False` even though output looks right | `demonstrates_fix` requires the **weak** response to fail too | Check both sides, not just the strong response |
| `FixtureMissing` error | Prompt text edited — even whitespace changes the fixture key | Use the constants exactly as given |
| `ModuleNotFoundError: openai` | `--group live` left off the command | Add `--group live` to `uv run`, or stay in fixture mode |
| `live` or `record` mode fails with an auth error | No `OPENAI_API_KEY` set in this terminal | Set it as shown above, or stay in fixture mode — it needs nothing |

## Going Further

1. Write a stricter Exercise 3 check that also fails a response that talks about products
   not in the document, as the weak run did when it described ChatGPT plans.
2. Add a sixth exercise for a failure mode of your own choosing — refusal, verbosity, or
   inconsistent formatting across repeated calls — and write its checker.
3. Run Exercise 1's weak prompt five times in `live` mode. Does the length and structure
   vary run to run? That variance is the ambiguity failure showing up
   a second way — not just wrong once, but *inconsistent* every time.

## Files

| Path | Purpose |
|------|---------|
| `src/lab.py` | Your starting point — runs against fixtures, with five TODOs |
| `solution/lab.py` | Complete reference implementation |
| `fixtures/chapter-10/` | Responses recorded from gpt-6-luna, replayed in fixture mode |
| `tests/test_lab.py` | Runs against `solution/` in CI |
| `expected/output.txt` | Captured reference output |
| `pyproject.toml` | Dependencies; `live` group only needed for `record`/`live` mode |
