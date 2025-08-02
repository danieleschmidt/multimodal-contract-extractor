# Multimodal Contract Extractor - Comprehensive Build System
# =============================================================================

# Variables
PYTHON := python
PIP := pip
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := multimodal-contract-extractor
VERSION := $(shell $(PYTHON) -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")
DOCKER_REGISTRY := ghcr.io/your-org
DOCKER_IMAGE := $(DOCKER_REGISTRY)/$(PROJECT_NAME)

# Environment detection
OS := $(shell uname -s)
ARCH := $(shell uname -m)

# Colors for terminal output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# =============================================================================
# PHONY TARGETS
# =============================================================================

.PHONY: help install install-dev install-gpu install-docs test lint format security \
        clean build docker-build docker-run setup-dev ci-setup ci-test docs-serve \
        env-create metrics quality-gate dev-run dev-extract dev-batch release-patch \
        release-minor migrate health-check performance-test benchmark load-test \
        security-scan vulnerability-scan deps-update deps-audit pre-commit-install \
        pre-commit-run docker-build-dev docker-build-prod docker-push docker-pull \
        docker-clean monitoring-up monitoring-down logs backup restore deployment-test \
        smoke-test integration-test unit-test e2e-test mutation-test coverage-report \
        profile performance-profile memory-profile cpu-profile analyze-code \
        dependencies-graph security-baseline compliance-check audit-logs \
        container-scan image-scan sbom-generate secrets-scan license-check \
        performance-baseline stress-test chaos-test

# =============================================================================
# HELP AND INFORMATION
# =============================================================================

help: ## Show comprehensive help message
	@echo "$(CYAN)Multimodal Contract Extractor - Build System$(RESET)"
	@echo "$(CYAN)===============================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)📦 SETUP & INSTALLATION:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Setup|.*Install' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔍 CODE QUALITY:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Lint|.*Format|.*Security|.*Quality' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🧪 TESTING:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Test|.*Coverage|.*Benchmark' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🐳 DOCKER & DEPLOYMENT:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Docker|.*Deploy|.*Build|.*Container' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🚀 DEVELOPMENT:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Dev|.*Run|.*Start' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)📊 MONITORING & OBSERVABILITY:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Monitor|.*Metrics|.*Health|.*Logs' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔒 SECURITY & COMPLIANCE:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Scan|.*Vulnerability|.*Compliance|.*Audit' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🧹 MAINTENANCE:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*Clean|.*Update|.*Backup|.*Restore' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2}'

info: ## Show project information
	@echo "$(CYAN)Project Information:$(RESET)"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Version: $(VERSION)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  OS: $(OS)"
	@echo "  Architecture: $(ARCH)"
	@echo "  Docker Image: $(DOCKER_IMAGE):$(VERSION)"

# Development setup
setup-dev: ## Setup complete development environment
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
	.venv/bin/pip install -e .
	.venv/bin/pre-commit install
	@echo "✅ Development environment ready! Activate with: source .venv/bin/activate"

install: ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pip install -e .
	pre-commit install

# Code quality
lint: ## Run linting checks
	ruff check .
	bandit -r src -q
	mypy src/ --ignore-missing-imports

format: ## Format code
	black .
	ruff check . --fix

security: ## Run security checks
	bandit -r src/
	safety check
	pip-audit

# Testing
test: ## Run tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "unit"

test-integration: ## Run integration tests only
	pytest -m "integration"

test-cov: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term

test-performance: ## Run performance benchmarks
	pytest -m "performance" --benchmark-only

# Build and package
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m build

# Docker
docker-build: ## Build production Docker image
	$(DOCKER) build --target production -t $(PROJECT_NAME):$(VERSION) -t $(PROJECT_NAME):latest .
	@echo "$(GREEN)✅ Production image built: $(PROJECT_NAME):$(VERSION)$(RESET)"

docker-build-dev: ## Build development Docker image
	$(DOCKER) build --target development -t $(PROJECT_NAME):dev .
	@echo "$(GREEN)✅ Development image built: $(PROJECT_NAME):dev$(RESET)"

docker-build-security: ## Build security-hardened Docker image
	$(DOCKER) build --target security -t $(PROJECT_NAME):security .
	@echo "$(GREEN)✅ Security-hardened image built: $(PROJECT_NAME):security$(RESET)"

docker-build-ci: ## Build CI Docker image
	$(DOCKER) build --target ci -t $(PROJECT_NAME):ci .
	@echo "$(GREEN)✅ CI image built: $(PROJECT_NAME):ci$(RESET)"

docker-build-all: ## Build all Docker images
	@echo "$(BLUE)🔨 Building all Docker images...$(RESET)"
	$(MAKE) docker-build-dev
	$(MAKE) docker-build
	$(MAKE) docker-build-security
	$(MAKE) docker-build-ci
	@echo "$(GREEN)✅ All Docker images built successfully$(RESET)"

docker-run: ## Run application in Docker
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Application started at http://localhost:8501$(RESET)"

docker-run-dev: ## Run development environment
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Development environment started$(RESET)"

docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down 2>/dev/null || true

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-push: ## Push Docker images to registry
	$(DOCKER) tag $(PROJECT_NAME):$(VERSION) $(DOCKER_IMAGE):$(VERSION)
	$(DOCKER) tag $(PROJECT_NAME):latest $(DOCKER_IMAGE):latest
	$(DOCKER) push $(DOCKER_IMAGE):$(VERSION)
	$(DOCKER) push $(DOCKER_IMAGE):latest
	@echo "$(GREEN)✅ Images pushed to $(DOCKER_REGISTRY)$(RESET)"

docker-pull: ## Pull Docker images from registry
	$(DOCKER) pull $(DOCKER_IMAGE):$(VERSION)
	$(DOCKER) pull $(DOCKER_IMAGE):latest

docker-clean: ## Clean Docker artifacts
	$(DOCKER) system prune -f
	$(DOCKER) image prune -f
	@echo "$(GREEN)✅ Docker artifacts cleaned$(RESET)"

docker-scan: ## Scan Docker images for vulnerabilities
	$(DOCKER) scout cves $(PROJECT_NAME):latest
	@echo "$(GREEN)✅ Docker image vulnerability scan completed$(RESET)"

# CI/CD helpers
ci-setup: ## Setup CI environment
	pip install -r requirements.txt -r requirements-dev.txt
	pip install -e .

ci-test: ## Run full CI test suite
	pre-commit run --all-files
	pytest --cov=src --cov-report=xml -v
	bandit -r src/ -f json -o bandit-report.json

# Documentation
docs-serve: ## Serve documentation locally
	@echo "📚 Documentation available in README.md and docs/"
	@echo "🌐 Web app: streamlit run web_app.py"

# Environment
env-create: ## Create .env file from template
	cp config.example.yml config.yml
	@echo "📝 Edit config.yml with your settings"

# Database and migrations (if applicable)
migrate: ## Run database migrations (placeholder)
	@echo "No migrations required for this project"

# Monitoring
metrics: ## Show application metrics
	@echo "🔍 Check health endpoint after starting the app"
	@echo "📊 Metrics available at: http://localhost:8501/health"

# Release
release-patch: ## Create patch release
	@echo "Creating patch release..."
	@echo "Run: git tag v$(shell python -c 'import src.multimodal_contract_extractor; print(src.multimodal_contract_extractor.__version__)')"

release-minor: ## Create minor release
	@echo "Creating minor release - update version in pyproject.toml first"

# Quality gates
quality-gate: lint security test ## Run all quality checks

# Local development
dev-run: ## Run development server
	streamlit run web_app.py

dev-extract: ## Run extraction on sample file
	python extract.py --help

dev-batch: ## Run batch extraction
	python batch_extract.py --help