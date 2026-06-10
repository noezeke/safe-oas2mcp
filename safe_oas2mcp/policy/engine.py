from __future__ import annotations

from safe_oas2mcp.models import Operation, RiskLevel, RiskResult, ToolStatus
from safe_oas2mcp.policy.rules import HIGH_RISK_KEYWORDS


RISK_ORDER: dict[RiskLevel, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def evaluate_operation_risk(operation: Operation) -> RiskResult:
    risk, status, reasons = _method_default(operation.method)

    for keyword in sorted(HIGH_RISK_KEYWORDS):
        source = _keyword_source(operation, keyword)
        if source is None:
            continue

        reasons.append(f"Matched high-risk keyword '{keyword}' in {source}")
        risk = _max_risk(risk, "high")
        if status == "enabled":
            status = "confirm"

    return RiskResult(risk=risk, status=status, reasons=reasons)


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


def _keyword_source(operation: Operation, keyword: str) -> str | None:
    fields: list[tuple[str, str]] = [
        ("path", operation.path),
        ("operationId", operation.operation_id or ""),
        ("summary", operation.summary or ""),
        ("description", operation.description or ""),
        ("tags", " ".join(operation.tags)),
    ]

    for source, value in fields:
        if keyword in value.lower():
            return source
    return None


def _max_risk(current: RiskLevel, candidate: RiskLevel) -> RiskLevel:
    if RISK_ORDER[candidate] > RISK_ORDER[current]:
        return candidate
    return current

