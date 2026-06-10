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


def test_json_response_redacts_email_and_phone_values():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"email": "ada@example.com", "phone": "+1 415 555 0100"},
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

    assert result["data"]["email"] == "a***@example.com"
    assert result["data"]["phone"] == "[REDACTED_PHONE]"


def test_text_response_redacts_secrets_email_and_phone():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="token=secret-token email ada@example.com phone +1 415 555 0100",
        )

    request_plan = build_http_request(
        Operation(method="GET", path="/log", server_urls=["https://api.example.com"]),
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

    assert "secret-token" not in result["data"]
    assert "ada@example.com" not in result["data"]
    assert "+1 415 555 0100" not in result["data"]
    assert "[REDACTED]" in result["data"]


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


def test_network_error_message_is_redacted():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("failed with token=secret-token", request=request)

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
    assert "secret-token" not in result["error"]["message"]
    assert "[REDACTED]" in result["error"]["message"]
