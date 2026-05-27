.PHONY: setup lint format test run

setup:
	python -m venv .venv
	.venv\\Scripts\\python -m pip install --upgrade pip
	.venv\\Scripts\\pip install -e .[dev]

lint:
	.venv\\Scripts\\ruff check .

format:
	.venv\\Scripts\\ruff format .

test:
	.venv\\Scripts\\pytest

run:
	.venv\\Scripts\\python -m pdf_extraction_benchmark.main
