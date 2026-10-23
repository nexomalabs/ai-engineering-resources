# Volume I · Chapter 9 — Lab: Comparing LLM vs. Reasoning Models

## What You Will Build

The same three multi-step math problems run under three conditions — a standard model
answering directly, the same model with chain-of-thought prompting, and a reasoning
model — scored for accuracy and compared for token cost.

## Learning Outcomes

- Explain why a direct answer to a multi-step problem fails silently.
- Explain what chain-of-thought prompting changes, and what it costs.
- Explain where a reasoning model's hidden tokens go, and why you pay for them.
- Build a simple automated accuracy check and know its limits.
- State the actual cost/accuracy trade-off between the three approaches, in numbers.

## Prerequisites

- Python 3.15
- Chapter 9 read through §9.2
- **No API key required by default.** This lab replays recorded model responses.
  Estimated API cost to complete: **$0.00**.

## Setup

```bash
cd volume-1/chapter-09      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py
```

`src/lab.py` runs as supplied against the fixtures, but `check_accuracy` always returns
`False`, so every condition reports 0/3. Complete the one TODO.

Reference implementation:

```bash
uv run python solution/lab.py
```

## Expected Result

Full output is in `expected/output.txt`. The summary:

```text
Accuracy over 3 problems:
  direct     2/3
  cot        3/3
  reasoning  3/3
```

**Direct fails where a step is hidden.** Asked for "only the final answer," gpt-5.4-mini
gets the probability and work-rate problems right, but answers the train problem with a
confident 2:30 PM instead of 3:13 PM. That is the problem with a trap in it: the first
train's one-hour head start. With no work shown, nothing catches the skipped step.

**Chain-of-thought fixes it, visibly.** Writing out its steps, the same model accounts for
the head start and reaches 3:13 PM. You can read every step, and you pay for every one:
440 tokens on P1, against 101 for the direct answer.

**The reasoning model gets all three right without being asked to show work**, but it
thinks before it answers. On P1, gpt-6-luna spent **128 hidden reasoning tokens** behind a
33-word answer. You are billed for those tokens and never see them. On this problem set it
used fewer tokens in total than chain-of-thought (267 against 440 on P1), but the two
models are priced differently, so compare prices per token before deciding which is
cheaper.

**The accuracy check reads LaTeX.** Current models often write fractions as
`\frac{2}{15}`. `plain_fractions()` rewrites them as `2/15` first, otherwise a correct
answer would be scored wrong. Automated checks need maintaining as model output changes.

## Verifying Your Work

```bash
uv run pytest
```

Fourteen tests. `test_direct_answer_misses_the_train_problem` and
`test_reasoning_model_gets_everything_right` check the lab's two clean claims directly.
`test_chain_of_thought_beats_direct` checks that writing out the steps scores higher than
answering directly.

## A Note on Model Names

The lab uses **gpt-5.4-mini** as the standard model and **gpt-6-luna** as the reasoning
model. gpt-6-luna accepts only its default temperature, so `call_reasoning` sends none.
Model lineups change between releases. If either model is retired, set `MODEL_STANDARD` to
a current model that accepts `temperature=0.0`, and `MODEL_REASONING` to a current
reasoning model, then record new fixtures.

## Running It Against the Real API

The bundled fixtures are real responses, recorded from gpt-5.4-mini and gpt-6-luna on
22 October 2026. With an `OPENAI_API_KEY` you can run the lab yourself. A full run is nine
requests and costs well under $0.05.

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
| Every condition reports 0/3 | `check_accuracy` still returns `False` | Complete TODO 1 |
| `FixtureMissing` error | Problem text or mode does not match a bundled fixture exactly | Use the three `PROBLEMS` as given; do not edit their text |
| `check_accuracy` reports a false positive | Matching on a digit substring that also appears elsewhere | See `test_partial_digit_overlap_is_not_a_false_positive` for the boundary case |
| `live` or `record` mode: `NotImplementedError` | The starter's `call_reasoning` has no live path | Run `solution/lab.py` against the real API, not `src/lab.py` |
| `400 Unsupported value: 'temperature'` | `MODEL_STANDARD` is set to a reasoning model | Use a standard model that accepts a temperature, such as gpt-5.4-mini |
| `ModuleNotFoundError: openai` | `--group live` left off the command | Add `--group live` to `uv run`, or stay in fixture mode |
| `live` or `record` mode fails with an auth error | No `OPENAI_API_KEY` set in this terminal | Set it as shown above, or stay in fixture mode — it needs nothing |

## Going Further

1. Write a stricter `check_accuracy` that requires the exact answer format rather than a
   digit substring. Does it change any of the three tallies?
2. Add a fourth problem of your choosing. Predict which condition will fail before running
   it, in `record` mode, against a real account.
3. Estimate the dollar cost of the reasoning condition across all three problems using
   `nexoma_labs.costs`, and compare it against running all three problems through the
   chain-of-thought condition three times each, majority-voting the answer. Which is
   cheaper for the same accuracy?

## Files

| Path | Purpose |
|------|---------|
| `src/lab.py` | Your starting point — runs against fixtures, with one TODO |
| `solution/lab.py` | Complete reference implementation |
| `fixtures/chapter-09/` | Responses recorded from gpt-5.4-mini and gpt-6-luna, replayed in fixture mode |
| `tests/test_lab.py` | Runs against `solution/` in CI |
| `expected/output.txt` | Captured reference output |
| `pyproject.toml` | Dependencies; `live` group only needed for `record`/`live` mode |
