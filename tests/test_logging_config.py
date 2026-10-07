import json
import logging

from ai.analyst.app.logging_config import JsonFormatter, configured_log_level, redact_sensitive


def test_redact_sensitive_recursively_without_hiding_usage_counts():
    value = {
        "api_key": "secret-key",
        "nested": {
            "Authorization": "Bearer secret",
            "refresh_token": "secret-token",
            "input_tokens": 123,
        },
        "password": "db-secret",
        "safe": "visible",
    }
    redacted = redact_sensitive(value)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["Authorization"] == "[REDACTED]"
    assert redacted["nested"]["refresh_token"] == "[REDACTED]"
    assert redacted["nested"]["input_tokens"] == 123
    assert redacted["password"] == "[REDACTED]"
    assert redacted["safe"] == "visible"


def test_json_formatter_redacts_structured_fields():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "event", (), None)
    record.fields = {"LLM_REMOTE_API_KEY": "secret", "route": "remote"}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["LLM_REMOTE_API_KEY"] == "[REDACTED]"
    assert payload["route"] == "remote"


def test_configured_log_level_uses_env_and_falls_back(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert configured_log_level() == logging.DEBUG
    monkeypatch.setenv("LOG_LEVEL", "not-a-level")
    assert configured_log_level() == logging.INFO
