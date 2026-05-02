PYTHONPATH = src

# Python version is pinned via `.python-version` (used by uv and CI).
PYTHON_VERSION := $(shell tr -d '[:space:]' < .python-version)

# Include environment files (same pattern as other repos).
#
# Important: in CI, environment variables passed by the runner must win over
# defaults from `env.example`, but GNU make gives Makefile assignments higher
# priority than the environment. Therefore we only auto-include env files for
# local development (when `CI` is not set).
#
# - `env.example` provides defaults and documents available settings.
# - `.env` (if present) overrides `env.example` for local development.
ifeq ($(strip $(CI)),)
    ifneq (,$(wildcard .env))
        ifneq (,$(wildcard env.example))
            include env.example
        endif
        include .env
    else
        ifneq (,$(wildcard env.example))
            include env.example
        endif
    endif
    export
endif

# Tooling-only SECRET_KEY used for local checks.
#
# Django settings require SECRET_KEY when DEBUG is disabled. Both pytest-django and
# django-stubs (mypy) import Django settings during initialization, so we provide a
# deterministic fake key for local tooling via Makefile targets.
TOOLING_SECRET_KEY = unsafe-secret-key-for-tooling

PYTEST_CMD = PYTHONPATH=$(PYTHONPATH) SECRET_KEY=$(TOOLING_SECRET_KEY) uv run python -m pytest -v
COVERAGE_OPTS = --cov --cov-report=term-missing --cov-report=html

DOCKER_IMAGE = sloths-inventory

.PHONY: all clean dead-code docker docker-build docker-run format help install lint run test test-coverage test-postgres

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv python install $(PYTHON_VERSION)
	uv sync --python $(PYTHON_VERSION)
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
		PYTHONPATH=$(PYTHONPATH) SECRET_KEY=$(TOOLING_SECRET_KEY) uv run mypy . && \
		PYTHONPATH=$(PYTHONPATH) uv run bandit -r -c pyproject.toml .

dead-code: ## Check for dead code using vulture
	@echo "Checking for dead code..."
	uv run vulture

test: ## Run tests
	@echo "Running tests..."
	$(PYTEST_CMD)

test-postgres: ## Run tests against PostgreSQL (set DATABASE_*; see README)
	@echo "Running tests with PYTEST_POSTGRES_USE=1..."
	PYTEST_POSTGRES_USE=1 $(PYTEST_CMD)

test-coverage: ## Run tests with HTML coverage report
	@echo "Running tests with coverage..."
	$(PYTEST_CMD) $(COVERAGE_OPTS)

all: lint test dead-code ## Run all checks (no mutations)
	@echo "All checks completed successfully!"

run: ## Run Django development server locally
	@echo "Running Django development server locally..."
	PYTHONPATH=$(PYTHONPATH) uv run python src/manage.py compilemessages
	PYTHONPATH=$(PYTHONPATH) uv run python src/manage.py migrate
	@if [ -n "$$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$$DJANGO_SUPERUSER_EMAIL" ]; then \
		echo "Ensuring Django superuser exists..."; \
		PYTHONPATH=$(PYTHONPATH) uv run python src/manage.py createsuperuser --noinput || true; \
	else \
		echo "Skipping createsuperuser (set DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL to enable)."; \
	fi
	PYTHONPATH=$(PYTHONPATH) uv run python src/manage.py runserver 0.0.0.0:8000

clean: ## Clean caches and coverage outputs
	@echo "Cleaning cache and temporary files..."
	rm -rf .mypy_cache/ .pytest_cache/ .venv/ build/ dist/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container
	@echo "Running Docker container..."
	docker run --rm \
		-p 8000:8000 \
		--add-host=host.docker.internal:host-gateway \
		$(if $(wildcard env.example),--env-file env.example,) \
		$(if $(wildcard env.docker),--env-file env.docker,) \
		$(if $(wildcard .env),--env-file .env,) \
		--entrypoint sh \
		$(DOCKER_IMAGE) -c '\
			python3 manage.py compilemessages && \
			python3 manage.py migrate && \
			if [ -n "$$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$$DJANGO_SUPERUSER_EMAIL" ]; then \
				echo "Ensuring Django superuser exists..."; \
				python3 manage.py createsuperuser --noinput || true; \
			else \
				echo "Skipping createsuperuser (set DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL to enable)."; \
			fi && \
			exec gunicorn sloths_inventory.wsgi --bind 0.0.0.0:8000 --access-logfile - --error-logfile -'

docker: docker-build docker-run ## Build and run Docker container
	@echo "Docker container built and running!"
