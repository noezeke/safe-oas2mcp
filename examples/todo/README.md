# Todo SaaS Demo

This demo shows the default safety policy:

```bash
safe-oas2mcp inspect examples/todo/openapi.yaml
```

Expected behavior:

- `GET /tasks` -> enabled
- `POST /tasks` -> confirm
- `PATCH /tasks/{task_id}` -> confirm
- `DELETE /tasks/{task_id}` -> disabled

Run as MCP stdio server:

```bash
safe-oas2mcp serve examples/todo/openapi.yaml
```

Run the optional mock HTTP API:

```bash
python examples/todo/mock_server.py
```

To point the gateway at the mock API, create a config:

```yaml
base_url: http://127.0.0.1:8088
```
