# Volume II — Laboratories

*Applied AI Engineering · Volume II: Prompt Engineering*

Every finished lab runs from a clean checkout and is tested in CI on every push.

**Python 3.15.** Install [uv](https://docs.astral.sh/uv/), then from any lab directory:

```bash
uv sync
uv run python src/lab.py       # your starting point (labs 17-20)
uv run python solution/lab.py  # the reference solution
uv run pytest                  # verify the reference solution
```

---

## Index

| Ch | Lab | Type | API cost | Status |
|:--:|-----|------|:--------:|:------:|
| 1 | [Establishing Your Prompt Engineering Baseline](chapter-01/) | Engineering | $0.00 (fixtures) | ✅ |
| 2 | [Prompt Anatomy Dissection and Construction](chapter-02/) | Engineering | $0.00 (fixtures) | ✅ |
| 3 | [Instruction Engineering Workshop](chapter-03/) | Engineering | $0.00 (fixtures) | ✅ |
| 4 | [Context Design: Relevance Filtering and Injection Defense](chapter-04/) | Engineering | $0.00 (fixtures) | ✅ |
| 5 | [Role Prompting: Expert Comparison and Voice Analysis](chapter-05/) | Engineering | $0.00 (fixtures) | ✅ |
| 6 | [Few-Shot Engineering: Label Balance and Selection](chapter-06/) | Engineering | $0.00 (fixtures) | ✅ |
| 7 | [Chain-of-Thought: Implementation and Faithfulness Testing](chapter-07/) | Engineering | $0.00 (fixtures) | ✅ |
| 8 | [Building a Structured Prompt Template System](chapter-08/) | Engineering | $0.00 (fixtures) | ✅ |
| 9 | [Output Control: Schema Enforcement and Validation](chapter-09/) | Engineering | $0.00 (fixtures) | ✅ |
| 10 | [Reasoning Strategies: Comparative Implementation](chapter-10/) | Engineering | $0.00 (fixtures) | ✅ |
| 11 | [Building a Multi-Metric Evaluation Pipeline](chapter-11/) | Engineering | $0.00 (fixtures) | ✅ |
| 12 | [Manual Optimization with OPRO-Style Meta-Prompting](chapter-12/) | Engineering | $0.00 (fixtures) | ✅ |
| 13 | [Building an Automated Prompt Test Suite](chapter-13/) | Engineering | $0.00 (fixtures) | ✅ |
| 14 | [Systematic Prompt Debugging](chapter-14/) | Engineering | $0.00 (fixtures) | ✅ |
| 15 | [Pattern Application Workshop](chapter-15/) | Engineering | $0.00 (fixtures) | ✅ |
| 16 | [Anti-Pattern Identification and Refactoring](chapter-16/) | Engineering | $0.00 (fixtures) | ✅ |
| 17 | [Build a Three-Pattern Prompt Framework](chapter-17/) | Engineering | $0.00 | ✅ |
| 18 | [Design and Implement a Prompt Library in Python](chapter-18/) | Engineering | $0.00 | ✅ |
| 19 | [Review Board vs. Single-Prompt Review](chapter-19/) | Engineering | $0.00 | ✅ |
| 20 | [Customer Support AI Prompt Engineering Workflow](chapter-20/) | Capstone | $0.00 | ✅ |

Legend — ✅ packaged and passing tests · ⬜ not packaged yet.

Labs 17–20 run with a deterministic mock model, so they need no API key.

Labs 1–16 call a model. Each one replays responses recorded from gpt-6-luna and gpt-6-sol on
22 October 2026, so it too runs with no API key, and its `solution/lab.py` is the chapter's
Lab Code with one changed import. Each lab's README shows how to run it against the real API.
