# safe-oas2mcp

OpenAPI to MCP, safely.

`safe-oas2mcp` turns OpenAPI specs into MCP tools with secure defaults, risk inspection, confirmation gates, response limits, audit logging, and secret redaction.

It is not a plain OpenAPI-to-MCP converter. It is a Safe OpenAPI to MCP Gateway for Agent developers, SaaS APIs, and internal platform teams that need to expose real business APIs without handing unsafe operations to models by default.

## Quick Start

Install from a local checkout:

```bash
python -m pip install -e ".[dev]"
```

Or run directly with uv from this checkout:

```bash
uvx --from . safe-oas2mcp --help
```

Inspect an OpenAPI file:

```bash
safe-oas2mcp inspect examples/todo/openapi.yaml
safe-oas2mcp inspect examples/todo/openapi.yaml --format json
```

Start the MCP stdio server:

```bash
safe-oas2mcp serve examples/todo/openapi.yaml
```

## Why

Many systems already expose OpenAPI, but most converters expose too much too quickly. Agent tool calls can create, update, delete, export, transfer, or leak sensitive data if the gateway does not apply a conservative policy.

`safe-oas2mcp` keeps safety decisions visible:

- GET operations are enabled by default, unless risky keywords are detected.
- POST operations require confirmation by default.
- PUT and PATCH operations require confirmation by default.
- DELETE operations are disabled by default.
- Risk and status decisions include reasons.
- Tokens and API keys are injected server-side and are not shown to the model.
- Sensitive response fields are redacted.

## Inspect Your API

```bash
safe-oas2mcp inspect ./openapi.yaml
```

Example output:

```text
Tool         Method  Path              Risk      Status    Reasons
list_tasks   GET     /tasks            low       enabled   GET is enabled by default
create_task  POST    /tasks            medium    confirm   POST write operation requires confirmation by default
delete_task  DELETE  /tasks/{task_id}  critical  disabled  DELETE is disabled by default
```

Use JSON output for CI or review:

```bash
safe-oas2mcp inspect ./openapi.yaml --format json
```

Use a policy config during inspect:

```bash
safe-oas2mcp inspect ./openapi.yaml --config ./safe-oas2mcp.config.yaml
```

## Serve as MCP Server

```bash
safe-oas2mcp serve ./openapi.yaml --config ./safe-oas2mcp.config.yaml
```

The server uses MCP stdio transport. It registers enabled and confirm tools, skips disabled tools, validates MCP input with the generated JSON Schema, builds an HTTP request, injects configured auth headers, and returns a redacted response.

Confirm tools return a request preview instead of executing the real HTTP request.

## Security Defaults

| Condition | Risk | Status |
| --- | --- | --- |
| GET | low | enabled |
| POST | medium | confirm |
| PUT | high | confirm |
| PATCH | high | confirm |
| DELETE | critical | disabled |
| money, permission, destructive, export, bulk, token, secret keywords | high or critical | confirm or disabled |

Default keyword groups include:

- `money`: payment, refund, transfer, payout, invoice, billing, charge
- `identity`: user, account, customer, password, token, secret, key, email, phone
- `permission`: admin, root, role, permission, policy, access, invite
- `destructive`: delete, remove, destroy, revoke, disable, suspend, terminate
- `bulk_data`: export, bulk, batch, dump, report, download

## Configuration

Create `safe-oas2mcp.config.yaml`:

```yaml
base_url: https://api.example.com

auth:
  type: bearer
  token_env: EXAMPLE_API_TOKEN

headers:
  X-Workspace-Id:
    env: WORKSPACE_ID

timeout_seconds: 30
max_response_bytes: 1000000

policy:
  include:
    - "GET /tasks"
  exclude:
    - "DELETE /*"
  overrides:
    "DELETE /tasks/{task_id}":
      status: confirm
      risk: high
      reason: "Allow task delete preview only"

audit:
  enabled: false
  path: safe-oas2mcp.audit.jsonl
```

Supported auth modes:

```yaml
auth:
  type: bearer
  token_env: API_TOKEN
```

```yaml
auth:
  type: api_key
  key_env: API_KEY
  header_name: X-API-Key
```

## Examples

- [Todo SaaS Demo](examples/todo/README.md)
- [Petstore Demo](examples/petstore/README.md)
- [GitHub API readonly Demo](examples/github-readonly/README.md)

## MCP Client Setup

- [Claude Desktop](docs/clients/claude-desktop.md)
- [Cursor](docs/clients/cursor.md)
- [Windsurf](docs/clients/windsurf.md)
- [Troubleshooting](docs/clients/troubleshooting.md)

## Docker

Build locally:

```bash
docker build -t safe-oas2mcp:local .
```

Inspect with Docker:

```bash
docker run --rm safe-oas2mcp:local inspect examples/todo/openapi.yaml
```

Serve with env-injected auth:

```bash
docker run --rm -i \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  safe-oas2mcp:local \
  serve examples/github-readonly/openapi.yaml --config examples/github-readonly/safe-oas2mcp.config.example.yaml
```

Do not bake API tokens into images.

## Development

Run checks:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
```

Run inspect locally:

```bash
safe-oas2mcp inspect examples/todo/openapi.yaml
```

Run an MCP stdio server:

```bash
safe-oas2mcp serve examples/todo/openapi.yaml
```

## Roadmap

- More OpenAPI schema coverage
- Safer confirmation flows
- CI diff command for OpenAPI changes
- Audit log export formats
- Docker image publishing
- PyPI release

## Security

Read [SECURITY.md](SECURITY.md) before connecting production APIs. The short version: keep auth in environment variables, inspect before serving, start readonly, and use policy overrides sparingly.

## License

License is not selected yet.
