# Applied AI Engineering — Companion Resources

Lab code, starter files, and reference solutions for the *Applied AI Engineering*
series, published by Nexoma Labs LLC.

This repository holds the runnable labs, every code listing of twelve lines or
more from the books, and the model answers to the review questions. It does not
contain the rest of the book text.

## Series

| Volume | Title | Labs |
|:------:|-------|:----:|
| I | AI and LLM Fundamentals | [`volume-1/`](volume-1/) — available now |
| II | Prompt Engineering | [`volume-2/`](volume-2/) — labs 17–20 now, the rest to follow |
| III | Context and Agents | [`volume-3/`](volume-3/) — 13 of 19 labs now, the rest to follow |
| IV | Production Systems | [`volume-4/`](volume-4/) — 8 labs now, the rest to follow |

Each volume's `README.md` lists every lab in the book and marks which are here
yet. A lab not yet here has its complete code in the chapter's Hands-on Lab
section.

## Running a lab

Requires [uv](https://docs.astral.sh/uv/). Each lab pins Python 3.15 in its
`.python-version` file, and `uv sync` downloads that version for you.

```bash
git clone https://github.com/nexomalabs/ai-engineering-resources.git
cd ai-engineering-resources/volume-1/chapter-03
uv sync
uv run python src/lab.py     # your starting point
uv run pytest                # verify your work
```

Every lab runs from a clean clone with **no API key** — tests replay recorded
responses by default (`NEXOMA_LAB_MODE=fixture`). See each chapter's own
`README.md` for that lab's objectives, expected output, and estimated API cost
if you choose to run it live.

On Windows, clone to a short path such as `C:\labs`: the 260-character path
limit can break package installs in deep folders.

## Structure

```text
volume-1/              — the same layout for volume-2/, volume-3/, volume-4/
├── README.md          — lab index: chapter, type, time, API cost, status
├── ANSWERS.md         — model answers to the review questions, as in Appendix B
├── listings/          — the book's code listings, by chapter, with an index of what each needs
├── shared/             — nexoma_labs package used by every lab (client, cost ledger, fixtures)
└── chapter-01/ … chapter-10/
    ├── README.md        — setup, run, expected output, failure table, API cost
    ├── src/lab.py        — starter with TODOs (chapters with runnable code)
    ├── solution/lab.py    — reference implementation
    ├── tests/              — runs in CI against the solution
    ├── expected/            — captured reference output
    └── fixtures/             — recorded model responses (chapters 8-10)
```

`listings/` and `ANSWERS.md` are generated from the manuscript, so report a
mistake in either as an erratum. Listings are printed code, some of it fragments
that build on an earlier listing, so CI lints and tests the labs, not the
listings.

In Volume I, chapters 1 and 2 are paper exercises: `README.md` only, no code.
Volume II–IV labs so far need no API key at all, so they have no `fixtures/`.
Some Volume IV labs name a script other than `src/lab.py`; each README says which.

## License

Code in this repository is licensed under the [MIT License](LICENSE). The book
text, including `ANSWERS.md`, is © 2027 Nexoma Labs LLC, all rights reserved —
see the volume's copyright page.

## Errata and issues

- **Errata:** https://books.nexomalabs.com/applied-ai-engineering/errata/
- **Issues:** open one on this repository
- **Email:** errata@nexomalabs.com
