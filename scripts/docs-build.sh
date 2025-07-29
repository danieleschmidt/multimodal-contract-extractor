#!/bin/bash
# Documentation Build and Deployment Script
# Automated API documentation generation and publishing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="${DOCS_DIR:-docs}"
SITE_DIR="${SITE_DIR:-site}"
BUILD_DIR="${BUILD_DIR:-docs_build}"
PYTHON_CMD="${PYTHON_CMD:-python}"
SERVE_PORT="${SERVE_PORT:-8000}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-gh-pages}"

echo -e "${BLUE}=== Documentation Build System ===${NC}"
echo -e "Docs directory: ${DOCS_DIR}"
echo -e "Build directory: ${BUILD_DIR}"
echo -e "Site directory: ${SITE_DIR}"
echo ""

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking documentation dependencies...${NC}"
    
    local missing_packages=()
    
    # Check for required Python packages
    local required_packages=(
        "mkdocs"
        "mkdocs-material"
        "mkdocstrings"
    )
    
    for package in "${required_packages[@]}"; do
        if ! $PYTHON_CMD -c "import ${package//-/_}" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Installing missing packages: ${missing_packages[*]}${NC}"
        $PYTHON_CMD -m pip install "${missing_packages[@]}"
    else
        echo -e "${GREEN}✓ All dependencies available${NC}"
    fi
}

# Function to validate documentation structure
validate_docs() {
    echo -e "${YELLOW}Validating documentation structure...${NC}"
    
    local validation_errors=()
    
    # Check if mkdocs.yml exists
    if [[ ! -f "mkdocs.yml" ]]; then
        validation_errors+=("mkdocs.yml not found")
    fi
    
    # Check if docs directory exists
    if [[ ! -d "$DOCS_DIR" ]]; then
        validation_errors+=("Documentation directory ($DOCS_DIR) not found")
    fi
    
    # Check for index file
    if [[ ! -f "$DOCS_DIR/index.md" ]] && [[ ! -f "README.md" ]]; then
        validation_errors+=("No index.md or README.md found")
    fi
    
    # Validate mkdocs configuration
    if [[ -f "mkdocs.yml" ]]; then
        if ! mkdocs build --strict --clean --quiet --site-dir /tmp/mkdocs_validation 2>/dev/null; then
            validation_errors+=("MkDocs configuration validation failed")
        else
            rm -rf /tmp/mkdocs_validation
        fi
    fi
    
    if [[ ${#validation_errors[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Documentation validation failed:${NC}"
        for error in "${validation_errors[@]}"; do
            echo -e "${RED}  - $error${NC}"
        done
        return 1
    else
        echo -e "${GREEN}✓ Documentation structure valid${NC}"
        return 0
    fi
}

# Function to generate API documentation
generate_api_docs() {
    echo -e "${YELLOW}Generating API documentation...${NC}"
    
    # Create API docs directory if it doesn't exist
    mkdir -p "$DOCS_DIR/api"
    
    # Generate module documentation using mkdocstrings
    if [[ -d "src" ]]; then
        echo -e "  Scanning Python modules in src/..."
        
        # Find Python modules
        local modules
        modules=$(find src -name "*.py" -not -name "__init__.py" | sed 's|src/||' | sed 's|\.py$||' | sed 's|/|.|g')
        
        # Generate documentation for each module
        for module in $modules; do
            local doc_file="$DOCS_DIR/api/$(echo "$module" | sed 's|\.|/|g').md"
            local doc_dir
            doc_dir=$(dirname "$doc_file")
            
            mkdir -p "$doc_dir"
            
            cat > "$doc_file" << EOF
# ${module}

::: ${module}
EOF
            echo -e "  Generated: $doc_file"
        done
    fi
    
    echo -e "${GREEN}✓ API documentation generated${NC}"
}

# Function to build documentation
build_docs() {
    echo -e "${YELLOW}Building documentation...${NC}"
    
    # Clean previous build
    if [[ -d "$SITE_DIR" ]]; then
        rm -rf "$SITE_DIR"
    fi
    
    # Build with MkDocs
    if mkdocs build --strict --clean --site-dir "$SITE_DIR"; then
        echo -e "${GREEN}✓ Documentation built successfully${NC}"
        
        # Show build statistics
        local total_files
        total_files=$(find "$SITE_DIR" -type f | wc -l)
        local total_size
        total_size=$(du -sh "$SITE_DIR" | cut -f1)
        
        echo -e "  Total files: $total_files"
        echo -e "  Total size: $total_size"
        
        return 0
    else
        echo -e "${RED}✗ Documentation build failed${NC}"
        return 1
    fi
}

# Function to serve documentation locally
serve_docs() {
    echo -e "${YELLOW}Starting documentation server...${NC}"
    echo -e "Server will be available at: http://localhost:$SERVE_PORT"
    echo -e "Press Ctrl+C to stop the server"
    
    # Serve with auto-reload
    mkdocs serve --dev-addr "0.0.0.0:$SERVE_PORT"
}

# Function to deploy documentation
deploy_docs() {
    local deploy_target="${1:-gh-pages}"
    
    echo -e "${YELLOW}Deploying documentation to $deploy_target...${NC}"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}✗ Not in a git repository${NC}"
        return 1
    fi
    
    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠ Warning: Uncommitted changes detected${NC}"
        read -p "Continue with deployment? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            return 1
        fi
    fi
    
    # Deploy using mkdocs
    if mkdocs gh-deploy --force --clean --remote-branch "$deploy_target"; then
        echo -e "${GREEN}✓ Documentation deployed successfully${NC}"
        
        # Show deployment URL if GitHub Pages
        if [[ "$deploy_target" == "gh-pages" ]]; then
            local repo_url
            repo_url=$(git remote get-url origin | sed 's/\.git$//')
            local github_pages_url
            github_pages_url=$(echo "$repo_url" | sed 's|github\.com[:/]|github.io/|' | sed 's|https://||')
            echo -e "  Documentation URL: https://$github_pages_url"
        fi
        
        return 0
    else
        echo -e "${RED}✗ Documentation deployment failed${NC}"
        return 1
    fi
}

# Function to run documentation tests
test_docs() {
    echo -e "${YELLOW}Running documentation tests...${NC}"
    
    local test_errors=()
    
    # Test 1: Check for broken internal links
    echo -e "  Testing internal links..."
    if [[ -d "$SITE_DIR" ]]; then
        # Simple link check (could be enhanced with tools like linkchecker)
        local broken_links
        broken_links=$(find "$SITE_DIR" -name "*.html" -exec grep -l "href.*404" {} \; 2>/dev/null || true)
        
        if [[ -n "$broken_links" ]]; then
            test_errors+=("Potential broken internal links found")
        fi
    else
        test_errors+=("Site directory not found - build documentation first")
    fi
    
    # Test 2: Check for missing pages referenced in nav
    echo -e "  Checking navigation references..."
    if [[ -f "mkdocs.yml" ]] && command -v python &> /dev/null; then
        # This is a simplified check - could be enhanced with proper YAML parsing
        local nav_files
        nav_files=$(grep -E "^\s*-\s*.*\.md" mkdocs.yml | sed 's/.*: *//' | tr -d ' ' || true)
        
        for nav_file in $nav_files; do
            if [[ ! -f "$DOCS_DIR/$nav_file" ]] && [[ ! -f "$nav_file" ]]; then
                test_errors+=("Referenced file not found: $nav_file")
            fi
        done
    fi
    
    # Test 3: Validate HTML output
    echo -e "  Validating HTML output..."
    if [[ -d "$SITE_DIR" ]]; then
        local html_files
        html_files=$(find "$SITE_DIR" -name "*.html" | head -5)  # Test first 5 files
        
        for html_file in $html_files; do
            if ! grep -q "</html>" "$html_file"; then
                test_errors+=("Invalid HTML structure in $(basename "$html_file")")
            fi
        done
    fi
    
    # Report test results
    if [[ ${#test_errors[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Documentation tests failed:${NC}"
        for error in "${test_errors[@]}"; do
            echo -e "${RED}  - $error${NC}"
        done
        return 1
    else
        echo -e "${GREEN}✓ All documentation tests passed${NC}"
        return 0
    fi
}

# Function to generate documentation coverage report
coverage_report() {
    echo -e "${YELLOW}Generating documentation coverage report...${NC}"
    
    local coverage_file="$BUILD_DIR/docs_coverage_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$BUILD_DIR"
    
    cat > "$coverage_file" << EOF
Documentation Coverage Report
============================
Generated: $(date)

Project Structure:
EOF
    
    # Count Python files vs documented modules
    if [[ -d "src" ]]; then
        local python_files
        python_files=$(find src -name "*.py" -not -name "__init__.py" | wc -l)
        
        local documented_modules
        documented_modules=$(find "$DOCS_DIR/api" -name "*.md" 2>/dev/null | wc -l || echo "0")
        
        local coverage_percent
        if [[ $python_files -gt 0 ]]; then
            coverage_percent=$(( documented_modules * 100 / python_files ))
        else
            coverage_percent=0
        fi
        
        cat >> "$coverage_file" << EOF
- Python modules: $python_files
- Documented modules: $documented_modules
- Documentation coverage: ${coverage_percent}%

EOF
    fi
    
    # List documentation files
    echo "Documentation Files:" >> "$coverage_file"
    find "$DOCS_DIR" -name "*.md" 2>/dev/null | sort >> "$coverage_file" || echo "No markdown files found" >> "$coverage_file"
    
    echo -e "${GREEN}✓ Coverage report generated: $coverage_file${NC}"
    
    # Show summary
    if [[ -f "$coverage_file" ]]; then
        echo -e "\nCoverage Summary:"
        grep -E "(coverage:|modules:|files:)" "$coverage_file" | sed 's/^/  /'
    fi
}

# Function to clean build artifacts
clean_docs() {
    echo -e "${YELLOW}Cleaning documentation build artifacts...${NC}"
    
    local cleaned_items=()
    
    if [[ -d "$SITE_DIR" ]]; then
        rm -rf "$SITE_DIR"
        cleaned_items+=("$SITE_DIR")
    fi
    
    if [[ -d "$BUILD_DIR" ]]; then
        rm -rf "$BUILD_DIR"
        cleaned_items+=("$BUILD_DIR")
    fi
    
    # Clean auto-generated API docs
    if [[ -d "$DOCS_DIR/api" ]]; then
        find "$DOCS_DIR/api" -name "*.md" -type f -exec rm {} \; 2>/dev/null || true
        cleaned_items+=("generated API docs")
    fi
    
    if [[ ${#cleaned_items[@]} -gt 0 ]]; then
        echo -e "${GREEN}✓ Cleaned: ${cleaned_items[*]}${NC}"
    else
        echo -e "${GREEN}✓ Nothing to clean${NC}"
    fi
}

# Main function
main() {
    local command="${1:-build}"
    
    case "$command" in
        "build")
            check_dependencies
            validate_docs
            generate_api_docs
            build_docs
            ;;
        "serve")
            check_dependencies
            validate_docs
            serve_docs
            ;;
        "deploy")
            check_dependencies
            validate_docs
            generate_api_docs
            build_docs
            test_docs
            deploy_docs "${2:-gh-pages}"
            ;;
        "test")
            build_docs
            test_docs
            ;;
        "coverage")
            generate_api_docs
            coverage_report
            ;;
        "clean")
            clean_docs
            ;;
        "validate")
            check_dependencies
            validate_docs
            ;;
        "generate")
            check_dependencies
            generate_api_docs
            ;;
        *)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  build     - Build documentation (default)"
            echo "  serve     - Serve documentation locally"
            echo "  deploy    - Deploy to GitHub Pages"
            echo "  test      - Run documentation tests"
            echo "  coverage  - Generate coverage report"
            echo "  clean     - Clean build artifacts"
            echo "  validate  - Validate documentation structure"
            echo "  generate  - Generate API documentation"
            echo ""
            echo "Environment variables:"
            echo "  DOCS_DIR    - Documentation directory (default: docs)"
            echo "  SITE_DIR    - Build output directory (default: site)"
            echo "  PYTHON_CMD  - Python command (default: python)"
            echo "  SERVE_PORT  - Development server port (default: 8000)"
            ;;
    esac
}

# Run main function with all arguments
main "$@"