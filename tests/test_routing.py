from __future__ import annotations

import pytest

from ai.analyst.app.llm.client import LLMClientError, OpenAICompatibleLLMClient
from ai.analyst.app.llm.routing import (
    RoutingSettings,
    create_routed_llm_client,
    decide_route,
)


def _settings(**overrides):
    values = {
        "enabled": True,
        "default_route": "remote",
        "allow_remote": True,
        "allow_local": True,
    }
    values.update(overrides)
    return RoutingSettings(**values)


def test_auto_uses_measured_remote_default():
    decision = decide_route("auto", _settings())
    assert decision.selected_route == "remote"
    assert decision.reason == "auto_default_remote_stage2_3_measurements"
    assert decision.fallback_route is None


def test_explicit_local_overrides_auto_default():
    decision = decide_route("local", _settings())
    assert decision.selected_route == "local"
    assert decision.reason == "explicit_local_request"


def test_explicit_remote_is_deterministic():
    decision = decide_route("remote", _settings(default_route="local"))
    assert decision.selected_route == "remote"
    assert decision.reason == "explicit_remote_request"


def test_disabled_routing_preserves_legacy_auto_path():
    decision = decide_route("auto", _settings(enabled=False))
    assert decision.selected_route == "legacy"
    assert decision.reason == "routing_disabled_legacy_client"


def test_explicit_route_requires_routing_to_be_enabled():
    with pytest.raises(LLMClientError) as exc:
        decide_route("local", _settings(enabled=False))
    assert exc.value.code == "LLM_ROUTING_DISABLED"


def test_disabled_route_is_rejected():
    with pytest.raises(LLMClientError) as exc:
        decide_route("local", _settings(allow_local=False))
    assert exc.value.code == "LLM_ROUTING_ROUTE_DISABLED"


def test_invalid_default_route_from_env_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_ROUTING_DEFAULT_ROUTE", "fastest")
    with pytest.raises(LLMClientError) as exc:
        RoutingSettings.from_env()
    assert exc.value.code == "LLM_ROUTING_CONFIGURATION_ERROR"


def test_remote_and_local_clients_use_separate_configuration(monkeypatch):
    monkeypatch.setenv("LLM_REMOTE_PROVIDER", "openai-compatible")
    monkeypatch.setenv("LLM_REMOTE_BASE_URL", "https://remote.example/v1")
    monkeypatch.setenv("LLM_REMOTE_MODEL", "remote-model")
    monkeypatch.setenv("LLM_REMOTE_REASONING_EFFORT", "low")
    monkeypatch.setenv("LLM_REMOTE_DISABLE_THINKING", "false")

    monkeypatch.setenv("LLM_LOCAL_PROVIDER", "openai-compatible")
    monkeypatch.setenv("LLM_LOCAL_BASE_URL", "http://local.example:11434")
    monkeypatch.setenv("LLM_LOCAL_MODEL", "local-model")
    monkeypatch.setenv("LLM_LOCAL_DISABLE_THINKING", "true")

    settings = _settings()
    remote_decision, remote = create_routed_llm_client("auto", settings=settings)
    local_decision, local = create_routed_llm_client("local", settings=settings)

    assert remote_decision.selected_route == "remote"
    assert local_decision.selected_route == "local"
    assert isinstance(remote, OpenAICompatibleLLMClient)
    assert isinstance(local, OpenAICompatibleLLMClient)
    assert remote.model == "remote-model"
    assert remote.base_url == "https://remote.example/v1"
    assert remote.reasoning_effort == "low"
    assert remote.disable_thinking is False
    assert local.model == "local-model"
    assert local.base_url == "http://local.example:11434"
    assert local.disable_thinking is True
