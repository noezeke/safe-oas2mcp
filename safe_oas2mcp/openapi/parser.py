from __future__ import annotations

from copy import deepcopy
from typing import Any

from safe_oas2mcp.models import Operation, Parameter


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


class OpenAPIParseError(ValueError):
    """Raised when a supported OpenAPI structure cannot be parsed."""


def parse_openapi(document: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    paths = document.get("paths", {})
    root_server_urls = _extract_server_urls(document.get("servers", []))

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_parameters = _parse_parameters(path_item.get("parameters", []), document)
        path_server_urls = _extract_server_urls(path_item.get("servers", [])) or root_server_urls

        for method, operation_object in path_item.items():
            method_lower = method.lower()
            if method_lower not in HTTP_METHODS or not isinstance(operation_object, dict):
                continue

            operation_parameters = _parse_parameters(
                operation_object.get("parameters", []), document
            )
            parameters = path_parameters + operation_parameters
            request_body = _resolve_maybe_ref(operation_object.get("requestBody"), document)

            operations.append(
                Operation(
                    method=method_lower.upper(),
                    path=path,
                    server_urls=_extract_server_urls(operation_object.get("servers", []))
                    or path_server_urls,
                    operation_id=operation_object.get("operationId"),
                    summary=operation_object.get("summary"),
                    description=operation_object.get("description"),
                    tags=list(operation_object.get("tags", [])),
                    path_parameters=[
                        parameter for parameter in parameters if parameter.location == "path"
                    ],
                    query_parameters=[
                        parameter for parameter in parameters if parameter.location == "query"
                    ],
                    header_parameters=[
                        parameter for parameter in parameters if parameter.location == "header"
                    ],
                    request_body_schema=_extract_json_body_schema(
                        operation_object.get("requestBody"), document
                    ),
                    request_body_required=bool(request_body.get("required", False))
                    if isinstance(request_body, dict)
                    else False,
                )
            )

    return operations


def _extract_server_urls(servers: list[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    if not isinstance(servers, list):
        return urls
    for server in servers:
        if isinstance(server, dict) and isinstance(server.get("url"), str):
            urls.append(server["url"])
    return urls


def _parse_parameters(
    parameter_objects: list[dict[str, Any]], document: dict[str, Any]
) -> list[Parameter]:
    parameters: list[Parameter] = []
    for parameter_object in parameter_objects:
        resolved = _resolve_maybe_ref(parameter_object, document)
        if not isinstance(resolved, dict):
            continue

        location = resolved.get("in")
        if location not in {"path", "query", "header"}:
            continue

        name = resolved.get("name")
        if not isinstance(name, str) or not name:
            continue

        parameters.append(
            Parameter(
                name=name,
                location=location,
                required=bool(resolved.get("required", location == "path")),
                schema=deepcopy(resolved.get("schema", {})),
                description=resolved.get("description"),
            )
        )

    return parameters


def _extract_json_body_schema(
    request_body: dict[str, Any] | None, document: dict[str, Any]
) -> dict[str, Any] | None:
    resolved_body = _resolve_maybe_ref(request_body, document)
    if not isinstance(resolved_body, dict):
        return None

    content = resolved_body.get("content", {})
    if not isinstance(content, dict):
        return None

    media_type = content.get("application/json")
    if not isinstance(media_type, dict):
        media_type = next(
            (
                value
                for key, value in content.items()
                if isinstance(key, str)
                and key.endswith("+json")
                and isinstance(value, dict)
            ),
            None,
        )

    if not isinstance(media_type, dict):
        return None

    schema = _resolve_maybe_ref(media_type.get("schema"), document)
    return deepcopy(schema) if isinstance(schema, dict) else None


def _resolve_maybe_ref(value: Any, document: dict[str, Any]) -> Any:
    if isinstance(value, dict) and "$ref" in value:
        return _resolve_local_ref(value["$ref"], document)
    return value


def _resolve_local_ref(ref: str, document: dict[str, Any]) -> Any:
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise OpenAPIParseError(f"Only local $ref values are supported: {ref}")

    current: Any = document
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise OpenAPIParseError(f"Unresolved local $ref: {ref}")
        current = current[part]

    if isinstance(current, dict) and "$ref" in current:
        return _resolve_local_ref(current["$ref"], document)

    return current
