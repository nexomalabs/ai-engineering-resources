# Volume III · Chapter 4 — Lab: Minimal RAG System

## What You Will Build

A complete retrieval-augmented generation loop in one file. Twelve technical passages and two versions of Wrenfield's battery shipping policy are embedded with `all-MiniLM-L6-v2` into a NumPy matrix; a query is embedded the same way and scored against every passage by cosine similarity; the top three passages are numbered into a prompt; and a mock model writes an answer that cites them. The mock stands where a real model call would go, so you can see every part of the pipeline without an API key. Each document can carry an effective date and a superseded date, and retrieval keeps only documents currently in force, before ranking: the fix for the chapter's opening story, in which Wren answered from a battery policy that had been replaced a year earlier.

## Learning Outcomes

- Embed a small knowledge base and hold it as a matrix of normalized vectors.
- Retrieve the top-k passages for a query with a single matrix product.
- Assemble numbered context that a model can cite.
- Keep superseded documents out of retrieval with an effective-date filter applied before ranking.
- Check retrieval quality by reading which passages each query surfaces, and their scores.
- See where a real model call replaces the mock, and what the prompt it receives looks like.

## Prerequisites

- Python 3.14. PyTorch, which `sentence-transformers` needs, had not published Python 3.15 builds at the time of writing; the lab's `.python-version` selects 3.14, and `uv` installs it for you.
- Chapter 4, read through its hands-on lab
- Dependencies: `sentence-transformers`, `torch`, `numpy`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (embeddings are computed locally; the answer comes from a mock)

The first run needs an internet connection and about 1 GB of disk: `uv sync` installs PyTorch (CPU build), and the first run downloads the `all-MiniLM-L6-v2` model (about 90 MB) from Hugging Face. Later runs use the cached copies.

## Setup

```bash
cd volume-3/chapter-04      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/rag_system.py          # your work
uv run python solution/rag_system.py     # reference
```

`src/rag_system.py` runs as supplied, but it returns the first three passages for every query with a score of 0.0 (TODO 1), and it puts the passages into the prompt without reference numbers, so the mock answer has only one citation to give (TODO 2). It also treats every document as in force (TODO 3), so the superseded 2023 battery policy is still searchable after the filter. Complete all three TODOs.

## Expected Result

The reference solution prints the following for the first query (full output in `expected/output.txt`):

```text
QUERY: How does JWT token authentication work?
============================================================

ANSWER:
Based on the retrieved context, how does jwt token authentication work
is addressed in the knowledge base as follows: The relevant technical
details are provided in [1], [2]. [Mock response — replace
mock_llm_call() with a real LLM API call for production.]

SOURCES:
  [1] Security Guide (score=0.6806)
       JWT (JSON Web Token) consists of three base64url-encoded parts: header, payload,...
  [2] Security Guide (score=0.4121)
       Access tokens should be short-lived (15–60 minutes). Refresh tokens are long-liv...
  [3] REST API Guide (score=0.2703)
       HTTP POST requests send data to a server to create a new resource. The request b...
```

The GET/POST query retrieves both REST API passages first, and the Docker query ranks the volumes passage first (0.677) ahead of the image passage. The battery question is asked twice. Searching every indexed document, the superseded 2023 policy ranks first (0.834) ahead of the 2025 policy that replaced it (0.753): the most similar text is not the current text. Searching only documents in force today, the 2023 policy is not a candidate, and the 2025 policy comes first. Read the third result of each of the first three queries too: with only twelve technical passages, the third is often only loosely related, which is why a production system sets a minimum score as well as `top_k`. Scores can differ in the third or fourth decimal place across machines.

## Verifying Your Work

```bash
uv run pytest
```

Eleven tests: fourteen unit-length embeddings, the top passages for each of the three technical queries, descending scores with `top_k` respected, the in-force check on both dates, the battery question with and without the filter and as of an earlier date, numbered citations in the answer, and the mock's parsing of the prompt. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/rag_system.py` over the one in `solution/` there, and run `uv run pytest`. With the three TODOs left in place, eight tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install uv (docs.astral.sh/uv) |
| `uv sync` downloads gigabytes | PyTorch came from PyPI with CUDA | Keep the `[tool.uv.sources]` section of `pyproject.toml`; it selects the CPU build |
| A network error on the first run | The embedding model downloads once from Hugging Face | Run it once with a connection; after that it is cached |
| A warning about unauthenticated requests to the HF Hub, or a `HF_TOKEN` | Hugging Face asks anonymous downloads to sign in for higher rate limits | Harmless: the model downloads without a token. To silence it, set `HF_TOKEN` to a free Hugging Face access token |
| A warning that symlinks are not supported, on Windows | Hugging Face caches files without symlinks unless Developer Mode is on | Harmless: the cache just uses more disk; set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` |
| Every score is 0.0 | TODO 1 still returns zeros | Multiply the document matrix by the query vector |
| The answer cites only `[1]` | TODO 2 still adds passages without numbers | Prefix each passage with `[i] Source: ...` |
| The filtered battery search still lists the 2023 policy | TODO 3: `in_force()` still returns True | Compare `effective_from` and `superseded_on` with `as_of` |

## Going Further

- Replace `mock_llm_call()` with a real model call, and check that the answer cites only what was retrieved.
- Add a minimum score, and make the generator say it has no information when nothing passes it.
- Ask a question the knowledge base cannot answer, such as "How do I configure Kubernetes?", and look at the scores.

## Files

| Path | Purpose |
|---|---|
| `src/rag_system.py` | Your starting point; runs, with 3 TODOs |
| `solution/rag_system.py` | Reference implementation, as printed in the chapter |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
