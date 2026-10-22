# Volume III · Chapter 7 — Lab: Extractive Context Compression

## What You Will Build

An extractive compressor: it splits a context into sentences, scores each by cosine similarity to the query with sentence embeddings, keeps the best-scoring sentences that fit a token budget, and puts them back in their original order. The demo halves an 800-token context and reports which of the facts the query asks about survived.

## Learning Outcomes

- Score sentences against a query with normalized embeddings.
- Fill a token budget greedily, best sentences first.
- Reassemble kept sentences in document order, so the text still reads coherently.
- Measure compression and check what was lost, not only what was kept.
- Explain why similarity to a query can miss the very definitions it asks for.

## Prerequisites

- Python 3.14. PyTorch, which this lab needs, had not published Python 3.15 builds at the
  time of writing; the lab's `.python-version` selects 3.14, and `uv` installs it for you.
- Chapter 7, read through its hands-on lab
- Dependencies: `sentence-transformers`, `torch`, `numpy`, installed by `uv sync`
- No API key. **Estimated API cost: $0.00** (embeddings are computed locally)

The first run needs an internet connection and about 1 GB of disk: `uv sync` installs PyTorch (CPU build), and the first run downloads the `all-MiniLM-L6-v2` model (about 90 MB) from Hugging Face. Later runs use the cached copies.

## Setup

```bash
cd volume-3/chapter-07      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but without TODO 1 it keeps the first 400 tokens, which is truncation, so its kept sentences and preserved terms differ from the reference. TODO 2 and TODO 3 change the order of the compressed text and of the top-3 list.

Token counts are estimated as 1.33 per word. The reference keeps three of the five metrics the query asks about; Lab Question 6 asks why MRR and F1 are lost.

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text
======================================================================
CONTEXT COMPRESSION LAB
======================================================================

Query: What are the main evaluation metrics for information retrieval systems?
Target token budget: 400
Original context tokens: ~831

Compressing...

── Results ──────────────────────────────────────────────────────
Original tokens:    831
Compressed tokens:  400
Compression ratio:  51.9%
Sentences kept:     21 / 44

── Top 3 Most Relevant Sentences (score) ────────────────────────
  [0.700] Evaluation campaigns like TREC, BEIR, and MS MARCO provide standardized datasets...
  [0.592] TREC (Text Retrieval Conference), organized by NIST since 1992, provides standar...
  [0.580] Information retrieval (IR) is the science of searching for documents, informatio...

── Compressed Context ───────────────────────────────────────────
Information retrieval (IR) is the science of searching for documents, information within documents, and metadata about documents, as well as searching relational databases and the World Wide Web. IR systems handle large collections of primarily unstructured text documents. The history of information retrieval dates to the 1950s, when early systems classified documents manually. Evaluation is central to IR research. TREC (Text Retrieval Conference), organized by NIST since 1992, provides standardized benchmarks and evaluation tracks. Precision measures the fraction of retrieved documents that are relevant. A search engine that returns only highly relevant results has high precision. Recall measures the fraction of all relevant documents that were retrieved. Systems optimized for recall retrieve more broadly at the cost of including irrelevant results. Normalized Discounted Cumulative Gain (NDCG) handles graded relevance judgments where documents may be highly relevant, partially relevant, or irrelevant. NDCG normalizes DCG by the ideal ranking. The document retrieval process begins with an offline indexing phase. Query processing involves parsing the user's query, applying the same normalization steps used during indexing, and executing the retrieval function. The dot product between query and document vectors measures their semantic relevance. Hybrid retrieval systems combine sparse (BM25) and dense retrieval. Reranking is a second-stage process that applies a more expensive but accurate cross-encoder model to rerank the top candidates from first-stage retrieval. Cross-encoders see both query and document simultaneously, enabling fine-grained relevance judgments. Methods include pseudo-relevance feedback, thesaurus expansion, and LLM-based expansion. Other important IR topics include faceted search, which allows filtering by attributes; learning to rank (LTR), which uses machine learning to optimize the ranking function; and diversity in ranking, which ensures results cover different aspects of the query. Evaluation campaigns like TREC, BEIR, and MS MARCO provide standardized datasets for comparing retrieval systems. The BEIR benchmark covers 18 datasets across nine task types, in domains including scientific, financial, and medical text.

── Key Metric Terms Preserved ───────────────────────────────────
  Found: ['precision', 'recall', 'NDCG']
  Missing: ['MRR', 'F1']
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

## Going Further

- Raise the budget to 600 tokens and see which sentences return (Lab Question 1).
- Compare with truncation to the first 400 tokens (Lab Question 4).
- Add a `min_similarity` threshold, and count how many sentences it removes (Lab Question 3).
- Count tokens with tiktoken instead of the 1.33-per-word estimate, and check the budget is still met.

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 3 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 6 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
