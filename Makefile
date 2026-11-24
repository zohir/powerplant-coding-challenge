IMAGE_NAME ?= powerplant-api
APP_HOST ?= 0.0.0.0
PORT ?= 8888
LOG_LEVEL ?= INFO
CONTAINER_CLI ?= $(shell command -v docker || command -v podman || echo /opt/podman/bin/podman)

.DEFAULT_GOAL := help

.PHONY: help install lint test check run clean docker-build docker-run docker-smoke

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install: ## Create/sync virtual environment with dev dependencies
	uv sync --extra dev

lint: ## Run Ruff linter
	uv run ruff check .

test: ## Run pytest suite
	APP_HOST=$(APP_HOST) APP_PORT=$(PORT) LOG_LEVEL=$(LOG_LEVEL) uv run pytest

check: lint test ## Run linter and test suite

run: ## Start FastAPI server locally on port 8888
	APP_HOST=$(APP_HOST) APP_PORT=$(PORT) LOG_LEVEL=$(LOG_LEVEL) uv run uvicorn powerplant.main:app --host $(APP_HOST) --port $(PORT)

clean: ## Remove local Python and test caches
	rm -rf .pytest_cache .ruff_cache && find src tests -type d -name __pycache__ -exec rm -rf {} +

docker-build: ## Build OCI container image (tar-streamed for macOS Podman safety)
	@if echo "$(CONTAINER_CLI)" | grep -q "podman"; then \
		tar --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.ruff_cache' -cf - . | $(CONTAINER_CLI) machine ssh "podman build --format docker -t $(IMAGE_NAME) -"; \
	else \
		tar --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.ruff_cache' -cf - . | $(CONTAINER_CLI) build -t $(IMAGE_NAME) -; \
	fi

docker-run: ## Run container exposing port 8888
	$(CONTAINER_CLI) run --rm -p $(PORT):8888 $(IMAGE_NAME)

docker-smoke: ## Smoke-test /health endpoint on running container
	@printf '%s\n' \
		'import sys, urllib.request' \
		'url = f"http://127.0.0.1:{sys.argv[1]}/health"' \
		'try:' \
		'    print(urllib.request.urlopen(url, timeout=3).read().decode())' \
		'except OSError as exc:' \
		'    sys.stderr.write(f"ERROR: Smoke check failed for {url}: {exc}. Start the service with make docker-run or make run.\n")' \
		'    sys.exit(1)' \
	| python3 - $(PORT)
