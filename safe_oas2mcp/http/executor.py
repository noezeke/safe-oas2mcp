from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urljoin

import httpx

from safe_oas2mcp.config import ConfigError, SafeOASConfig
from safe_oas2mcp.http.auth import build_configured_headers
from safe_oas2mcp.models import Operation
from safe_oas2mcp.security.redactor import redact_secrets, redact_text


@dataclass(frozen=True)
class HTTPRequestPlan:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, Any] = field(default_factory=dict)
    json_body: Any | None = None


def build_http_request(
    operation: Operation,
    arguments: dict[str, Any],
    config: SafeOASConfig,
) -> HTTPRequestPlan:
    base_url = _base_url(operation, config)
    path = _replace_path_parameters(operation, arguments)
    query = {
        parameter.name: arguments[parameter.name]
        for parameter in operation.query_parameters
        if parameter.name in arguments
    }

    return HTTPRequestPlan(
        method=operation.method,
        url=urljoin(_ensure_trailing_slash(base_url), path.lstrip("/")),
        headers=build_configured_headers(config),
        query=query,
        json_body=arguments.get("body") if operation.request_body_schema is not None else None,
    )


async def execute_http_request(
    request_plan: HTTPRequestPlan,
    timeout_seconds: float,
    max_response_bytes: int,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
            transport=transport,
            trust_env=False,
        ) as client:
            response = await client.request(
                request_plan.method,
                request_plan.url,
                headers=request_plan.headers,
                params=request_plan.query,
                json=request_plan.json_body,
            )
    except httpx.TimeoutException as exc:
        return {
            "ok": False,
            "error": {"type": "timeout", "message": redact_text(str(exc))},
        }
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "error": {"type": "network_error", "message": redact_text(str(exc))},
        }

    if len(response.content) > max_response_bytes:
        return {
            "ok": False,
            "status_code": response.status_code,
            "error": {
                "type": "response_too_large",
                "message": f"Response exceeded limit of {max_response_bytes} bytes",
            },
            "truncated": True,
        }

    data = redact_secrets(_response_data(response))
    return {
        "ok": 200 <= response.status_code < 300,
        "status_code": response.status_code,
        "headers": {"content-type": response.headers.get("content-type", "")},
        "data": data,
    }


def _base_url(operation: Operation, config: SafeOASConfig) -> str:
    if config.base_url:
        return config.base_url
    if operation.server_urls:
        return operation.server_urls[0]
    raise ConfigError("No base_url configured and OpenAPI operation has no server URL")


def _replace_path_parameters(operation: Operation, arguments: dict[str, Any]) -> str:
    path = operation.path
    for parameter in operation.path_parameters:
        if parameter.name not in arguments:
            raise ConfigError(f"Missing required path parameter: {parameter.name}")
        encoded = quote(str(arguments[parameter.name]), safe="")
        path = path.replace("{" + parameter.name + "}", encoded)
    return path


def _ensure_trailing_slash(value: str) -> str:
    return value if value.endswith("/") else value + "/"


def _response_data(response: httpx.Response) -> Any:
    if not response.content:
        return None

    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return response.json()
        except ValueError:
            return response.text

    return response.text
