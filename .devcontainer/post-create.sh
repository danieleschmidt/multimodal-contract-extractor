#!/bin/bash

# Post-create script for Multimodal Contract Extractor development environment
# This script runs after the container is created to set up the development environment

set -e

echo "🚀 Setting up Multimodal Contract Extractor development environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    redis-tools \
    curl \
    wget \
    jq \
    htop \
    tree \
    fd-find \
    ripgrep

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install the package in development mode
echo "📦 Installing package in development mode..."
pip install -e .

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p \
    data/contracts \
    data/processed \
    data/cache \
    logs \
    temp \
    exports \
    backups

# Set up environment variables
echo "🔧 Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from example"
fi

# Configure git if not already configured
echo "🔧 Configuring git..."
if [ -z "$(git config --global user.name)" ]; then
    git config --global user.name "Developer"
    git config --global user.email "developer@terragon.ai"
    echo "✅ Configured default git user"
fi

# Test the installation
echo "🧪 Testing installation..."
python -c "
import sys
sys.path.insert(0, 'src')
import multimodal_contract_extractor
print(f'✅ Package version: {multimodal_contract_extractor.__version__}')
"

echo "✅ Development environment setup complete!"
echo ""
echo "🎉 Welcome to Multimodal Contract Extractor Development!"
echo ""
echo "Quick start commands:"
echo "  source .venv/bin/activate  - Activate Python virtual environment"
echo "  pytest tests/             - Run test suite"
echo "  streamlit run web_app.py   - Start Streamlit app"
echo "  ruff check .               - Run code linting"
echo "  black .                    - Format code"
echo ""