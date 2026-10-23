# Volume II · Chapter 9 — Lab: Output Control: Schema Enforcement and Validation

## What You Will Build

The Hands-on Lab from Chapter 9, as printed in the book, running against recorded model
responses so it needs no API key. Follow the chapter's lab section for the walkthrough; this
folder holds the code, the recordings and the output to compare against.

## Learning Outcomes

- Compare format compliance rates for Levels 1, 2, and 4 format control.
- Implement a JSON schema extraction pipeline with Pydantic validation.
- Build a retry mechanism that automatically corrects format failures.

## Prerequisites

- Python 3.15
- Chapter 9, read through its Hands-on Lab
- **No API key required by default.** The lab replays 3 responses recorded from
  `gpt-6-sol` on 22 October 2026. Estimated API cost: **$0.00**.
- To run it against the real API instead, see "Running It Against the Real API" below.

## Setup

```bash
cd volume-2/chapter-09      # from the repository root
uv sync
```

## Running It

```bash
uv run python solution/lab.py     # the reference run, replaying the recordings
uv run python src/lab.py          # your copy, identical until you change it
```

Both files are the chapter's Lab Code with one change: they import `OpenAI` from
`nexoma_labs` (in `../shared/`) instead of from the `openai` package. That stand-in replays
the recorded responses, or calls the real API when you ask it to.

This lab is an experiment rather than an exercise in filling in code, so `src/lab.py` starts
as a full copy. Change its prompts and settings and compare the results with the reference.
The recordings cover only the prompts as printed, so once you change a prompt, run
`src/lab.py` in `live` mode (see below). `solution/lab.py` stays as the book prints it.

## Expected Result

The full output is in `expected/output.txt`.

In the recorded run (gpt-6-sol), all three postings were extracted into the `JobPosting` model: success rate 3/3. `is_remote` came out `True` for both remote postings and `False` for the New York office-only one, and the salary fields stayed `null` where no salary was stated. Two details are worth a second look. The lab prints a missing salary as `$None–$None`, so the printing, not the extraction, needs a fix. And the model filled `company` for posting 3 with "Remote-first company", a description rather than a name, which a stricter schema or instruction would catch.

## Verifying Your Work

```bash
uv run pytest
```

One test. It runs `solution/lab.py` against the recordings and checks that the output
matches `expected/output.txt` exactly. It always tests the reference, never
your `src/lab.py`: in this lab, checking your work means comparing your live results with
the expected pattern described above.

## Running It Against the Real API

With an `OPENAI_API_KEY` you can run the lab yourself. A full run makes 3 requests and
costs a few cents at most.

**Use `live` mode for your first run.** It calls the API and saves nothing, so your clone
stays exactly as shipped and `uv run pytest` keeps passing.

macOS or Linux:

```bash
export OPENAI_API_KEY=sk-...
NEXOMA_LAB_MODE=live uv run --group live python src/lab.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:NEXOMA_LAB_MODE = "live"
uv run --group live python src/lab.py
Remove-Item Env:NEXOMA_LAB_MODE     # back to replaying fixtures
```

`--group live` installs the OpenAI SDK, which fixture mode does not need. Expect your output
to differ from *Expected Result*: these are fresh answers from the model.

**`record` mode overwrites the bundled fixtures.** `NEXOMA_LAB_MODE=record` replaces them
with your responses, and the test that compares against `expected/output.txt` will then
fail. Restore the originals with `git checkout -- fixtures/`.

## If It Does Not Work

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FixtureMissing` error | A prompt, model or setting was changed, so no recording matches | Run your changed `src/lab.py` in `live` mode; `git checkout -- solution/lab.py` if you edited the reference |
| `ModuleNotFoundError: openai` | `--group live` left off the command | Add `--group live` to `uv run`, or stay in fixture mode |
| `live` or `record` mode fails with an auth error | No `OPENAI_API_KEY` set in this terminal | Set it as shown above, or stay in fixture mode — it needs nothing |
| `400 Unsupported value: 'temperature'` | `reasoning_effort="none"` removed from a call | Put it back: these models accept a temperature only with reasoning off |

## Files

| Path | Purpose |
|------|---------|
| `src/lab.py` | Your copy of the chapter's Lab Code, to change and run live |
| `solution/lab.py` | The chapter's Lab Code as printed, importing the recording client |
| `fixtures/` | Responses recorded from `gpt-6-sol`, replayed in fixture mode |
| `tests/test_lab.py` | Replays the recordings and compares the output with `expected/output.txt` |
| `expected/output.txt` | Output of the recorded run |
| `pyproject.toml` | Dependencies; the `live` group is only needed for `record`/`live` mode |
