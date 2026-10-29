# Volume IV · Chapter 7 — Lab: Pipeline Profiling and Optimization

## What You Will Build

A document pipeline in two versions, and the profile that justifies the change. The slow version calls three model functions (classify, summarize, extract keywords) one after another for each of ten documents, builds its report by repeated string concatenation, and writes the report to a temporary file only to read it back. The fast version runs the calls concurrently, within a limit on requests in flight, and builds the report in memory. A profiling script runs both under cProfile and reports where the time went and how much was saved. A second script, `wren_profile.py`, times each stage of one reply from Wren, as the team did in the chapter's opening story, before and after fixing the two delays that profile found: a shipment lookup that blocks retrieval, and a scan history of 300 events formatted into the prompt.

## Learning Outcomes

- Profile a pipeline before changing it, and rank its costs from evidence.
- Tell a bottleneck from a waste: work that is unnecessary but costs almost nothing.
- Run independent API calls concurrently with `asyncio.gather`, under a concurrency cap.
- Read cProfile output for async code, which counts running time but not waiting time.
- Report an improvement as before-and-after wall time, from the same input.
- Find the time that is not the model's, and cut it, without changing the model.

## Prerequisites

- Python 3.15
- Chapter 7, read through Section 7.8 and the hands-on lab
- The standard library only (`line-profiler` is optional, for Step 5)
- Default mode: a simulated API, no key. **Estimated API cost: $0.00**
- Live mode (optional): `uv sync --group live` and `OPENAI_API_KEY`. **Estimated API cost: under $0.01 per run** with `gpt-6-luna` (sixty short calls)

## Setup

```bash
cd volume-4/chapter-07      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/profile_pipelines.py          # your work: profiles src/ versions
uv run python solution/profile_pipelines.py     # reference
```

By default the API is simulated (`stand_in.py`): each call waits the latency Section 7.8 uses as its example (classify 200 ms, summarize 300 ms, keywords 500 ms), the provider serves ten requests at once, and the answers are short and fixed in shape. A run takes about twelve seconds. `pipeline_slow.py` and `pipeline_fast.py` also run on their own and print the report.

`src/pipeline_fast.py` runs as supplied and gives the right report, but it is no faster: it awaits each call in turn (TODO 1), processes one document at a time (TODO 2), and has no cap on requests in flight once those are fixed (TODO 3). Complete all three.

**Step 5, line by line.** Install the optional profiler with `uv sync --group profile`. In `src/pipeline_slow.py`, add `from line_profiler import profile` and put `@profile` on `build_report`, then run:

```bash
LINE_PROFILE=1 uv run python src/pipeline_slow.py        # PowerShell: $env:LINE_PROFILE = "1"
```

The per-line timings are written to `profile_output.txt`.

## Expected Result

The reference prints the following (also saved in `expected/output.txt`; times vary by a few hundredths of a second):

```text
=== Before: sequential, via disk: 10.33 s wall time ===
  model calls            10.255 s cumulative ( 99.3% of wall)
  file write and read     0.033 s cumulative (  0.3% of wall)
  report building         0.000 s cumulative (  0.0% of wall)

=== After: concurrent, in memory: 1.33 s wall time ===
  model calls             0.006 s cumulative (  0.4% of wall)
  ...

=== Improvement ===
Wall time: 10.33 s -> 1.33 s (87% less)
Same report: True
```

The profile ranks the costs clearly: the thirty model calls are 99% of the slow pipeline's time, and the file round trip, though pointless, is a third of a percent. Fixing the calls is what moved the wall time. In the fast version the model calls appear to cost almost nothing, because cProfile counts the time a coroutine runs, not the time it waits; the waiting still happens, but overlapped. Against the real API, the saving depends on its latency and on your rate limit.

## Wren's Reply

```bash
uv run python src/wren_profile.py          # your work
uv run python solution/wren_profile.py     # reference
```

The services and the model are simulated with fixed delays, so the timings are a model of the story rather than a measurement, and they vary by a few hundredths of a second between runs. The reference prints (also saved in `expected/wren_profile.txt`):

```text
Where is my parcel? (WF-2291, 300 scan events)

before: 2.36 s in all, a prompt of about 2505 tokens
  shipment lookup                 0.50 s   21%
  policy retrieval                0.30 s   13%
  scan history                    0.74 s   31%
  model call                      0.81 s   34%

after: 1.33 s in all, a prompt of about 72 tokens
  shipment lookup and retrieval   0.51 s   38%
  scan history                    0.01 s    1%
  model call                      0.80 s   60%
```

Before the fix the model call is about a third of the reply, which is what surprised the team: two thirds of the time went to a lookup that blocked retrieval and to formatting 300 scan events that the answer did not need. After it, the reply takes a little over half as long, the prompt is a thirtieth of the size, and the model call is most of what remains.

## Verifying Your Work

```bash
uv run pytest
```

Five tests, with the simulated API sped up twentyfold: both pipelines produce the same report, the report covers every document, the slow pipeline cleans up its temporary file, the fast pipeline takes less than half the slow one's time, and it never has more requests in flight than its cap. They run against `solution/`, which is what CI checks. To test your own version, copy this folder somewhere else, copy your `src/` files over those in `solution/` there, and run `uv run pytest`. Three more test `wren_profile.py`: the fixed reply gives the same answer from a prompt a tenth the size, the lookup and retrieval overlap, and the model is well under half of the reply before the fix and most of it after. With the four TODOs left in place, five of the eight tests fail.

## If It Does Not Work

| Symptom | Cause | Fix |
|---|---|---|
| "After" takes as long as "Before" | TODOs 1 and 2: the calls and documents still run one at a time | Use `asyncio.gather` for the three calls, and again over the documents |
| Wren's "after" profile matches "before" | TODO 4: `reply_after` still calls `reply_before` | Gather the lookup and retrieval, and describe only the last `RECENT_EVENTS` events |
| `Same report: False` | The fast version's results are in a different order | `asyncio.gather` keeps its arguments' order; build the report from its result |
| Live mode returns 429 errors | Too many requests at once for your account | Lower `MAX_IN_FLIGHT` |
| `ModuleNotFoundError: line_profiler` | The optional group was not installed | Run `uv sync --group profile` |
| `ModuleNotFoundError: openai` in live mode | `--group live` was not installed | Run `uv sync --group live` |

## Going Further

- Write the deliverable the chapter asks for: a short Markdown report with the before-and-after profiles, the bottlenecks with evidence, the code diffs and the measured improvement.
- Vary `MAX_IN_FLIGHT` from 1 to 30 and plot wall time against it; find where the provider's limit flattens the curve.
- Stream the summaries and measure time to first token per document.

## Files

| Path | Purpose |
|---|---|
| `src/` | Your starting point: `pipeline_fast.py` has 3 TODOs and `wren_profile.py` has TODO 4; the other files match `solution/` |
| `solution/wren_profile.py` | The profile of one reply from Wren, before and after the fix |
| `solution/pipeline_slow.py` | Step 1: the slow, sequential pipeline |
| `solution/pipeline_fast.py` | Step 3: the fixed, concurrent pipeline |
| `solution/profile_pipelines.py` | Steps 2 and 4: profiles both and compares them |
| `solution/documents.py`, `solution/stand_in.py` | The ten documents, and the simulated API |
| `tests/test_lab.py` | 8 tests, run against `solution/` |
| `expected/wren_profile.txt` | Captured output of `wren_profile.py` |
| `expected/output.txt` | Captured output of the reference |
