import json

import pytest

from safe_oas2mcp.openapi.loader import OpenAPILoadError, load_openapi


def test_loads_yaml_openapi_document(tmp_path):
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

    document = load_openapi(spec_path)

    assert document["openapi"] == "3.0.3"
    assert document["info"]["title"] == "Todo API"


def test_loads_yml_openapi_document(tmp_path):
    spec_path = tmp_path / "openapi.yml"
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

    document = load_openapi(spec_path)

    assert document["openapi"] == "3.0.3"


def test_loads_json_openapi_document(tmp_path):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Todo API", "version": "1.0.0"},
                "paths": {},
            }
        ),
        encoding="utf-8",
    )

    document = load_openapi(spec_path)

    assert document["openapi"] == "3.1.0"
    assert document["paths"] == {}


def test_missing_file_raises_clear_error(tmp_path):
    spec_path = tmp_path / "missing.yaml"

    with pytest.raises(OpenAPILoadError, match="OpenAPI file not found"):
        load_openapi(spec_path)


def test_invalid_yaml_raises_clear_error(tmp_path):
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text("openapi: [", encoding="utf-8")

    with pytest.raises(OpenAPILoadError, match="Invalid YAML"):
        load_openapi(spec_path)


def test_invalid_json_raises_clear_error(tmp_path):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text("{", encoding="utf-8")

    with pytest.raises(OpenAPILoadError, match="Invalid JSON"):
        load_openapi(spec_path)


def test_non_openapi_3_document_raises_clear_error(tmp_path):
    spec_path = tmp_path / "swagger.yaml"
    spec_path.write_text(
        """
swagger: "2.0"
info:
  title: Old API
  version: 1.0.0
paths: {}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(OpenAPILoadError, match="Only OpenAPI 3.x is supported"):
        load_openapi(spec_path)
