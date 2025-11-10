.PHONY: help install dev-up dev-down test test-watch test-unit test-integration test-e2e \
        lint format typecheck clean migrate migration docker-build

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

install-dev: ## Install dependencies including dev tools
	poetry install --with dev

# Development environment
dev-up: ## Start all development services (PostgreSQL, Redis, Kafka, Temporal, Jaeger)
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started! 🚀"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - Kafka: localhost:9092"
	@echo "  - Temporal: localhost:7233"
	@echo "  - Temporal Web UI: http://localhost:8233"
	@echo "  - Jaeger UI: http://localhost:16686"

dev-down: ## Stop all development services
	docker compose down

dev-restart: ## Restart all development services
	docker compose restart

dev-logs: ## Show logs from all services
	docker compose logs -f

dev-clean: ## Stop services and remove volumes (WARNING: deletes all data!)
	docker compose down -v

# Testing
test: ## Run all tests with coverage
	poetry run pytest -v --cov=wflo --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	poetry run ptw -- -v --cov=wflo

test-unit: ## Run only unit tests
	poetry run pytest tests/unit -v

test-integration: ## Run only integration tests (requires services running)
	poetry run pytest tests/integration -v

test-e2e: ## Run only end-to-end tests (requires services running)
	poetry run pytest tests/e2e -v

test-fast: ## Run tests without coverage (faster)
	poetry run pytest -v --no-cov

# Code quality
lint: ## Run linting with ruff
	poetry run ruff check src/ tests/

lint-fix: ## Run linting and auto-fix issues
	poetry run ruff check --fix src/ tests/

format: ## Format code with black and ruff
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

format-check: ## Check if code is formatted correctly
	poetry run black --check src/ tests/

typecheck: ## Run type checking with mypy
	poetry run mypy src/

check: lint typecheck ## Run all code quality checks

# Database
migrate: ## Run database migrations
	poetry run alembic upgrade head

migration: ## Create a new database migration (usage: make migration msg="description")
	@if [ -z "$(msg)" ]; then \
		echo "Error: msg is required. Usage: make migration msg='description'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(msg)"

migration-history: ## Show migration history
	poetry run alembic history

migration-current: ## Show current migration version
	poetry run alembic current

# Docker
docker-build: ## Build Wflo Docker image
	docker build -t wflo:latest -f Dockerfile .

docker-push: ## Push Docker image to registry
	docker push wflo:latest

# Cleanup
clean: ## Clean up generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true

clean-all: clean dev-clean ## Clean everything including Docker volumes

# Development workflow
dev: dev-up migrate ## Start development environment and run migrations
	@echo "Development environment ready! ✨"

# Run the application (to be implemented)
run: ## Run the Wflo application
	@echo "Application runner not yet implemented"

# Documentation (to be implemented)
docs: ## Build documentation
	@echo "Documentation builder not yet implemented"

docs-serve: ## Serve documentation locally
	@echo "Documentation server not yet implemented"

# Release (to be implemented)
release: ## Create a new release
	@echo "Release process not yet implemented"

# Quick commands for development
.PHONY: dev dev-up dev-down test lint format
