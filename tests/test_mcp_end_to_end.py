import asyncio
import json
from pathlib import Path

import mcp.types as types

from safe_oas2mcp.cli import build_gateway_from_files
from safe_oas2mcp.mcp.server import create_mcp_server


def test_openapi_file_becomes_mcp_tools_with_safe_defaults():
    gateway = build_gateway_from_files(Path("examples/todo/openapi.yaml"), config_path=None)
    server = create_mcp_server(gateway)

    tools_result = asyncio.run(
        server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
    )
    tool_names = [tool.name for tool in tools_result.root.tools]

    assert "list_tasks" in tool_names
    assert "create_task" in tool_names
    assert "delete_task" not in tool_names

    call_result = asyncio.run(
        server.request_handlers[types.CallToolRequest](
            types.CallToolRequest(
                params=types.CallToolRequestParams(
                    name="create_task",
                    arguments={"body": {"title": "New task"}},
                )
            )
        )
    )
    payload = json.loads(call_result.root.content[0].text)

    assert payload["status"] == "confirmation_required"
    assert payload["executed"] is False


def test_confirm_patch_returns_preview_and_auth_is_not_in_tool_schema(monkeypatch):
    monkeypatch.setenv("TODO_TOKEN", "secret-token")
    gateway = build_gateway_from_files(Path("examples/todo/openapi.yaml"), config_path=None)
    server = create_mcp_server(gateway)

    tools_result = asyncio.run(
        server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
    )
    update_tool = next(tool for tool in tools_result.root.tools if tool.name == "update_task")
    serialized_schema = json.dumps(update_tool.inputSchema)

    assert "Authorization" not in serialized_schema
    assert "secret-token" not in serialized_schema

    call_result = asyncio.run(
        server.request_handlers[types.CallToolRequest](
            types.CallToolRequest(
                params=types.CallToolRequestParams(
                    name="update_task",
                    arguments={
                        "task_id": "task-1",
                        "body": {"completed": True},
                    },
                )
            )
        )
    )
    payload = json.loads(call_result.root.content[0].text)

    assert payload["status"] == "confirmation_required"
    assert payload["executed"] is False
