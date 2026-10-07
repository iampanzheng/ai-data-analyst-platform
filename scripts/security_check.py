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
    env_example = (ROOT / ".env.example").read_text()

    require(".env" in gitignore, ".env must be ignored by Git")
    require(".env" in dockerignore, ".env must be excluded from Docker build context")
    require(
        "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-analyst}" in compose,
        "Compose database password must be environment-configurable with the local compatibility default",
    )
    expected_database_url = (
        "postgresql://${POSTGRES_USER:-analyst}:${POSTGRES_PASSWORD:-analyst}"
        "@postgres:5432/${POSTGRES_DB:-ai_analyst}"
    )
    require(
        compose.count(expected_database_url) >= 2,
        "FastAPI and ETL database URLs must use the same environment-configurable local compatibility defaults",
    )
    require(
        "changing it does not rotate an existing PostgreSQL volume" in env_example,
        ".env.example must document that POSTGRES_PASSWORD does not rotate an existing PostgreSQL volume",
    )
    require("CORS_ALLOWED_ORIGIN: http://localhost:5173" not in compose, "CORS origin must be environment-configurable")

    expected_bindings = (
        '127.0.0.1:${POSTGRES_PORT:-5432}:5432',
        '127.0.0.1:${FASTAPI_PORT:-8000}:8000',
        '127.0.0.1:${GATEWAY_PORT:-8080}:8080',
        '127.0.0.1:${WEB_PORT:-5173}:5173',
    )
    for binding in expected_bindings:
        require(binding in compose, f"missing loopback-only port binding: {binding}")

    application_dockerfiles = {
        "FastAPI": ROOT / "ai/analyst/Dockerfile",
        "ETL": ROOT / "etl/Dockerfile",
        "Gateway": ROOT / "backend/springboot/Dockerfile",
        "Web": ROOT / "frontend/web/Dockerfile",
    }
    for service, path in application_dockerfiles.items():
        dockerfile = path.read_text()
        user_lines = [
            line.strip()
            for line in dockerfile.splitlines()
            if line.strip().upper().startswith("USER ")
        ]
        require(user_lines, f"{service} Dockerfile must declare an explicit runtime USER")
        runtime_user = user_lines[-1].split(maxsplit=1)[1].strip().lower()
        require(runtime_user not in {"root", "0", "0:0"}, f"{service} runtime USER must be non-root")

    print("security configuration baseline: PASS")


if __name__ == "__main__":
    main()
