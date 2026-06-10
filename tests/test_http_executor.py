import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.http.executor import build_http_request, execute_http_request
from safe_oas2mcp.models import Operation


def test_execute_get_request_returns_json_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://api.example.com/tasks?status=open"
        return httpx.Response(200, json={"items": [{"id": "task-1"}]})

    operation = Operation(
        method="GET",
        path="/tasks",
        server_urls=["https://api.example.com"],
        query_parameters=[
            {
                "name": "status",
                "location": "query",
                "required": False,
                "schema": {"type": "string"},
            }
        ],
    )
    request_plan = build_http_request(operation, {"status": "open"}, SafeOASConfig())

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["data"] == {"items": [{"id": "task-1"}]}


def test_execute_request_returns_text_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="pong", headers={"content-type": "text/plain"})

    request_plan = build_http_request(
        Operation(method="GET", path="/ping", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is True
    assert result["data"] == "pong"


def test_execute_request_returns_structured_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    request_plan = build_http_request(
        Operation(method="GET", path="/missing", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is False
    assert result["status_code"] == 404
    assert result["data"] == {"error": "not found"}


def test_execute_request_returns_structured_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server error"})

    request_plan = build_http_request(
        Operation(method="GET", path="/broken", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert result["data"] == {"error": "server error"}


def test_execute_request_handles_empty_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    request_plan = build_http_request(
        Operation(method="GET", path="/empty", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is True
    assert result["status_code"] == 204
    assert result["data"] is None


def test_execute_request_returns_structured_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    request_plan = build_http_request(
        Operation(method="GET", path="/tasks", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "network_error"
    assert "connection refused" in result["error"]["message"]


def test_execute_request_returns_structured_timeout_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    request_plan = build_http_request(
        Operation(method="GET", path="/tasks", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=1024,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "timeout"


def test_execute_request_ignores_ambient_proxy_for_direct_api_calls(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = b'{"items":[{"id":"task-1"}]}'
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
        monkeypatch.delenv("NO_PROXY", raising=False)
        port = server.server_address[1]
        request_plan = build_http_request(
            Operation(method="GET", path="/tasks", server_urls=[f"http://127.0.0.1:{port}"]),
            {},
            SafeOASConfig(),
        )

        result = asyncio.run(
            execute_http_request(
                request_plan,
                timeout_seconds=3,
                max_response_bytes=1024,
            )
        )

        assert result["ok"] is True
        assert result["data"] == {"items": [{"id": "task-1"}]}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_executor_supports_write_methods_even_when_policy_blocks_registration():
    seen_methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_methods.append(request.method)
        return httpx.Response(200, json={"ok": True})

    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        request_plan = build_http_request(
            Operation(method=method, path="/tasks", server_urls=["https://api.example.com"]),
            {"body": {"title": "Task"}},
            SafeOASConfig(),
        )
        result = asyncio.run(
            execute_http_request(
                request_plan,
                timeout_seconds=30,
                max_response_bytes=1024,
                transport=httpx.MockTransport(handler),
            )
        )
        assert result["ok"] is True

    assert seen_methods == ["POST", "PUT", "PATCH", "DELETE"]
