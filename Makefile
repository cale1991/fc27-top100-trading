.PHONY: up down migrate test lint smoke
up:
	docker compose up -d postgres redis

down:
	docker compose down

migrate:
	alembic upgrade head

test:
	pytest -q

lint:
	ruff check src tests scripts

smoke:
	python scripts/smoke_test.py
