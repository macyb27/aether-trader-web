# Aether Trader - Makefile
# Common commands for development and deployment

.PHONY: help install dev test lint docker-up docker-down backend frontend clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Development
# ============================================================

install: ## Install all dependencies
	pip install -r requirements.txt
	npm install

dev: ## Start development servers (backend + frontend)
	@echo "Starting Aether Trader development environment..."
	@make backend &
	@make frontend

backend: ## Start backend server
	uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start frontend dev server
	npm run dev

# ============================================================
# Testing
# ============================================================

test: ## Run all tests
	pytest backend/tests/ -v --cov=backend --cov-report=html

test-fast: ## Run tests without coverage
	pytest backend/tests/ -v

lint: ## Run linters
	ruff check backend/
	mypy backend/

# ============================================================
# Docker
# ============================================================

docker-up: ## Start all services with Docker Compose
	docker compose up -d --build

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

docker-clean: ## Remove all Docker volumes and images
	docker compose down -v --rmi all

# ============================================================
# Database
# ============================================================

db-migrate: ## Run database migrations
	alembic upgrade head

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(msg)"

db-reset: ## Reset database
	alembic downgrade base
	alembic upgrade head

# ============================================================
# Pipeline
# ============================================================

pipeline: ## Run the trading pipeline once
	python -c "from backend.core import TradingPipeline; p = TradingPipeline({}); p.run(['BTC/USDT'], max_iterations=1)"

# ============================================================
# Cleanup
# ============================================================

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf .next out build
