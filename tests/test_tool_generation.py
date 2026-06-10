from safe_oas2mcp.models import Operation, Parameter
from safe_oas2mcp.openapi.tools import build_tool_metadata


def test_generates_agent_friendly_name_from_operation_id():
    operation = Operation(
        method="GET",
        path="/tasks",
        operation_id="listTasks",
        summary="List tasks",
    )

    tool = build_tool_metadata(operation, used_names=set())

    assert tool.name == "list_tasks"
    assert tool.description == "List tasks"


def test_generates_name_from_method_and_path_without_operation_id():
    operation = Operation(method="GET", path="/tasks/{task_id}/comments")

    tool = build_tool_metadata(operation, used_names=set())

    assert tool.name == "get_tasks_by_task_id_comments"


def test_appends_suffix_for_duplicate_tool_names():
    first = Operation(method="GET", path="/tasks", operation_id="listTasks")
    second = Operation(method="GET", path="/archived-tasks", operation_id="listTasks")
    used_names: set[str] = set()

    first_tool = build_tool_metadata(first, used_names=used_names)
    second_tool = build_tool_metadata(second, used_names=used_names)

    assert first_tool.name == "list_tasks"
    assert second_tool.name == "list_tasks_2"


def test_builds_input_schema_from_path_query_and_body():
    operation = Operation(
        method="PATCH",
        path="/tasks/{task_id}",
        path_parameters=[
            Parameter(
                name="task_id",
                location="path",
                required=True,
                schema={"type": "string"},
            )
        ],
        query_parameters=[
            Parameter(
                name="notify",
                location="query",
                required=False,
                schema={"type": "boolean"},
            )
        ],
        request_body_required=True,
        request_body_schema={
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        },
    )

    tool = build_tool_metadata(operation, used_names=set())

    assert tool.input_schema["required"] == ["task_id", "body"]
    assert tool.input_schema["properties"]["task_id"]["type"] == "string"
    assert tool.input_schema["properties"]["notify"]["type"] == "boolean"
    assert tool.input_schema["properties"]["body"]["required"] == ["title"]


def test_does_not_expose_header_or_auth_parameters_in_input_schema():
    operation = Operation(
        method="GET",
        path="/tasks",
        header_parameters=[
            Parameter(
                name="Authorization",
                location="header",
                required=True,
                schema={"type": "string"},
            ),
            Parameter(
                name="X-Workspace-Id",
                location="header",
                required=False,
                schema={"type": "string"},
            ),
        ],
    )

    tool = build_tool_metadata(operation, used_names=set())

    assert "Authorization" not in tool.input_schema["properties"]
    assert "X-Workspace-Id" not in tool.input_schema["properties"]

