import asyncio
import json

import httpx

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.gateway import SafeGateway
from safe_oas2mcp.models import Operation


def test_audit_log_is_disabled_by_default(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    gateway = SafeGateway(
        operations=[Operation(method="POST", path="/tasks", operation_id="createTask")],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )

    asyncio.run(gateway.call_tool("create_task", {"body": {"title": "Task"}}))

    assert not audit_path.exists()


def test_audit_log_records_preview_without_secrets(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    gateway = SafeGateway(
        operations=[
            Operation(
                method="POST",
                path="/tasks",
                operation_id="createTask",
                request_body_schema={
                    "type": "object",
                    "properties": {"password": {"type": "string"}},
                },
            )
        ],
        config=SafeOASConfig.model_validate(
            {
                "base_url": "https://api.example.com",
                "audit": {"enabled": True, "path": str(audit_path)},
            }
        ),
    )

    asyncio.run(
        gateway.call_tool("create_task", {"body": {"password": "secret-password"}})
    )

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    serialized = json.dumps(record)
    assert record["tool"] == "create_task"
    assert record["method"] == "POST"
    assert record["path"] == "/tasks"
    assert record["risk"] == "high"
    assert record["status"] == "confirm"
    assert record["executed"] is False
    assert "secret-password" not in serialized


def test_audit_log_records_executed_http_result(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "secret-token"})

    gateway = SafeGateway(
        operations=[
            Operation(
                method="GET",
                path="/tasks",
                operation_id="listTasks",
                server_urls=["https://api.example.com"],
            )
        ],
        config=SafeOASConfig.model_validate(
            {"audit": {"enabled": True, "path": str(audit_path)}}
        ),
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(gateway.call_tool("list_tasks", {}))

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    serialized = json.dumps(record)
    assert record["tool"] == "list_tasks"
    assert record["executed"] is True
    assert record["http_status_code"] == 200
    assert record["duration_ms"] >= 0
    assert "secret-token" not in serialized


def test_audit_log_records_truncated_response(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="x" * 20)

    gateway = SafeGateway(
        operations=[
            Operation(
                method="GET",
                path="/large",
                operation_id="getLarge",
                server_urls=["https://api.example.com"],
            )
        ],
        config=SafeOASConfig.model_validate(
            {
                "audit": {"enabled": True, "path": str(audit_path)},
                "max_response_bytes": 10,
            }
        ),
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(gateway.call_tool("get_large", {}))

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["executed"] is True
    assert record["error_category"] == "response_too_large"
    assert record["truncated"] is True
