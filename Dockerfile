# =============================================================================
# Multi-stage Docker build for Multimodal Contract Extractor
# =============================================================================

# Base image with Python 3.11
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install security updates and basic tools
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# Dependencies stage - Install system dependencies
# =============================================================================
FROM base as dependencies

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    gcc \
    g++ \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    imagemagick \
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure ImageMagick security policy for PDF processing
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml || true

# =============================================================================
# Builder stage - Install Python dependencies
# =============================================================================
FROM dependencies as builder

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies in user directory
RUN pip install --user --no-cache-dir -r requirements.txt

# =============================================================================
# Development stage - For development and testing
# =============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install all dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Create development user
RUN groupadd -r developer && useradd -r -g developer -m developer

# Set up application directory
WORKDIR /workspace

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    nano \
    htop \
    tree \
    jq \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy application code
COPY --chown=developer:developer . .

# Install package in development mode
RUN pip install -e .

# Switch to development user
USER developer

# Set development environment variables
ENV MCE_ENV=development \
    MCE_DEBUG=true \
    MCE_LOG_LEVEL=DEBUG

# Default command for development
CMD ["streamlit", "run", "web_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

# =============================================================================
# Production stage - Optimized for production deployment
# =============================================================================
FROM base as production

# Create non-root user with minimal permissions
RUN groupadd -r appuser && \
    useradd -r -g appuser -m -d /home/appuser -s /bin/bash appuser && \
    mkdir -p /app /app/data /app/logs /app/cache /app/tmp && \
    chown -R appuser:appuser /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    poppler-utils \
    imagemagick \
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Configure ImageMagick security policy
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml || true

# Copy Python packages from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Set up application directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser extract.py batch_extract.py web_app.py ./
COPY --chown=appuser:appuser config.example.yml ./config.yml

# Switch to non-root user
USER appuser

# Set up environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONPATH=/app/src \
    MCE_ENV=production \
    MCE_DATA_DIR=/app/data \
    MCE_LOGS_DIR=/app/logs \
    MCE_CACHE_DIR=/app/cache \
    MCE_TMP_DIR=/app/tmp

# Install the package
RUN pip install --user -e .

# Health check with proper error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import multimodal_contract_extractor.health; multimodal_contract_extractor.health.check_health()" || exit 1

# Expose port
EXPOSE 8501

# Default command
CMD ["streamlit", "run", "web_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

# =============================================================================
# Security-hardened stage - Additional security measures
# =============================================================================
FROM production as security

# Switch back to root for security configurations
USER root

# Additional security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Remove unnecessary packages and files
RUN apt-get autoremove -y && \
    apt-get autoclean && \
    rm -rf /tmp/* /var/tmp/* /root/.cache

# Set strict file permissions
RUN chmod -R o-rwx /home/appuser && \
    chmod -R g-w /home/appuser && \
    chmod 755 /app && \
    chmod -R 644 /app/src && \
    chmod 755 /app/*.py

# Switch back to non-root user
USER appuser

# =============================================================================
# CI/CD stage - For automated testing and deployment
# =============================================================================
FROM development as ci

# Install additional CI tools
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy all files for CI
COPY . /workspace/

# Install package and run tests
RUN pip install -e . && \
    python -m pytest --version

USER developer

# Set CI environment variables
ENV CI=true \
    MCE_ENV=test \
    PYTHONPATH=/workspace/src

# Default command for CI
CMD ["pytest", "--cov=src", "--cov-report=xml", "--cov-report=term"]

# =============================================================================
# Metadata and labels
# =============================================================================

# Common labels for all stages
LABEL org.opencontainers.image.title="Multimodal Contract Extractor"
LABEL org.opencontainers.image.description="Vision-Language-Model pipeline for contract clause extraction"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="Terragon Labs"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/danieleschmidt/multimodal-contract-extractor"
LABEL org.opencontainers.image.documentation="https://github.com/danieleschmidt/multimodal-contract-extractor#readme"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${BUILD_REVISION}"

# Maintenance labels
LABEL maintainer="Terragon Labs <contact@terragon.ai>"
LABEL org.opencontainers.image.authors="Terragon Labs <contact@terragon.ai>"