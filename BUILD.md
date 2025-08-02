# Build & Containerization Guide

This document provides comprehensive instructions for building, containerizing, and deploying the Multimodal Contract Extractor.

## Table of Contents

- [Quick Start](#quick-start)
- [Build System Overview](#build-system-overview)
- [Docker Images](#docker-images)
- [Build Targets](#build-targets)
- [Environment Setup](#environment-setup)
- [CI/CD Integration](#cicd-integration)
- [Security & Compliance](#security--compliance)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Local Development

```bash
# Setup development environment
make setup-dev

# Run development server
make dev-run

# Run tests
make test
```

### Docker Deployment

```bash
# Build and run production container
make docker-build
make docker-run

# View logs
make docker-logs

# Stop containers
make docker-down
```

## Build System Overview

The project uses a comprehensive build system with the following components:

### Build Tools

- **Make**: Primary build orchestration
- **Docker**: Multi-stage containerization
- **Python Build**: Package building with `python -m build`
- **Poetry/Pip**: Dependency management
- **Pre-commit**: Code quality automation

### Build Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source Code   │───▶│   Build Stage   │───▶│  Final Images   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ├─ src/                 ├─ Dependencies         ├─ Production
        ├─ tests/               ├─ Compilation          ├─ Development
        ├─ docs/                ├─ Security Scan        ├─ Security
        └─ config/              └─ Quality Checks       └─ CI/CD
```

## Docker Images

The project provides multiple specialized Docker images built from a single Dockerfile using multi-stage builds:

### 1. Development Image (`development`)

**Purpose**: Local development and debugging
**Target**: `docker build --target development`
**Size**: ~2.5GB (includes dev tools)

**Features**:
- Development dependencies
- Debug tools (vim, nano, htop, tree, jq)
- Non-root developer user
- Hot-reload capabilities
- Streamlit development server

**Usage**:
```bash
make docker-build-dev
docker run -it -p 8501:8501 -v $(pwd):/workspace multimodal-contract-extractor:dev
```

### 2. Production Image (`production`)

**Purpose**: Production deployment
**Target**: `docker build --target production`
**Size**: ~1.2GB (optimized)

**Features**:
- Minimal runtime dependencies
- Non-root appuser
- Optimized Python packages
- Health checks
- Production-ready configuration

**Usage**:
```bash
make docker-build
make docker-run
```

### 3. Security-Hardened Image (`security`)

**Purpose**: High-security environments
**Target**: `docker build --target security`
**Size**: ~1.1GB (minimal)

**Features**:
- Additional security hardening
- Strict file permissions
- Minimal attack surface
- Updated CA certificates
- Security-focused configurations

**Usage**:
```bash
make docker-build-security
docker run -p 8501:8501 multimodal-contract-extractor:security
```

### 4. CI/CD Image (`ci`)

**Purpose**: Automated testing and deployment
**Target**: `docker build --target ci`
**Size**: ~2.8GB (includes test tools)

**Features**:
- All test dependencies
- CI/CD tools (git, ssh)
- Coverage reporting
- Test execution environment

**Usage**:
```bash
make docker-build-ci
docker run multimodal-contract-extractor:ci pytest --cov=src
```

## Build Targets

### Core Build Commands

```bash
# Development setup
make setup-dev              # Complete development environment setup
make install                # Install production dependencies
make install-dev            # Install development dependencies

# Code quality
make lint                   # Run linting checks (ruff, bandit, mypy)
make format                 # Format code (black, ruff --fix)
make security               # Security scans (bandit, safety, pip-audit)
make quality-gate           # Run all quality checks

# Testing
make test                   # Run all tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-cov               # Tests with coverage report
make test-performance       # Performance benchmarks

# Build and package
make clean                  # Clean build artifacts
make build                  # Build Python package

# Docker operations
make docker-build-all       # Build all Docker images
make docker-build           # Production image
make docker-build-dev       # Development image
make docker-build-security  # Security-hardened image
make docker-build-ci        # CI/CD image
make docker-run             # Run production containers
make docker-run-dev         # Run development environment
make docker-push            # Push to registry
make docker-clean           # Clean Docker artifacts
make docker-scan            # Vulnerability scan

# CI/CD
make ci-setup               # Setup CI environment
make ci-test                # Full CI test suite
```

### Advanced Build Options

```bash
# Build with specific version
VERSION=1.2.3 make docker-build

# Build for different architecture
docker buildx build --platform linux/amd64,linux/arm64 --target production .

# Build with build arguments
docker build --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
             --build-arg BUILD_REVISION=$(git rev-parse HEAD) \
             --target production .
```

## Environment Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+
- Make (GNU Make 4.0+)
- Git 2.30+

### Development Environment

1. **Clone Repository**:
```bash
git clone https://github.com/danieleschmidt/multimodal-contract-extractor.git
cd multimodal-contract-extractor
```

2. **Setup Development Environment**:
```bash
make setup-dev
source .venv/bin/activate
```

3. **Configure Application**:
```bash
make env-create
# Edit config.yml with your settings
```

### Production Environment

1. **Environment Variables**:
```bash
# Required
export MCE_ENV=production
export MCE_DATA_DIR=/app/data
export MCE_LOGS_DIR=/app/logs

# Optional
export MCE_SECURITY_MAX_FILE_SIZE_MB=100
export MCE_HEALTH_CHECK_TIMEOUT_SECONDS=5
```

2. **Volume Mounts**:
```bash
# Data persistence
docker run -v /host/data:/app/data \
           -v /host/logs:/app/logs \
           -v /host/config.yml:/app/config.yml:ro \
           multimodal-contract-extractor:latest
```

## CI/CD Integration

### GitHub Actions

The build system integrates with GitHub Actions for automated CI/CD:

```yaml
# Example workflow snippet
- name: Setup build environment
  run: make ci-setup

- name: Run quality checks
  run: make quality-gate

- name: Build Docker images
  run: make docker-build-all

- name: Run tests
  run: make ci-test

- name: Security scan
  run: make docker-scan
```

### Build Matrix

Tests run across multiple environments:

| Environment | Python | OS | Docker |
|-------------|--------|----|--------|
| Development | 3.11 | Ubuntu 22.04 | Latest |
| Staging | 3.11 | Ubuntu 22.04 | Latest |
| Production | 3.11 | Ubuntu 22.04 | Latest |

### Deployment Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │───▶│   Build     │───▶│    Test     │───▶│   Deploy    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ├─ Lint             ├─ Compile          ├─ Unit             ├─ Staging
       ├─ Security         ├─ Package          ├─ Integration      ├─ Production
       └─ Format           └─ Container        └─ E2E              └─ Monitoring
```

## Security & Compliance

### Security Features

1. **Container Security**:
   - Non-root user execution
   - Minimal base images
   - Security updates applied
   - Vulnerability scanning
   - Read-only root filesystem

2. **Build Security**:
   - Dependency vulnerability scanning
   - Secret detection
   - Code security analysis
   - License compliance checking

3. **Runtime Security**:
   - Health checks
   - Resource limits
   - Network isolation
   - File system restrictions

### Security Scanning

```bash
# Container vulnerability scan
make docker-scan

# Dependency audit
make security

# Code security analysis
bandit -r src/

# License compliance
pip-licenses --format=json
```

### Compliance Standards

- **GDPR**: Data processing compliance
- **SOC 2**: Security controls
- **ISO 27001**: Information security
- **NIST**: Cybersecurity framework

## Performance Optimization

### Build Performance

1. **Docker Layer Caching**:
   - Dependencies cached separately
   - Multi-stage builds minimize rebuilds
   - BuildKit enabled for parallel builds

2. **Build Optimization**:
   - Parallel test execution
   - Incremental builds
   - Artifact caching

### Runtime Performance

1. **Production Optimizations**:
   - Minimal runtime dependencies
   - Optimized Python settings
   - Resource-efficient containers

2. **Monitoring**:
   - Health checks
   - Performance metrics
   - Resource monitoring

### Benchmarking

```bash
# Performance testing
make test-performance

# Build time measurement
time make docker-build

# Image size analysis
docker images multimodal-contract-extractor
```

## Troubleshooting

### Common Build Issues

1. **Docker Build Fails**:
```bash
# Clear Docker cache
make docker-clean

# Rebuild without cache
docker build --no-cache --target production .

# Check Docker disk space
docker system df
```

2. **Dependency Conflicts**:
```bash
# Clean Python cache
make clean

# Recreate virtual environment
rm -rf .venv
make setup-dev

# Update dependencies
pip install --upgrade pip setuptools wheel
```

3. **Test Failures**:
```bash
# Run specific test
pytest tests/test_specific.py -v

# Debug mode
pytest --pdb

# Check test environment
pytest --collect-only
```

### Performance Issues

1. **Slow Builds**:
   - Enable BuildKit: `export DOCKER_BUILDKIT=1`
   - Use build cache: `docker build --cache-from`
   - Parallel builds: `make -j$(nproc)`

2. **Large Images**:
   - Use multi-stage builds (already implemented)
   - Minimize dependencies
   - Use .dockerignore (already configured)

### Security Issues

1. **Vulnerability Warnings**:
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Security audit
make security

# Container scan
make docker-scan
```

2. **Permission Issues**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Docker permission
sudo usermod -aG docker $USER
```

### Getting Help

1. **Build Logs**: Check detailed build output
2. **Docker Logs**: `docker logs <container_id>`
3. **System Status**: `make info`
4. **Community**: Open GitHub issue with build logs

For additional support, consult the main project documentation or open an issue in the repository.