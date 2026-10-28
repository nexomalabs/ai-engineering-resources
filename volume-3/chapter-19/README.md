# Volume III · Chapter 19 — Lab: Intelligent Research Assistant (Capstone)

## What You Will Build

A research assistant that integrates the volume's techniques in one program: semantic retrieval over a document corpus (Chapter 4), episodic memory of past sessions (Chapter 13), tools (Chapter 8), a ReAct agent loop (Chapter 11), and the security layer and hash-chained audit log (Chapter 18). The chapter gives a working starter; the capstone asks you to complete four integration points: a token budget for retrieved context, memory deduplication, a ten-case evaluation suite, and a short architecture document.

## Learning Outcomes

- Wire retrieval, memory, tools, an agent loop and security checks into one request path.
- Enforce a token budget on retrieved context, best passage first.
- Keep memory from repeating what retrieval already supplied.
- Evaluate the whole system on task completion, tool-use accuracy and step efficiency.
- Describe the system's components, data flow and design trade-offs in an architecture document.

## Prerequisites

- Python 3.15
- Chapter 19, read through its hands-on lab; Chapters 4, 11, 13, 17 and 18 for the parts it combines
- Dependencies: `numpy`, installed by `uv sync`
- Default mode: no API key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.05 per run** with `gpt-6-luna` and `text-embedding-3-small`

## Setup

```bash
cd volume-3/chapter-19      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/research_assistant.py          # the chapter's starter: your work
uv run python solution/research_assistant.py     # reference: demo, then the evaluation
```

Both write `capstone_audit_log.json` in the current folder. By default a stand-in replaces the API (`stand_in.py`). It provides deterministic embeddings (a hashed bag of words: it matches words, not meaning) and a rule-based agent: arithmetic goes to the calculator, "tell me more about" goes to web search, a question about how two things relate reads the top document, and anything else is answered from the top retrieved passage.

`src/research_assistant.py` is the chapter's starter, and it runs as supplied: all five demo queries get an answer, and the injection attempt is blocked. The capstone is the four integration points the chapter lists. The reference completes them:

1. `_build_rag_context()` keeps retrieved passages within 2,000 tokens, best first, truncating the passage that crosses the limit or dropping it when too little room is left.
2. `_overlaps_rag()` drops a recalled memory whose embedding matches a retrieved passage above 0.85 cosine similarity.
3. `run_evaluation()` runs ten cases and reports completion, tool-use accuracy and step efficiency.
4. `ARCHITECTURE.md` is the system architecture document, with a Mermaid component diagram.

For live mode, set your key and the mode, and add `--group live`, which installs the OpenAI
SDK that the default mode does not need.

macOS or Linux:

```bash
export OPENAI_API_KEY=sk-...
NEXOMA_LAB_MODE=live uv run --group live python solution/research_assistant.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:NEXOMA_LAB_MODE = "live"
uv run --group live python solution/research_assistant.py
Remove-Item Env:NEXOMA_LAB_MODE     # back to the stand-in
```

## Expected Result

The demo answers the Transformer question from the retrieved passage, computes 2 to the power of 16 with the calculator (`The result is 65536.0.`), adds a web search to the RAG question, blocks the injection, and reads the vector-database document for the last question. The reference then prints its evaluation (full output in `expected/output.txt`):

```text
✗ E10  tool=ok     steps=1/1  Prompt engineering is the practice of designing inputs to language mod
----------------------------------------------------------------------
Task completion rate: 90.0%
Tool use accuracy:    100.0%
Step efficiency:      100.0%
Failures:             ['E10']
```

E10 asks for the capital of Australia, which the corpus cannot answer. The assistant should say the information is not available; instead it answers from whichever passage ranked first. It has no minimum relevance score, and the evaluation is what exposes that. Fixing it is the first item under *Going Further*. Timings in the demo output change on every run. In live mode the answers come from the model.

## Verifying Your Work

```bash
uv run pytest
```

Nine tests: the calculator's allow-list, the security helpers, the audit chain, retrieval ranking, three demo queries end to end, the context budget (truncate, then drop), score ordering, memory deduplication, and the evaluation report. They run against `solution/`, which is what CI checks. To test your own integration points, copy this folder somewhere else, copy your `src/research_assistant.py` over the one in `solution/` there, and run `uv run pytest`. The tests expect the reference's names (`_build_rag_context(passages, token_budget=...)`, `_overlaps_rag`, `run_evaluation`) and a `tools_used` list in each query result.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: numpy` | Dependencies not installed | Run `uv sync` |
| Answers ignore a document you added to the corpus | The index is built once, on an orchestrator's first query | Create a new `ResearchAssistantOrchestrator` after editing `DOCUMENT_CORPUS` |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |
| Live mode fails with an auth error | No `OPENAI_API_KEY` in this terminal | Set it, or stay in the default mode |
| `400 Unsupported value: 'temperature'` in live mode | `reasoning_effort="none"` was removed from the agent's call | Put it back: gpt-6-luna accepts a temperature only with reasoning off |

## Going Further

- Add a minimum retrieval score and answer "That information is not available" below it; E10 should then pass.
- Count tokens with a tokenizer instead of the four-characters estimate.
- Persist episodic memory to SQLite, as in Chapter 13's lab, so it survives restarts.

## Files

| Path | Purpose |
|---|---|
| `src/research_assistant.py` | The chapter's starter, with the mode switch where the client is created |
| `src/stand_in.py`, `solution/stand_in.py` | The stand-in for the model and the embeddings |
| `solution/research_assistant.py` | Reference: the starter with integration points 1–3 completed |
| `solution/ARCHITECTURE.md` | Integration point 4: the system architecture document |
| `tests/test_lab.py` | 9 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
