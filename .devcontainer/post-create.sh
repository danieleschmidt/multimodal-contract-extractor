#!/bin/bash
# Post-create script for Multimodal Contract Extractor development container
# This script sets up the development environment after container creation

set -e

echo "🚀 Setting up Multimodal Contract Extractor development environment..."

# Create necessary directories
echo "📁 Creating development directories..."
mkdir -p logs cache tmp data
mkdir -p tests/fixtures
mkdir -p docs/api/generated

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# Install Node.js dependencies for documentation
echo "📝 Installing documentation dependencies..."
if command -v npm &> /dev/null; then
    npm install -g markdownlint-cli
    npm install -g @apidevtools/swagger-cli
fi

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Set up Git configuration for development
echo "⚙️ Configuring Git for development..."
git config --global --add safe.directory /workspaces/multimodal-contract-extractor
git config --global pull.rebase false
git config --global init.defaultBranch main

# Create development environment file
echo "📋 Creating development environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# Set up development aliases and functions
echo "🔗 Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# Multimodal Contract Extractor Development Aliases
alias mce-test="pytest -xvs"
alias mce-test-cov="pytest --cov=src --cov-report=html --cov-report=term"
alias mce-lint="ruff check . && black --check ."
alias mce-format="ruff check . --fix && black ."
alias mce-type="mypy src/"
alias mce-security="bandit -r src/"
alias mce-dev="streamlit run web_app.py"
alias mce-clean="find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"

# Quick development functions
mce-full-check() {
    echo "🔍 Running full code quality checks..."
    mce-format
    mce-type
    mce-security
    mce-test-cov
    echo "✅ All checks completed!"
}

mce-quick-check() {
    echo "⚡ Running quick checks..."
    ruff check .
    pytest -x
    echo "✅ Quick checks completed!"
}

mce-setup-test-data() {
    echo "📊 Setting up test data..."
    mkdir -p tests/fixtures/pdf tests/fixtures/images
    echo "✅ Test data directories created!"
}
EOF

# Add zsh aliases if zsh is available
if command -v zsh &> /dev/null; then
    cat >> ~/.zshrc << 'EOF'

# Multimodal Contract Extractor Development Aliases
alias mce-test="pytest -xvs"
alias mce-test-cov="pytest --cov=src --cov-report=html --cov-report=term"
alias mce-lint="ruff check . && black --check ."
alias mce-format="ruff check . --fix && black ."
alias mce-type="mypy src/"
alias mce-security="bandit -r src/"
alias mce-dev="streamlit run web_app.py"
alias mce-clean="find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"

# Quick development functions
mce-full-check() {
    echo "🔍 Running full code quality checks..."
    mce-format
    mce-type
    mce-security
    mce-test-cov
    echo "✅ All checks completed!"
}

mce-quick-check() {
    echo "⚡ Running quick checks..."
    ruff check .
    pytest -x
    echo "✅ Quick checks completed!"
}

mce-setup-test-data() {
    echo "📊 Setting up test data..."
    mkdir -p tests/fixtures/pdf tests/fixtures/images
    echo "✅ Test data directories created!"
}
EOF
fi

# Install system dependencies for OCR and image processing
echo "🖼️ Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    imagemagick \
    ghostscript \
    libmagickwand-dev

# Set up OCR language data
echo "🌍 Setting up OCR language support..."
sudo apt-get install -y \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    tesseract-ocr-por

# Configure ImageMagick security policy for PDF processing
echo "🔐 Configuring ImageMagick security policy..."
sudo sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml || true

# Set up development database (if needed)
echo "🗄️ Setting up development database..."
# Future: Add database setup when implemented

# Create useful development scripts
echo "📜 Creating development utility scripts..."
mkdir -p scripts/dev

# Create a quick test script
cat > scripts/dev/quick-test.sh << 'EOF'
#!/bin/bash
# Quick test script for development
set -e

echo "🚀 Running quick development tests..."

# Run linting
echo "🔍 Checking code style..."
ruff check src/ tests/

# Run type checking
echo "🔍 Running type checks..."
mypy src/

# Run unit tests
echo "🧪 Running unit tests..."
pytest tests/unit/ -v

echo "✅ Quick tests completed successfully!"
EOF

chmod +x scripts/dev/quick-test.sh

# Create a development server script
cat > scripts/dev/start-dev.sh << 'EOF'
#!/bin/bash
# Development server startup script
set -e

echo "🚀 Starting Multimodal Contract Extractor development server..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# Start Streamlit in development mode
export STREAMLIT_SERVER_HEADLESS=false
export STREAMLIT_SERVER_ENABLE_CORS=true
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

echo "🌐 Starting Streamlit development server..."
streamlit run web_app.py --server.port 8501 --server.address 0.0.0.0
EOF

chmod +x scripts/dev/start-dev.sh

# Set up documentation building
echo "📚 Setting up documentation tools..."
if [ -f mkdocs.yml ]; then
    echo "MkDocs configuration found. Installing additional dependencies..."
    pip install mkdocs-material mkdocstrings[python] mkdocs-swagger-ui-tag
fi

# Run initial code quality checks
echo "🔍 Running initial code quality checks..."
if command -v ruff &> /dev/null; then
    ruff check . --fix || echo "⚠️  Some linting issues found. Please review."
fi

# Set permissions for scripts
echo "🔧 Setting script permissions..."
find scripts/ -name "*.sh" -exec chmod +x {} \;

# Clean up cache directories
echo "🧹 Cleaning up cache directories..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true

# Create development README
cat > DEV_README.md << 'EOF'
# Development Environment Setup

This development container is configured with all the tools needed for Multimodal Contract Extractor development.

## Quick Commands

- `mce-test` - Run tests
- `mce-test-cov` - Run tests with coverage
- `mce-lint` - Check code style
- `mce-format` - Auto-format code
- `mce-type` - Run type checking
- `mce-security` - Security scanning
- `mce-dev` - Start development server
- `mce-full-check` - Run all quality checks
- `mce-quick-check` - Run quick checks

## Development Workflow

1. **Make your changes** to the codebase
2. **Run tests**: `mce-test`
3. **Check code quality**: `mce-quick-check`
4. **Start development server**: `mce-dev`
5. **Before committing**: `mce-full-check`

## Available Services

- **Streamlit App**: http://localhost:8501
- **Prometheus Metrics**: http://localhost:9090
- **API Documentation**: Available when API is implemented

## Development Scripts

- `scripts/dev/quick-test.sh` - Run quick development tests
- `scripts/dev/start-dev.sh` - Start development server

## Environment Variables

Copy `.env.example` to `.env` and customize as needed for your development environment.

## Pre-commit Hooks

Pre-commit hooks are automatically installed and will run:
- Code formatting (black, ruff)
- Type checking (mypy)
- Security scanning (bandit)
- YAML/JSON validation

Happy coding! 🚀
EOF

echo "✅ Development environment setup completed!"
echo ""
echo "🎉 Welcome to Multimodal Contract Extractor development!"
echo "📝 Check DEV_README.md for quick commands and workflow"
echo "🚀 Run 'mce-dev' to start the development server"
echo "🧪 Run 'mce-test' to run the test suite"
echo ""