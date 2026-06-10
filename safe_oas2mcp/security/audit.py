from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from safe_oas2mcp.config import AuditConfig
from safe_oas2mcp.security.redactor import redact_secrets


def write_audit_record(config: AuditConfig, record: dict[str, Any]) -> None:
    if not config.enabled:
        return

    path = Path(config.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_record = redact_secrets(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **record,
        }
    )
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(safe_record, ensure_ascii=False) + "\n")
