"""Tests for Lab 10. Run against solution/ in CI."""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solution"))

from lab import MCP_VERSION, MCPClientSimulator, MCPServer  # noqa: E402


def run_server(*messages):
    """Feed lines to serve() and return the parsed responses."""
    lines = [m if isinstance(m, str) else json.dumps(m) for m in messages]
    out = io.StringIO()
    MCPServer(stdin=io.StringIO("\n".join(lines) + "\n"), stdout=out).serve()
    return [json.loads(line) for line in out.getvalue().splitlines()]


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}


def call(client, name, arguments):
    return client._call("tools/call", {"name": name, "arguments": arguments})


def initialized_client():
    client = MCPClientSimulator()
    client._call("initialize", {"protocolVersion": MCP_VERSION})
    return client


def test_initialize_declares_only_implemented_capabilities():
    (resp,) = run_server(INIT)
    assert resp["result"]["protocolVersion"] == MCP_VERSION
    assert set(resp["result"]["capabilities"]) == {"resources", "tools"}


def test_requests_before_initialize_are_refused():
    (resp,) = run_server({"jsonrpc": "2.0", "id": 7, "method": "tools/list"})
    assert resp["id"] == 7
    assert resp["error"]["code"] == -32600


def test_notifications_get_no_response_and_bad_json_gets_a_parse_error():
    responses = run_server(
        INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"}, "{not json"
    )
    assert [r.get("id") for r in responses] == [1, None]
    assert responses[1]["error"]["code"] == -32700


def test_unknown_method():
    _, resp = run_server(INIT, {"jsonrpc": "2.0", "id": 2, "method": "sampling/run"})
    assert resp["error"]["code"] == -32601


def test_read_resource_and_missing_resource():
    client = initialized_client()
    ok = client._call("resources/read", {"uri": "db://products"})
    rows = json.loads(ok["result"]["contents"][0]["text"])
    assert [r["id"] for r in rows] == ["P001", "P002", "P003"]
    missing = client._call("resources/read", {"uri": "docs://mcp/nothing"})
    assert missing["error"]["code"] == -32002


def test_query_database_filters():
    client = initialized_client()
    resp = call(
        client, "query_database", {"table": "products", "filter_key": "stock", "filter_value": 0}
    )
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data["count"] == 1
    assert data["rows"][0]["name"] == "Doohickey Max"


def test_tool_failure_is_a_result_with_is_error():
    client = initialized_client()
    resp = call(client, "query_database", {"table": "orders"})
    assert "error" not in resp
    assert resp["result"]["isError"] is True
    assert resp["result"]["content"][0]["text"] == "Error: Invalid table: orders"


def test_unknown_tool_is_a_protocol_error():
    client = initialized_client()
    resp = call(client, "drop_tables", {})
    assert resp["error"] == {"code": -32602, "message": "Unknown tool: drop_tables"}


def test_execute_python_captures_output():
    client = initialized_client()
    resp = call(client, "execute_python", {"code": "print(sum(range(4)))"})
    assert resp["result"]["content"][0]["text"] == "6\n"


def test_execute_python_blocks_forbidden_terms():
    client = initialized_client()
    resp = call(client, "execute_python", {"code": "import os"})
    assert resp["result"]["isError"] is True
    assert "Forbidden operation: 'import'" in resp["result"]["content"][0]["text"]


def test_execute_python_rejects_long_code():
    client = initialized_client()
    resp = call(client, "execute_python", {"code": "x = 1\n" * 100})
    assert resp["result"]["isError"] is True
