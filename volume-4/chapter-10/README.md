# Volume IV · Chapter 10 — Lab: PII Detection and Redaction Pipeline

## What You Will Build

A pipeline that keeps personal data away from a model and out of what the model says: it redacts names, email addresses, phone numbers and Social Security numbers from the user's message, sends only the redacted text to the model, then redacts the model's answer too. It runs on ten test messages and compares two detectors: Microsoft Presidio, which uses a language model to find names, and the chapter's regular-expression fallback, which needs nothing installed.

## Learning Outcomes

- Redact both directions of a model call: the input before it leaves, the output before it is shown or stored.
- Measure a detector's recall per kind of PII, on test data whose answers you know.
- Explain what regular expressions catch (structured values) and what they cannot (names).
- Find a detector's gaps by testing it, then cover them with a second method.
- Use test data that belongs to no one: reserved SSNs, fictional phone numbers, example domains.

## Prerequisites

- Python 3.14. Presidio's spaCy dependencies did not build on Python 3.15 at the time of writing, so the lab's `.python-version` selects 3.14; `uv` installs it for you.
- Chapter 10, read through Section 10.3 and the hands-on lab
- Default path: the standard library only. **Estimated API cost: $0.00**
- Presidio (optional): `uv sync --group presidio` installs Presidio, spaCy and the `en_core_web_lg` model, about 600 MB in all.
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (ten short calls)

## Setup

```bash
cd volume-4/chapter-10      # from the repository root
uv sync                     # the default path
uv sync --group presidio    # optional: adds Presidio and its language model
```

## Running It

```bash
uv run python src/lab10_pipeline.py          # your work
uv run python solution/lab10_pipeline.py     # reference
```

Add `--group presidio` to `uv run` once it is installed: `uv run --group presidio python solution/lab10_pipeline.py`. Without Presidio the pipeline redacts with the regex fallback and compares only that; with it, it redacts with Presidio and compares both.

By default a stand-in answers instead of the model (`stand_in.py`). Its reply includes a support address, `support@example.com`, as a real assistant's reply often does, so the output-redaction step has something to find. `pii_presidio.py`, `pii_regex.py` and `scoring.py` are Section 10.3 and Step 5 as printed.

`src/` runs as supplied, but the regex fallback redacts nothing (TODO 1), and the score compares Presidio's label names with the fallback's without mapping them, so Presidio's email, phone and SSN detections never count (TODO 2). Complete both.

## Expected Result

With Presidio installed, the reference ends with the following (also saved in `expected/output-presidio.txt`; without Presidio, only the second row appears, as in `expected/output.txt`):

```text
Detector          recall  PERSON   EMAIL   PHONE     SSN
Presidio             89%    100%     75%    100%    100%
regex fallback       71%      0%    100%    100%    100%
```

Each detector misses what the other finds. The regex fallback catches every structured value and no names, as the chapter predicts; a pattern cannot tell "James O'Brien" from any other two words. Presidio finds every name, but misses one of the four email addresses, `accounts@contoso.example`. Its email recogniser checks the domain against the list of real top-level domains, and `.example` is reserved, not real. The regex has no such check. In production, run both, or test your detector on the PII your users actually send.

Every redacted message reaches the model without its PII, and every reply has the support address replaced with `[EMAIL]`.

## Verifying Your Work

```bash
uv run pytest                       # 9 tests; the Presidio test is skipped
uv run --group presidio pytest      # all 10
```

The tests check that the fallback redacts whole values (including numbers that begin with `(` or `+1`), leaves names and plain text alone, maps Presidio's labels before scoring, reaches the chapter's recall on the dataset, sends only redacted input to the model and redacts its output, and, with Presidio, detects a name. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| Nothing is redacted | TODO 1: the fallback loop is empty | Substitute each pattern's matches with `[LABEL]` |
| Presidio scores 0% for email, phone and SSN | TODO 2: `EMAIL_ADDRESS` is compared with `EMAIL` | Map labels through `LABELS` first |
| A phone number becomes `([PHONE]` or `+[PHONE]` | The pattern starts with `\b`, which never matches before `(` or `+` | Start it with `(?<!\w)`, as the chapter now does |
| `OSError: [E050] Can't find model 'en_core_web_lg'` | The model was not installed | Run `uv sync --group presidio` |
| Presidio fails to install on Python 3.15 | spaCy's dependencies have no 3.15 build yet | Keep `.python-version` at 3.14 |

## Going Further

- Add a custom Presidio recognizer for street addresses, which neither detector catches; Section 10.3's third sample shows the gap.
- Replace redaction with consistent pseudonyms (`[PERSON_1]`, `[PERSON_2]`), so the model can still tell people apart.
- Measure precision as well as recall: write inputs that look like PII but are not, and count false alarms.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `pii_regex.py` and `scoring.py` have a TODO each |
| `solution/lab10_pipeline.py` | Steps 1, 3, 4 and 5 |
| `solution/pii_presidio.py`, `solution/pii_regex.py` | Section 10.3: Presidio redaction and the regex fallback |
| `solution/scoring.py` | Step 5: recall on comparable labels |
| `solution/dataset.py` | Step 2: ten messages and the PII in each |
| `solution/stand_in.py` | The stand-in for the model |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
| `expected/output.txt`, `expected/output-presidio.txt` | Captured output, without and with Presidio |
