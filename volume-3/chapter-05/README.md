# Volume III · Chapter 5 — Lab: Vector Index with FAISS

## What You Will Build

A local vector index: 15 technical passages encoded with sentence embeddings and stored twice, in an exact flat FAISS index and an approximate HNSW index. Four queries run against both, the demo reports each result list, its search time and HNSW's recall against the exact answer, and it saves the HNSW index to disk and reloads it.

## Learning Outcomes

- Encode text to normalized vectors, so inner product equals cosine similarity.
- Build exact (flat) and approximate (HNSW) FAISS indexes, and set their parameters.
- Measure an approximate index's recall against exact search.
- Handle FAISS's placeholder results when fewer than k vectors match.
- Save an index to disk and load it back.

## Prerequisites

- Python 3.14. PyTorch, which this lab needs, had not published Python 3.15 builds at the
  time of writing; the lab's `.python-version` selects 3.14, and `uv` installs it for you.
- Chapter 5, read through its hands-on lab
- Dependencies: `sentence-transformers`, `torch`, `faiss-cpu`, `numpy`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (embeddings are computed locally)

The first run needs an internet connection and about 1 GB of disk: `uv sync` installs PyTorch (CPU build), and the first run downloads the `all-MiniLM-L6-v2` model (about 90 MB) from Hugging Face. Later runs use the cached copies.

## Setup

```bash
cd volume-3/chapter-05      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

Search times and the HNSW build time vary from run to run, so those numbers will differ from the output below; the results and recall will not. On 15 passages HNSW is no faster than exact search: approximate indexes pay off on large collections.

`src/lab.py` runs as supplied. Its TODOs do not change this demo's output, because both indexes agree and every query asks for fewer results than there are passages; the tests check both. The run writes `corpus.index` to the folder you run it from.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
Corpus size: 15 passages

Loading model: all-MiniLM-L6-v2
Encoding 15 passages...
Embeddings shape: (15, 384) (dtype=float32)

[Flat Index] Built. Total vectors: 15

[HNSW Index] Building (M=16, efConstruction=100)...
[HNSW Index] Built in 0.2ms. Total vectors: 15

======================================================================
RETRIEVAL COMPARISON: FLAT (exact) vs. HNSW (approximate)
======================================================================

──────────────────────────────────────────────────────────────────────

[FLAT (exact)] Query: 'How does Python handle concurrent programming?'  (52.3 µs)
  1. [score=0.6530] asyncio enables concurrent I/O in Python using async/await syntax....
  2. [score=0.6052] The Global Interpreter Lock (GIL) in CPython limits true parallelism for CPU-bou...
  3. [score=0.3100] Decorators in Python wrap functions to extend behavior without modification....

[HNSW (approx)] Query: 'How does Python handle concurrent programming?'  (74.9 µs)
  1. [score=0.6530] asyncio enables concurrent I/O in Python using async/await syntax....
  2. [score=0.6052] The Global Interpreter Lock (GIL) in CPython limits true parallelism for CPU-bou...
  3. [score=0.3100] Decorators in Python wrap functions to extend behavior without modification....
  Recall@3 (HNSW vs Flat): 100.0%

──────────────────────────────────────────────────────────────────────

[FLAT (exact)] Query: 'What is the difference between Docker and Kubernetes?'  (31.6 µs)
  1. [score=0.5894] Kubernetes orchestrates containerized workloads across a cluster of nodes....
  2. [score=0.5206] Docker images are immutable; containers are running instances of images....
  3. [score=0.1544] Python list comprehensions create lists concisely using bracket notation....

[HNSW (approx)] Query: 'What is the difference between Docker and Kubernetes?'  (41.8 µs)
  1. [score=0.5894] Kubernetes orchestrates containerized workloads across a cluster of nodes....
  2. [score=0.5206] Docker images are immutable; containers are running instances of images....
  3. [score=0.1544] Python list comprehensions create lists concisely using bracket notation....
  Recall@3 (HNSW vs Flat): 100.0%

──────────────────────────────────────────────────────────────────────

[FLAT (exact)] Query: 'How do vector databases support semantic search?'  (30.1 µs)
  1. [score=0.5944] Vector databases store high-dimensional embeddings and support approximate neare...
  2. [score=0.3853] B-tree indexes in relational databases support efficient equality and range quer...
  3. [score=0.2994] GraphQL allows clients to request exactly the data fields they need....

[HNSW (approx)] Query: 'How do vector databases support semantic search?'  (39.7 µs)
  1. [score=0.5944] Vector databases store high-dimensional embeddings and support approximate neare...
  2. [score=0.3853] B-tree indexes in relational databases support efficient equality and range quer...
  3. [score=0.2994] GraphQL allows clients to request exactly the data fields they need....
  Recall@3 (HNSW vs Flat): 100.0%

──────────────────────────────────────────────────────────────────────

[FLAT (exact)] Query: 'What security protocol protects data in transit?'  (29.4 µs)
  1. [score=0.4607] TLS 1.3 provides transport layer security with reduced handshake latency....
  2. [score=0.2216] REST APIs use HTTP verbs: GET retrieves data, POST creates, PUT replaces, DELETE...
  3. [score=0.2001] GraphQL allows clients to request exactly the data fields they need....

[HNSW (approx)] Query: 'What security protocol protects data in transit?'  (41.1 µs)
  1. [score=0.4607] TLS 1.3 provides transport layer security with reduced handshake latency....
  2. [score=0.2216] REST APIs use HTTP verbs: GET retrieves data, POST creates, PUT replaces, DELETE...
  3. [score=0.2001] GraphQL allows clients to request exactly the data fields they need....
  Recall@3 (HNSW vs Flat): 100.0%

======================================================================
Average Recall@3 across 4 queries: 100.0%

======================================================================
INDEX STATISTICS
Flat index: 15 vectors, 384 dims
HNSW index: 15 vectors, M=16, efSearch=64
Flat memory (approx): 22.5 KB

Saving HNSW index to disk...
Reloaded index has 15 vectors.
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
| A warning about unauthenticated requests to the HF Hub, or a `HF_TOKEN` | Hugging Face asks anonymous downloads to sign in for higher rate limits | Harmless: the model downloads without a token. To silence it, set `HF_TOKEN` to a free Hugging Face access token |
| A warning that symlinks are not supported, on Windows | Hugging Face caches files without symlinks unless Developer Mode is on | Harmless: the cache just uses more disk; set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` |
| `faiss-cpu` will not install | No wheel for your platform and Python version | Use the ChromaDB variant in the chapter, with `pip install chromadb` |

## Going Further

- Grow the corpus to 10,000 synthetic passages and compare flat and HNSW search times.
- Lower `efSearch` to 4 and measure how recall falls.
- Run the chapter's ChromaDB variant on the same corpus and compare its top results.
- Store the passage IDs alongside the index, so a reloaded index can be searched without the original list.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 2 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 6 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
