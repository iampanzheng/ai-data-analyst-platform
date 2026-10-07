PYTHON ?= uv run python
COMPOSE ?= docker compose

.PHONY: security-check repo-check publish-check ci help data-download etl up down logs ps compile test test-backend eval smoke smoke-docker acceptance web-test web-build compose-check verify

help:
	@printf '%s\n' \
	  'make up             Build/start the full local stack' \
	  'make test           Run FastAPI/Python tests in Compose' \
	  'make web-test       Run deterministic frontend tests in Compose' \
	  'make web-build      Run the frontend production build in Compose' \
	  'make security-check Run deterministic security/configuration checks' \
	  'make repo-check     Check current Git tree for publication hygiene' \
	  'make publish-check  Scan current tree + Git history before first public push' \
	  'make ci             Run repository hygiene + deterministic production verification' \
	  'make verify         Run the complete deterministic local production baseline' \
	  'make acceptance     Run the real-stack Stage 3.8 acceptance suite from the host' \
	  'make eval           Run the evaluation harness from the host'

data-download:
	$(PYTHON) scripts/download_data.py

etl:
	$(PYTHON) etl/load_sample.py

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

compile:
	$(PYTHON) -m compileall -q ai etl scripts tests acceptance

test: test-backend

test-backend:
	$(COMPOSE) exec -T fastapi pytest -q

eval:
	$(PYTHON) -m evaluation.run

smoke:
	$(PYTHON) -m evaluation.smoke

smoke-docker:
	$(COMPOSE) exec -T fastapi python -m evaluation.smoke

acceptance:
	$(PYTHON) -m acceptance.run

web-test:
	$(COMPOSE) exec -T web npm test

web-build:
	$(COMPOSE) exec -T web npm run build

compose-check:
	$(COMPOSE) config --quiet

verify:
	COMPOSE='$(COMPOSE)' sh scripts/verify_local.sh

security-check:
	$(PYTHON) scripts/security_check.py

repo-check:
	$(PYTHON) scripts/repository_check.py

publish-check:
	$(PYTHON) scripts/repository_check.py --history

ci: repo-check verify
