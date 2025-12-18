.PHONY: help install dev test lint format clean docker-up docker-down migrate seed

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Compliance OS - Available Commands"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed"

install-backend: ## Install backend dependencies only
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies only
	cd frontend && npm install

dev: ## Start development servers (backend + frontend in parallel)
	@echo "Starting backend (http://localhost:8000) and frontend (http://localhost:3000)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "✅ All tests passed"

test-backend: ## Run backend tests only
	cd backend && pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm test

test-coverage: ## Run tests with coverage report
	@echo "Running backend tests with coverage..."
	cd backend && pytest --cov=app --cov-report=html --cov-report=term
	@echo "Running frontend tests with coverage..."
	cd frontend && npm test -- --coverage
	@echo "✅ Coverage reports generated"

lint: ## Run linters for both backend and frontend
	@echo "Linting backend..."
	cd backend && flake8 app/
	@echo "Linting frontend..."
	cd frontend && npm run lint
	@echo "✅ Linting completed"

lint-backend: ## Run backend linter (Flake8)
	cd backend && flake8 app/

lint-frontend: ## Run frontend linter (ESLint)
	cd frontend && npm run lint

format: ## Format code for both backend and frontend
	@echo "Formatting backend with Black..."
	cd backend && black app/
	@echo "Formatting frontend with Prettier..."
	cd frontend && npm run format
	@echo "✅ Code formatted"

format-backend: ## Format backend code with Black
	cd backend && black app/

format-frontend: ## Format frontend code with Prettier
	cd frontend && npm run format

type-check: ## Run type checking for both backend and frontend
	@echo "Type checking backend with MyPy..."
	cd backend && mypy app/
	@echo "Type checking frontend with TypeScript..."
	cd frontend && npm run type-check
	@echo "✅ Type checking completed"

type-check-backend: ## Run backend type checking (MyPy)
	cd backend && mypy app/

type-check-frontend: ## Run frontend type checking (TypeScript)
	cd frontend && npm run type-check

clean: ## Clean build artifacts and caches
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaning frontend build..."
	cd frontend && rm -rf .next out node_modules/.cache 2>/dev/null || true
	@echo "✅ Cleaned successfully"

clean-all: clean ## Clean everything including node_modules and venv
	@echo "Removing node_modules..."
	cd frontend && rm -rf node_modules 2>/dev/null || true
	@echo "Removing Python virtual environment..."
	cd backend && rm -rf venv 2>/dev/null || true
	@echo "✅ Deep clean completed"

docker-up: ## Start all Docker containers
	docker-compose up -d
	@echo "✅ Docker containers started"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

docker-down: ## Stop all Docker containers
	docker-compose down
	@echo "✅ Docker containers stopped"

docker-restart: ## Restart all Docker containers
	docker-compose restart
	@echo "✅ Docker containers restarted"

docker-logs: ## Show Docker container logs
	docker-compose logs -f

docker-build: ## Rebuild Docker images
	docker-compose build --no-cache
	@echo "✅ Docker images rebuilt"

docker-clean: ## Remove Docker containers and volumes
	docker-compose down -v
	@echo "✅ Docker containers and volumes removed"

migrate: ## Run database migrations
	cd backend && alembic upgrade head
	@echo "✅ Database migrated to latest version"

migrate-create: ## Create a new migration (Usage: make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate-create MSG='description'"; \
		exit 1; \
	fi
	cd backend && alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration created"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1
	@echo "✅ Rolled back last migration"

migrate-history: ## Show migration history
	cd backend && alembic history

seed: ## Seed database with initial data
	cd backend && python -m app.seeds.run_seed
	@echo "✅ Database seeded successfully"

db-reset: ## Reset database (drop all, migrate, seed)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 3; \
		make migrate; \
		make seed; \
		echo "✅ Database reset completed"; \
	else \
		echo "Cancelled"; \
	fi

celery-worker: ## Start Celery worker
	cd backend && celery -A app.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	cd backend && celery -A app.celery_app beat --loglevel=info

celery-flower: ## Start Celery Flower monitoring UI
	cd backend && celery -A app.celery_app flower
	@echo "Flower UI: http://localhost:5555"

setup: install migrate seed ## Initial project setup (install, migrate, seed)
	@echo "✅ Project setup completed"
	@echo "Run 'make dev' to start development servers"

check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "✅ All checks passed"

ci: ## Run CI checks (used in GitHub Actions)
	make lint
	make type-check
	make test-coverage
	@echo "✅ CI checks passed"

# Local development quick commands
run: dev ## Alias for 'make dev'

build: ## Build production artifacts
	@echo "Building backend..."
	cd backend && pip install -r requirements.txt
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "✅ Production build completed"

deploy-check: ## Verify deployment readiness
	@echo "Checking backend..."
	cd backend && black --check app/ && flake8 app/ && mypy app/
	@echo "Checking frontend..."
	cd frontend && npm run lint && npm run type-check && npm run build
	@echo "Running tests..."
	make test
	@echo "✅ Deploy checks passed"
