from pathlib import Path

from safe_oas2mcp.cli import inspect_openapi


def test_todo_example_inspects_expected_statuses():
    payload = inspect_openapi(Path("examples/todo/openapi.yaml"))

    assert payload["summary"]["enabled"] >= 1
    assert payload["summary"]["confirm"] >= 1
    assert payload["summary"]["disabled"] >= 1


def test_petstore_subset_example_can_be_inspected():
    payload = inspect_openapi(Path("examples/petstore/openapi.yaml"))

    assert payload["summary"]["total"] >= 1
    assert all(tool["reasons"] for tool in payload["tools"])

