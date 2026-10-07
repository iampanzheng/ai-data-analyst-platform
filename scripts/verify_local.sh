#!/usr/bin/env sh
set -eu

COMPOSE="${COMPOSE:-docker compose}"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required for host-side Python verification." >&2
  exit 127
fi

echo "[1/6] Validate Docker Compose configuration"
$COMPOSE config --quiet

echo "[2/6] Build and start the local stack"
$COMPOSE up -d --build postgres etl fastapi gateway web

echo "[3/6] Run FastAPI/Python regression suite"
$COMPOSE exec -T fastapi pytest -q

echo "[4/6] Run deterministic frontend regression suite"
$COMPOSE exec -T web npm test

echo "[5/6] Run frontend production build"
$COMPOSE exec -T web npm run build

echo "[6/6] Verify Gateway health endpoint"
uv run python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("http://localhost:8080/api/health", timeout=5) as response:
    if response.status != 200:
        raise SystemExit(f"gateway health returned HTTP {response.status}")
    payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") != "ok":
        raise SystemExit(f"gateway health returned unexpected payload: {payload!r}")
print("gateway health: PASS")
PY

echo "Local production baseline: PASS"
