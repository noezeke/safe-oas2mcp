from __future__ import annotations

import re
from typing import Any


SECRET_KEYWORDS = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "password",
    "credential",
    "private_key",
}


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _is_secret_key(str(key)):
                redacted[key] = "[REDACTED]"
            elif str(key).lower() == "email" and isinstance(item, str):
                redacted[key] = _mask_email(item)
            elif str(key).lower() == "phone" and isinstance(item, str):
                redacted[key] = "[REDACTED_PHONE]"
            else:
                redacted[key] = redact_secrets(item)
        return redacted

    if isinstance(value, list):
        return [redact_secrets(item) for item in value]

    if isinstance(value, str):
        return redact_text(value)

    return value


def redact_text(value: str) -> str:
    redacted = re.sub(
        r"(?i)\b(access_token|refresh_token|token|api_key|apikey|secret|password)"
        r"\s*[:=]\s*([^\s,;]+)",
        lambda match: f"{match.group(1)}=[REDACTED]",
        value,
    )
    redacted = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        lambda match: _mask_email(match.group(0)),
        redacted,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"\+?\d[\d\s().-]{7,}\d",
        "[REDACTED_PHONE]",
        redacted,
    )
    return redacted


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(keyword in normalized for keyword in SECRET_KEYWORDS)


def _mask_email(value: str) -> str:
    if "@" not in value:
        return "[REDACTED_EMAIL]"
    local, domain = value.split("@", 1)
    first = local[:1] or "*"
    return f"{first}***@{domain}"
