# Volume II — Laboratories

*Applied AI Engineering · Volume II: Prompt Engineering*

Every finished lab runs from a clean checkout and is tested in CI on every push.

**Python 3.15.** Install [uv](https://docs.astral.sh/uv/), then from any lab directory:

```bash
uv sync
uv run python src/lab.py     # your starting point
uv run pytest                # verify the reference solution
```

---

## Index

| Ch | Lab | Type | API cost | Status |
|:--:|-----|------|:--------:|:------:|
| 1 | Establishing Your Prompt Engineering Baseline | Engineering | live API | ⬜ |
| 2 | Prompt Anatomy Dissection and Construction | Engineering | live API | ⬜ |
| 3 | Instruction Engineering Workshop | Engineering | live API | ⬜ |
| 4 | Context Design: Relevance Filtering and Injection Defense | Engineering | live API | ⬜ |
| 5 | Role Prompting: Expert Comparison and Voice Analysis | Engineering | live API | ⬜ |
| 6 | Few-Shot Engineering: Label Balance and Selection | Engineering | live API | ⬜ |
| 7 | Chain-of-Thought: Implementation and Faithfulness Testing | Engineering | live API | ⬜ |
| 8 | Building a Structured Prompt Template System | Engineering | live API | ⬜ |
| 9 | Output Control: Schema Enforcement and Validation | Engineering | live API | ⬜ |
| 10 | Reasoning Strategies: Comparative Implementation | Engineering | live API | ⬜ |
| 11 | Building a Multi-Metric Evaluation Pipeline | Engineering | live API | ⬜ |
| 12 | Manual Optimization with OPRO-Style Meta-Prompting | Engineering | live API | ⬜ |
| 13 | Building an Automated Prompt Test Suite | Engineering | live API | ⬜ |
| 14 | Systematic Prompt Debugging | Engineering | live API | ⬜ |
| 15 | Pattern Application Workshop | Engineering | live API | ⬜ |
| 16 | Anti-Pattern Identification and Refactoring | Engineering | live API | ⬜ |
| 17 | [Build a Three-Pattern Prompt Framework](chapter-17/) | Engineering | $0.00 | ✅ |
| 18 | [Design and Implement a Prompt Library in Python](chapter-18/) | Engineering | $0.00 | ✅ |
| 19 | [Review Board vs. Single-Prompt Review](chapter-19/) | Engineering | $0.00 | ✅ |
| 20 | [Customer Support AI Prompt Engineering Workflow](chapter-20/) | Capstone | $0.00 | ✅ |

Legend — ✅ packaged and passing tests · ⬜ not packaged yet.

Labs 17–20 run with a deterministic mock model, so they need no API key.

Labs 1–16 (marked ⬜) call a model. They will be added here with recorded responses, so that
they too run with no API key. Until then, each chapter's Hands-on Lab section has the
complete code.
