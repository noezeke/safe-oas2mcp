# Release Process

This project is pre-1.0. Do not publish a release until tests, security checks, and packaging are verified.

## Local Verification

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
uv build
uvx --from . safe-oas2mcp --help
```

## PyPI

PyPI publishing is not configured yet. Before publishing:

- Confirm the package name is available.
- Confirm the license.
- Add release notes to `CHANGELOG.md`.
- Build with `uv build`.
- Upload through a trusted publisher or scoped token.

## Docker

Docker image publishing is not configured yet. Before publishing:

- Build locally.
- Verify `inspect` works in the container.
- Verify env-injected auth does not print secrets.
- Choose a registry, such as GHCR.

