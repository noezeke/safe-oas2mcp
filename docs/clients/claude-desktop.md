# Claude Desktop

Add a local MCP server entry that runs `safe-oas2mcp serve`.

Example:

```json
{
  "mcpServers": {
    "todo-api": {
      "command": "safe-oas2mcp",
      "args": [
        "serve",
        "D:/corevo/openapi2mcp/examples/todo/openapi.yaml"
      ]
    }
  }
}
```

For authenticated APIs, set environment variables outside the model context and pass `--config`:

```json
{
  "mcpServers": {
    "github-readonly": {
      "command": "safe-oas2mcp",
      "args": [
        "serve",
        "D:/corevo/openapi2mcp/examples/github-readonly/openapi.yaml",
        "--config",
        "D:/corevo/openapi2mcp/safe-oas2mcp.config.yaml"
      ],
      "env": {
        "GITHUB_TOKEN": "your_token_here"
      }
    }
  }
}
```

Prefer readonly APIs first. Run `safe-oas2mcp inspect` before connecting a new API.

