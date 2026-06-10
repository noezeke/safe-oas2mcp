# Contributing

Thanks for working on `safe-oas2mcp`.

## Development Setup

```bash
python -m pip install -e ".[dev]"
```

Run checks:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
```

## Pull Request Expectations

- Add or update tests for behavior changes.
- Keep security defaults conservative.
- Do not expose auth headers, API keys, or tokens to tool schemas or logs.
- Update README or docs when user-visible behavior changes.
- Use `safe-oas2mcp inspect` examples to explain policy changes when relevant.

## Scope

MVP scope is a safe OpenAPI-to-MCP gateway. Avoid adding Web UI, RBAC, OAuth2 flows, or platform features unless they are part of an accepted roadmap item.

