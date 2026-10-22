# Volume IV · Chapter 17 — Lab: Enterprise AI Adoption Roadmap

## What You Will Build

A three-year AI adoption roadmap for MediCore Analytics, a hypothetical healthcare analytics company, built from a reusable template. Each initiative records its category, quarters, owner, cost estimate, risk, success metric and dependencies; the report groups them by year and totals the investment from the estimates.

## Learning Outcomes

- Sequence a roadmap from foundation (governance, literacy, data) to differentiation.
- Give every initiative an owner, a measurable success metric and its dependencies.
- Derive totals from the data, so they stay right when the roadmap changes.
- Present quarters within each year of a multi-year plan.

## Prerequisites

- Python 3.15
- Chapter 17, read through its hands-on lab
- Dependencies: `tabulate`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (no model is called)

## Setup

```bash
cd volume-4/chapter-17      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but Year 2 shows timelines such as Q5–Q7 (TODO 2), and the total investment is $0.00M because no estimate is converted (TODO 1).

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

======================================================================
  MEDICORE ANALYTICS — 3-YEAR AI ADOPTION ROADMAP
======================================================================

──────────────────────────────────────────────────────────────────────
  YEAR 1: FOUNDATION
──────────────────────────────────────────────────────────────────────
Initiative                                  Category    Timeline    Owner                Cost    Risk
------------------------------------------  ----------  ----------  -------------------  ------  ------
AI Governance Framework                     Governance  Q1–Q2       Legal + Engineering  $80K    Low
AI Literacy Program                         People      Q1–Q4       HR + AI Team         $120K   Low
Data Foundation Upgrade                     Technology  Q1–Q4       Data Engineering     $350K   Medium
Pilot: AI Clinical Documentation Assistant  Process     Q3–Q4       Product              $200K   High

  [AI Governance Framework]
  Goal: Establish AI policy, risk register, designated AI officer, and incident response procedures. Adopt NIST AI RMF profile.
  Success: AI governance policy approved; AI officer designated; risk register operational

  [AI Literacy Program]
  Goal: Training for all 500 employees on AI fundamentals, appropriate use, and risk awareness. Advanced training for 50 power users.
  Success: 90% completion rate; power users certified

  [Data Foundation Upgrade]
  Goal: Implement data catalog, data lineage tracking, and HIPAA-compliant data access controls. Prerequisite for AI use with PHI.
  Success: Data catalog covers 100% of clinical datasets; HIPAA audit passed
  Depends on: AI Governance Framework

  [Pilot: AI Clinical Documentation Assistant]
  Goal: Pilot AI-assisted clinical note summarization for 5 hospital clients. Measure time savings and clinician satisfaction.
  Success: 20% reduction in documentation time; NPS > 40
  Depends on: Data Foundation Upgrade, AI Governance Framework


──────────────────────────────────────────────────────────────────────
  YEAR 2: INTEGRATION
──────────────────────────────────────────────────────────────────────
Initiative                         Category    Timeline    Owner             Cost    Risk
---------------------------------  ----------  ----------  ----------------  ------  ------
AI Platform Build                  Technology  Q1–Q3       AI Platform Team  $600K   Medium
Patient Risk Stratification Model  Technology  Q2–Q4       Data Science      $450K   High
Evaluation and Quality Program     Governance  Q1–Q2       AI Team           $150K   Low

  [AI Platform Build]
  Goal: Build internal AI platform: LLM gateway, evaluation pipeline, cost tracking, monitoring dashboard, prompt registry.
  Success: Platform serving 3+ products; evaluation running continuously; cost visibility for all teams
  Depends on: Pilot: AI Clinical Documentation Assistant

  [Patient Risk Stratification Model]
  Goal: Deploy AI-powered patient risk stratification into clinical analytics dashboards, after independent model validation.
  Success: AUC > 0.82; validated for 3 clinical outcomes; deployed to 20 hospital clients
  Depends on: AI Platform Build, Data Foundation Upgrade

  [Evaluation and Quality Program]
  Goal: Implement LLM-as-Judge evaluation, A/B testing infrastructure, and quality gates in CI/CD for all AI products.
  Success: 100% of AI deployments pass quality gate; weekly quality reports published
  Depends on: AI Platform Build


──────────────────────────────────────────────────────────────────────
  YEAR 3: DIFFERENTIATION
──────────────────────────────────────────────────────────────────────
Initiative                     Category    Timeline    Owner                          Cost    Risk
-----------------------------  ----------  ----------  -----------------------------  ------  ---------
Clinical Trial AI Automation   Process     Q1–Q3       Clinical Affairs + AI Team     $800K   Very High
Proprietary Clinical AI Model  Technology  Q2–Q4       Data Science + Infrastructure  $1.2M   High

  [Clinical Trial AI Automation]
  Goal: AI-powered clinical trial data extraction, validation, and regulatory submission package preparation.
  Success: 50% reduction in trial data processing time; FDA submission package generation validated
  Depends on: AI Platform Build, Evaluation and Quality Program

  [Proprietary Clinical AI Model]
  Goal: Fine-tune an open-source base model on MediCore's proprietary clinical data. Deploy on sovereign infrastructure.
  Success: Model outperforms GPT-6.1 Sol on MediCore clinical benchmarks; fully on-premises deployment
  Depends on: Patient Risk Stratification Model, Evaluation and Quality Program

──────────────────────────────────────────────────────────────────────
  Total estimated investment: ~$3.95M over 3 years
──────────────────────────────────────────────────────────────────────
```

## Verifying Your Work

```bash
uv run pytest
```

The tests run against `solution/`, which is what CI checks. To test your own version, copy
this folder somewhere else, replace `solution/lab.py` there with your `src/lab.py`, and run
`uv run pytest`. Every test passing means your TODOs behave like the reference.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv), or create a virtual environment with `python -m venv .venv` and `pip install -e .` |
| `requires-python >=3.12` error | An older Python is active | Install Python 3.12 or later; `uv python install 3.12` does this |
| Install fails with "path not found" on Windows | The folder path is longer than Windows' 260-character limit | Clone the repository to a short path such as `C:\labs` |
| The total is wrong after you add an initiative | Its `estimated_cost` is in a format `parse_cost` does not read | Write estimates as `$80K` or `$1.2M`, or `TBD` |
| `UnicodeEncodeError` printing `─` or `—` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Rewrite the roadmap for a bank with 2,000 employees, focused on fraud detection, customer service and regulatory reporting (Lab Exercise 1).
- Draw the initiatives as a Gantt chart with matplotlib (Lab Exercise 2).
- Compute the critical path through the dependencies (Lab Exercise 3).
- Check that no initiative starts before the initiatives it depends on, and decide which overlaps in this roadmap are deliberate.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 2 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 9 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
