.PHONY: data-download etl up down logs ps test eval smoke smoke-docker acceptance web-test
data-download:
	python scripts/download_data.py
etl:
	python etl/load_sample.py
up:
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f
ps:
	docker compose ps
test:
	python -m compileall ai etl scripts tests

eval:
	python -m evaluation.run

smoke:
	python -m evaluation.smoke

smoke-docker:
	docker compose exec fastapi python -m evaluation.smoke

acceptance:
	python -m acceptance.run

web-test:
	cd frontend/web && npm test
