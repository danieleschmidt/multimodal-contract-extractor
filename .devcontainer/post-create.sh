#!/bin/bash

# Multimodal Contract Extractor - Development Container Setup
# This script runs after the development container is created

set -e

echo "🚀 Setting up Multimodal Contract Extractor development environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update

# Install system dependencies for OCR and document processing
echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    imagemagick \
    ghostscript \
    curl \
    wget \
    htop \
    tree \
    jq

# Clean up apt cache
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

# Create workspace directories
echo "📁 Creating workspace directories..."
mkdir -p /workspaces/multimodal-contract-extractor/{data,logs,tmp,cache}

# Set up Python environment
echo "🐍 Setting up Python environment..."

# Upgrade pip and install build tools
python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Install the package in development mode
echo "📦 Installing package in development mode..."
pip install -e .

# Set up pre-commit hooks
echo "🔒 Setting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  No .pre-commit-config.yaml found, skipping pre-commit setup"
fi

# Set up Git configuration
echo "🔧 Configuring Git settings..."
git config --global core.autocrlf input
git config --global init.defaultBranch main
git config --global pull.rebase false

# Create useful aliases
echo "⚡ Setting up development aliases..."
cat >> /home/vscode/.bashrc << 'EOF'

# Multimodal Contract Extractor Development Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Project specific aliases
alias mce-test='pytest -v'
alias mce-test-cov='pytest --cov=src --cov-report=html --cov-report=term'
alias mce-lint='ruff check . && mypy src/'
alias mce-format='black . && isort .'
alias mce-clean='find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true'
alias mce-web='streamlit run web_app.py'
alias mce-extract='python extract.py'
alias mce-batch='python batch_extract.py'

# Docker aliases
alias dc='docker-compose'
alias dcu='docker-compose up'
alias dcd='docker-compose down'
alias dcb='docker-compose build'
alias dcl='docker-compose logs'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gco='git checkout'
alias gb='git branch'
alias gd='git diff'
alias glog='git log --oneline --graph --decorate'

EOF

# Set up zsh aliases if zsh is available
if command -v zsh &> /dev/null; then
    cat >> /home/vscode/.zshrc << 'EOF'

# Multimodal Contract Extractor Development Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Project specific aliases
alias mce-test='pytest -v'
alias mce-test-cov='pytest --cov=src --cov-report=html --cov-report=term'
alias mce-lint='ruff check . && mypy src/'
alias mce-format='black . && isort .'
alias mce-clean='find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true'
alias mce-web='streamlit run web_app.py'
alias mce-extract='python extract.py'
alias mce-batch='python batch_extract.py'

# Docker aliases
alias dc='docker-compose'
alias dcu='docker-compose up'
alias dcd='docker-compose down'
alias dcb='docker-compose build'
alias dcl='docker-compose logs'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gco='git checkout'
alias gb='git branch'
alias gd='git diff'
alias glog='git log --oneline --graph --decorate'

EOF
fi

# Create development configuration files
echo "⚙️  Creating development configuration..."

# Create a local development config
if [ ! -f "config.dev.yml" ]; then
    cat > config.dev.yml << 'EOF'
# Development configuration for Multimodal Contract Extractor
ocr:
  cache_size_limit: 50  # Smaller cache for development
  context_window_size: 100

extraction:
  base_confidence_score: 0.7  # Lower threshold for development
  length_bonus_divisor: 1000
  max_confidence_cap: 0.95
  file_size_threshold_mb: 5  # Smaller files for development
  streaming_chunk_size: 3

security:
  max_file_size_mb: 50  # Smaller limit for development
  request_id_length_limit: 64

health:
  check_timeout_seconds: 3  # Faster timeout for development

document:
  default_streaming_chunk_size: 5

# Development-specific settings
development:
  debug_mode: true
  verbose_logging: true
  mock_external_services: false
EOF
    echo "✅ Created config.dev.yml"
fi

# Set up environment variables for development
echo "🌍 Setting up environment variables..."
if [ ! -f ".env.dev" ]; then
    cat > .env.dev << 'EOF'
# Development environment variables for Multimodal Contract Extractor

# Application settings
MCE_ENV=development
MCE_DEBUG=true
MCE_LOG_LEVEL=DEBUG

# OCR settings
MCE_OCR_CACHE_SIZE_LIMIT=50
MCE_OCR_CONTEXT_WINDOW_SIZE=100

# Extraction settings
MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.7
MCE_EXTRACTION_MAX_CONFIDENCE_CAP=0.95

# Security settings
MCE_SECURITY_MAX_FILE_SIZE_MB=50

# Health check settings
MCE_HEALTH_CHECK_TIMEOUT_SECONDS=3

# Streamlit settings
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_SERVER_PORT=8501

# Development paths
MCE_DATA_DIR=/workspaces/multimodal-contract-extractor/data
MCE_LOGS_DIR=/workspaces/multimodal-contract-extractor/logs
MCE_CACHE_DIR=/workspaces/multimodal-contract-extractor/cache
MCE_TMP_DIR=/workspaces/multimodal-contract-extractor/tmp
EOF
    echo "✅ Created .env.dev"
fi

# Create sample test data directory
echo "📊 Setting up test data structure..."
mkdir -p data/{samples,test,output}
mkdir -p logs/{app,test,performance}
mkdir -p cache/{ocr,models,preprocessed}
mkdir -p tmp/{uploads,processing,exports}

# Create a README for the data directory
cat > data/README.md << 'EOF'
# Test Data Directory

This directory contains test data for the Multimodal Contract Extractor.

## Structure

- `samples/` - Sample contract documents for testing
- `test/` - Test fixtures and mock data
- `output/` - Output from test runs and development

## Usage

Place your test PDF and image files in the `samples/` directory to test the application.
The `test/` directory contains automated test fixtures.
The `output/` directory is used for development outputs and can be cleaned regularly.

## File Formats Supported

- PDF documents (native and scanned)
- Images: PNG, JPEG, TIFF, BMP
- Multi-page documents

## Security Note

Do not commit real contract documents to this repository. Use only synthetic or anonymized test data.
EOF

# Set up development database/cache if needed
echo "💾 Setting up development cache structure..."
mkdir -p cache/{ocr_results,document_metadata,processing_stats}

# Create development utilities
echo "🛠️  Creating development utilities..."
cat > scripts/dev-setup.sh << 'EOF'
#!/bin/bash
# Development setup utilities

echo "🔄 Refreshing development environment..."

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean test artifacts
rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

# Reinstall in development mode
pip install -e .

echo "✅ Development environment refreshed!"
EOF

mkdir -p scripts
chmod +x scripts/dev-setup.sh

# Set permissions
echo "🔐 Setting proper permissions..."
sudo chown -R vscode:vscode /workspaces/multimodal-contract-extractor/
chmod -R 755 /workspaces/multimodal-contract-extractor/data
chmod -R 755 /workspaces/multimodal-contract-extractor/logs
chmod -R 755 /workspaces/multimodal-contract-extractor/cache
chmod -R 755 /workspaces/multimodal-contract-extractor/tmp

# Verify installation
echo "🔍 Verifying installation..."
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Test key dependencies
echo "🧪 Testing key dependencies..."
python -c "import PIL; print(f'✅ Pillow version: {PIL.__version__}')" || echo "❌ Pillow not installed"
python -c "import pytesseract; print('✅ PyTesseract available')" || echo "❌ PyTesseract not available"
python -c "import streamlit; print(f'✅ Streamlit version: {streamlit.__version__}')" || echo "❌ Streamlit not installed"

# Test tesseract
tesseract --version && echo "✅ Tesseract OCR available" || echo "❌ Tesseract OCR not available"

# Test poppler utilities
pdftoppm -h > /dev/null 2>&1 && echo "✅ Poppler utilities available" || echo "❌ Poppler utilities not available"

# Display helpful information
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📚 Useful commands:"
echo "  mce-test          - Run tests"
echo "  mce-test-cov      - Run tests with coverage"
echo "  mce-lint          - Run linting"
echo "  mce-format        - Format code"
echo "  mce-web           - Start web interface"
echo "  mce-extract       - Run CLI extraction tool"
echo "  scripts/dev-setup.sh - Refresh development environment"
echo ""
echo "🔧 Configuration files:"
echo "  config.dev.yml    - Development configuration"
echo "  .env.dev          - Development environment variables"
echo ""
echo "📁 Development directories:"
echo "  data/samples/     - Place test documents here"
echo "  logs/             - Application logs"
echo "  cache/            - Cached processing results"
echo "  tmp/              - Temporary files"
echo ""
echo "🚀 Start developing with:"
echo "  streamlit run web_app.py"
echo "  python extract.py --help"
echo ""