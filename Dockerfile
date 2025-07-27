# Multi-stage build for production optimization
FROM python:3.11-slim as base

# Build stage
FROM base as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM base as production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set up application directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser extract.py batch_extract.py web_app.py ./

# Install the package
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
RUN pip install --user -e .

# Security: Run as non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import multimodal_contract_extractor; print('OK')" || exit 1

# Default command
CMD ["python", "web_app.py"]

# Expose port
EXPOSE 8501

# Labels for metadata
LABEL org.opencontainers.image.title="Multimodal Contract Extractor"
LABEL org.opencontainers.image.description="Vision-Language-Model pipeline for contract clause extraction"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/your-org/multimodal-contract-extractor"