PYTEST_CMD = PYTHONPATH=src uv run python -m pytest -v

.PHONY: all test help

help: ## Show available make targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

test: ## Run tests
	$(PYTEST_CMD)

all: test ## Run all checks (initially: tests only)
	@echo "All checks completed successfully!"

