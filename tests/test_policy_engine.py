from safe_oas2mcp.models import Operation
from safe_oas2mcp.policy.engine import evaluate_operation_risk


def test_get_is_enabled_by_default():
    result = evaluate_operation_risk(Operation(method="GET", path="/tasks"))

    assert result.risk == "low"
    assert result.status == "enabled"
    assert "GET is enabled by default" in result.reasons


def test_post_is_confirm_by_default():
    result = evaluate_operation_risk(Operation(method="POST", path="/tasks"))

    assert result.risk == "medium"
    assert result.status == "confirm"
    assert "POST write operation requires confirmation by default" in result.reasons


def test_put_and_patch_are_high_confirm_by_default():
    put_result = evaluate_operation_risk(Operation(method="PUT", path="/tasks/{id}"))
    patch_result = evaluate_operation_risk(Operation(method="PATCH", path="/tasks/{id}"))

    assert put_result.risk == "high"
    assert put_result.status == "confirm"
    assert patch_result.risk == "high"
    assert patch_result.status == "confirm"


def test_delete_is_disabled_by_default():
    result = evaluate_operation_risk(Operation(method="DELETE", path="/tasks/{id}"))

    assert result.risk == "critical"
    assert result.status == "disabled"
    assert "DELETE is disabled by default" in result.reasons


def test_high_risk_keyword_raises_get_risk_and_requires_confirmation():
    result = evaluate_operation_risk(
        Operation(
            method="GET",
            path="/reports/export",
            operation_id="exportUsers",
            summary="Export users",
            tags=["reports"],
        )
    )

    assert result.risk == "high"
    assert result.status == "confirm"
    assert "high-risk keyword 'export'" in " ".join(result.reasons)


def test_critical_keyword_keeps_delete_disabled():
    result = evaluate_operation_risk(
        Operation(method="DELETE", path="/admin/users/{id}", operation_id="deleteUser")
    )

    assert result.risk == "critical"
    assert result.status == "disabled"
    assert "high-risk keyword 'admin'" in " ".join(result.reasons)

