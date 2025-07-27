# Multimodal Contract Extractor - Build System
.PHONY: help install install-dev test lint format security clean build docker-build docker-run setup-dev

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

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
docker-build: ## Build Docker image
	docker build -t multimodal-contract-extractor:latest .

docker-build-dev: ## Build Docker image for development
	docker build --target builder -t multimodal-contract-extractor:dev .

docker-run: ## Run application in Docker
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

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