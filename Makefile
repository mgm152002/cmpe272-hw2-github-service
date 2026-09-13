# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

.PHONY: install run test lint format docker-build

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m uvicorn app.main:app --reload --port $${PORT:-8000}

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

docker-build:
	docker build -t cmpe272-hw2-github-service .
