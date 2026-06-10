from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from safe_oas2mcp.config import PolicyConfig
from safe_oas2mcp.models import Operation, RiskLevel, RiskResult, ToolStatus
from safe_oas2mcp.policy.rules import KEYWORD_GROUPS


RISK_ORDER: dict[RiskLevel, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def evaluate_operation_risk(
    operation: Operation,
    policy: PolicyConfig | None = None,
) -> RiskResult:
    risk, status, reasons = _method_default(operation.method)

    for group, keyword, source in _keyword_matches(operation):
        reasons.append(
            f"Matched high-risk keyword '{keyword}' in {source} "
            f"({group} keyword '{keyword}' in {source})"
        )
        risk = _max_risk(risk, "high")
        if status == "enabled":
            status = "confirm"

    if policy is not None:
        risk, status, reasons = _apply_policy(operation, policy, risk, status, reasons)

    return RiskResult(risk=risk, status=status, reasons=reasons)


def _apply_policy(
    operation: Operation,
    policy: PolicyConfig,
    risk: RiskLevel,
    status: ToolStatus,
    reasons: list[str],
) -> tuple[RiskLevel, ToolStatus, list[str]]:
    if policy.include and not _matches_any(operation, policy.include):
        reasons.append("No policy include rule matched")
        risk = _max_risk(risk, "high")
        status = "disabled"

    override = _matching_override(operation, policy)
    if override is not None:
        pattern, policy_override = override
        reasons.append(f"Policy override matched: {pattern}")
        reasons.append(policy_override.reason)
        if policy_override.risk is not None:
            risk = policy_override.risk
        if policy_override.status is not None:
            status = policy_override.status

    matching_exclude = _matching_pattern(operation, policy.exclude)
    if matching_exclude is not None:
        reasons.append(f"Policy exclude matched: {matching_exclude}")
        risk = "critical"
        status = "disabled"

    return risk, status, reasons


def _matching_override(
    operation: Operation,
    policy: PolicyConfig,
) -> tuple[str, Any] | None:
    for pattern, override in policy.overrides.items():
        if _matches_pattern(operation, pattern):
            return pattern, override
    return None


def _matches_any(operation: Operation, patterns: list[str]) -> bool:
    return _matching_pattern(operation, patterns) is not None


def _matching_pattern(operation: Operation, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if _matches_pattern(operation, pattern):
            return pattern
    return None


def _matches_pattern(operation: Operation, pattern: str) -> bool:
    method, _, path_pattern = pattern.strip().partition(" ")
    if not method or not path_pattern:
        return False
    if method.upper() != operation.method.upper() and method != "*":
        return False

    operation_path = operation.path.strip("/")
    pattern_path = path_pattern.strip("/")
    if pattern_path == "*":
        return True
    if pattern_path.endswith("/*"):
        return operation_path.startswith(pattern_path[:-2].strip("/"))
    return path_pattern == operation.path


def _method_default(method: str) -> tuple[RiskLevel, ToolStatus, list[str]]:
    method = method.upper()
    if method == "GET":
        return "low", "enabled", ["GET is enabled by default"]
    if method == "POST":
        return (
            "medium",
            "confirm",
            ["POST write operation requires confirmation by default"],
        )
    if method == "PUT":
        return (
            "high",
            "confirm",
            ["PUT write operation requires confirmation by default"],
        )
    if method == "PATCH":
        return (
            "high",
            "confirm",
            ["PATCH write operation requires confirmation by default"],
        )
    if method == "DELETE":
        return "critical", "disabled", ["DELETE is disabled by default"]
    return "high", "confirm", [f"{method} operation is not recognized as safe"]


def _keyword_matches(operation: Operation) -> list[tuple[str, str, str]]:
    matches: list[tuple[str, str, str]] = []
    fields = list(_keyword_fields(operation))

    for group, keywords in KEYWORD_GROUPS.items():
        for keyword in sorted(keywords):
            for source, value in fields:
                if keyword in value.lower():
                    matches.append((group, keyword, source))
                    break

    return matches


def _keyword_fields(operation: Operation) -> Iterable[tuple[str, str]]:
    fields: list[tuple[str, str]] = [
        ("path", operation.path),
        ("operationId", operation.operation_id or ""),
        ("summary", operation.summary or ""),
        ("description", operation.description or ""),
        ("tags", " ".join(operation.tags)),
    ]

    for parameter in [
        *operation.path_parameters,
        *operation.query_parameters,
        *operation.header_parameters,
    ]:
        fields.append(("parameter name", parameter.name))

    for property_name in _schema_property_names(operation.request_body_schema):
        fields.append(("requestBody property", property_name))

    return fields


def _schema_property_names(schema: dict[str, Any] | None) -> list[str]:
    if not isinstance(schema, dict):
        return []

    names: list[str] = []
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, child_schema in properties.items():
            names.append(str(name))
            if isinstance(child_schema, dict):
                names.extend(_schema_property_names(child_schema))

    items = schema.get("items")
    if isinstance(items, dict):
        names.extend(_schema_property_names(items))

    return names


def _max_risk(current: RiskLevel, candidate: RiskLevel) -> RiskLevel:
    if RISK_ORDER[candidate] > RISK_ORDER[current]:
        return candidate
    return current
