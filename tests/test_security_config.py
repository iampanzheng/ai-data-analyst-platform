from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compose_keeps_existing_local_postgres_volume_compatible():
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-analyst}" in compose
    assert "postgresql://${POSTGRES_USER:-analyst}:${POSTGRES_PASSWORD:-analyst}@postgres:5432/${POSTGRES_DB:-ai_analyst}" in compose


def test_env_example_explains_password_rotation_limit():
    env_example = (ROOT / ".env.example").read_text()
    assert "changing it does not rotate an existing PostgreSQL volume" in env_example
