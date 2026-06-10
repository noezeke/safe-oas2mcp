from safe_oas2mcp.openapi.parser import parse_openapi


def test_parses_operations_with_parameters_and_json_body():
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Todo API", "version": "1.0.0"},
        "servers": [{"url": "https://api.todo.example.com"}],
        "paths": {
            "/tasks/{task_id}": {
                "patch": {
                    "operationId": "updateTask",
                    "summary": "Update a task",
                    "description": "Updates a task title",
                    "tags": ["tasks"],
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "notify",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean"},
                        },
                        {
                            "name": "X-Workspace-Id",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["title"],
                                    "properties": {"title": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    operation = parse_openapi(document)[0]

    assert operation.method == "PATCH"
    assert operation.path == "/tasks/{task_id}"
    assert operation.server_urls == ["https://api.todo.example.com"]
    assert operation.operation_id == "updateTask"
    assert operation.summary == "Update a task"
    assert operation.description == "Updates a task title"
    assert operation.tags == ["tasks"]
    assert operation.path_parameters[0].name == "task_id"
    assert operation.query_parameters[0].name == "notify"
    assert operation.header_parameters[0].name == "X-Workspace-Id"
    assert operation.request_body_required is True
    assert operation.request_body_schema["required"] == ["title"]


def test_resolves_local_refs_for_parameters_and_request_body():
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Todo API", "version": "1.0.0"},
        "components": {
            "parameters": {
                "TaskId": {
                    "name": "task_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            },
            "schemas": {
                "CreateTask": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {"title": {"type": "string"}},
                }
            },
        },
        "paths": {
            "/tasks/{task_id}": {
                "put": {
                    "operationId": "replaceTask",
                    "parameters": [{"$ref": "#/components/parameters/TaskId"}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateTask"}
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    operation = parse_openapi(document)[0]

    assert operation.path_parameters[0].name == "task_id"
    assert operation.request_body_schema["properties"]["title"]["type"] == "string"
