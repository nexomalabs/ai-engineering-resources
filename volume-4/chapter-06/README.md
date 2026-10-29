# Volume IV · Chapter 6 — Lab: Inference Benchmark Harness

## What You Will Build

A benchmark harness for a model API that reports latency percentiles (p50, p95, p99), throughput and cost per 1,000 tokens, with and without an exact-match cache. It runs three experiments: twenty unique prompts with no cache; a mixed set of forty prompts with the cache on; and a concurrency sweep that shows where tail latency starts to climb. A second script, `batching_sim.py`, simulates the customs GPUs from the chapter's opening story, and shows that the same two GPUs fall ever further behind with fixed batches and keep up with continuous batching.

## Learning Outcomes

- Measure latency as percentiles, not averages, and read the tail.
- Price a run from the response's token counts, with separate input and output rates.
- Show what a cache saves, and why identical requests that arrive together all miss a naive cache.
- Fix that with single-flight: duplicates in flight share one call.
- Find the concurrency at which the provider's limit makes tail latency grow.
- Show, by simulation, why continuous batching keeps a GPU busy that fixed batches leave idle.

## Prerequisites

- Python 3.15
- Chapter 6, read through Section 6.10 and the hands-on lab
- Dependencies: `numpy`, installed by `uv sync`
- Default mode: a simulated API, no key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (about 200 short calls)

## Setup

```bash
cd volume-4/chapter-06      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab06_benchmark.py          # your work
uv run python solution/lab06_benchmark.py     # reference
```

A full run takes about 50 seconds. By default the API is simulated (`stand_in.py`): every prompt has a fixed latency between 300 and 800 ms, derived from its hash so runs repeat; the provider serves at most ten requests at once, so a client that sends more queues behind it; and each response carries token counts. These are a model of an API, not measurements of one; live mode measures the real thing. Set `NEXOMA_LATENCY_SCALE=0.1` to run ten times faster.

`src/lab06_benchmark.py` runs as supplied, but duplicates in flight each make their own call (TODO 1), tokens are estimated from words and priced at one rate (TODO 2), and the concurrency limit is ignored, so the sweep shows the same numbers at every setting (TODO 3). Complete all three.

The scheduler simulation runs on its own, in about seven seconds:

```bash
uv run python src/batching_sim.py          # your work
uv run python solution/batching_sim.py     # reference
```

The reference prints the following (also saved in `expected/batching_sim.txt`):

```text
Afternoon rush: 30 minutes at 2.0 documents a second (3655 documents), 2 GPUs with 8 slots each

scheduler            completed      p50      p95  longest queue  slots busy
fixed batches             1738   448.7s   910.4s           1909         37%
continuous batching       3634     4.0s    22.0s             35         78%
```

With fixed batches, a batch waits for its longest document while its other slots sit idle, so the GPUs are only 37% busy and the queue still reaches 1,909. Continuous batching refills each freed slot at the next step: the same GPUs are 78% busy, and the p95 is the 22 seconds the longest documents take to decode. `src/batching_sim.py` runs as supplied, but both schedulers behave as fixed batches until you complete TODO 4.

## Expected Result

The reference prints the following (also saved in `expected/output.txt`; latencies vary by a few milliseconds):

```text
=== Step 4: 40 prompts (20 unique, 20 repeats), cache on ===
Requests      : 40
Served without a model call: 20 (50.0%) | from cache 7, shared in flight 13
Throughput    : 11.31 req/s | 166.0 tok/s
Latency p50   : 435 ms
Latency p95   : 769 ms
Latency p99   : 780 ms
From-cache p99: 0.02 ms
Cost/1K tokens: $0.00034

=== Step 6: p99 latency by concurrency (40 unique prompts, no cache) ===
concurrency  1: p50   550 ms | p99   776 ms |  1.91 req/s
concurrency  5: p50   554 ms | p99   779 ms |  8.69 req/s
concurrency 10: p50   550 ms | p99   779 ms | 16.24 req/s
concurrency 20: p50   988 ms | p99  1490 ms | 16.25 req/s
```

Half the mixed set is served without a model call, but in two ways. Seven answers came from the cache in 0.02 ms. Thirteen were duplicates that arrived while the first request was still running; they waited for it and took as long as it did, but cost nothing. Without single-flight, those thirteen would each have made a call.

The sweep shows the provider's limit. Up to ten concurrent requests, throughput grows and the tail stays flat; at twenty, throughput stops growing and p50 and p99 nearly double, because half the requests now queue. Against the real API, the knee falls wherever your account's rate limit puts it.

## Verifying Your Work

```bash
uv run pytest
```

Eight tests, with the simulated API sped up a hundredfold: a repeat is served from the cache at no token cost, five concurrent duplicates make one call, `use_cache=False` calls every time, the mixed set saves twenty calls, cost uses both token counts and both prices, and the concurrency limit holds at 1, 3 and 7. Two more test the scheduler simulation: a request behind a long one waits for it under fixed batching but not under continuous batching, and over a five-minute rush continuous batching keeps up and keeps the slots busier. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. With all four TODOs left in place, eight of the ten tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| The mixed set saves fewer than 20 calls | TODO 1: duplicates in flight each call the model | Await the in-flight request's future |
| Cost/1K tokens looks too high | TODO 2 still prices every token at the output rate | Price prompt and completion tokens separately |
| The sweep shows the same p99 at every concurrency | TODO 3: the semaphore is never held | Wrap the request in `async with semaphore:` |
| Both schedulers print the same row | TODO 4: `admit()` fills a batch only when it is empty | When `continuous` is True, top the batch up at every step |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |
| Live mode returns 429 errors at high concurrency | Your account's rate limit | Lower the concurrency; that limit is what the sweep measures |

## Going Further

- Answer Step 6's first question: at what hit rate does the cache's own overhead pay for itself?
- Add time to first token by streaming the response, and report it next to end-to-end latency.
- Generate arrivals from a Poisson process instead of firing every request at once.

## Files

| Path | Purpose |
|---|---|
| `src/lab06_benchmark.py` | Your starting point; runs, with 3 TODOs |
| `src/batching_sim.py` | The scheduler simulation's starting point, with TODO 4 |
| `solution/batching_sim.py` | Reference scheduler simulation |
| `src/stand_in.py`, `solution/stand_in.py` | The simulated API |
| `solution/lab06_benchmark.py` | Reference: Section 6.10's harness with the lab's steps added |
| `tests/test_lab.py` | 10 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
| `expected/batching_sim.txt` | Captured output of the reference simulation |
