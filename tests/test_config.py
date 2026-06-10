import pytest

from safe_oas2mcp.config import ConfigError, load_config


def test_loads_config_from_explicit_path(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_TOKEN", "secret-token")
    monkeypatch.setenv("WORKSPACE_ID", "workspace-123")
    config_path = tmp_path / "safe-oas2mcp.config.yaml"
    config_path.write_text(
        """
base_url: https://api.todo.example.com
auth:
  type: bearer
  token_env: TODO_TOKEN
headers:
  X-Workspace-Id:
    env: WORKSPACE_ID
timeout_seconds: 15
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.base_url == "https://api.todo.example.com"
    assert config.auth.type == "bearer"
    assert config.auth.token_env == "TODO_TOKEN"
    assert config.headers["X-Workspace-Id"].env == "WORKSPACE_ID"
    assert config.timeout_seconds == 15


def test_load_config_returns_defaults_when_no_config_exists(tmp_path):
    config = load_config(tmp_path / "missing.yaml")

    assert config.base_url is None
    assert config.timeout_seconds == 30


def test_missing_required_auth_env_raises_without_secret_value(tmp_path, monkeypatch):
    monkeypatch.delenv("TODO_TOKEN", raising=False)
    config_path = tmp_path / "safe-oas2mcp.config.yaml"
    config_path.write_text(
        """
auth:
  type: bearer
  token_env: TODO_TOKEN
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Missing required environment variable: TODO_TOKEN"):
        load_config(config_path)


def test_invalid_auth_type_raises_clear_error(tmp_path):
    config_path = tmp_path / "safe-oas2mcp.config.yaml"
    config_path.write_text(
        """
auth:
  type: oauth2
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="auth.type must be one of"):
        load_config(config_path)

