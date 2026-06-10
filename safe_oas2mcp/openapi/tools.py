from __future__ import annotations

import re
from copy import deepcopy

from safe_oas2mcp.models import Operation, Parameter, ToolMetadata


def build_tool_metadata(operation: Operation, used_names: set[str]) -> ToolMetadata:
    base_name = _tool_name(operation)
    name = _unique_name(base_name, used_names)
    used_names.add(name)

    return ToolMetadata(
        name=name,
        description=_description(operation),
        input_schema=build_input_schema(operation),
    )


def build_input_schema(operation: Operation) -> dict[str, object]:
    properties: dict[str, object] = {}
    required: list[str] = []

    for parameter in [*operation.path_parameters, *operation.query_parameters]:
        properties[parameter.name] = _parameter_schema(parameter)
        if parameter.required:
            required.append(parameter.name)

    if operation.request_body_schema is not None:
        properties["body"] = deepcopy(operation.request_body_schema)
        if operation.request_body_required:
            required.append("body")

    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def _tool_name(operation: Operation) -> str:
    if operation.operation_id:
        return _sanitize_name(operation.operation_id)

    path_part = operation.path.strip("/")
    if not path_part:
        return _sanitize_name(operation.method.lower())

    tokens: list[str] = []
    for token in re.split(r"[/]+", path_part):
        if not token:
            continue
        if token.startswith("{") and token.endswith("}"):
            tokens.extend(["by", token.strip("{}")])
        else:
            tokens.append(token)
    return _sanitize_name("_".join([operation.method.lower(), *tokens]))


def _sanitize_name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = value.replace("-", "_").replace(".", "_")
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_").lower()
    return value or "operation"


def _unique_name(base_name: str, used_names: set[str]) -> str:
    if base_name not in used_names:
        return base_name

    index = 2
    while f"{base_name}_{index}" in used_names:
        index += 1
    return f"{base_name}_{index}"


def _description(operation: Operation) -> str:
    if operation.summary:
        return operation.summary
    if operation.description:
        return operation.description
    return f"{operation.method} {operation.path}"


def _parameter_schema(parameter: Parameter) -> dict[str, object]:
    schema = deepcopy(parameter.schema_)
    if parameter.description:
        schema["description"] = parameter.description
    return schema
