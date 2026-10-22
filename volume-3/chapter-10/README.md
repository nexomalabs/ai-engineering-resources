# Volume III · Chapter 10 — Lab: MCP-Compatible Server

## What You Will Build

A Model Context Protocol server that speaks JSON-RPC 2.0 over stdio. It answers the `initialize` handshake, lists and reads four resources, and exposes three tools: a database query, a restricted Python runner, and a documentation lookup. A client simulator drives it in-process for the demo; `server` mode runs it as a real stdio server that an MCP host can launch.

## Learning Outcomes

- Implement the `initialize` handshake and declare only the capabilities you implement.
- Refuse every other request until the client has initialized.
- Serve resources by URI, and return MCP's `-32002` code for one that does not exist.
- Distinguish protocol errors (a JSON-RPC `error`) from tool execution errors (a result with `isError: true`).
- Explain why a blocklist is a weak sandbox for model-supplied code.

## Prerequisites

- Python 3.15
- Chapter 10, read through its hands-on lab
- No third-party dependencies: the standard library only
- No API key. **Estimated API cost: $0.00** (the client is simulated; no model is involved)

## Setup

```bash
cd volume-3/chapter-10      # from the repository root
uv sync
```

## Running It

```bash
uv run python src/lab.py          # your work
uv run python solution/lab.py     # reference
```

`src/lab.py` runs as supplied, but it has no blocklist (TODO 2), so in step [7] the `import os` snippet reaches the sandbox, which happens to fail it with an ImportError, reported as `isError: False`. TODO 1 and TODO 3 do not change this demo's output; the tests check them.

To see the raw stdio transport (Lab Question 5), pipe JSON-RPC messages into server mode, one per line:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | uv run python solution/lab.py server
```

## Expected Result

The reference solution prints the following (also saved in `expected/output.txt`).

```text

============================================================
MCP SERVER DEMO — Stdio Transport Simulation
============================================================

[1] Initialize
    Server: {'name': 'lab-mcp-server', 'version': '1.0.0'}
    Capabilities: ['resources', 'tools']

[2] resources/list
    docs://mcp/overview — MCP Overview Documentation
    docs://mcp/tools — MCP Tools Guide
    db://users — Users Table
    db://products — Products Table

[3] resources/read — docs://mcp/overview
    [text/markdown] # Model Context Protocol (MCP)  MCP is a standard protocol for connecting AI models to external data sources and tools. ...

[4] tools/list
    query_database — Query the in-memory database. Supports 'users' and 'products...
    execute_python — Execute a Python code snippet in a restricted environment. O...
    lookup_documentation — Look up MCP documentation by topic. Returns the documentatio...

[5] tools/call — query_database(table=users)
    isError: False
    Returned 2 record(s) from users

[6] tools/call — execute_python
    isError: False
    Output:  Sum 1..10 = 55

[7] tools/call — execute_python (security test: import os)
    isError: True
    Output:  Error: Forbidden operation: 'import' is not allowed.

[8] tools/call — lookup_documentation(topic=tools)
    Preview: # MCP Tools  Tools are the action primitives of MCP. A tool has: - name: snake_case identifier - des...

✓ MCP server demo complete.
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
| `Server not initialized` in server mode | The first message was not `initialize` | Send `initialize` first, as every MCP host does |
| `UnicodeEncodeError` printing `—` or `✓` on Windows | The console uses a legacy code page | Set `PYTHONUTF8=1`, or run in Windows Terminal |

## Going Further

- Add `prompts/list` and `prompts/get` with an `analyze_table` prompt, and declare the `prompts` capability (Lab Question 1).
- Add a `db://schema` resource describing both tables (Lab Question 2).
- Log every method call, with its parameters and a timestamp, to `mcp-server.log` (Lab Question 4).
- Find a snippet that defeats the blocklist, then explain what a real sandbox (a separate process, container or WebAssembly runtime) would do instead (Lab Question 3).

## Files

| Path | Purpose |
|---|---|
| `src/lab.py` | Your starting point: runs, with 3 TODOs |
| `solution/lab.py` | Reference implementation |
| `tests/test_lab.py` | 11 tests, run against `solution/` |
| `expected/output.txt` | Captured output of the reference |
