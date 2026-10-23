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
| 1 | [Build a Context Pipeline in Python](chapter-01/) | — | $0.00 | ✅ |
| 2 | [Context Window Manager](chapter-02/) | — | $0.00 | ✅ |
| 3 | [Three-Type Memory System](chapter-03/) | — | $0.00 | ✅ |
| 4 | [Minimal RAG System](chapter-04/) | embedding model (downloaded on first run) | $0.00 | ✅ |
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
| 16 | [Document Processing Workflow](chapter-16/) | — (stand-in model; live mode optional) | $0.00 | ✅ |
| 17 | [Agent Evaluation Suite](chapter-17/) | — (stand-in model; live mode optional) | $0.00 | ✅ |
| 18 | [Agent Security Layer](chapter-18/) | — (stand-in model; live mode optional) | $0.00 | ✅ |
| 19 | [Intelligent Research Assistant (Capstone)](chapter-19/) | — (stand-in model and embeddings; live mode optional) | $0.00 | ✅ |

Legend — ✅ packaged and passing tests · ⬜ not packaged yet.

Every lab runs with no API key. Labs 16–19 call a model in the chapter's code; here a
deterministic stand-in plays the model (and, in Lab 19, the embeddings), so the output is
the same on every run. Set `NEXOMA_LAB_MODE=live` and `OPENAI_API_KEY`, and add
`--group live` to `uv run`, to call the real API instead; each lab's README gives the
estimated cost.

Labs 4–7 download the `all-MiniLM-L6-v2` embedding model, about 90 MB, on first run. Their
`pyproject.toml` takes PyTorch from its CPU-only index, so `uv sync` does not fetch the
multi-gigabyte CUDA build, and selects Python 3.14, for which PyTorch publishes builds.
Labs 11–15 had no complete code in the book; their reference solutions were written from
the chapter's specification. Lab 19 is the capstone: `src/` is the chapter's starter, and
`solution/` completes its four integration points.
