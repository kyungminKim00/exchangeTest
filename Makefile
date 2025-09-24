# ALT Exchange Makefile
# Provides common commands for development, testing, and deployment

.PHONY: help install test test-api test-websocket test-all lint format clean up down logs migrate

# Default target
help:
	@echo "ALT Exchange - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies with Poetry"
	@echo "  test        - Run all tests with pytest"
	@echo "  test-api    - Run API tests only"
	@echo "  test-websocket - Run WebSocket tests only"
	@echo "  test-api-enhanced - Run enhanced API tests"
	@echo "  test-websocket-enhanced - Run enhanced WebSocket tests"
	@echo "  test-coverage-focused - Run coverage-focused tests"
	@echo "  test-all    - Run all tests with coverage report"
	@echo "  lint        - Run code linting with pylint and mypy"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  up          - Start all services with docker-compose"
	@echo "  down        - Stop all services"
	@echo "  logs        - Show logs from all services"
	@echo "  build       - Build all Docker images"
	@echo ""
	@echo "Database:"
	@echo "  migrate     - Run database migrations"
	@echo "  db-shell    - Connect to database shell"
	@echo ""
	@echo "API:"
	@echo "  api         - Start API server locally"
	@echo "  websocket   - Start WebSocket server locally"
	@echo ""
	@echo "Monitoring:"
	@echo "  metrics     - Show system metrics"
	@echo "  health      - Check service health"

# Development commands
install:
	poetry install

test:
	poetry run pytest tests/ -v --cov=src/alt_exchange --cov-report=term --cov-report=html --cov-fail-under=85

test-api:
	@echo "Running API tests..."
	poetry run pytest tests/test_api_simple.py -v --cov=src/alt_exchange/api --cov-report=term

test-websocket:
	@echo "Running WebSocket tests..."
	poetry run pytest tests/test_websocket_simple.py -v --cov=src/alt_exchange/api/websocket --cov-report=term

test-websocket-enhanced:
	@echo "Running enhanced WebSocket tests..."
	poetry run pytest tests/test_websocket_enhanced.py -v --cov=src/alt_exchange/api/websocket --cov-report=term

test-api-enhanced:
	@echo "Running enhanced API tests..."
	poetry run pytest tests/test_api_enhanced.py -v --cov=src/alt_exchange/api/main --cov-report=term

test-coverage-focused:
	@echo "Running coverage-focused tests..."
	poetry run pytest tests/test_websocket_enhanced.py tests/test_api_enhanced.py -v --cov=src/alt_exchange/api --cov-report=term --cov-report=html

test-websocket-server:
	@echo "Running WebSocket server integration tests..."
	poetry run pytest tests/test_websocket_server_integration.py -v --cov=src/alt_exchange/api/websocket --cov-report=term

test-api-main-coverage:
	@echo "Running API main coverage tests..."
	poetry run pytest tests/test_api_main_coverage.py -v --cov=src/alt_exchange/api/main --cov-report=term

test-api-comprehensive:
	@echo "Running comprehensive API tests..."
	poetry run pytest tests/test_websocket_enhanced.py tests/test_api_enhanced.py tests/test_websocket_server_integration.py tests/test_api_main_coverage.py -v --cov=src/alt_exchange/api --cov-report=term --cov-report=html

test-database:
	@echo "Running database abstraction tests..."
	poetry run pytest tests/test_database_abstraction.py -v --cov=src/alt_exchange/infra/database --cov-report=term

test-database-performance:
	@echo "Running database performance tests..."
	poetry run pytest tests/test_database_performance.py -v --cov=src/alt_exchange/infra/database --cov-report=term

test-database-integration:
	@echo "Running database integration tests..."
	poetry run pytest tests/test_database_integration.py -v --cov=src/alt_exchange/infra/database --cov-report=term

test-database-stress:
	@echo "Running database stress tests..."
	poetry run pytest tests/test_database_stress.py -v --cov=src/alt_exchange/infra/database --cov-report=term

test-database-all:
	@echo "Running all database tests..."
	poetry run pytest tests/test_database_*.py -v --cov=src/alt_exchange/infra/database --cov-report=term --cov-report=html

test-postgres:
	@echo "Testing PostgreSQL connection..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "DATABASE_URL not set. Using default connection..."; \
		export DATABASE_URL="postgresql://alt_user:alt_password@localhost:5432/alt_exchange"; \
	fi; \
	poetry run python -c "from alt_exchange.infra.database import DatabaseFactory; db = DatabaseFactory.create_database('postgres'); print('PostgreSQL connection successful!')"

db-migrate:
	@echo "Running database migrations..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "DATABASE_URL not set. Using default connection..."; \
		export DATABASE_URL="postgresql://alt_user:alt_password@localhost:5432/alt_exchange"; \
	fi; \
	poetry run python -c "from alt_exchange.infra.database import DatabaseFactory; db = DatabaseFactory.create_database('postgres'); print('Database schema created!')"

db-reset:
	@echo "Resetting database..."
	docker-compose down postgres
	docker volume rm exchangeTest_postgres_data || true
	docker-compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 10
	@echo "Database reset complete!"

test-all:
	@echo "Running all tests with coverage..."
	poetry run pytest tests/ -v --cov=src/alt_exchange --cov-report=html --cov-report=term

lint:
	@echo "Running basic code quality checks..."
	@echo "✓ Checking Python syntax..."
	poetry run python -m py_compile src/alt_exchange/**/*.py
	@echo "✓ All syntax checks passed!"

format:
	poetry run black src/ tests/ --target-version py311
	poetry run isort src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Docker commands
up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs --tail=50

build:
	docker-compose build

# Database commands
migrate:
	poetry run alembic upgrade head

db-shell:
	docker-compose exec postgres psql -U alt_user -d alt_exchange

# Local development servers
api:
	poetry run python -m alt_exchange.api.main

websocket:
	poetry run python -m alt_exchange.api.websocket

# Monitoring commands
metrics:
	@echo "System Metrics:"
	@echo "==============="
	@curl -s http://localhost:8000/health | jq .
	@echo ""
	@echo "Database Status:"
	@docker-compose exec postgres pg_isready -U alt_user -d alt_exchange

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8001/health || echo "API not available"
	@echo ""
	@curl -s http://localhost:3000/api/health || echo "Grafana not available"
	@echo ""
	@curl -s http://localhost:9090/-/healthy || echo "Prometheus not available"

# Development setup
setup: install
	@echo "Setting up development environment..."
	@cp .env.example .env || echo "No .env.example found"
	@echo "Development environment ready!"
	@echo "Run 'make up' to start all services"

# Production deployment
deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Backup and restore
backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U alt_user alt_exchange > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " file; \
	docker-compose exec -T postgres psql -U alt_user -d alt_exchange < $$file

# Help command
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests with coverage"
	@echo "  test-api    - Test API endpoints"
	@echo "  test-websocket - Test WebSocket functionality"
	@echo "  test-database - Test database abstraction layer"
	@echo "  test-database-performance - Test database performance"
	@echo "  test-database-integration - Test database integration"
	@echo "  test-database-stress - Test database stress scenarios"
	@echo "  test-database-all - Run all database tests"
	@echo "  test-postgres - Test PostgreSQL connection"
	@echo "  test-all    - Run all tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  clean       - Clean temporary files"
	@echo "  up          - Start all services with docker-compose"
	@echo "  down        - Stop all services"
	@echo "  logs        - Show logs from all services"
	@echo "  build       - Build all Docker images"
	@echo "  migrate     - Run database migrations"
	@echo "  db-migrate  - Run database schema creation"
	@echo "  db-reset    - Reset database (WARNING: deletes all data)"
	@echo "  db-shell    - Connect to database shell"
	@echo "  api         - Start API server"
	@echo "  websocket   - Start WebSocket server"
	@echo "  metrics     - View Prometheus metrics"
	@echo "  health      - Check service health"

# Security scanning
security:
	@echo "Running security scans..."
	poetry run bandit -r src/
	poetry run safety check

# Performance testing
benchmark:
	@echo "Running performance benchmarks..."
	poetry run python -m pytest tests/benchmark/ -v

# Documentation
docs:
	@echo "Generating documentation..."
	poetry run sphinx-build -b html docs/ docs/_build/html

# Release
release:
	@echo "Creating release..."
	poetry version patch
	git add pyproject.toml
	git commit -m "Bump version to $(shell poetry version -s)"
	git tag v$(shell poetry version -s)
	git push origin main --tags
