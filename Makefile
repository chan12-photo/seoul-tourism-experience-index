.PHONY: install test lint check-public

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	python -m ruff check src tests

check-public:
	tei-pipeline check-public .

