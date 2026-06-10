from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import httpx

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.http.executor import (
    HTTPRequestPlan,
    build_http_request,
    execute_http_request,
)
from safe_oas2mcp.models import Operation, RiskResult, ToolMetadata
from safe_oas2mcp.openapi.tools import build_tool_metadata
from safe_oas2mcp.policy.engine import evaluate_operation_risk
from safe_oas2mcp.security.audit import write_audit_record
from safe_oas2mcp.security.redactor import redact_secrets


@dataclass(frozen=True)
class RegisteredTool:
    metadata: ToolMetadata
    operation: Operation
    risk: RiskResult


class SafeGateway:
    def __init__(
        self,
        operations: list[Operation],
        config: SafeOASConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport
        self._tools: dict[str, RegisteredTool] = {}
        used_names: set[str] = set()

        for operation in operations:
            metadata = build_tool_metadata(operation, used_names)
            risk = evaluate_operation_risk(operation, self._config.policy)
            if risk.status == "disabled":
                continue
            self._tools[metadata.name] = RegisteredTool(metadata, operation, risk)

    def list_tools(self) -> list[ToolMetadata]:
        return [tool.metadata for tool in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        registered = self._tools.get(name)
        if registered is None:
            return {
                "ok": False,
                "error": {"type": "unknown_tool", "message": f"Unknown tool: {name}"},
            }

        request_plan = build_http_request(
            registered.operation,
            arguments,
            self._config,
        )

        if registered.risk.status == "confirm":
            result = _preview(registered, request_plan)
            self._write_audit(registered, executed=False)
            return result

        started = perf_counter()
        result = await execute_http_request(
            request_plan,
            timeout_seconds=self._config.timeout_seconds,
            max_response_bytes=self._config.max_response_bytes,
            transport=self._transport,
        )

        duration_ms = int((perf_counter() - started) * 1000)
        self._write_audit(
            registered,
            executed=True,
            http_status_code=result.get("status_code"),
            duration_ms=duration_ms,
            error_category=result.get("error", {}).get("type")
            if isinstance(result.get("error"), dict)
            else None,
            truncated=result.get("truncated") is True,
        )
        return result

    def _write_audit(
        self,
        registered: RegisteredTool,
        *,
        executed: bool,
        http_status_code: int | None = None,
        duration_ms: int | None = None,
        error_category: str | None = None,
        truncated: bool = False,
    ) -> None:
        write_audit_record(
            self._config.audit,
            {
                "tool": registered.metadata.name,
                "method": registered.operation.method,
                "path": registered.operation.path,
                "risk": registered.risk.risk,
                "status": registered.risk.status,
                "executed": executed,
                "http_status_code": http_status_code,
                "duration_ms": duration_ms,
                "error_category": error_category,
                "truncated": truncated,
            },
        )


def _preview(registered: RegisteredTool, request_plan: HTTPRequestPlan) -> dict[str, Any]:
    return {
        "status": "confirmation_required",
        "executed": False,
        "tool": registered.metadata.name,
        "tool_status": registered.risk.status,
        "method": request_plan.method,
        "url": request_plan.url,
        "query": redact_secrets(request_plan.query),
        "body_preview": redact_secrets(request_plan.json_body),
        "risk": registered.risk.risk,
        "reasons": registered.risk.reasons,
        "message": "This operation requires confirmation and was not executed.",
    }
