import json

import httpx
import pytest

from ai.analyst.app.llm.client import (
    LLMClientError,
    OpenAICompatibleLLMClient,
    normalize_usage,
)
from ai.analyst.app.llm.models import ChatMessage


def _messages():
    return [ChatMessage(role="user", content="hello")]


def _client(monkeypatch, handler, api_key="test-key", *, retries=0, backoff=0):
    transport = httpx.MockTransport(handler)

    def mock_post(url, **kwargs):
        with httpx.Client(transport=transport) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_MAX_RETRIES", str(retries))
    monkeypatch.setenv("LLM_RETRY_BACKOFF_SECONDS", str(backoff))

    if api_key is None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
    else:
        monkeypatch.setenv("LLM_API_KEY", api_key)

    return OpenAICompatibleLLMClient()


def test_success_response_normalizes_usage(monkeypatch):
    def handler(request):
        assert request.url == "http://mock-llm/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"message": {"content": "SELECT 1"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

    result = _client(monkeypatch, handler).chat(_messages())

    assert result.content == "SELECT 1"
    assert result.model == "test-model"
    assert result.provider == "openai-compatible"
    assert result.usage == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }


def test_normalize_usage_accepts_native_names():
    assert normalize_usage({"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}) == {
        "input_tokens": 7,
        "output_tokens": 3,
        "total_tokens": 10,
    }


def test_normalize_usage_derives_total():
    assert normalize_usage({"prompt_tokens": 4, "completion_tokens": 6}) == {
        "input_tokens": 4,
        "output_tokens": 6,
        "total_tokens": 10,
    }


def test_api_key_is_optional(monkeypatch):
    def handler(request):
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"model": "test-model", "choices": [{"message": {"content": "hello"}}]})

    result = _client(monkeypatch, handler, api_key=None).chat(_messages())
    assert result.content == "hello"


@pytest.mark.parametrize(
    "status,code,retryable",
    [
        (401, "LLM_AUTH_ERROR", False),
        (403, "LLM_AUTH_ERROR", False),
        (400, "LLM_REQUEST_ERROR", False),
        (429, "LLM_RATE_LIMIT", True),
        (500, "LLM_SERVER_ERROR", True),
        (503, "LLM_SERVER_ERROR", True),
    ],
)
def test_http_errors_are_classified(monkeypatch, status, code, retryable):
    def handler(request):
        return httpx.Response(status, json={"error": "failure"})

    with pytest.raises(LLMClientError) as exc:
        _client(monkeypatch, handler).chat(_messages())

    assert exc.value.code == code
    assert exc.value.retryable is retryable
    assert exc.value.status_code == status


def test_retryable_500_is_retried_then_succeeds(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(500, json={"error": "temporary"})
        return httpx.Response(200, json={"model": "test-model", "choices": [{"message": {"content": "ok"}}]})

    result = _client(monkeypatch, handler, retries=1).chat(_messages())
    assert result.content == "ok"
    assert calls["count"] == 2


def test_auth_error_is_not_retried(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return httpx.Response(401, json={"error": "bad key"})

    with pytest.raises(LLMClientError) as exc:
        _client(monkeypatch, handler, retries=3).chat(_messages())

    assert exc.value.code == "LLM_AUTH_ERROR"
    assert calls["count"] == 1


def test_timeout_is_classified_and_retried(monkeypatch):
    calls = {"count": 0}

    def mock_post(url, **kwargs):
        calls["count"] += 1
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_MAX_RETRIES", "1")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_SECONDS", "0")

    with pytest.raises(LLMClientError) as exc:
        OpenAICompatibleLLMClient().chat(_messages())

    assert exc.value.code == "LLM_TIMEOUT"
    assert exc.value.retryable is True
    assert calls["count"] == 2


def test_invalid_json_becomes_invalid_response(monkeypatch):
    def handler(request):
        return httpx.Response(200, content=b"not-json", headers={"Content-Type": "application/json"})

    with pytest.raises(LLMClientError) as exc:
        _client(monkeypatch, handler).chat(_messages())
    assert exc.value.code == "LLM_INVALID_RESPONSE"


def test_missing_choices_becomes_invalid_response(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"model": "test-model"})

    with pytest.raises(LLMClientError) as exc:
        _client(monkeypatch, handler).chat(_messages())
    assert exc.value.code == "LLM_INVALID_RESPONSE"


def test_empty_content_becomes_invalid_response(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"model": "test-model", "choices": [{"message": {"content": ""}}]})

    with pytest.raises(LLMClientError) as exc:
        _client(monkeypatch, handler).chat(_messages())
    assert exc.value.code == "LLM_INVALID_RESPONSE"


def test_missing_base_url(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    with pytest.raises(LLMClientError) as exc:
        OpenAICompatibleLLMClient()
    assert exc.value.code == "LLM_CONFIGURATION_ERROR"


def test_missing_model(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(LLMClientError) as exc:
        OpenAICompatibleLLMClient()
    assert exc.value.code == "LLM_CONFIGURATION_ERROR"


def test_create_request_payload(monkeypatch):
    captured = {}

    def handler(request):
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"model": "test-model", "choices": [{"message": {"content": "ok"}}]})

    _client(monkeypatch, handler).chat(_messages(), temperature=0.2)

    assert captured["json"] == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.2,
    }


def test_base_url_may_end_with_v1(monkeypatch):
    def handler(request):
        assert request.url == "http://mock-llm/v1/chat/completions"
        return httpx.Response(
            200,
            json={"model": "test-model", "choices": [{"message": {"content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)

    def mock_post(url, **kwargs):
        with httpx.Client(transport=transport) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm/v1/")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_MAX_RETRIES", "0")

    result = OpenAICompatibleLLMClient().chat(_messages())
    assert result.content == "ok"


def test_chat_completions_url_supports_gemini_openai_root():
    from ai.analyst.app.llm.client import _chat_completions_url

    assert _chat_completions_url(
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    ) == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def test_optional_reasoning_effort_is_sent(monkeypatch):
    import httpx
    from ai.analyst.app.llm.client import OpenAICompatibleLLMClient
    from ai.analyst.app.llm.models import ChatMessage

    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "example-model")
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    captured = {}

    class Response:
        status_code = 200
        def json(self):
            return {"model": "example-model", "choices": [{"message": {"content": "ok"}}], "usage": {}}

    def fake_post(url, *, json, headers, timeout):
        captured.update(json)
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OpenAICompatibleLLMClient()
    client.chat([ChatMessage(role="user", content="hello")])
    assert captured["reasoning_effort"] == "low"
