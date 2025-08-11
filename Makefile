PY=python3

.PHONY: test backend-test frontend-test up down build

test: backend-test frontend-test

backend-test:
	$(PY) -m unittest discover -s backend/tests -v

frontend-test:
	$(PY) -m unittest discover -s frontend/tests -v

build:
	docker compose build --no-cache

up:
	docker compose up -d

down:
	docker compose down -v