from safe_oas2mcp.config import PolicyConfig, PolicyOverride
from safe_oas2mcp.models import Operation, Parameter
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


def test_keyword_groups_raise_risk_with_group_and_source_details():
    result = evaluate_operation_risk(
        Operation(
            method="GET",
            path="/billing/transfers",
            operation_id="listTransfers",
        )
    )

    joined_reasons = " ".join(result.reasons)
    assert result.risk == "high"
    assert result.status == "confirm"
    assert "money keyword 'transfer' in path" in joined_reasons


def test_keywords_match_parameter_names_and_request_body_properties():
    result = evaluate_operation_risk(
        Operation(
            method="GET",
            path="/reports",
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
                    "profile": {
                        "type": "object",
                        "properties": {"phone": {"type": "string"}},
                    },
                },
            },
        )
    )

    joined_reasons = " ".join(result.reasons)
    assert result.risk == "high"
    assert result.status == "confirm"
    assert "identity keyword 'key' in parameter name" in joined_reasons
    assert "identity keyword 'password' in requestBody property" in joined_reasons


def test_policy_exclude_disables_matching_operation():
    result = evaluate_operation_risk(
        Operation(method="GET", path="/tasks"),
        PolicyConfig(exclude=["GET /tasks"]),
    )

    assert result.risk == "critical"
    assert result.status == "disabled"
    assert "Policy exclude matched: GET /tasks" in result.reasons


def test_policy_include_limits_unmatched_operations():
    result = evaluate_operation_risk(
        Operation(method="GET", path="/admin"),
        PolicyConfig(include=["GET /tasks"]),
    )

    assert result.risk == "high"
    assert result.status == "disabled"
    assert "No policy include rule matched" in result.reasons


def test_policy_override_can_change_delete_to_confirm_with_reason():
    result = evaluate_operation_risk(
        Operation(method="DELETE", path="/tasks/{task_id}"),
        PolicyConfig(
            overrides={
                "DELETE /tasks/{task_id}": PolicyOverride(
                    status="confirm",
                    risk="high",
                    reason="Allow task delete preview only",
                )
            }
        ),
    )

    assert result.risk == "high"
    assert result.status == "confirm"
    assert "Policy override matched: DELETE /tasks/{task_id}" in result.reasons
    assert "Allow task delete preview only" in result.reasons
