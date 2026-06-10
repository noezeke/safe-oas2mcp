# Cursor

Use `safe-oas2mcp` as a local MCP stdio server.

Example command:

```bash
safe-oas2mcp serve D:/corevo/openapi2mcp/examples/todo/openapi.yaml
```

For APIs with auth:

```bash
safe-oas2mcp serve D:/corevo/openapi2mcp/examples/github-readonly/openapi.yaml --config D:/corevo/openapi2mcp/safe-oas2mcp.config.yaml
```

Set tokens as environment variables in the MCP server configuration. Do not place tokens in OpenAPI files.

