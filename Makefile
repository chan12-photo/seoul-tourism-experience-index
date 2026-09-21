PYTHON ?= python

.PHONY: install test lint format format-check smoke check-public verify

install:
	$(PYTHON) -m pip install -e ".[dev,geo,viz]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests scripts

format:
	$(PYTHON) -m ruff format src tests scripts

format-check:
	$(PYTHON) -m ruff format --check src tests scripts

smoke:
	$(PYTHON) -m compileall -q src scripts
	$(PYTHON) scripts/build_portfolio_assets.py --help >/dev/null
	$(PYTHON) -m pip check

check-public:
	$(PYTHON) -m tei_pipeline check-public .

verify: test lint format-check smoke check-public
