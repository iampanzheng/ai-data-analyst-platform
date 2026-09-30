from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .client import LLMClient, LLMClientError, create_llm_client
from .reliability import FallbackMode, ReliabilityPolicy, ResilientLLMClient

RoutingMode = Literal["auto", "remote", "local"]
RouteName = Literal["remote", "local", "legacy"]


@dataclass(frozen=True)
class RoutingSettings:
    enabled: bool
    default_route: Literal["remote", "local"]
    allow_remote: bool
    allow_local: bool
    fallback_enabled: bool = True
    fallback_error_codes: frozenset[str] = frozenset({
        "LLM_TIMEOUT", "LLM_CONNECTION_ERROR", "LLM_RATE_LIMIT", "LLM_SERVER_ERROR"
    })
    max_estimated_cost_usd: float = 0.0

    @classmethod
    def from_env(cls) -> "RoutingSettings":
        default_route = os.getenv("LLM_ROUTING_DEFAULT_ROUTE", "remote").strip().lower()
        if default_route not in {"remote", "local"}:
            raise LLMClientError(
                "LLM_ROUTING_CONFIGURATION_ERROR",
                "LLM_ROUTING_DEFAULT_ROUTE must be 'remote' or 'local'",
            )
        raw_codes = os.getenv(
            "LLM_ROUTING_FALLBACK_ERROR_CODES",
            "LLM_TIMEOUT,LLM_CONNECTION_ERROR,LLM_RATE_LIMIT,LLM_SERVER_ERROR",
        )
        return cls(
            enabled=_env_bool("LLM_ROUTING_ENABLED", False),
            default_route=default_route,
            allow_remote=_env_bool("LLM_ROUTING_ALLOW_REMOTE", True),
            allow_local=_env_bool("LLM_ROUTING_ALLOW_LOCAL", True),
            fallback_enabled=_env_bool("LLM_ROUTING_FALLBACK_ENABLED", True),
            fallback_error_codes=frozenset(code.strip() for code in raw_codes.split(",") if code.strip()),
            max_estimated_cost_usd=float(os.getenv("LLM_ROUTING_MAX_ESTIMATED_COST_USD", "0")),
        )


@dataclass(frozen=True)
class RouteDecision:
    requested_mode: RoutingMode
    selected_route: RouteName
    reason: str
    fallback_route: RouteName | None = None


def decide_route(
    requested_mode: RoutingMode,
    settings: RoutingSettings,
    *,
    fallback_mode: FallbackMode = "auto",
) -> RouteDecision:
    if requested_mode not in {"auto", "remote", "local"}:
        raise LLMClientError("LLM_ROUTING_REQUEST_ERROR", f"Unsupported routing mode: {requested_mode}")
    if fallback_mode not in {"auto", "disabled", "cross_route"}:
        raise LLMClientError("LLM_ROUTING_REQUEST_ERROR", f"Unsupported fallback mode: {fallback_mode}")

    if not settings.enabled:
        if requested_mode != "auto":
            raise LLMClientError(
                "LLM_ROUTING_DISABLED",
                "Explicit local/remote routing requires LLM_ROUTING_ENABLED=true",
            )
        return RouteDecision(requested_mode, "legacy", "routing_disabled_legacy_client", None)

    if requested_mode == "remote":
        _ensure_allowed("remote", settings.allow_remote)
        selected, reason = "remote", "explicit_remote_request"
    elif requested_mode == "local":
        _ensure_allowed("local", settings.allow_local)
        selected, reason = "local", "explicit_local_request"
    else:
        selected = settings.default_route
        if selected == "remote":
            _ensure_allowed("remote", settings.allow_remote)
            reason = "auto_default_remote_stage2_3_measurements"
        else:
            _ensure_allowed("local", settings.allow_local)
            reason = "auto_default_local_configuration"

    fallback_route: RouteName | None = None
    if settings.fallback_enabled and fallback_mode != "disabled":
        alternate: RouteName = "local" if selected == "remote" else "remote"
        alternate_allowed = settings.allow_local if alternate == "local" else settings.allow_remote
        if alternate_allowed:
            # Explicit local remains local-only unless caller explicitly opts into
            # cross-route fallback. Auto selected-local follows the same privacy rule.
            if not (selected == "local" and alternate == "remote" and fallback_mode != "cross_route"):
                fallback_route = alternate

    return RouteDecision(requested_mode, selected, reason, fallback_route)


def create_routed_llm_client(
    requested_mode: RoutingMode = "auto",
    *,
    fallback_mode: FallbackMode = "auto",
    settings: RoutingSettings | None = None,
) -> tuple[RouteDecision, LLMClient]:
    settings = settings or RoutingSettings.from_env()
    decision = decide_route(requested_mode, settings, fallback_mode=fallback_mode)

    if decision.selected_route == "legacy":
        return decision, create_llm_client()

    primary = create_llm_client(prefix="LLM_REMOTE" if decision.selected_route == "remote" else "LLM_LOCAL")
    fallback = None
    if decision.fallback_route is not None:
        fallback = create_llm_client(prefix="LLM_REMOTE" if decision.fallback_route == "remote" else "LLM_LOCAL")

    return decision, ResilientLLMClient(
        primary_route=decision.selected_route,
        primary=primary,
        fallback_route=decision.fallback_route,
        fallback=fallback,
        fallback_mode=fallback_mode,
        policy=ReliabilityPolicy(
            fallback_enabled=settings.fallback_enabled,
            fallback_error_codes=settings.fallback_error_codes,
            max_estimated_cost_usd=settings.max_estimated_cost_usd,
        ),
    )


def _ensure_allowed(route: str, allowed: bool) -> None:
    if not allowed:
        raise LLMClientError("LLM_ROUTING_ROUTE_DISABLED", f"The {route} LLM route is disabled by configuration")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
