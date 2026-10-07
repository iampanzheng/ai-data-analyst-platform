from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"security check failed: {message}")


def main() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    gitignore = (ROOT / ".gitignore").read_text().splitlines()
    dockerignore = (ROOT / ".dockerignore").read_text().splitlines()

    require(".env" in gitignore, ".env must be ignored by Git")
    require(".env" in dockerignore, ".env must be excluded from Docker build context")
    require("POSTGRES_PASSWORD: analyst" not in compose, "Compose must not hard-code the legacy database password")
    require("CORS_ALLOWED_ORIGIN: http://localhost:5173" not in compose, "CORS origin must be environment-configurable")

    expected_bindings = (
        '127.0.0.1:${POSTGRES_PORT:-5432}:5432',
        '127.0.0.1:${FASTAPI_PORT:-8000}:8000',
        '127.0.0.1:${GATEWAY_PORT:-8080}:8080',
        '127.0.0.1:${WEB_PORT:-5173}:5173',
    )
    for binding in expected_bindings:
        require(binding in compose, f"missing loopback-only port binding: {binding}")

    print("security configuration baseline: PASS")


if __name__ == "__main__":
    main()
