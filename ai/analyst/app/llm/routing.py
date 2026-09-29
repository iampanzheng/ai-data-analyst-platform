from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .client import LLMClient, LLMClientError, create_llm_client


RoutingMode = Literal["auto", "remote", "local"]
RouteName = Literal["remote", "local", "legacy"]


@dataclass(frozen=True)
class RoutingSettings:
    enabled: bool
    default_route: Literal["remote", "local"]
    allow_remote: bool
    allow_local: bool

    @classmethod
    def from_env(cls) -> "RoutingSettings":
        default_route = os.getenv("LLM_ROUTING_DEFAULT_ROUTE", "remote").strip().lower()
        if default_route not in {"remote", "local"}:
            raise LLMClientError(
                "LLM_ROUTING_CONFIGURATION_ERROR",
                "LLM_ROUTING_DEFAULT_ROUTE must be 'remote' or 'local'",
            )
        return cls(
            enabled=_env_bool("LLM_ROUTING_ENABLED", False),
            default_route=default_route,
            allow_remote=_env_bool("LLM_ROUTING_ALLOW_REMOTE", True),
            allow_local=_env_bool("LLM_ROUTING_ALLOW_LOCAL", True),
        )


@dataclass(frozen=True)
class RouteDecision:
    requested_mode: RoutingMode
    selected_route: RouteName
    reason: str
    fallback_route: None = None


def decide_route(
    requested_mode: RoutingMode,
    settings: RoutingSettings,
) -> RouteDecision:
    """Deterministic Stage 2.4 routing policy.

    The router never asks an LLM to choose an LLM.  Stage 2.3 measurements make
    the remote Groq path the default interactive route, while local Ollama is an
    explicit privacy/offline/$0-API-cost route.  Automatic runtime fallback is
    intentionally deferred to Stage 2.5.
    """
    if requested_mode not in {"auto", "remote", "local"}:
        raise LLMClientError(
            "LLM_ROUTING_REQUEST_ERROR",
            f"Unsupported routing mode: {requested_mode}",
        )

    if not settings.enabled:
        if requested_mode != "auto":
            raise LLMClientError(
                "LLM_ROUTING_DISABLED",
                "Explicit local/remote routing requires LLM_ROUTING_ENABLED=true",
            )
        return RouteDecision(
            requested_mode=requested_mode,
            selected_route="legacy",
            reason="routing_disabled_legacy_client",
        )

    if requested_mode == "remote":
        _ensure_allowed("remote", settings.allow_remote)
        return RouteDecision(
            requested_mode=requested_mode,
            selected_route="remote",
            reason="explicit_remote_request",
        )

    if requested_mode == "local":
        _ensure_allowed("local", settings.allow_local)
        return RouteDecision(
            requested_mode=requested_mode,
            selected_route="local",
            reason="explicit_local_request",
        )

    selected = settings.default_route
    if selected == "remote":
        _ensure_allowed("remote", settings.allow_remote)
        reason = "auto_default_remote_stage2_3_measurements"
    else:
        _ensure_allowed("local", settings.allow_local)
        reason = "auto_default_local_configuration"

    return RouteDecision(
        requested_mode=requested_mode,
        selected_route=selected,
        reason=reason,
    )


def create_routed_llm_client(
    requested_mode: RoutingMode = "auto",
    *,
    settings: RoutingSettings | None = None,
) -> tuple[RouteDecision, LLMClient]:
    settings = settings or RoutingSettings.from_env()
    decision = decide_route(requested_mode, settings)

    if decision.selected_route == "legacy":
        return decision, create_llm_client()
    if decision.selected_route == "remote":
        return decision, create_llm_client(prefix="LLM_REMOTE")
    return decision, create_llm_client(prefix="LLM_LOCAL")


def _ensure_allowed(route: str, allowed: bool) -> None:
    if not allowed:
        raise LLMClientError(
            "LLM_ROUTING_ROUTE_DISABLED",
            f"The {route} LLM route is disabled by configuration",
        )


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
