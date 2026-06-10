# MCP Client Troubleshooting

## Command not found

Install the package in the same environment used by the MCP client:

```bash
python -m pip install -e ".[dev]"
safe-oas2mcp --help
```

Use an absolute path if the client does not inherit your shell `PATH`.

## Tool is missing

Run inspect:

```bash
safe-oas2mcp inspect ./openapi.yaml --config ./safe-oas2mcp.config.yaml
```

Disabled tools are not registered with MCP. DELETE is disabled by default.

## Write operation does not execute

POST, PUT, and PATCH tools return a request preview by default. This is intentional.

## Token is missing

Check that the environment variable referenced by config exists in the process that launches the MCP server:

```yaml
auth:
  type: bearer
  token_env: API_TOKEN
```

## Secret appears in output

Open a security report. Include a minimal redacted example and do not include real tokens.

