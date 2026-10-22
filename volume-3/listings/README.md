# Volume III — Code Listings

Every code example and prompt of 12 lines or more from *Applied AI Engineering, Volume
III*, so you can copy it instead of typing it. Each file is named after the section it
comes from: `2.3-token-counting.py` is from Section 2.3 of Chapter 2. Labs that have their
own folder in this volume are not repeated here; open the lab folder instead.

**Running a Python listing.** From the repository root, add the packages in its **Needs**
column. For example:

```bash
uv run --with tiktoken python volume-3/listings/chapter-01/context_pipeline.py
```

The **Runs** column says what else it needs:

- **on its own**: runs as it is.
- **after `x.py`**: builds on an earlier listing in the same chapter. Paste that listing
  above this one, or run them together in one file.
- **with the other files in `src/`**: one file of a small application; the chapter's lab
  shows how to run it.
- **sketch: see the text**: a fragment that shows one idea; the section explains what
  surrounds it.

Listings marked `OPENAI_API_KEY` call the OpenAI API and need a key in your environment.
Listings marked `CUDA GPU` need an NVIDIA graphics card.

## Chapter 1 — Introduction to Context Engineering

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| Lab | [`context_pipeline.py`](chapter-01/context_pipeline.py) | 17 | `tiktoken` | on its own |
| Lab | [`lab-implement-the-context-pipeline.py`](chapter-01/lab-implement-the-context-pipeline.py) | 91 | — | after `context_pipeline.py` |
| Lab | [`lab-populate-the-pipeline-with-mock-data.py`](chapter-01/lab-populate-the-pipeline-with-mock-data.py) | 107 | — | after `context_pipeline.py`, `lab-implement-the-context-pipeline.py` |

## Chapter 2 — Context Windows

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 2.3 | [`2.3-token-counting.py`](chapter-02/2.3-token-counting.py) | 33 | `tiktoken` | on its own |

## Chapter 4 — Retrieval-Augmented Generation (RAG)

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| Lab | [`rag_system.py`](chapter-04/rag_system.py) | 67 | `numpy`, `sentence-transformers` | on its own |
| Lab | [`lab-implement-the-indexing-pipeline.py`](chapter-04/lab-implement-the-indexing-pipeline.py) | 25 | — | after `rag_system.py` |
| Lab | [`lab-implement-the-retrieval-pipeline.py`](chapter-04/lab-implement-the-retrieval-pipeline.py) | 25 | — | after `lab-implement-the-indexing-pipeline.py`, `rag_system.py` |
| Lab | [`lab-implement-the-generation-pipeline.py`](chapter-04/lab-implement-the-generation-pipeline.py) | 97 | `OPENAI_API_KEY` | after `lab-implement-the-indexing-pipeline.py`, `lab-implement-the-retrieval-pipeline.py`, `rag_system.py` |

## Chapter 6 — Knowledge Retrieval

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 6.3 | [`6.3-bm25-and-keyword-search.py`](chapter-06/6.3-bm25-and-keyword-search.py) | 35 | `numpy`, `rank-bm25` | on its own |
| 6.4 | [`6.4-dense-retrieval-with-embeddings.py`](chapter-06/6.4-dense-retrieval-with-embeddings.py) | 44 | `faiss-cpu`, `numpy`, `sentence-transformers` | on its own |
| 6.6 | [`6.6-query-expansion.py`](chapter-06/6.6-query-expansion.py) | 27 | — | on its own |
| 6.7 | [`6.7-metadata-filtering.py`](chapter-06/6.7-metadata-filtering.py) | 37 | — | after `6.3-bm25-and-keyword-search.py`, `6.4-dense-retrieval-with-embeddings.py` |
| 6.8 | [`6.8-cross-encoder-reranking.py`](chapter-06/6.8-cross-encoder-reranking.py) | 41 | `sentence-transformers` | after `6.3-bm25-and-keyword-search.py`, `6.4-dense-retrieval-with-embeddings.py` |
| 6.10 | [`6.10-evaluation-metrics.py`](chapter-06/6.10-evaluation-metrics.py) | 25 | — | after `6.3-bm25-and-keyword-search.py` |

## Chapter 7 — Context Compression

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 7.3 | [`7.3-extractive-compression.py`](chapter-07/7.3-extractive-compression.py) | 77 | `numpy`, `sentence-transformers` | on its own |
| 7.4 | [`7.4-abstractive-compression.py`](chapter-07/7.4-abstractive-compression.py) | 26 | — | on its own |
| 7.8 | [`7.8-compression-evaluation.py`](chapter-07/7.8-compression-evaluation.py) | 26 | — | after `7.3-extractive-compression.py` |

## Chapter 8 — Tool Calling

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 8.5 | [`8.5-function-schema-design.json`](chapter-08/8.5-function-schema-design.json) | 23 | — | — |
| 8.6 | [`8.6-tool-invocation-flow.py`](chapter-08/8.6-tool-invocation-flow.py) | 64 | — | on its own |
| 8.8 | [`8.8-parallel-tool-calls.py`](chapter-08/8.8-parallel-tool-calls.py) | 31 | — | after `8.6-tool-invocation-flow.py` |
| 8.9 | [`8.9-tool-error-handling.py`](chapter-08/8.9-tool-error-handling.py) | 19 | — | on its own |

## Chapter 9 — Function Calling

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 9.3 | [`9.3-nested-objects.json`](chapter-09/9.3-nested-objects.json) | 13 | — | — |
| 9.3 | [`9.3-schema-anti-pattern-overly-generic-types.jsonc`](chapter-09/9.3-schema-anti-pattern-overly-generic-types.jsonc) | 15 | — | — |
| 9.5 | [`9.5-handling-function-call-results.py`](chapter-09/9.5-handling-function-call-results.py) | 25 | — | on its own |
| 9.6 | [`9.6-multi-step-function-calls.py`](chapter-09/9.6-multi-step-function-calls.py) | 157 | `openai`, `OPENAI_API_KEY` | on its own |
| 9.7 | [`9.7-validation-and-type-safety.py`](chapter-09/9.7-validation-and-type-safety.py) | 53 | `pydantic` | after `9.6-multi-step-function-calls.py` |
| 9.8 | [`9.8-function-calling-in-practice.py`](chapter-09/9.8-function-calling-in-practice.py) | 53 | — | after `9.5-handling-function-call-results.py`, `9.6-multi-step-function-calls.py` |

## Chapter 10 — Model Context Protocol (MCP)

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 10.5 | [`10.5-resource-discovery.json`](chapter-10/10.5-resource-discovery.json) | 16 | — | — |
| 10.5 | [`10.5-resource-reading.json`](chapter-10/10.5-resource-reading.json) | 13 | — | — |
| 10.6 | [`10.6-tool-discovery.json`](chapter-10/10.6-tool-discovery.json) | 16 | — | — |
| 10.6 | [`10.6-tool-invocation.json`](chapter-10/10.6-tool-invocation.json) | 12 | — | — |
| 10.6 | [`10.6-tool-invocation-2.json`](chapter-10/10.6-tool-invocation-2.json) | 13 | — | — |
| 10.7 | [`10.7-mcp-prompts.json`](chapter-10/10.7-mcp-prompts.json) | 20 | — | — |
| 10.8 | [`10.8-mcp-sampling.json`](chapter-10/10.8-mcp-sampling.json) | 18 | — | — |

## Chapter 11 — AI Agents

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 11.6 | [`11.6-action.py`](chapter-11/11.6-action.py) | 16 | — | on its own |
| 11.9 | [`11.9-agent-loops.py`](chapter-11/11.9-agent-loops.py) | 18 | — | sketch: see the text |
| 11.11 | [`11.11-building-a-simple-agent.py`](chapter-11/11.11-building-a-simple-agent.py) | 168 | `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 12 — Agent Planning

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 12.4 | [`12.4-task-trees.py`](chapter-12/12.4-task-trees.py) | 34 | — | on its own |
| 12.5 | [`12.5-llm-based-planning.py`](chapter-12/12.5-llm-based-planning.py) | 44 | — | after `12.4-task-trees.py` |
| 12.6 | [`12.6-plan-validation.py`](chapter-12/12.6-plan-validation.py) | 43 | — | after `12.4-task-trees.py` |
| 12.7 | [`12.7-dynamic-replanning.py`](chapter-12/12.7-dynamic-replanning.py) | 22 | — | sketch: see the text |
| 12.10 | [`12.10-planning-evaluation.py`](chapter-12/12.10-planning-evaluation.py) | 14 | — | after `12.4-task-trees.py` |

## Chapter 13 — Agent Memory

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 13.3 | [`13.3-memory-write-strategies.py`](chapter-13/13.3-memory-write-strategies.py) | 19 | — | on its own |
| 13.5 | [`13.5-episodic-memory-for-agents.py`](chapter-13/13.5-episodic-memory-for-agents.py) | 14 | — | on its own |
| 13.10 | [`13.10-implementation-patterns.py`](chapter-13/13.10-implementation-patterns.py) | 250 | — | on its own |

## Chapter 14 — Multi-Agent Systems

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 14.6 | [`14.6-communication-protocols.py`](chapter-14/14.6-communication-protocols.py) | 16 | — | on its own |
| 14.7 | [`14.7-task-distribution.py`](chapter-14/14.7-task-distribution.py) | 43 | — | after `14.6-communication-protocols.py` |

## Chapter 15 — Agent Communication

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 15.3 | [`15.3-structured-message-formats.py`](chapter-15/15.3-structured-message-formats.py) | 72 | — | on its own |
| 15.5 | [`15.5-synchronous-communication.py`](chapter-15/15.5-synchronous-communication.py) | 32 | — | after `15.3-structured-message-formats.py` |
| 15.6 | [`15.6-broadcast-vs-point-to-point.py`](chapter-15/15.6-broadcast-vs-point-to-point.py) | 32 | — | after `15.3-structured-message-formats.py`, `15.5-synchronous-communication.py` |
| 15.8 | [`15.8-shared-state.py`](chapter-15/15.8-shared-state.py) | 37 | — | on its own |
| 15.9 | [`15.9-communication-failures.py`](chapter-15/15.9-communication-failures.py) | 21 | — | after `15.5-synchronous-communication.py`, `15.6-broadcast-vs-point-to-point.py` |
| 15.10 | [`15.10-communication-security.py`](chapter-15/15.10-communication-security.py) | 19 | — | on its own |

## Chapter 16 — Workflow Automation

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 16.4 | [`16.4-sequential-workflows.py`](chapter-16/16.4-sequential-workflows.py) | 129 | `openai`, `OPENAI_API_KEY` | on its own |
| 16.5 | [`16.5-parallel-workflows.py`](chapter-16/16.5-parallel-workflows.py) | 85 | `openai` | after `16.4-sequential-workflows.py` |
| 16.8 | [`16.8-error-handling-in-workflows.py`](chapter-16/16.8-error-handling-in-workflows.py) | 97 | — | after `16.4-sequential-workflows.py` |
| 16.10 | [`16.10-monitoring-workflows.py`](chapter-16/16.10-monitoring-workflows.py) | 29 | — | on its own |
| Lab | [`lab-document-processing-workflow.py`](chapter-16/lab-document-processing-workflow.py) | 208 | `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 17 — Agent Evaluation

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| Lab | [`lab-agent-evaluation-suite.py`](chapter-17/lab-agent-evaluation-suite.py) | 350 | `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 18 — Agent Security

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| Lab | [`lab-agent-security-layer.py`](chapter-18/lab-agent-security-layer.py) | 410 | `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 19 — Volume III Capstone: Intelligent AI Assistant

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| Lab | [`lab-intelligent-research-assistant-capstone.py`](chapter-19/lab-intelligent-research-assistant-capstone.py) | 582 | `numpy`, `openai`, `OPENAI_API_KEY` | on its own |
