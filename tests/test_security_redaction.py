import asyncio

import httpx

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.http.executor import build_http_request, execute_http_request
from safe_oas2mcp.models import Operation


def test_json_response_redacts_secret_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "user": {
                    "name": "Ada",
                    "access_token": "secret-token",
                    "password": "secret-password",
                }
            },
        )

    request_plan = build_http_request(
        Operation(method="GET", path="/me", server_urls=["https://api.example.com"]),
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

    assert result["data"]["user"]["name"] == "Ada"
    assert result["data"]["user"]["access_token"] == "[REDACTED]"
    assert result["data"]["user"]["password"] == "[REDACTED]"


def test_response_larger_than_limit_is_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="x" * 20)

    request_plan = build_http_request(
        Operation(method="GET", path="/large", server_urls=["https://api.example.com"]),
        {},
        SafeOASConfig(),
    )

    result = asyncio.run(
        execute_http_request(
            request_plan,
            timeout_seconds=30,
            max_response_bytes=10,
            transport=httpx.MockTransport(handler),
        )
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "response_too_large"
    assert result["truncated"] is True

