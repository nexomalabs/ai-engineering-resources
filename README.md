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

New to this? Follow the four steps below once. They take about ten minutes, and
after that every lab in every volume runs the same way.

### 1. Install three tools (once)

| Tool | What it is for | Windows | macOS |
|------|----------------|---------|-------|
| **Git** | Downloads this repository | Install from [git-scm.com](https://git-scm.com/downloads/win) and accept the defaults | Open **Terminal** and run `git --version`. If Git is missing, macOS offers to install it: click **Install** |
| **VS Code** | The editor you write and run the labs in | Install from [code.visualstudio.com](https://code.visualstudio.com/) | Install from [code.visualstudio.com](https://code.visualstudio.com/) |
| **uv** | Installs Python 3.15 and each lab's packages for you | Open **PowerShell** and run the first command below | In **Terminal**, run the second command below |

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS (Terminal):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then **close the window and open a new one**, so it finds `uv`. Check that everything
is in place; each command should print a version number:

```bash
git --version
uv --version
```

You do not need to install Python yourself: uv downloads the right version the
first time you run a lab. Linux works too: use the macOS command for uv, and
your package manager for Git (for example `sudo apt install git`).

### 2. Download the labs

Windows (PowerShell). Use a short folder such as `C:\labs`: long Windows paths
can break package installs.

```powershell
mkdir C:\labs
cd C:\labs
git clone https://github.com/nexomalabs/ai-engineering-resources.git
```

macOS (Terminal):

```bash
cd ~
git clone https://github.com/nexomalabs/ai-engineering-resources.git
```

### 3. Open the folder in VS Code

Start VS Code, choose **File → Open Folder…**, and select the
`ai-engineering-resources` folder you just downloaded. Then open a terminal inside
VS Code with **Terminal → New Terminal**. Run every command from here on in that
terminal.

### 4. Run a lab

Go into the lab's folder (Volume I, Chapter 3 here) and run three commands:

```bash
cd volume-1/chapter-03
uv sync                      # installs Python and the lab's packages (slow only the first time)
uv run pytest                # checks your setup: every test should pass
uv run python src/lab.py     # runs your starting code
```

The tests check the lab's reference answer in `solution/`, so if they pass, your
setup works. Now open `src/lab.py` in VS Code, complete its `TODO`s, and run it
again. Compare what it prints with `expected/output.txt`, or run the reference
answer with `uv run python solution/lab.py`.

To have the tests check your own code: copy the whole lab folder, replace
`solution/lab.py` in the copy with your `src/lab.py`, and run `uv run pytest` in
the copy. Every test passing means your code behaves like the reference answer.

To move to the next lab, go up a folder and into it, for example
`cd ../chapter-04`. Each lab's `README.md` says which file to run, if it is not
`src/lab.py`.

Every lab runs with **no API key**: where a lab would call a model, it replays
recorded responses (`NEXOMA_LAB_MODE=fixture`). Each chapter's `README.md` gives
the lab's objectives, the output to expect, and the estimated API cost if you
choose to run it live.

### If something goes wrong

| Problem | Fix |
|---------|-----|
| `uv` or `git` is "not recognized" or "command not found" | Close every terminal window, including VS Code's, and open a new one. If it still fails, rerun the install command from step 1 |
| `uv sync` fails on Windows with a path error | The repository is in a folder with a long path. Download it again into `C:\labs` (step 2) |
| `cd volume-1/chapter-03` says the path does not exist | You are in the wrong folder. Run `cd` to the `ai-engineering-resources` folder first, or reopen it in VS Code (step 3) |
| `uv run pytest` fails | Something in the setup is wrong, not your code. See *If It Does Not Work* in that lab's `README.md` |

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
