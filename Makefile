.PHONY: help build up down restart logs clean setup test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - copy env file
	@echo "Setting up environment..."
	@cp -n .env.example .env || true
	@echo "Please edit .env file with your configuration"
	@echo "Run 'make build' to build containers"

build: ## Build all Docker containers
	@echo "Building containers..."
	docker-compose build

up: ## Start all services
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "  - API: http://localhost:8000"
	@echo "  - UI: http://localhost:3000"
	@echo "  - Prefect: http://localhost:4200"
	@echo "  - PostgreSQL: localhost:5432"

down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting services..."
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-ui: ## Show UI logs
	docker-compose logs -f curator-ui

logs-prefect: ## Show Prefect logs
	docker-compose logs -f prefect prefect-worker

logs-db: ## Show database logs
	docker-compose logs -f postgres

clean: ## Remove all containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup complete!"

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

api-shell: ## Open API container shell
	docker-compose exec api /bin/bash

test-api: ## Test API connectivity
	@echo "Testing API..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"

test-prefect: ## Test Prefect connectivity
	@echo "Testing Prefect..."
	@curl -s http://localhost:4200/api/health || echo "Prefect not responding"

migrate: ## Run database migrations (initialize schema)
	@echo "Database schema is auto-initialized on first startup"
	@echo "Check logs with: make logs-db"

status: ## Show status of all services
	docker-compose ps

pull: ## Pull latest images
	docker-compose pull

prune: ## Clean up Docker resources
	@echo "Pruning Docker resources..."
	docker system prune -f
	@echo "Prune complete!"
