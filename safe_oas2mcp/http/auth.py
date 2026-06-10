from __future__ import annotations

import os

from safe_oas2mcp.config import SafeOASConfig, resolve_header_value


def build_configured_headers(config: SafeOASConfig) -> dict[str, str]:
    headers: dict[str, str] = {}

    if config.auth.type == "bearer" and config.auth.token_env:
        headers["Authorization"] = f"Bearer {os.environ[config.auth.token_env]}"

    if (
        config.auth.type == "api_key"
        and config.auth.key_env
        and config.auth.header_name
    ):
        headers[config.auth.header_name] = os.environ[config.auth.key_env]

    for name, header in config.headers.items():
        headers[name] = resolve_header_value(header)

    return headers

