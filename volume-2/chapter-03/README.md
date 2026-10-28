# Volume II · Chapter 3 — Lab: Instruction Engineering Workshop

## What You Will Build

The Hands-on Lab from Chapter 3, as printed in the book, running against recorded model
responses so it needs no API key. Follow the chapter's lab section for the walkthrough; this
folder holds the code, the recordings and the output to compare against.

## Learning Outcomes

- Score the three original instructions using the SMART framework.
- Rewrite each instruction to a Level 4 specification.
- Compare outputs from original and rewritten instructions.

## Prerequisites

- Python 3.15
- Chapter 3, read through its Hands-on Lab
- **No API key required by default.** The lab replays 6 responses recorded from
  `gpt-6-luna` on 22 October 2026. Estimated API cost: **$0.00**.
- To run it against the real API instead, see "Running It Against the Real API" below.

## Setup

```bash
cd volume-2/chapter-03      # from the repository root
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

In the recorded run (gpt-6-luna), the original instructions did not produce sloppy output; the model chose sensible formats on its own, such as a bulleted review summary and an email with an invented subject line and a `[Your Name]` placeholder. The engineered instructions produced exactly the formats they specified: a sentiment table labelled POSITIVE and NEGATIVE, an email that added no details beyond the original, and a JSON array with `metric`, `previous`, `current` and `change` fields that code can parse. The difference is not quality but predictability.

## Verifying Your Work

```bash
uv run pytest
```

One test. It runs `solution/lab.py` against the recordings and checks that the output
matches `expected/output.txt` exactly. It always tests the reference, never
your `src/lab.py`: in this lab, checking your work means comparing your live results with
the expected pattern described above.

## Running It Against the Real API

With an `OPENAI_API_KEY` you can run the lab yourself. A full run makes 6 requests and
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
| `fixtures/` | Responses recorded from `gpt-6-luna`, replayed in fixture mode |
| `tests/test_lab.py` | Replays the recordings and compares the output with `expected/output.txt` |
| `expected/output.txt` | Output of the recorded run |
| `pyproject.toml` | Dependencies; the `live` group is only needed for `record`/`live` mode |
