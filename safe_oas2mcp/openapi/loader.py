from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class OpenAPILoadError(ValueError):
    """Raised when an OpenAPI document cannot be loaded safely."""


def load_openapi(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    if not spec_path.exists():
        raise OpenAPILoadError(f"OpenAPI file not found: {spec_path}")

    try:
        raw = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OpenAPILoadError(f"Unable to read OpenAPI file: {spec_path}") from exc

    suffix = spec_path.suffix.lower()
    if suffix == ".json":
        document = _load_json(raw, spec_path)
    else:
        document = _load_yaml(raw, spec_path)

    if not isinstance(document, dict):
        raise OpenAPILoadError("OpenAPI document must be a JSON/YAML object")

    version = document.get("openapi")
    if not isinstance(version, str) or not version.startswith("3."):
        raise OpenAPILoadError("Only OpenAPI 3.x is supported")

    if not isinstance(document.get("paths"), dict):
        raise OpenAPILoadError("OpenAPI document must contain a paths object")

    return document


def _load_json(raw: str, spec_path: Path) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenAPILoadError(f"Invalid JSON in OpenAPI file: {spec_path}") from exc


def _load_yaml(raw: str, spec_path: Path) -> Any:
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise OpenAPILoadError(f"Invalid YAML in OpenAPI file: {spec_path}") from exc
