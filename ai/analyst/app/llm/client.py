from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from .models import ChatMessage, LLMResponse


class LLMClientError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
        retry_after_seconds: float | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    """Deterministic client for local/dev tests. No network, no API key."""

    provider = "mock"

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if "Generate SQL" in user or "生成 SQL" in user:
            if "DROP TABLE" in user.upper():
                return LLMResponse(
                    content="DROP TABLE city",
                    model="mock-analyst-v0.1",
                    provider=self.provider,
                )
            return LLMResponse(
                content=(
                    "SELECT name, state, population, year FROM city "
                    "ORDER BY population DESC LIMIT 5"
                ),
                model="mock-analyst-v0.1",
                provider=self.provider,
            )
        return LLMResponse(
            content="基于查询结果，人口最多的城市及其人口数据如下。",
            model="mock-analyst-v0.1",
            provider=self.provider,
        )


def normalize_usage(raw_usage: Any) -> dict[str, int]:
    """Normalize provider-specific usage into stable input/output/total token fields."""
    if not isinstance(raw_usage, dict):
        return {}

    def token_value(*keys: str) -> int:
        for key in keys:
            value = raw_usage.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                return max(0, int(value))
        return 0

    input_tokens = token_value("input_tokens", "prompt_tokens")
    output_tokens = token_value("output_tokens", "completion_tokens")
    total_tokens = token_value("total_tokens") or (input_tokens + output_tokens)
    if not (input_tokens or output_tokens or total_tokens):
        return {}
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _chat_completions_url(base_url: str) -> str:
    """Build a chat-completions URL from common OpenAI-compatible API roots.

    Supports provider roots (where /v1 is implied) and API roots that already
    end in /v1 or /openai, such as Gemini's /v1beta/openai endpoint.
    """
    normalized = base_url.rstrip("/")
    if normalized.endswith(("/v1", "/openai")):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


class OpenAICompatibleLLMClient(LLMClient):
    """OpenAI-compatible /v1/chat/completions client with retries and normalized telemetry."""

    provider = "openai-compatible"

    def __init__(self) -> None:
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.retry_backoff_seconds = float(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "0.5"))
        self.reasoning_effort = os.getenv("LLM_REASONING_EFFORT", "").strip().lower()
        if not self.base_url or not self.model:
            raise LLMClientError(
                "LLM_CONFIGURATION_ERROR",
                "LLM_BASE_URL and LLM_MODEL are required",
            )
        if self.max_retries < 0:
            raise LLMClientError(
                "LLM_CONFIGURATION_ERROR",
                "LLM_MAX_RETRIES must be >= 0",
            )
        if self.retry_backoff_seconds < 0:
            raise LLMClientError(
                "LLM_CONFIGURATION_ERROR",
                "LLM_RETRY_BACKOFF_SECONDS must be >= 0",
            )

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        url = _chat_completions_url(self.base_url)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_error: LLMClientError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
                if response.status_code >= 400:
                    raise self._http_status_error(response)

                try:
                    data = response.json()
                except ValueError as exc:
                    raise LLMClientError(
                        "LLM_INVALID_RESPONSE",
                        "LLM response was not valid JSON",
                    ) from exc

                choices = data.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise LLMClientError(
                        "LLM_INVALID_RESPONSE",
                        "LLM response did not contain choices",
                    )
                choice = choices[0]
                if not isinstance(choice, dict):
                    raise LLMClientError(
                        "LLM_INVALID_RESPONSE",
                        "LLM response choice was invalid",
                    )
                message = choice.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if not isinstance(content, str) or not content.strip():
                    raise LLMClientError(
                        "LLM_INVALID_RESPONSE",
                        "LLM response did not contain message content",
                    )

                return LLMResponse(
                    content=content,
                    model=str(data.get("model") or self.model),
                    provider=self.provider,
                    usage=normalize_usage(data.get("usage")),
                )
            except LLMClientError as exc:
                last_error = exc
            except httpx.TimeoutException as exc:
                last_error = LLMClientError(
                    "LLM_TIMEOUT",
                    f"LLM request timed out: {exc}",
                    retryable=True,
                )
            except httpx.RequestError as exc:
                last_error = LLMClientError(
                    "LLM_CONNECTION_ERROR",
                    f"LLM connection failed: {exc}",
                    retryable=True,
                )

            if not last_error.retryable or attempt >= self.max_retries:
                raise last_error
            self._sleep_before_retry(attempt, last_error)

        raise last_error or LLMClientError("LLM_ERROR", "Unknown LLM client error")

    def _sleep_before_retry(
        self,
        attempt: int,
        error: LLMClientError,
    ) -> None:
        if error.retry_after_seconds is not None:
            delay = error.retry_after_seconds
        else:
            delay = self.retry_backoff_seconds * (2**attempt)

        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _http_status_error(response: httpx.Response) -> LLMClientError:
        status = response.status_code
        if status in {401, 403}:
            return LLMClientError(
                "LLM_AUTH_ERROR",
                f"LLM authentication/authorization failed with HTTP {status}",
                status_code=status,
            )
        if status == 429:
            retry_after_seconds = None
            raw_retry_after = response.headers.get("Retry-After")

            if raw_retry_after:
                try:
                    retry_after_seconds = max(0.0, float(raw_retry_after))
                except ValueError:
                    pass

            return LLMClientError(
                "LLM_RATE_LIMIT",
                "LLM provider rate limit exceeded",
                retryable=True,
                status_code=status,
                retry_after_seconds=retry_after_seconds,
            )
        if 500 <= status <= 599:
            return LLMClientError(
                "LLM_SERVER_ERROR",
                f"LLM provider returned HTTP {status}",
                retryable=True,
                status_code=status,
            )
        return LLMClientError(
            "LLM_REQUEST_ERROR",
            f"LLM provider rejected the request with HTTP {status}",
            status_code=status,
        )


def create_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider in {"", "mock"}:
        return MockLLMClient()
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleLLMClient()
    raise LLMClientError(
        "LLM_CONFIGURATION_ERROR",
        f"Unsupported LLM_PROVIDER: {provider}",
    )
