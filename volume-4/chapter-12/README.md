# Volume IV · Chapter 12 — Lab: Compliance Audit Checklist Runner

## What You Will Build

A compliance audit runner in three modules: `compliance_runner.py` defines controls, results and the profile of the AI system under audit; `nist_controls.py` holds a catalogue of fifteen controls grouped by the four NIST AI RMF functions; and `audit_runner.py` evaluates the profile, computes a severity-weighted compliance score, prints a gap report, and saves the results as JSON. A fourth module, `transparency.py`, adds the control from the chapter's opening story: an EU AI Act check, run on every deployment, that a chatbot's greeting says it is an AI and how to reach a person. Wren's original greeting, "Hi, I'm Wren!", fails it.

## Learning Outcomes

- Express compliance controls as data with automated evaluators.
- Score compliance by severity, so a missed critical control costs more than a low one.
- Report gaps, including partially met controls, for remediation.
- Treat an evaluator that fails as NOT_EVALUATED, never as compliant.
- Export audit results as JSON for an evidence trail.
- Turn one obligation, a chatbot's duty to say it is an AI, into a check that runs on every deployment.

## Prerequisites

- Python 3.15
- Chapter 12, read through its hands-on lab
- Dependencies: `tabulate`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (no model is called)

## Setup

```bash
cd volume-4/chapter-12      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/audit_runner.py          # your work
uv run python solution/audit_runner.py     # reference
```

`src/audit_runner.py` runs as supplied, but it scores every control equally (TODO 1) and leaves partial controls out of the gap report (TODO 2), so its score and gap count differ from the reference. TODO 3 is in `src/compliance_runner.py`; it does not change this demo's output, and the tests check it.

The run also writes `compliance_report.json` to the folder you run it from. The report's date is the day you run it.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

============================================================
  COMPLIANCE AUDIT REPORT
  System:  CustomerSupportBot v2.1.0
  Date:    2026-10-14
  Score:   74.0%
============================================================

Control ID    Category    Title                         Severity    Status
------------  ----------  ----------------------------  ----------  -------------
GV-1.1        GOVERN      AI Risk Management Policy     CRITICAL    COMPLIANT
GV-1.2        GOVERN      AI Risk Register              HIGH        COMPLIANT
GV-1.3        GOVERN      Designated AI Accountability  HIGH        NON_COMPLIANT
GV-1.4        GOVERN      AI Incident Response Plan     HIGH        COMPLIANT
MP-2.1        MAP         System Documentation          CRITICAL    PARTIAL
MP-2.2        MAP         AI Impact Assessment          CRITICAL    COMPLIANT
MP-2.3        MAP         Affected Groups Documented    MEDIUM      COMPLIANT
MS-3.1        MEASURE     Bias Evaluation               CRITICAL    COMPLIANT
MS-3.2        MEASURE     Performance Benchmarks        HIGH        COMPLIANT
MS-3.3        MEASURE     Adversarial Testing           HIGH        NON_COMPLIANT
MG-4.1        MANAGE      Audit Logging                 CRITICAL    PARTIAL
MG-4.2        MANAGE      Human Oversight               CRITICAL    COMPLIANT
MG-4.3        MANAGE      Rollback Procedure            HIGH        COMPLIANT
MG-4.4        MANAGE      Monitoring and Alerting       HIGH        COMPLIANT
MG-4.5        MANAGE      Data Provenance               HIGH        NON_COMPLIANT

============================================================
  GAP REPORT — 5 controls require attention
============================================================

  [HIGH] GV-1.3: Designated AI Accountability
  Status: NON_COMPLIANT

  [CRITICAL] MP-2.1: System Documentation
  Status: PARTIAL

  [HIGH] MS-3.3: Adversarial Testing
  Status: NON_COMPLIANT

  [CRITICAL] MG-4.1: Audit Logging
  Status: PARTIAL

  [HIGH] MG-4.5: Data Provenance
  Status: NON_COMPLIANT

Report saved to compliance_report.json
```

## The Greeting Check

```bash
uv run python src/transparency.py          # your work
uv run python solution/transparency.py     # reference
```

The reference prints (also saved in `expected/transparency.txt`):

```text
EU-50.1 Chatbot tells users it is an AI

  NON_COMPLIANT  before the mapping  Hi, I'm Wren!
  PARTIAL        a first fix         Hi, I'm Wren, Wrenfield's AI assistant. How can I help?
  COMPLIANT      after the mapping   Hi, I'm Wren, Wrenfield's AI assistant. To talk to a person instead, type 'agent' at any time.
  NOT_APPLICABLE customs pipeline    (no chat, so no greeting)
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, copy your files from `src/` over those in `solution/` there, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference. Five of the tests check the transparency control: the story's greeting fails, disclosing the AI without a route to a person is partial, the new greeting passes, a system that does not chat is not applicable, and words that merely contain "ai" are not a disclosure. With the four TODOs left in place, ten of the fourteen tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| `ModuleNotFoundError: No module named 'compliance_runner'` | Python cannot see the other two modules | Run the script by its path, `python src/audit_runner.py`, so its folder is on the path |
| `ModuleNotFoundError: No module named 'tabulate'` | Dependencies are not installed | Run `uv sync` in this folder |

## Going Further

- Add five EU AI Act controls, such as Annex IV documentation, human oversight and robustness testing (Lab Exercise 1).
- Double the weight of CRITICAL controls when the system's risk tier is `high` (Lab Exercise 2).
- Fill each result's `remediation` field with actionable guidance (Lab Exercise 3).
- Exclude NOT_APPLICABLE controls from the denominator instead of counting them as met, and compare the scores.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `compliance_runner.py`, `nist_controls.py`, `audit_runner.py`; runs, with 3 TODOs; `transparency.py` has TODO 4 |
| `solution/transparency.py` | The chatbot disclosure control from the chapter's story |
| `solution/` | Reference implementation of the same files |
| `tests/test_lab.py` | 14 tests, run against `solution/` |
| `expected/transparency.txt` | Captured output of `transparency.py` |
| `expected/output.txt` | Captured output of the reference |
