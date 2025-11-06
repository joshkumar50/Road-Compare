SHELL := /bin/sh

.PHONY: build up down logs test sample-run fmt

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	docker compose exec backend pytest -q

sample-run:
	bash scripts/sample_run.sh






