# GitHub Readonly Demo

This example shows how to expose a small readonly subset of the GitHub REST API.

```bash
safe-oas2mcp inspect examples/github-readonly/openapi.yaml --config examples/github-readonly/safe-oas2mcp.config.example.yaml
```

To serve it, copy the example config and set a token:

```bash
copy examples\github-readonly\safe-oas2mcp.config.example.yaml safe-oas2mcp.config.yaml
set GITHUB_TOKEN=your_token_here
safe-oas2mcp serve examples/github-readonly/openapi.yaml --config safe-oas2mcp.config.yaml
```

The token is injected by the server and is not exposed to MCP tool input schemas.

