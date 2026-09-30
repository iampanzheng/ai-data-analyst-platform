from __future__ import annotations

import pytest

from ai.analyst.app.llm.client import LLMClient, LLMClientError
from ai.analyst.app.llm.models import ChatMessage, LLMResponse
from ai.analyst.app.llm.reliability import ReliabilityPolicy, ResilientLLMClient
from ai.analyst.app.llm.routing import RoutingSettings, decide_route


class FakeClient(LLMClient):
    disable_thinking = False

    def __init__(self, *, responses=None, error=None, cost=0.0):
        self.responses = list(responses or [])
        self.error = error
        self.calls = 0
        self.cost = cost

    def chat(self, messages, *, temperature=0.0):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.responses.pop(0)

    def estimate_cost(self, usage):
        return self.cost


def response(content="ok", usage=None):
    return LLMResponse(content=content, model="fake", provider="fake", usage=usage or {})


def retryable(code="LLM_TIMEOUT"):
    return LLMClientError(code, "temporary", retryable=True)


def settings(**overrides):
    values = dict(enabled=True, default_route="remote", allow_remote=True, allow_local=True)
    values.update(overrides)
    return RoutingSettings(**values)


def test_auto_remote_has_local_fallback():
    decision = decide_route("auto", settings(), fallback_mode="auto")
    assert decision.selected_route == "remote"
    assert decision.fallback_route == "local"


def test_explicit_local_is_privacy_safe_by_default():
    decision = decide_route("local", settings(), fallback_mode="auto")
    assert decision.selected_route == "local"
    assert decision.fallback_route is None


def test_explicit_local_can_cross_route_only_when_opted_in():
    decision = decide_route("local", settings(), fallback_mode="cross_route")
    assert decision.fallback_route == "remote"


def test_disabled_fallback_has_no_alternate():
    decision = decide_route("remote", settings(), fallback_mode="disabled")
    assert decision.fallback_route is None


def test_retryable_primary_failure_falls_back_and_sticks():
    primary = FakeClient(error=retryable())
    fallback = FakeClient(responses=[response("sql"), response("answer")])
    client = ResilientLLMClient("remote", primary, "local", fallback)
    msg = [ChatMessage(role="user", content="x")]

    assert client.chat(msg).content == "sql"
    assert client.chat(msg).content == "answer"
    assert primary.calls == 1
    assert fallback.calls == 2
    assert client.current_route == "local"
    assert len(client.fallback_events) == 1


def test_non_retryable_error_does_not_fallback():
    primary = FakeClient(error=LLMClientError("LLM_AUTH_ERROR", "bad key", retryable=False))
    fallback = FakeClient(responses=[response()])
    client = ResilientLLMClient("remote", primary, "local", fallback)
    with pytest.raises(LLMClientError) as exc:
        client.chat([ChatMessage(role="user", content="x")])
    assert exc.value.code == "LLM_AUTH_ERROR"
    assert fallback.calls == 0


def test_local_to_remote_requires_cross_route():
    local = FakeClient(error=retryable())
    remote = FakeClient(responses=[response()])
    client = ResilientLLMClient("local", local, "remote", remote, fallback_mode="auto")
    with pytest.raises(LLMClientError):
        client.chat([ChatMessage(role="user", content="x")])
    assert remote.calls == 0


def test_route_usage_and_cost_are_recorded():
    primary = FakeClient(responses=[response(usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})], cost=0.001)
    client = ResilientLLMClient("remote", primary)
    client.chat([ChatMessage(role="user", content="x")])
    assert client.route_usage["remote"] == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    assert client.estimated_cost_usd == pytest.approx(0.001)


def test_cost_budget_blocks_next_llm_call():
    primary = FakeClient(responses=[response(), response()], cost=0.01)
    client = ResilientLLMClient(
        "remote", primary,
        policy=ReliabilityPolicy(max_estimated_cost_usd=0.005),
    )
    client.chat([ChatMessage(role="user", content="x")])
    with pytest.raises(LLMClientError) as exc:
        client.chat([ChatMessage(role="user", content="x")])
    assert exc.value.code == "LLM_COST_BUDGET_EXCEEDED"
    assert primary.calls == 1
