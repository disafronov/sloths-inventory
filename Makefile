PYTHONPATH = src

PYTEST_CMD = PYTHONPATH=$(PYTHONPATH) uv run python -m pytest -v
COVERAGE_OPTS = --cov --cov-report=term-missing --cov-report=html

.PHONY: all clean help format lint test test-coverage dead-code install

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv sync
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

format: ## Format code
	@echo "Formatting code..."
	PYTHONPATH=$(PYTHONPATH) uv run black . && PYTHONPATH=$(PYTHONPATH) uv run isort .

lint: ## Run linting tools
	@echo "Running linting tools..."
	PYTHONPATH=$(PYTHONPATH) uv run black --check . && \
	PYTHONPATH=$(PYTHONPATH) uv run isort --check-only . && \
		PYTHONPATH=$(PYTHONPATH) uv run flake8 . && \
		PYTHONPATH=$(PYTHONPATH) uv run mypy . && \
		PYTHONPATH=$(PYTHONPATH) uv run bandit -r -c pyproject.toml .

dead-code: ## Check for dead code using vulture
	@echo "Checking for dead code..."
	PYTHONPATH=$(PYTHONPATH) uv run vulture .

test: ## Run tests
	@echo "Running tests..."
	$(PYTEST_CMD)

test-coverage: ## Run tests with HTML coverage report
	@echo "Running tests with coverage..."
	$(PYTEST_CMD) $(COVERAGE_OPTS)

all: format lint test dead-code ## Run format, lint, test, and dead-code check
	@echo "All checks completed successfully!"

clean: ## Clean caches and coverage outputs
	@echo "Cleaning cache and temporary files..."
	rm -rf .mypy_cache/ .pytest_cache/ .venv/ build/ dist/ htmlcov/ .coverage coverage.xml .coverage.*

