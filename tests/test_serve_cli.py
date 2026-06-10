from typer.testing import CliRunner

from safe_oas2mcp.cli import app, build_gateway_from_files


runner = CliRunner()


def test_cli_help_lists_serve_command():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "serve" in result.stdout


def test_build_gateway_from_files_registers_enabled_and_confirm_tools(tmp_path):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
servers:
  - url: https://api.todo.example.com
paths:
  /tasks:
    get:
      operationId: listTasks
      summary: List tasks
      responses:
        "200":
          description: OK
    post:
      operationId: createTask
      summary: Create task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
      responses:
        "201":
          description: Created
  /tasks/{task_id}:
    delete:
      operationId: deleteTask
      summary: Delete task
      parameters:
        - name: task_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "204":
          description: Deleted
""".strip(),
        encoding="utf-8",
    )

    gateway = build_gateway_from_files(spec_path, config_path=None)

    assert [tool.name for tool in gateway.list_tools()] == ["list_tasks", "create_task"]


def test_serve_missing_file_returns_non_zero_exit_code(tmp_path):
    result = runner.invoke(app, ["serve", str(tmp_path / "missing.yaml")])

    assert result.exit_code == 1
    assert "OpenAPI file not found" in result.stderr
