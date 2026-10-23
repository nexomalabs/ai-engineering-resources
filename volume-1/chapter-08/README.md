# Volume I · Chapter 8 — Lab: Exploring Generative Models

## What You Will Build

An experiment that asks the same question five times at five different temperatures,
and measures how much the independent answers agree with each other. You will discover
that word-diversity *within* one sentence does not move with temperature — what moves is
how much five separate samples *diverge from each other*.

## Learning Outcomes

- Explain what temperature controls in sampling, and what it does not control.
- Measure output diversity across independent samples using Jaccard similarity.
- Explain why 0.0 is "closest to deterministic" rather than "deterministic."
- Read a cost report and connect sample count to API spend.
- Recognise when a within-sample metric is measuring the wrong thing.

## Prerequisites

- Python 3.15
- Chapter 8 read through §8.2
- **No API key required by default.** This lab replays recorded model responses.
  Estimated API cost to complete: **$0.00**.
- To run it against the real API instead, see "Running It Against the Real API" below.

## Setup

```bash
cd volume-1/chapter-08      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py
```

`src/lab.py` runs as supplied against the recorded fixtures, but the diversity metric is
a stub and `generate_samples` returns only one sample, so every row reads 0.000 with
1 distinct sample. Complete the two TODOs.

Reference implementation:

```bash
uv run python solution/lab.py
```

## Expected Result

Full output is in `expected/output.txt`:

```text
[OpenAI: replaying recorded fixtures, no API key needed]

  temp  distinct    cross-sample diversity
------------------------------------------
   0.0         2                     0.125
   0.3         5                     0.225
   0.7         5                     0.249
   1.0         5                     0.544
   1.4         5                     0.562
------------------------------------------

At temperature 0.0, 4 of 5 samples are identical.
At temperature 1.4, 5 of 5 samples are distinct.

Cross-sample diversity rises from 0.125 at T=0.0 to 0.562 at T=1.4.
```

**Look at the first row.** At T=0.0, four samples are word-for-word identical and the
fifth changes one clause. That is what "closest to deterministic, not guaranteed" means in
practice: the model almost always takes the same path, but not always.

**Read the trend, not single steps.** Diversity rises across the range, with the biggest
jump between 0.7 and 1.0. Five samples is a small number, so each estimate has real
variance; the direction across the full range is what the lab asks you to demonstrate.

**Why gpt-5.4-mini.** This lab needs a model that accepts a temperature. Reasoning models
such as gpt-6-luna accept only their default (1) and reject any other value with a
`400 Unsupported value` error, so the lab uses gpt-5.4-mini, a standard model.

**The metric itself is the harder lesson.** An earlier version of this lab measured
unique-word ratio *within* each single sentence, and that number stayed flat around
0.82–0.86 regardless of temperature — because any one well-formed sentence is lexically
dense whether it was sampled hot or cold. Temperature does not make a sentence use more
distinct words; it makes independent samples *disagree with each other more*. Only a
metric computed *across* samples — pairwise Jaccard similarity here — can see that.

## Verifying Your Work

```bash
uv run pytest
```

Twelve tests. `test_zero_temperature_samples_mostly_agree` checks the lab's first claim:
most T=0.0 samples match, without demanding that all of them do.
`test_diversity_rises_overall` checks the trend end-to-end rather than step-to-step,
because a stricter test would demand perfect monotonicity from only five samples.

## Running It Against the Real API

The bundled fixtures are real responses, recorded from gpt-5.4-mini on 22 October 2026.
With an `OPENAI_API_KEY` you can run the lab yourself. A full run is 25 short requests
and costs about one cent.

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
| Every row reads 0.000 | `cross_sample_diversity` still returns `0.0` | Complete TODO 1 |
| Every row shows 1 distinct sample | `generate_samples` returns a single-item list | Complete TODO 2, with a distinct `seed` per call |
| `FixtureMissing` error | A temperature or seed outside the bundled set | Only `TEMPERATURES` and `seed=0..4` are recorded |
| `ModuleNotFoundError: openai` | `--group live` left off the command | Add `--group live` to `uv run`, or stay in fixture mode |
| `live` or `record` mode fails with an auth error | No `OPENAI_API_KEY` set in this terminal | Set it as shown above, or stay in fixture mode — it needs nothing |

## Going Further

1. Raise `SAMPLES_PER_TEMPERATURE` to 20 in a `live` run. How many T=0.0 samples differ
   from the most common one?
2. Compute the within-sentence unique-word ratio yourself and confirm it stays flat. This
   is the metric the lab deliberately does not use — verify why for yourself.
3. Add a sixth temperature of 2.0, the highest gpt-5.4-mini accepts. Does diversity keep
   rising, or does output quality visibly break down first?
4. Set `MODEL = "gpt-6-luna"` and run in `live` mode. Read the error, and explain why a
   reasoning model would fix its own temperature.

## Files

| Path | Purpose |
|------|---------|
| `src/lab.py` | Your starting point — runs against fixtures, with two TODOs |
| `solution/lab.py` | Complete reference implementation |
| `fixtures/chapter-08/` | Responses recorded from gpt-5.4-mini, replayed in fixture mode |
| `tests/test_lab.py` | Runs against `solution/` in CI |
| `expected/output.txt` | Captured reference output |
| `pyproject.toml` | Dependencies; `live` group only needed for `record`/`live` mode |
