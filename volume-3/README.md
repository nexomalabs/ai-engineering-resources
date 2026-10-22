# Volume III — Laboratories

*Applied AI Engineering · Volume III: Context and Agents*

Every finished lab runs from a clean checkout and is tested in CI on every push.

**Python 3.15.** Install [uv](https://docs.astral.sh/uv/), then from any lab directory:

```bash
uv sync
uv run python src/lab.py     # your starting point
uv run pytest                # verify the reference solution
```

---

## Index

| Ch | Lab | Needs | API cost | Status |
|:--:|-----|-------|:--------:|:------:|
| 1 | Build a Context Pipeline in Python | live API | — | ⬜ |
| 2 | [Context Window Manager](chapter-02/) | — | $0.00 | ✅ |
| 3 | [Three-Type Memory System](chapter-03/) | — | $0.00 | ✅ |
| 4 | Minimal RAG System | embedding model, live API | — | ⬜ |
| 5 | [Vector Index with FAISS](chapter-05/) | embedding model (downloaded on first run) | $0.00 | ✅ |
| 6 | [Hybrid Retrieval System](chapter-06/) | embedding model (downloaded on first run) | $0.00 | ✅ |
| 7 | [Extractive Context Compression](chapter-07/) | embedding model (downloaded on first run) | $0.00 | ✅ |
| 8 | [Tool-Calling System](chapter-08/) | — | $0.00 | ✅ |
| 9 | [Multi-Step Function Calling Pipeline](chapter-09/) | — | $0.00 | ✅ |
| 10 | [MCP-Compatible Server](chapter-10/) | — | $0.00 | ✅ |
| 11 | [Build a ReAct Agent with Three Tools](chapter-11/) | — | $0.00 | ✅ |
| 12 | [Task Planning Agent](chapter-12/) | — | $0.00 | ✅ |
| 13 | [Agent Memory System with SQLite](chapter-13/) | — | $0.00 | ✅ |
| 14 | [Two-Agent Research Pipeline](chapter-14/) | — | $0.00 | ✅ |
| 15 | [Async Agent Communication System](chapter-15/) | — | $0.00 | ✅ |
| 16 | Document Processing Workflow | live API | — | ⬜ |
| 17 | Agent Evaluation Suite | live API | — | ⬜ |
| 18 | Agent Security Layer | live API | — | ⬜ |
| 19 | Intelligent Research Assistant (Capstone) | live API | — | ⬜ |

Legend — ✅ packaged and passing tests · ⬜ not packaged yet.

What the remaining labs need:

- **live API** — the lab calls a model. These labs will be added here with recorded responses,
  so that they too run with no API key. Until then, each chapter's Hands-on Lab section has the
  complete code.

Labs 5–7 (and Lab 4, once recorded) download the `all-MiniLM-L6-v2` embedding model, about
90 MB, on first run. Their `pyproject.toml` takes PyTorch from its CPU-only index, so
`uv sync` does not fetch the multi-gigabyte CUDA build. Labs 11–15 had no complete code in
the book; their reference solutions were written from the chapter's specification.
