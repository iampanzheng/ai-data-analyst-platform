import json

import httpx
import pytest

from ai.analyst.app.llm.client import (
    LLMClientError,
    OpenAICompatibleLLMClient,
)
from ai.analyst.app.llm.models import ChatMessage


def _messages():
    return [
        ChatMessage(role="user", content="hello"),
    ]


def _client(monkeypatch, handler, api_key="test-key"):
    transport = httpx.MockTransport(handler)

    def mock_post(url, **kwargs):
        with httpx.Client(transport=transport) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(httpx, "post", mock_post)

    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    if api_key is None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
    else:
        monkeypatch.setenv("LLM_API_KEY", api_key)

    return OpenAICompatibleLLMClient()


def test_success_response(monkeypatch):
    def handler(request):
        assert request.url == "http://mock-llm/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"

        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "content": "SELECT 1",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

    client = _client(monkeypatch, handler)

    result = client.chat(_messages())

    assert result.content == "SELECT 1"
    assert result.model == "test-model"
    assert result.usage == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


def test_api_key_is_optional(monkeypatch):
    def handler(request):
        assert "Authorization" not in request.headers

        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "content": "hello",
                        }
                    }
                ],
            },
        )

    client = _client(monkeypatch, handler, api_key=None)

    result = client.chat(_messages())

    assert result.content == "hello"


def test_http_error_becomes_llm_client_error(monkeypatch):
    def handler(request):
        return httpx.Response(500, json={"error": "server error"})

    client = _client(monkeypatch, handler)

    with pytest.raises(LLMClientError, match="LLM request failed"):
        client.chat(_messages())


def test_invalid_json_becomes_llm_client_error(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )

    client = _client(monkeypatch, handler)

    with pytest.raises(LLMClientError, match="LLM request failed"):
        client.chat(_messages())


def test_missing_choices_becomes_llm_client_error(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "test-model",
            },
        )

    client = _client(monkeypatch, handler)

    with pytest.raises(LLMClientError):
        client.chat(_messages())


def test_empty_content_becomes_llm_client_error(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "content": "",
                        }
                    }
                ],
            },
        )

    client = _client(monkeypatch, handler)

    with pytest.raises(LLMClientError, match="message content"):
        client.chat(_messages())


def test_missing_base_url(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")

    with pytest.raises(
        LLMClientError,
        match="LLM_BASE_URL and LLM_MODEL are required",
    ):
        OpenAICompatibleLLMClient()


def test_missing_model(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://mock-llm")
    monkeypatch.delenv("LLM_MODEL", raising=False)

    with pytest.raises(
        LLMClientError,
        match="LLM_BASE_URL and LLM_MODEL are required",
    ):
        OpenAICompatibleLLMClient()


def test_create_request_payload(monkeypatch):
    captured = {}

    def handler(request):
        captured["json"] = json.loads(request.content)

        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "content": "ok",
                        }
                    }
                ],
            },
        )

    client = _client(monkeypatch, handler)

    client.chat(_messages(), temperature=0.2)

    assert captured["json"] == {
        "model": "test-model",
        "messages": [
            {
                "role": "user",
                "content": "hello",
            }
        ],
        "temperature": 0.2,
    }
