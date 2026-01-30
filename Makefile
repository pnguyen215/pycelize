# =============================================================================
# Pycelize Makefile
# =============================================================================
# This Makefile provides convenient commands for setting up, running, testing,
# and managing the Pycelize Flask application.
#
# Usage:
#   make help          - Show available commands
#   make setup         - Create virtual environment
#   make install       - Install dependencies
#   make run           - Run the application
#   make test          - Run tests
#   make clean         - Clean generated files
# =============================================================================

.PHONY: help setup install run test lint clean format dev prod test-cov \
        setup-dirs clean-all docker-build docker-run freeze

# =============================================================================
# Configuration
# =============================================================================

# Docker configuration
DOCKER_IMAGE = pycelize
DOCKER_TAG = latest
DOCKER_CONTAINER = pycelize-app

# Virtual environment directory
VENV_DIR = venv

# Python interpreter
PYTHON = python3

# Virtual environment Python and pip
VENV_PYTHON = $(VENV_DIR)/bin/python3
VENV_PIP = $(VENV_DIR)/bin/pip

# Application settings
APP_MODULE = run.py
HOST = 0.0.0.0
PORT = 5050

# Project directories
SRC_DIR = app
TEST_DIR = tests
CONFIG_DIR = configs

# Colors for terminal output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m

# =============================================================================
# Help
# =============================================================================

help:
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║           Pycelize - Available Commands                      ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make setup       - Create Python virtual environment"
	@echo "  make install     - Create venv and install all dependencies"
	@echo "  make install-dev - Install with development dependencies"
	@echo "  make freeze      - Freeze current dependencies to requirements.txt"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make run         - Run the Flask application"
	@echo "  make dev         - Run in development mode with auto-reload"
	@echo "  make prod        - Run with production settings"
	@echo ""
	@echo "$(GREEN)Testing & Quality:$(NC)"
	@echo "  make test        - Run unit tests"
	@echo "  make test-cov    - Run tests with coverage report"
	@echo "  make lint        - Run code linting (flake8)"
	@echo "  make format      - Format code with black and isort"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make clean       - Remove generated files and caches"
	@echo "  make clean-all   - Remove all generated files including venv"
	@echo "  make setup-dirs  - Create required directories"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make docker-logs  - View Docker container logs"
	@echo "  make docker-shell - Access shell in Docker container"
	@echo "  make docker-restart - Restart Docker container"
	@echo "  make docker-compose-up   - Start services with Docker Compose"
	@echo "  make docker-compose-down - Stop services with Docker Compose"
	@echo "  make docker-compose-logs - View logs from Docker Compose"
	@echo "  make docker-compose-rebuild - Rebuild and start Docker Compose services"
	@echo "  make docker-clean  - Clean Docker resources"
	@echo "  make docker-prune  - Prune unused Docker resources"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

setup:
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)✓ Virtual environment created in $(VENV_DIR)$(NC)"

install: setup setup-dirs
	@echo "$(CYAN)Upgrading pip and setuptools...$(NC)"
	$(VENV_PIP) install -U pip setuptools wheel
	@echo "$(CYAN)Installing dependencies...$(NC)"
	$(VENV_PIP) install -r requirements.txt
	@echo "$(GREEN)✓ All dependencies installed successfully$(NC)"

install-dev: install
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	$(VENV_PIP) install pytest pytest-cov black flake8 isort
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

freeze:
	@echo "$(CYAN)Freezing dependencies...$(NC)"
	$(VENV_PIP) freeze > requirements.txt
	@echo "$(GREEN)✓ Dependencies frozen to requirements.txt$(NC)"

# =============================================================================
# Running the Application
# =============================================================================

run: setup-dirs
	@echo "$(CYAN)Starting Pycelize...$(NC)"
	$(VENV_PYTHON) $(APP_MODULE)

dev: setup-dirs
	@echo "$(CYAN)Starting Pycelize in development mode...$(NC)"
	FLASK_ENV=development FLASK_DEBUG=1 $(VENV_PYTHON) $(APP_MODULE)

prod: setup-dirs
	@echo "$(CYAN)Starting Pycelize in production mode...$(NC)"
	FLASK_ENV=production FLASK_DEBUG=0 $(VENV_PYTHON) $(APP_MODULE)

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "$(CYAN)Running tests...$(NC)"
	$(VENV_PYTHON) -m pytest $(TEST_DIR) -v
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	$(VENV_PYTHON) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "$(CYAN)Running linter...$(NC)"
	$(VENV_PYTHON) -m flake8 $(SRC_DIR) --max-line-length=100 --ignore=E501,W503
	@echo "$(GREEN)✓ Linting completed$(NC)"

format:
	@echo "$(CYAN)Formatting code...$(NC)"
	$(VENV_PYTHON) -m black $(SRC_DIR) $(TEST_DIR) --line-length=100
	$(VENV_PYTHON) -m isort $(SRC_DIR) $(TEST_DIR) --profile=black
	@echo "$(GREEN)✓ Code formatted$(NC)"

# =============================================================================
# Maintenance
# =============================================================================

setup-dirs:
	@mkdir -p uploads outputs logs

clean:
	@echo "$(CYAN)Cleaning generated files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf uploads/* outputs/* 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned successfully$(NC)"

clean-all: clean
	@echo "$(CYAN)Removing all generated files including venv...$(NC)"
	rm -rf $(VENV_DIR) 2>/dev/null || true
	rm -rf logs/* 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "$(GREEN)✓ All generated files removed$(NC)"

# =============================================================================
# Docker
# =============================================================================

docker-build:
	@echo "$(CYAN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✓ Docker image '$(DOCKER_IMAGE):$(DOCKER_TAG)' built$(NC)"

docker-build-no-cache:
	@echo "$(CYAN)Building Docker image (no cache)...$(NC)"
	docker build --no-cache -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run:
	@echo "$(CYAN)Running Docker container...$(NC)"
	docker run -d \
		--name $(DOCKER_CONTAINER) \
		-p $(PORT):5050 \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/outputs:/app/outputs \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/configs:/app/configs:ro \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✓ Container '$(DOCKER_CONTAINER)' started$(NC)"
	@echo "$(CYAN)Application running at http://localhost:$(PORT)$(NC)"

docker-stop:
	@echo "$(CYAN)Stopping Docker container...$(NC)"
	docker stop $(DOCKER_CONTAINER) 2>/dev/null || true
	docker rm $(DOCKER_CONTAINER) 2>/dev/null || true
	@echo "$(GREEN)✓ Container stopped$(NC)"

docker-logs:
	@docker logs -f $(DOCKER_CONTAINER)

docker-shell:
	@docker exec -it $(DOCKER_CONTAINER) /bin/bash

docker-restart: docker-stop docker-run

docker-compose-up:
	@echo "$(CYAN)Starting with Docker Compose...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo "$(CYAN)Application running at http://localhost:5050$(NC)"

docker-compose-down:
	@echo "$(CYAN)Stopping Docker Compose...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-compose-logs:
	@docker-compose logs -f

docker-compose-rebuild:
	@echo "$(CYAN)Rebuilding and starting containers...$(NC)"
	docker-compose up -d --build
	@echo "$(GREEN)✓ Containers rebuilt and started$(NC)"

docker-clean:
	@echo "$(CYAN)Cleaning Docker resources...$(NC)"
	docker stop $(DOCKER_CONTAINER) 2>/dev/null || true
	docker rm $(DOCKER_CONTAINER) 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

docker-prune:
	@echo "$(CYAN)Pruning unused Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Docker resources pruned$(NC)"

# =============================================================================
# Shortcuts
# =============================================================================

# Shortcut: Install and run
start: install run

# Shortcut: Clean, install, and run
fresh: clean-all install run

# Shortcut: Format, lint, and test
check: format lint test