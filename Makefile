.PHONY: help install install-dev test test-cov lint format clean demo run docs

help:
	@echo "PyVirtOS - Development Commands"
	@echo "================================"
	@echo "make install      - Install dependencies"
	@echo "make install-dev  - Install with dev dependencies"
	@echo "make test         - Run tests"
	@echo "make test-cov     - Run tests with coverage"
	@echo "make lint         - Run linting checks"
	@echo "make format       - Format code with black and isort"
	@echo "make clean        - Clean build artifacts"
	@echo "make demo         - Run demo script"
	@echo "make run          - Run PyVirtOS"
	@echo "make docs         - Generate documentation"

install:
	poetry install --no-dev

install-dev:
	poetry install

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=pyvirtos --cov-report=html --cov-report=term

lint:
	poetry run flake8 pyvirtos tests
	poetry run mypy pyvirtos --ignore-missing-imports

format:
	poetry run black pyvirtos tests scripts
	poetry run isort pyvirtos tests scripts

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
	rm -rf build dist *.egg-info

demo:
	poetry run python scripts/demo.py

run:
	poetry run python -m pyvirtos

docs:
	@echo "Documentation generation not yet implemented"
	@echo "See README.md for architecture overview"

.DEFAULT_GOAL := help
