import asyncio
import json

import mcp.types as types

from safe_oas2mcp.config import SafeOASConfig
from safe_oas2mcp.gateway import SafeGateway
from safe_oas2mcp.mcp.server import create_mcp_server
from safe_oas2mcp.models import Operation


def test_create_mcp_server_registers_gateway_tools():
    gateway = SafeGateway(
        operations=[Operation(method="GET", path="/tasks", operation_id="listTasks")],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )
    server = create_mcp_server(gateway)

    result = asyncio.run(
        server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())
    )
    tools = result.root.tools

    assert tools[0].name == "list_tasks"
    assert tools[0].inputSchema["type"] == "object"


def test_mcp_call_tool_returns_json_text_content():
    gateway = SafeGateway(
        operations=[
            Operation(
                method="POST",
                path="/tasks",
                operation_id="createTask",
                request_body_required=True,
                request_body_schema={
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                },
            )
        ],
        config=SafeOASConfig(base_url="https://api.example.com"),
    )
    server = create_mcp_server(gateway)

    result = asyncio.run(
        server.request_handlers[types.CallToolRequest](
            types.CallToolRequest(
                params=types.CallToolRequestParams(
                    name="create_task",
                    arguments={"body": {"title": "New"}},
                )
            )
        )
    )
    content = result.root.content[0]
    payload = json.loads(content.text)

    assert content.type == "text"
    assert payload["status"] == "confirmation_required"
    assert payload["executed"] is False
