#!/usr/bin/env sh
set -eu

COMPOSE="${COMPOSE:-docker compose}"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required for host-side Python verification." >&2
  exit 127
fi

assert_non_root_service() {
  service="$1"
  uid="$($COMPOSE run --rm --no-deps --entrypoint id "$service" -u | tail -n 1 | tr -d '[:space:]')"
  if [ -z "$uid" ] || [ "$uid" = "0" ]; then
    echo "ERROR: service '$service' runtime UID must be non-root; got '${uid:-unknown}'." >&2
    exit 1
  fi
  echo "$service runtime uid: $uid"
}

echo "[1/8] Run security/configuration baseline checks"
uv run python scripts/security_check.py

echo "[2/8] Validate Docker Compose configuration"
$COMPOSE config --quiet

echo "[3/8] Build and start the local stack"
$COMPOSE up -d --build postgres etl fastapi gateway web

echo "[4/8] Verify application containers run as non-root"
assert_non_root_service fastapi
assert_non_root_service etl
assert_non_root_service gateway
assert_non_root_service web

echo "[5/8] Run FastAPI/Python regression suite"
$COMPOSE exec -T fastapi pytest -q

echo "[6/8] Run deterministic frontend regression suite"
$COMPOSE exec -T web npm test

echo "[7/8] Run frontend production build"
$COMPOSE exec -T web npm run build

echo "[8/8] Verify Gateway health endpoint"
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
