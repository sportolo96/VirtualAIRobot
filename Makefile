.PHONY: test lint lint-fix typecheck quality quality-fix docker-env-check docker-build docker-start docker-check build start check

COMPOSE_ENV_FILE := .env
COMPOSE := docker compose --env-file $(COMPOSE_ENV_FILE)

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check src tests

lint-fix:
	python3 -m ruff check src tests --fix
	python3 -m ruff format src tests

typecheck:
	python3 -m mypy src tests

quality:
	$(MAKE) lint
	$(MAKE) typecheck

quality-fix:
	$(MAKE) lint-fix
	$(MAKE) typecheck

docker-env-check:
	@test -f "$(COMPOSE_ENV_FILE)" || (echo "Missing $(COMPOSE_ENV_FILE). Create it from .env.example first." >&2; exit 1)

docker-build: docker-env-check
	$(COMPOSE) build

docker-start: docker-env-check
	$(COMPOSE) up -d

docker-check:
	@for i in $$(seq 1 30); do \
		if curl -fsS http://localhost:8000/health > /tmp/virtualairobot_health.json 2>/dev/null; then \
			cat /tmp/virtualairobot_health.json; \
			echo; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "API health check failed after waiting 30 seconds." >&2; \
	exit 1

build: docker-build

start: docker-start

check: docker-check
