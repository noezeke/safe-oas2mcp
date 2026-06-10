from safe_oas2mcp.config import AuthConfig, HeaderValueConfig, SafeOASConfig
from safe_oas2mcp.http.executor import build_http_request
from safe_oas2mcp.models import Operation, Parameter


def test_builds_request_from_path_query_and_json_body(monkeypatch):
    monkeypatch.setenv("TODO_TOKEN", "secret-token")
    monkeypatch.setenv("WORKSPACE_ID", "workspace-123")
    operation = Operation(
        method="PATCH",
        path="/tasks/{task_id}",
        server_urls=["https://openapi.example.com"],
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
        request_body_schema={"type": "object"},
    )
    config = SafeOASConfig(
        base_url="https://api.todo.example.com",
        auth=AuthConfig(type="bearer", token_env="TODO_TOKEN"),
        headers={"X-Workspace-Id": HeaderValueConfig(env="WORKSPACE_ID")},
    )

    request = build_http_request(
        operation,
        {"task_id": "task-1", "notify": True, "body": {"title": "Updated"}},
        config,
    )

    assert request.method == "PATCH"
    assert request.url == "https://api.todo.example.com/tasks/task-1"
    assert request.query == {"notify": True}
    assert request.json_body == {"title": "Updated"}
    assert request.headers["Authorization"] == "Bearer secret-token"
    assert request.headers["X-Workspace-Id"] == "workspace-123"


def test_uses_openapi_server_url_when_config_base_url_is_missing():
    operation = Operation(
        method="GET",
        path="/tasks",
        server_urls=["https://openapi.example.com"],
    )

    request = build_http_request(operation, {}, SafeOASConfig())

    assert request.url == "https://openapi.example.com/tasks"


def test_ignores_model_supplied_base_url():
    operation = Operation(
        method="GET",
        path="/tasks",
        server_urls=["https://openapi.example.com"],
    )

    request = build_http_request(
        operation,
        {"base_url": "https://evil.example.com"},
        SafeOASConfig(base_url="https://api.todo.example.com"),
    )

    assert request.url == "https://api.todo.example.com/tasks"


def test_api_key_auth_uses_configured_header(monkeypatch):
    monkeypatch.setenv("TODO_API_KEY", "api-key-secret")
    operation = Operation(method="GET", path="/tasks", server_urls=["https://api.example.com"])
    config = SafeOASConfig(
        auth=AuthConfig(
            type="api_key",
            key_env="TODO_API_KEY",
            header_name="X-API-Key",
        )
    )

    request = build_http_request(operation, {}, config)

    assert request.headers["X-API-Key"] == "api-key-secret"

