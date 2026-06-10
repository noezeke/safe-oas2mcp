import asyncio

import httpx

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.gateway import SafeGateway
from safe_oas2mcp.models import Operation, Parameter


def test_gateway_lists_enabled_and_confirm_tools_but_not_disabled():
    gateway = SafeGateway(
        operations=[
            Operation(method="GET", path="/tasks", operation_id="listTasks"),
            Operation(method="POST", path="/tasks", operation_id="createTask"),
            Operation(method="DELETE", path="/tasks/{id}", operation_id="deleteTask"),
        ],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )

    tools = gateway.list_tools()

    assert [tool.name for tool in tools] == ["list_tasks", "create_task"]


def test_gateway_returns_preview_for_confirm_tool_without_executing_http():
    gateway = SafeGateway(
        operations=[Operation(method="POST", path="/tasks", operation_id="createTask")],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )

    result = asyncio.run(gateway.call_tool("create_task", {"body": {"title": "New"}}))

    assert result["status"] == "confirmation_required"
    assert result["method"] == "POST"
    assert result["url"] == "https://api.example.com/tasks"
    assert result["executed"] is False


def test_gateway_executes_enabled_tool():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": []})

    gateway = SafeGateway(
        operations=[
            Operation(
                method="GET",
                path="/tasks",
                operation_id="listTasks",
                server_urls=["https://api.example.com"],
            )
        ],
        config=SafeOASConfig(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(gateway.call_tool("list_tasks", {}))

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["data"] == {"items": []}


def test_gateway_rejects_unknown_tool():
    gateway = SafeGateway(operations=[], config=SafeOASConfig(base_url="https://api.example.com"))

    result = asyncio.run(gateway.call_tool("missing_tool", {}))

    assert result["ok"] is False
    assert result["error"]["type"] == "unknown_tool"


def test_gateway_applies_policy_override_to_register_delete_preview():
    gateway = SafeGateway(
        operations=[
            Operation(method="DELETE", path="/tasks/{task_id}", operation_id="deleteTask")
        ],
        config=SafeOASConfig.model_validate(
            {
                "base_url": "https://api.example.com",
                "policy": {
                    "overrides": {
                        "DELETE /tasks/{task_id}": {
                            "status": "confirm",
                            "risk": "high",
                            "reason": "Allow task delete preview only",
                        }
                    }
                },
            }
        ),
    )

    tools = gateway.list_tools()
    result = asyncio.run(gateway.call_tool("delete_task", {"task_id": "task-1"}))

    assert [tool.name for tool in tools] == ["delete_task"]
    assert result["status"] == "confirmation_required"
    assert result["tool_status"] == "confirm"
    assert result["executed"] is False


def test_gateway_preview_redacts_query_and_body_secrets():
    gateway = SafeGateway(
        operations=[
            Operation(
                method="POST",
                path="/tasks",
                operation_id="createTask",
                query_parameters=[
                    Parameter(
                        name="api_key",
                        location="query",
                        schema={"type": "string"},
                    )
                ],
                request_body_schema={
                    "type": "object",
                    "properties": {
                        "password": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            )
        ],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )

    result = asyncio.run(
        gateway.call_tool(
            "create_task",
            {
                "api_key": "secret-api-key",
                "body": {
                    "password": "secret-password",
                    "email": "ada@example.com",
                },
            },
        )
    )

    assert result["query"]["api_key"] == "[REDACTED]"
    assert result["body_preview"]["password"] == "[REDACTED]"
    assert result["body_preview"]["email"] == "a***@example.com"
