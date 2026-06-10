from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

from safe_oas2mcp.models import RiskLevel, ToolStatus


class ConfigError(ValueError):
    """Raised when safe-oas2mcp configuration is invalid."""


class AuthConfig(BaseModel):
    type: Literal["none", "bearer", "api_key"] = "none"
    token_env: str | None = None
    key_env: str | None = None
    header_name: str | None = None


class HeaderValueConfig(BaseModel):
    value: str | None = None
    env: str | None = None


class PolicyOverride(BaseModel):
    status: ToolStatus | None = None
    risk: RiskLevel | None = None
    reason: str


class PolicyConfig(BaseModel):
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    overrides: dict[str, PolicyOverride] = Field(default_factory=dict)


class AuditConfig(BaseModel):
    enabled: bool = False
    path: str = "safe-oas2mcp.audit.jsonl"


class SafeOASConfig(BaseModel):
    base_url: str | None = None
    auth: AuthConfig = Field(default_factory=AuthConfig)
    headers: dict[str, HeaderValueConfig] = Field(default_factory=dict)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    timeout_seconds: float = 30
    max_response_bytes: int = 1_000_000


def load_config(path: str | Path | None = None) -> SafeOASConfig:
    config_path = Path(path) if path is not None else Path("safe-oas2mcp.config.yaml")
    if not config_path.exists():
        return SafeOASConfig()

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML config: {config_path}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read config file: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML object")

    try:
        config = SafeOASConfig.model_validate(raw)
    except ValidationError as exc:
        if "auth.type" in str(exc) or "literal_error" in str(exc):
            raise ConfigError("auth.type must be one of: none, bearer, api_key") from exc
        raise ConfigError(f"Invalid config: {exc}") from exc

    _validate_required_env(config)
    return config


def _validate_required_env(config: SafeOASConfig) -> None:
    if config.auth.type == "bearer":
        if not config.auth.token_env:
            raise ConfigError("auth.token_env is required for bearer auth")
        _require_env(config.auth.token_env)

    if config.auth.type == "api_key":
        if not config.auth.key_env:
            raise ConfigError("auth.key_env is required for api_key auth")
        if not config.auth.header_name:
            raise ConfigError("auth.header_name is required for api_key auth")
        _require_env(config.auth.key_env)

    for header in config.headers.values():
        if header.env:
            _require_env(header.env)


def _require_env(name: str) -> None:
    if os.getenv(name) is None:
        raise ConfigError(f"Missing required environment variable: {name}")


def resolve_header_value(header: HeaderValueConfig) -> str:
    if header.env:
        return os.environ[header.env]
    return header.value or ""


def raw_config_from_file(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ConfigError("Config file must contain a YAML object")
    return loaded
