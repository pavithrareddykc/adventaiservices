PY=python3

.PHONY: test backend-test frontend-test up down build backup-db

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

backup-db:
	DB_PATH=backend/contacts.db BACKUP_DIR=backups RETENTION=7 bash scripts/backup_db.sh