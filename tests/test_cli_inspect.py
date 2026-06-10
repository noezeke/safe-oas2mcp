import json

from typer.testing import CliRunner

from safe_oas2mcp.cli import app


runner = CliRunner()


def test_inspect_outputs_json_with_risk_status_and_reasons(tmp_path):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
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
              required: [title]
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

    result = runner.invoke(app, ["inspect", str(spec_path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    tools = {tool["name"]: tool for tool in payload["tools"]}
    assert tools["list_tasks"]["risk"] == "low"
    assert tools["list_tasks"]["status"] == "enabled"
    assert tools["create_task"]["status"] == "confirm"
    assert tools["delete_task"]["risk"] == "critical"
    assert tools["delete_task"]["status"] == "disabled"
    assert tools["delete_task"]["reasons"]


def test_inspect_table_shows_disabled_tools_and_reasons(tmp_path):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
paths:
  /reports/export:
    get:
      operationId: exportReports
      summary: Export reports
      responses:
        "200":
          description: OK
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["inspect", str(spec_path)])

    assert result.exit_code == 0
    assert "export_reports" in result.stdout
    assert "GET" in result.stdout
    assert "/reports/export" in result.stdout
    assert "high" in result.stdout
    assert "confirm" in result.stdout
    assert "high-risk keyword" in result.stdout
    assert "Summary:" in result.stdout


def test_inspect_missing_file_returns_non_zero_exit_code(tmp_path):
    result = runner.invoke(app, ["inspect", str(tmp_path / "missing.yaml")])

    assert result.exit_code == 1
    assert "OpenAPI file not found" in result.stderr


def test_inspect_rejects_unknown_format(tmp_path):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
paths: {}
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["inspect", str(spec_path), "--format", "xml"])

    assert result.exit_code == 1
    assert "--format must be either 'table' or 'json'" in result.stderr
