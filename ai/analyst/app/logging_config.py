from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

_REDACTED = "[REDACTED]"


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return (
        normalized in {"authorization", "password", "secret", "token", "database_url"}
        or "api_key" in normalized
        or normalized.endswith("_password")
        or normalized.endswith("_secret")
        or normalized.endswith("_token")
    )


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _REDACTED if _is_sensitive_key(key) else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item) for item in value]
    return value


def configured_log_level() -> int:
    name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, name, None)
    return level if isinstance(level, int) else logging.INFO


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(redact_sensitive(fields))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(configured_log_level())
