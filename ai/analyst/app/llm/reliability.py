from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .client import LLMClient, LLMClientError
from .models import ChatMessage, LLMResponse

RouteName = Literal["remote", "local", "legacy"]
FallbackMode = Literal["auto", "disabled", "cross_route"]

DEFAULT_FALLBACK_ERROR_CODES = frozenset({
    "LLM_TIMEOUT",
    "LLM_CONNECTION_ERROR",
    "LLM_RATE_LIMIT",
    "LLM_SERVER_ERROR",
})


@dataclass(frozen=True)
class ReliabilityPolicy:
    fallback_enabled: bool = True
    fallback_error_codes: frozenset[str] = DEFAULT_FALLBACK_ERROR_CODES
    max_estimated_cost_usd: float = 0.0


@dataclass
class ResilientLLMClient(LLMClient):
    primary_route: RouteName
    primary: LLMClient
    fallback_route: RouteName | None = None
    fallback: LLMClient | None = None
    fallback_mode: FallbackMode = "auto"
    policy: ReliabilityPolicy = field(default_factory=ReliabilityPolicy)
    current_route: RouteName = field(init=False)
    fallback_events: list[dict[str, str]] = field(default_factory=list, init=False)
    route_usage: dict[str, dict[str, int]] = field(default_factory=dict, init=False)
    estimated_cost_usd: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.current_route = self.primary_route

    @property
    def disable_thinking(self) -> bool:
        return bool(getattr(self._client_for(self.current_route), "disable_thinking", False))

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.0) -> LLMResponse:
        self._enforce_cost_budget()
        route = self.current_route
        client = self._client_for(route)
        try:
            response = client.chat(messages, temperature=temperature)
            self._record_response(route, client, response)
            return response
        except LLMClientError as exc:
            if not self._should_fallback(route, exc):
                raise

            assert self.fallback_route is not None and self.fallback is not None
            fallback_route = self.fallback_route
            self.fallback_events.append({
                "from_route": route,
                "to_route": fallback_route,
                "error_code": exc.code,
                "reason": "retryable_provider_failure",
            })
            self.current_route = fallback_route
            self._enforce_cost_budget()
            response = self.fallback.chat(messages, temperature=temperature)
            self._record_response(fallback_route, self.fallback, response)
            return response

    def _should_fallback(self, route: RouteName, error: LLMClientError) -> bool:
        if not self.policy.fallback_enabled or self.fallback_mode == "disabled":
            return False
        if self.fallback is None or self.fallback_route is None:
            return False
        if route != self.primary_route:
            return False
        if error.code not in self.policy.fallback_error_codes:
            return False
        if not error.retryable:
            return False
        # Explicit local is privacy-preserving by default. Only a caller that
        # explicitly opts into cross_route may send that request to remote.
        if self.primary_route == "local" and self.fallback_route == "remote":
            return self.fallback_mode == "cross_route"
        return self.fallback_mode in {"auto", "cross_route"}

    def _client_for(self, route: RouteName) -> LLMClient:
        if route == self.primary_route:
            return self.primary
        if route == self.fallback_route and self.fallback is not None:
            return self.fallback
        raise LLMClientError("LLM_ROUTING_CONFIGURATION_ERROR", f"No client configured for route {route}")

    def _record_response(self, route: RouteName, client: LLMClient, response: LLMResponse) -> None:
        bucket = self.route_usage.setdefault(route, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
        for key in bucket:
            bucket[key] += int(response.usage.get(key, 0) or 0)
        estimator = getattr(client, "estimate_cost", None)
        if callable(estimator):
            self.estimated_cost_usd += float(estimator(response.usage))

    def _enforce_cost_budget(self) -> None:
        budget = self.policy.max_estimated_cost_usd
        if budget > 0 and self.estimated_cost_usd >= budget:
            raise LLMClientError(
                "LLM_COST_BUDGET_EXCEEDED",
                f"Estimated request cost reached configured budget ${budget:.6f}",
            )
