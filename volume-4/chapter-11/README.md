# Volume IV · Chapter 11 — Lab: Model Card, System Card, and Governance Validator

## What You Will Build

Governance documentation for a hypothetical enterprise AI assistant: a model card for EnterpriseAssist-7B, a system card for the help desk service built on it, and a Python validator that checks both contain every required section before deployment. The validator also holds the launch review from the chapter's opening story: it asks of a system card who owns the feature, what it may promise and who is called at two in the morning, and approves Wren's late-delivery vouchers only once their card answers all three.

## Learning Outcomes

- Write a model card: model details, intended and out-of-scope use, training data, evaluation, performance, ethical considerations and limitations.
- Write a system card: the deployed service, its safety evaluations, safeguards, usage policy, monitoring, limitations and escalation path.
- Automate a documentation gate that a deployment pipeline can run.
- Check structure, not keywords: a word in a paragraph is not a section.
- Hold a launch to an accountable owner, a written cap on what the system may promise, and a contact at any hour.

## Prerequisites

- Python 3.15
- Chapter 11, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (no model is called)

## Setup

```bash
cd volume-4/chapter-11      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/governance_validator.py          # your work
uv run python solution/governance_validator.py     # reference
```

`src/governance_validator.py` runs as supplied and checks the cards in `src/`. It reports PASS, although `src/system_card.md` is unfinished (TODO 2): the TODO comment in that card names every required section, and the starter accepts a name anywhere in the text. That false pass is what TODO 1 fixes. Once only headings count, the validator reports the missing sections until you complete the card.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
=== model_card.md ===
Pass rate: 100% (8/8 sections)
All required sections present.

=== system_card.md ===
Pass rate: 100% (7/7 sections)
All required sections present.

Overall: PASS

=== Launch review: voucher_card_draft.md ===
  Who owns this if it goes wrong?        NO ANSWER
  What may the system promise?           NO ANSWER
  Who is called at two in the morning?   NO ANSWER
Launch: WAIT: the card does not answer every question

=== Launch review: voucher_system_card.md ===
  Who owns this if it goes wrong?        Sam Whitlock, product manager
  What may the system promise?           Wren may offer one voucher per late parcel, worth at most £10; Wren ...
  Who is called at two in the morning?   Wrenfield AI on-call engineer, 020 7946 0018, at any hour
Launch: APPROVED
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. Four of the tests check the launch review: the draft voucher card answers none of the questions, the finished card names an owner, a £10 cap and a contact at any hour, a card missing only its night contact waits, and the finished card passes the section check too. With the TODOs left in place, three of the eleven tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `FileNotFoundError: ... model_card.md` | The cards are not next to the script | Keep `model_card.md` and `system_card.md` in the same folder as the validator |
| A section you wrote is reported missing | It is in the text but not a heading, or the heading uses different words | Give it its own heading, such as `## Escalation` |

## Going Further

- Check that each required section has content, not just a heading.
- Validate the front matter: require `model_name`, `version` and `date`, and check the version matches the one in the title.
- Run the validator in CI, and fail the build when either card falls below 100%.
- Add a third document, the usage policy from Section 11.5, with its own required sections.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `governance_validator.py`, `model_card.md`, `system_card.md`; runs, with 3 TODOs (TODO 4 is the launch decision) |
| `solution/voucher_card_draft.md`, `solution/voucher_system_card.md` | The voucher feature's system card, as first proposed and as approved |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
