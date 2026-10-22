# Volume IV — Laboratories

*Applied AI Engineering · Volume IV: Production Systems*

Every finished lab runs from a clean checkout and is tested in CI on every push.

**Python 3.15.** Install [uv](https://docs.astral.sh/uv/), then from any lab directory:

```bash
uv sync
uv run python src/<script>.py    # your starting point; each README names the script
uv run pytest                    # verify the reference solution
```

---

## Index

| Ch | Lab | Needs | API cost | Status |
|:--:|-----|-------|:--------:|:------:|
| 1 | Design a Production AI Architecture | design exercise, no code | — | — |
| 2 | System Design Document for an AI Document Analysis Service | design exercise | — | — |
| 3 | [Enterprise Document Review Workflow](chapter-03/) | — | $0.00 | ✅ |
| 4 | [Event-Driven Document Automation Pipeline](chapter-04/) | — | $0.00 | ✅ |
| 5 | Containerized AI API Service | Docker, live API | — | ⬜ |
| 6 | Inference Benchmark Harness | live API | — | ⬜ |
| 7 | Pipeline Profiling and Optimization | live API | — | ⬜ |
| 8 | Two-Level Cache System | live API | — | ⬜ |
| 9 | Security Middleware for FastAPI | live API (moderation) | — | ⬜ |
| 10 | PII Detection and Redaction Pipeline | live API; Presidio and a spaCy model | — | ⬜ |
| 11 | [Model Card, System Card, and Governance Validator](chapter-11/) | — | $0.00 | ✅ |
| 12 | [Compliance Audit Checklist Runner](chapter-12/) | — | $0.00 | ✅ |
| 13 | [Instrumenting an AI Service with Prometheus Metrics](chapter-13/) | — | $0.00 | ✅ |
| 14 | LLM-as-Judge Evaluation Pipeline | live API | — | ⬜ |
| 15 | [Cost Tracking and Optimization Dashboard](chapter-15/) | — | $0.00 | ✅ |
| 16 | [Request Queue Simulation with Autoscaling](chapter-16/) | — | $0.00 | ✅ |
| 17 | [Enterprise AI Adoption Roadmap](chapter-17/) | — | $0.00 | ✅ |
| 18 | Capstone: the series' four volumes integrated | integration project | — | — |

Legend — ✅ packaged and passing tests · ⬜ not packaged yet · — not a code lab.

What the remaining labs need:

- **live API** — the lab calls a model. These labs will be added here with recorded responses,
  so that they too run with no API key. Until then, each chapter's Hands-on Lab section has the
  complete code.
- **Docker** — Lab 5 builds a container image; its tests can cover the service, but the
  image build needs Docker in CI.
- **Presidio and a spaCy model** — Lab 10 downloads a spaCy language model on setup.
