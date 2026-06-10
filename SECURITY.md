# Security Policy

`safe-oas2mcp` is designed to put a conservative gateway between AI agents and real HTTP APIs. It reduces risk, but it does not make unsafe APIs safe by itself.

## Supported Versions

The project is pre-1.0. Security fixes target the current `main` branch until releases are formalized.

## Threat Model

Primary risks:

- Agent accidentally calls write or destructive endpoints.
- Dangerous endpoints are exposed without human review.
- API tokens are exposed to model-visible schemas, descriptions, logs, or responses.
- Sensitive response fields are returned to the Agent.
- Very large responses overwhelm the model or client.
- OpenAPI changes expose new tools without review.

Current mitigations:

- DELETE is disabled by default.
- POST, PUT, and PATCH require confirmation by default.
- Risky keywords raise risk and can force confirmation.
- Disabled tools are not registered with MCP.
- Auth tokens are injected server-side.
- Response data is redacted for common token, secret, password, email, and phone fields.
- Response size is limited.
- Audit logging is available and disabled by default.

## Token Handling

Use environment variables for secrets:

```yaml
auth:
  type: bearer
  token_env: API_TOKEN
```

Do not put tokens into OpenAPI examples, tool input schemas, or committed config files.

## Reporting Vulnerabilities

Open a private security advisory on GitHub if available. If not, create a minimal issue that says a security report is needed without including exploit details or secrets.

