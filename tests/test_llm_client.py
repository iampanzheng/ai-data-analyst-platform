import json
from types import SimpleNamespace

import httpx
import pytest

from ai.analyst.app.agent.prompts import build_answer_messages
from ai.analyst.app.llm.client import (
    LLMClientError,
    OpenAICompatibleLLMClient,
    normalize_usage,
)
from ai.analyst.app.llm.models import ChatMessage
from ai.analyst.app.security import SQLValidationError, validate_sql
from evaluation.smoke import SMOKE_CASES


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
    monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)

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


def test_create_request_payload_with_reasoning_effort(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")

    captured = {}

    def handler(request):
        captured["json"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"message": {"content": "ok"}}],
            },
        )

    _client(monkeypatch, handler).chat(_messages(), temperature=0.2)

    assert captured["json"]["reasoning_effort"] == "low"


def test_entity_matching_normalizes_unicode_whitespace():
    from evaluation.smoke import _mentions_entity

    assert _mentions_entity("New\u202fYork", "New York")
    assert _mentions_entity("Los\u202fAngeles", "Los Angeles")


def test_state_counts_support_markdown_table():
    from evaluation.smoke import _extract_state_counts

    answer = """
    | State | Count |
    |---|---:|
    | CA | 3 |
    | TX | 5 |
    """

    assert _extract_state_counts(answer)["CA"] == 3
    assert _extract_state_counts(answer)["TX"] == 5


def test_markdown_state_counts_do_not_hide_wrong_city_total():
    from evaluation.smoke import _answer_check

    case = next(c for c in SMOKE_CASES if c.case_id == "SMOKE-004")

    state = SimpleNamespace(
        final_answer="| CA | 3 |\n| TX | 5 |\n城市总数为13个。",
        errors=[],
    )

    assert _answer_check(state, case)[0] is False


def test_rate_limit_retry_honors_retry_after(monkeypatch):
    sleeps = []
    request_count = 0

    def fake_sleep(seconds):
        sleeps.append(seconds)


    monkeypatch.setattr(
        "ai.analyst.app.llm.client.time.sleep",
        fake_sleep,
    )

    # first response 429 Retry-After: 2
    # second response 200
    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"error": {"message": "rate limit exceeded"}},
            )

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
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "total_tokens": 12,
                },
            },
        )

    client = _client(monkeypatch, handler, retries=1)

    response = client.chat(
        _messages(),
        temperature=0.2,
    )

    assert response.content == "ok"
    assert request_count == 2
    assert sleeps == [2.0]


def test_rate_limit_retry_falls_back_to_backoff(monkeypatch):
    sleeps = []
    request_count = 0

    monkeypatch.setattr(
        "ai.analyst.app.llm.client.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    def handler(request):
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            return httpx.Response(
                429,
                json={"error": {"message": "rate limit"}},
            )

        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {"message": {"content": "ok"}}
                ],
            },
        )

    client = _client(monkeypatch, handler, retries=1, backoff=0.5)

    client.chat(_messages())

    assert sleeps == [0.5]


def test_city_count_answer_accepts_15():
    from evaluation.smoke import _answer_check

    case = next(
        c for c in SMOKE_CASES
        if c.case_id == "SMOKE-002"
    )

    state = SimpleNamespace(
        final_answer="共有 15 个城市。",
        errors=[],
    )

    passed, _ = _answer_check(state, case)

    assert passed is True


def test_group_count_accepts_markdown_table():
    from evaluation.smoke import _answer_check

    case = next(
        c for c in SMOKE_CASES
        if c.case_id == "SMOKE-004"
    )

    state = SimpleNamespace(
        final_answer="""
        州与城市数量：

        | 州 | 城市数 |
        |----|--------|
        | AZ | 1 |
        | CA | 3 |
        | FL | 1 |
        | TX | 5 |
        """,
        errors=[],
    )

    passed, _ = _answer_check(state, case)

    assert passed is True


def test_drop_table_is_rejected():
    with pytest.raises(SQLValidationError) as exc_info:
        validate_sql("DROP TABLE city;")

    assert exc_info.value.code == "STATEMENT_NOT_READ_ONLY"


def test_answer_prompt_requires_result_grounding():
    sql = ""
    result = []
    messages = build_answer_messages("每个州有多少个城市？", sql, result)

    system_prompt = messages[0].content.lower()

    assert "strictly" in system_prompt
    assert "query result" in system_prompt


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


def test_retry_after_above_cap_fails_fast(monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        "ai.analyst.app.llm.client.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    def handler(request):
        return httpx.Response(
            429,
            headers={"Retry-After": "120"},
            json={"error": {"message": "rate limit exceeded"}},
        )

    monkeypatch.setenv("LLM_MAX_RETRY_AFTER_SECONDS", "60")
    client = _client(monkeypatch, handler, retries=2, backoff=0.5)

    with pytest.raises(LLMClientError) as exc:
        client.chat(_messages())

    assert exc.value.code == "LLM_RATE_LIMIT"
    assert sleeps == []
