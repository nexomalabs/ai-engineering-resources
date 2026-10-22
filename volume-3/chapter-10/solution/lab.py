"""Lab 10 — MCP-Compatible Server with Stdio Transport (reference solution).

An MCP server implementing:
  - resources/list   — list available resources
  - resources/read   — read a specific resource
  - tools/list       — list available tools
  - tools/call       — invoke a tool
  - initialize       — capability negotiation

Run as a server:      python solution/lab.py server
Run as a client test: python solution/lab.py client
"""

import io
import json
import sys
import textwrap

MCP_VERSION = "2024-11-05"

# ── Resource Data ─────────────────────────────────────────────────────────────
DOCUMENTATION = {
    "docs://mcp/overview": {
        "name": "MCP Overview",
        "mimeType": "text/markdown",
        "text": textwrap.dedent("""
            # Model Context Protocol (MCP)

            MCP is a standard protocol for connecting AI models to external data
            sources and tools. It defines resources (read-only data), tools
            (executable actions), and prompts (reusable templates).

            ## Core Concepts
            - **Resources**: URI-identified read-only content
            - **Tools**: Functions with side effects, invokable by the LLM
            - **Prompts**: Parameterizable message templates
            - **Sampling**: Server-initiated LLM generation
        """).strip(),
    },
    "docs://mcp/tools": {
        "name": "MCP Tools Guide",
        "mimeType": "text/markdown",
        "text": textwrap.dedent("""
            # MCP Tools

            Tools are the action primitives of MCP. A tool has:
            - name: snake_case identifier
            - description: natural language for LLM consumption
            - inputSchema: JSON Schema for arguments

            Tools are invoked via tools/call with name and arguments.
            The result includes content (list of content items) and isError flag.
        """).strip(),
    },
}

DATABASE = {
    "table:users": [
        {"id": 1, "name": "Alice Smith", "role": "admin", "active": True},
        {"id": 2, "name": "Bob Jones", "role": "editor", "active": True},
        {"id": 3, "name": "Carol White", "role": "viewer", "active": False},
    ],
    "table:products": [
        {"id": "P001", "name": "Widget Pro", "price": 49.99, "stock": 150},
        {"id": "P002", "name": "Gadget Plus", "price": 89.99, "stock": 42},
        {"id": "P003", "name": "Doohickey Max", "price": 24.99, "stock": 0},
    ],
}


# ── Server Implementation ─────────────────────────────────────────────────────
class MCPServer:
    """
    A minimal MCP-compatible server using stdio transport.
    Implements the MCP protocol over JSON-RPC 2.0.
    """

    RESOURCES = [
        {
            "uri": "docs://mcp/overview",
            "name": "MCP Overview Documentation",
            "description": "Introduction to the Model Context Protocol",
            "mimeType": "text/markdown",
        },
        {
            "uri": "docs://mcp/tools",
            "name": "MCP Tools Guide",
            "description": "Guide to implementing MCP tools",
            "mimeType": "text/markdown",
        },
        {
            "uri": "db://users",
            "name": "Users Table",
            "description": "All user records from the database",
            "mimeType": "application/json",
        },
        {
            "uri": "db://products",
            "name": "Products Table",
            "description": "Product catalog with pricing and stock levels",
            "mimeType": "application/json",
        },
    ]

    TOOLS = [
        {
            "name": "query_database",
            "description": (
                "Query the in-memory database. Supports 'users' and 'products' tables. "
                "Returns matching records as JSON."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": ["users", "products"],
                        "description": "The table to query",
                    },
                    "filter_key": {
                        "type": "string",
                        "description": "Optional field name to filter on",
                    },
                    "filter_value": {
                        "description": "Optional value to match in filter_key",
                    },
                },
                "required": ["table"],
            },
        },
        {
            "name": "execute_python",
            "description": (
                "Execute a Python code snippet in a restricted environment. "
                "Only math, json, and string operations are allowed. "
                "Returns the result of the last expression or printed output."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute (max 500 chars, no imports)",
                    }
                },
                "required": ["code"],
            },
        },
        {
            "name": "lookup_documentation",
            "description": "Look up MCP documentation by topic. Returns the documentation text.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["overview", "tools"],
                        "description": "Documentation topic to retrieve",
                    }
                },
                "required": ["topic"],
            },
        },
    ]

    def __init__(self, stdin=None, stdout=None):
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.initialized = False

    def _send(self, message: dict) -> None:
        line = json.dumps(message) + "\n"
        self.stdout.write(line)
        self.stdout.flush()

    def _error(self, request_id, code: int, message: str) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )

    def _result(self, request_id, result: dict) -> None:
        self._send({"jsonrpc": "2.0", "id": request_id, "result": result})

    # ── Request Handlers ──────────────────────────────────────────────────────

    def handle_initialize(self, request_id, params: dict) -> None:
        self.initialized = True
        self._result(
            request_id,
            {
                "protocolVersion": MCP_VERSION,
                "serverInfo": {"name": "lab-mcp-server", "version": "1.0.0"},
                "capabilities": {
                    "resources": {"subscribe": False, "listChanged": False},
                    "tools": {"listChanged": False},
                },
            },
        )

    def handle_resources_list(self, request_id, params: dict) -> None:
        self._result(request_id, {"resources": self.RESOURCES})

    def handle_resources_read(self, request_id, params: dict) -> None:
        uri = params.get("uri", "")
        if uri.startswith("docs://"):
            doc = DOCUMENTATION.get(uri)
            if not doc:
                return self._error(request_id, -32002, f"Resource not found: {uri}")
            self._result(
                request_id,
                {"contents": [{"uri": uri, "mimeType": doc["mimeType"], "text": doc["text"]}]},
            )
        elif uri.startswith("db://"):
            table_name = uri.replace("db://", "")
            key = f"table:{table_name}"
            data = DATABASE.get(key)
            if data is None:
                return self._error(request_id, -32002, f"Table not found: {table_name}")
            self._result(
                request_id,
                {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(data, indent=2),
                        }
                    ]
                },
            )
        else:
            self._error(request_id, -32602, f"Unknown URI scheme: {uri}")

    def handle_tools_list(self, request_id, params: dict) -> None:
        self._result(request_id, {"tools": self.TOOLS})

    def handle_tools_call(self, request_id, params: dict) -> None:
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "query_database":
                result_text = self._tool_query_database(args)
            elif name == "execute_python":
                result_text = self._tool_execute_python(args)
            elif name == "lookup_documentation":
                result_text = self._tool_lookup_documentation(args)
            else:
                return self._error(request_id, -32602, f"Unknown tool: {name}")
            self._result(
                request_id,
                {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False,
                },
            )
        except ValueError as e:
            self._result(
                request_id,
                {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                },
            )

    def _tool_query_database(self, args: dict) -> str:
        table = args.get("table")
        if table not in ("users", "products"):
            raise ValueError(f"Invalid table: {table}")
        records = DATABASE[f"table:{table}"]
        filter_key = args.get("filter_key")
        filter_value = args.get("filter_value")
        if filter_key and filter_value is not None:
            records = [r for r in records if str(r.get(filter_key)) == str(filter_value)]
        return json.dumps({"table": table, "rows": records, "count": len(records)}, indent=2)

    def _tool_execute_python(self, args: dict) -> str:
        code = args.get("code", "")
        if len(code) > 500:
            raise ValueError("Code exceeds 500 character limit.")
        # Restricted execution environment
        forbidden = [
            "import",
            "__import__",
            "open(",
            "exec(",
            "eval(",
            "os.",
            "sys.",
            "subprocess",
            "socket",
            "__builtins__",
        ]
        for term in forbidden:
            if term in code:
                raise ValueError(f"Forbidden operation: '{term}' is not allowed.")
        sandbox = {
            "__builtins__": {
                "abs": abs,
                "len": len,
                "round": round,
                "range": range,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "list": list,
                "dict": dict,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "print": print,
            }
        }
        output_buffer = io.StringIO()
        original_stdout = sys.stdout
        try:
            sys.stdout = output_buffer
            exec(compile(code, "<mcp_sandbox>", "exec"), sandbox)
            sys.stdout = original_stdout
        except Exception as e:
            sys.stdout = original_stdout
            return f"Execution error: {type(e).__name__}: {e}"
        captured = output_buffer.getvalue()
        return captured if captured else "Code executed successfully (no output)."

    def _tool_lookup_documentation(self, args: dict) -> str:
        topic = args.get("topic")
        uri_map = {"overview": "docs://mcp/overview", "tools": "docs://mcp/tools"}
        uri = uri_map.get(topic)
        if not uri:
            raise ValueError(f"Unknown topic: {topic}")
        return DOCUMENTATION[uri]["text"]

    # ── Main Dispatch Loop ────────────────────────────────────────────────────

    def serve(self) -> None:
        """Main message dispatch loop — reads JSON-RPC messages from stdin."""
        for line in self.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                )
                continue
            self.dispatch(message)

    def dispatch(self, message: dict) -> None:
        """Route one JSON-RPC message to its handler."""
        method = message.get("method", "")
        request_id = message.get("id")
        params = message.get("params", {})

        # Notifications have no id — no response expected
        if request_id is None and method.startswith("notifications/"):
            return

        if method == "initialize":
            self.handle_initialize(request_id, params)
        elif not self.initialized:
            self._error(request_id, -32600, "Server not initialized")
        elif method == "resources/list":
            self.handle_resources_list(request_id, params)
        elif method == "resources/read":
            self.handle_resources_read(request_id, params)
        elif method == "tools/list":
            self.handle_tools_list(request_id, params)
        elif method == "tools/call":
            self.handle_tools_call(request_id, params)
        else:
            self._error(request_id, -32601, f"Method not found: {method}")


# ── Client Simulator (for lab testing) ───────────────────────────────────────
class MCPClientSimulator:
    """
    Simulates an MCP client communicating with the server via in-process pipes.
    Used for testing without spawning a subprocess.
    """

    def __init__(self):
        self.request_id = 0
        # The server writes its responses to an in-memory buffer instead of stdout
        self.server_out = io.StringIO()
        self.server = MCPServer(stdin=None, stdout=self.server_out)

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def _call(self, method: str, params: dict) -> dict:
        """Send one request to the server and return its response."""
        req_id = self._next_id()
        message = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}

        # Capture current output position
        pos_before = self.server_out.tell()

        # Route the request through the same dispatch the stdio loop uses
        self.server.dispatch(message)

        # Read response
        self.server_out.seek(pos_before)
        response_line = self.server_out.readline()
        if response_line:
            return json.loads(response_line)
        return {}

    def run_demo(self):
        print("\n" + "=" * 60)
        print("MCP SERVER DEMO — Stdio Transport Simulation")
        print("=" * 60)

        # 1. Initialize
        print("\n[1] Initialize")
        resp = self._call(
            "initialize",
            {
                "protocolVersion": MCP_VERSION,
                "clientInfo": {"name": "lab-client", "version": "1.0"},
                "capabilities": {"sampling": {}},
            },
        )
        info = resp.get("result", {})
        print(f"    Server: {info.get('serverInfo', {})}")
        print(f"    Capabilities: {list(info.get('capabilities', {}).keys())}")

        # 2. List resources
        print("\n[2] resources/list")
        resp = self._call("resources/list", {})
        resources = resp.get("result", {}).get("resources", [])
        for r in resources:
            print(f"    {r['uri']} — {r['name']}")

        # 3. Read documentation resource
        print("\n[3] resources/read — docs://mcp/overview")
        resp = self._call("resources/read", {"uri": "docs://mcp/overview"})
        content = resp.get("result", {}).get("contents", [{}])[0]
        preview = content.get("text", "")[:120].replace("\n", " ")
        print(f"    [{content.get('mimeType')}] {preview}...")

        # 4. List tools
        print("\n[4] tools/list")
        resp = self._call("tools/list", {})
        tools = resp.get("result", {}).get("tools", [])
        for t in tools:
            print(f"    {t['name']} — {t['description'][:60]}...")

        # 5. Invoke query_database
        print("\n[5] tools/call — query_database(table=users)")
        resp = self._call(
            "tools/call",
            {
                "name": "query_database",
                "arguments": {"table": "users", "filter_key": "active", "filter_value": "True"},
            },
        )
        result = resp.get("result", {})
        print(f"    isError: {result.get('isError')}")
        content_text = result.get("content", [{}])[0].get("text", "")
        data = json.loads(content_text)
        print(f"    Returned {data['count']} record(s) from {data['table']}")

        # 6. Invoke execute_python
        print("\n[6] tools/call — execute_python")
        code = "result = sum(range(1, 11))\nprint(f'Sum 1..10 = {result}')"
        resp = self._call(
            "tools/call",
            {
                "name": "execute_python",
                "arguments": {"code": code},
            },
        )
        result = resp.get("result", {})
        print(f"    isError: {result.get('isError')}")
        print(f"    Output:  {result.get('content', [{}])[0].get('text', '').strip()}")

        # 7. Security test — forbidden operation
        print("\n[7] tools/call — execute_python (security test: import os)")
        resp = self._call(
            "tools/call",
            {
                "name": "execute_python",
                "arguments": {"code": "import os; print(os.getcwd())"},
            },
        )
        result = resp.get("result", {})
        print(f"    isError: {result.get('isError')}")
        print(f"    Output:  {result.get('content', [{}])[0].get('text', '').strip()[:80]}")

        # 8. Invoke lookup_documentation
        print("\n[8] tools/call — lookup_documentation(topic=tools)")
        resp = self._call(
            "tools/call",
            {
                "name": "lookup_documentation",
                "arguments": {"topic": "tools"},
            },
        )
        result = resp.get("result", {})
        preview = result.get("content", [{}])[0].get("text", "")[:100].replace("\n", " ")
        print(f"    Preview: {preview}...")

        print("\n✓ MCP server demo complete.")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "client"
    if mode == "server":
        # Run as a real stdio server (used when spawned by a real MCP host)
        server = MCPServer()
        server.serve()
    else:
        # Run the in-process client simulation for lab demonstration
        client = MCPClientSimulator()
        client.run_demo()
