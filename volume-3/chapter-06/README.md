# Volume III · Chapter 6 — Lab: Hybrid Retrieval System

## What You Will Build

A retrieval benchmark over a 15-document corpus with labelled relevant documents: BM25 keyword retrieval, dense retrieval with sentence embeddings in a FAISS index, and the two fused with reciprocal rank fusion (RRF). It reports Recall@5 per query and on average, and states what the numbers show.

## Learning Outcomes

- Build a BM25 index and a dense FAISS index over the same corpus.
- Fuse ranked lists with reciprocal rank fusion.
- Measure retrieval with Recall@K against labelled relevant documents.
- Explain why fusion cannot recover a document that neither retriever returns.
- Report measured results rather than expected ones.

## Prerequisites

- Python 3.14. PyTorch, which this lab needs, had not published Python 3.15 builds at the
  time of writing; the lab's `.python-version` selects 3.14, and `uv` installs it for you.
- Chapter 6, read through its hands-on lab
- Dependencies: `sentence-transformers`, `torch`, `faiss-cpu`, `rank-bm25`, `numpy`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (embeddings are computed locally)

The first run needs an internet connection and about 1 GB of disk: `uv sync` installs PyTorch (CPU build), and the first run downloads the `all-MiniLM-L6-v2` model (about 90 MB) from Hugging Face. Later runs use the cached copies.

## Setup

```bash
cd volume-3/chapter-06      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but its Hybrid column just repeats BM25 (TODO 1), and every recall is divided by 5 instead of by the number of relevant documents (TODO 2), so the figures differ from the reference.

The figures below come from `all-MiniLM-L6-v2`. On this small corpus fusion matches dense retrieval but does not beat it; Lab Question 1 asks why.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

Query                                             BM25    Dense   Hybrid
-------------------------------------------------------------------------
how does BM25 work for information retrieva       0.50     0.50     0.50
semantic search using vector embeddings           1.00     1.00     1.00
machine learning models trained on data           0.75     1.00     1.00
language understanding NLP                        0.50     0.50     0.50
-------------------------------------------------------------------------
Mean Recall@5                                     0.69     0.75     0.75

Hybrid retrieval matches the better single method.
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
| `OSError` or a connection error loading the model | The model could not be downloaded from Hugging Face | Connect to the internet for the first run; set `HF_HUB_OFFLINE=1` afterwards |
| A warning that symlinks are not supported, on Windows | Hugging Face caches files without symlinks unless Developer Mode is on | Harmless: the cache just uses more disk; set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` |
| `uv sync` downloads several gigabytes on Linux | PyTorch was resolved from PyPI instead of its CPU index | Keep the `[tool.uv.sources]` entry for torch in `pyproject.toml` |

## Going Further

- Change the RRF constant from 60 to 10 and to 120, and compare the rankings (Lab Question 3).
- Add a query on which BM25 and dense retrieval disagree, and show fusion helping (Lab Questions 1 and 4).
- Swap in `all-mpnet-base-v2` and measure dense recall again (Lab Question 5).
- Tokenize for BM25 with a regular expression instead of `split()`, so punctuation does not hide matches, and check whether recall changes.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 2 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 6 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
