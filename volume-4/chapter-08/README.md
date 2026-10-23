# Volume IV · Chapter 8 — Lab: Two-Level Cache System

## What You Will Build

A two-level cache in front of a model. Level one is an exact-match dictionary keyed by a hash of the normalised query; level two embeds each query and serves a stored answer when a new query is similar enough to an old one. A benchmark runs fifty queries through it (originals, paraphrases, exact repeats and unrelated questions), records where each answer came from and how long it took, and reports the hit rate and the latency of each level.

## Learning Outcomes

- Build an exact-match cache with a normalised key.
- Build a semantic cache with embeddings, cosine similarity and a threshold.
- Promote a semantic hit to the exact level so the same wording costs nothing next time.
- Measure each level's latency separately, and explain why a single "cache speedup" figure misleads.
- Reason about the threshold: too high and paraphrases miss, too low and wrong answers are served.

## Prerequisites

- Python 3.15
- Chapter 8, read through Section 8.4 and the hands-on lab
- Dependencies: `numpy`, installed by `uv sync`
- Default mode: a simulated API, no key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` and `text-embedding-3-small`

## Setup

```bash
cd volume-4/chapter-08      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab08_benchmark.py          # your work
uv run python solution/lab08_benchmark.py     # reference
```

A run takes about fifty seconds. By default the API is simulated (`stand_in.py`). Its embeddings are a hashed bag of the query's content words, with question words and filler dropped and plurals folded, so two phrasings that share their key words score close to 1.0 and a rewording scores much lower. Real embeddings capture meaning, not just shared words, and will match more of the paraphrases. Embedding calls wait 60–120 ms and model calls 300–1,500 ms. `semantic_cache.py` is Section 8.4's code with its one bug fixed: the semantic store started as a dict, so the first `store()` failed.

`src/semantic_cache.py` runs as supplied, but its exact key is case- and space-sensitive (TODO 1), it never searches the semantic level (TODO 2), and it does not promote semantic hits (TODO 3). Complete all three.

## Expected Result

The reference prints the following (also saved in `expected/output.txt`; latencies vary a little):

```text
=== Cache Report ===
Total queries  : 50
Exact hits     : 10
Semantic hits  : 6
Misses         : 34
Hit rate       : 32.0%
...
Exact-cache p50    : 0.004 ms
Semantic-cache p50 : 91.4 ms  (11x faster than the LLM)
LLM p50            : 1048.1 ms
```

Twenty queries could have hit; sixteen did. All ten repeats hit exactly, including the ones with different case and spacing. Six of the ten paraphrases cleared the 0.93 threshold: those that reuse the original's key words ("Can you explain gradient descent?"). The four that reword it ("Why do gradients vanish in deep networks?") missed and paid for a model call. That is the threshold's trade-off in miniature. An exact hit costs microseconds and a semantic hit costs an embedding, so report the levels separately: a single median over all hits would put the speedup in the hundreds of thousands, which says nothing useful.

## Verifying Your Work

```bash
uv run pytest
```

Seven tests, with the simulated API sped up a hundredfold: `store()` fills both levels, the exact key ignores case and spaces, a paraphrase with the same key words hits, a reworded one misses at 0.93, a lower threshold accepts a looser match, a promoted hit needs no second embedding, and the full dataset gives 10 exact hits, 6 semantic hits and 34 misses. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With all three TODOs left in place, five tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| `AttributeError: 'dict' object has no attribute 'append'` | The semantic store was initialised as `{}` | Initialise it as a list, `[]` |
| The repeats with different case miss | TODO 1: the key is not normalised | Hash `query.strip().lower()` |
| No semantic hits at all | TODO 2: the semantic level is never searched | Embed the query and compare it with every stored embedding |
| A repeated paraphrase embeds again | TODO 3: semantic hits are not promoted | Store the answer under the new query's exact key |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |

## Going Further

- Run with thresholds from 0.80 to 0.97, and plot hit rate against how many served answers were for a different question.
- Avoid embedding a query twice on a miss: keep the embedding from `lookup()` for `store()`.
- Replace the list scan with a vector index (Volume III, Chapter 5) and time it with 10,000 stored queries.

## Files

| Path | Purpose |
|---|---|
| `src/semantic_cache.py` | Your starting point; runs, with 3 TODOs |
| `solution/semantic_cache.py` | Section 8.4's cache with its bug fixed, and the mode switch |
| `solution/lab08_benchmark.py` | Steps 1, 3 and 4: timing and analysis |
| `solution/queries.py` | Step 2: the fifty queries |
| `solution/stand_in.py` | The simulated API |
| `tests/test_lab.py` | 7 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
