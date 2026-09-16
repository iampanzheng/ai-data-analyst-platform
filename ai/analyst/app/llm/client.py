from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from .models import ChatMessage, LLMResponse


class LLMClientError(RuntimeError):
    pass


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    """Deterministic client for local/dev tests. No network, no API key."""

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if "Generate SQL" in user or "生成 SQL" in user:
            return LLMResponse(
                content=(
                    'SELECT name, state, population, year FROM city '
                    'ORDER BY population DESC LIMIT 5'
                ),
                model="mock-analyst-v0.1",
            )
        return LLMResponse(
            content="基于查询结果，人口最多的城市及其人口数据如下。",
            model="mock-analyst-v0.1",
        )


class OpenAICompatibleLLMClient(LLMClient):
    """Minimal OpenAI-compatible /v1/chat/completions client without SDK coupling."""

    def __init__(self) -> None:
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        if not self.base_url or not self.model:
            raise LLMClientError("LLM_BASE_URL and LLM_MODEL are required")

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        url = f"{self.base_url}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise LLMClientError("LLM response did not contain message content")
            usage = data.get("usage") or {}
            return LLMResponse(content=content, model=str(data.get("model") or self.model), usage=usage)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise LLMClientError(f"LLM request failed: {exc}") from exc


def create_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider in {"", "mock"}:
        return MockLLMClient()
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleLLMClient()
    raise LLMClientError(f"Unsupported LLM_PROVIDER: {provider}")
