.PHONY: test lint lint-fix typecheck quality quality-fix

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
