#!/bin/bash
# Container Security Scanning Script with Trivy
# Enhanced SDLC security automation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="${DOCKER_IMAGE:-multimodal-contract-extractor}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
TRIVY_CONFIG="${TRIVY_CONFIG:-trivy.yaml}"
REPORTS_DIR="${REPORTS_DIR:-security-reports}"
SEVERITY_THRESHOLD="${SEVERITY_THRESHOLD:-HIGH}"

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}=== Container Security Scanning Suite ===${NC}"
echo -e "Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
echo -e "Config: ${TRIVY_CONFIG}"
echo -e "Reports: ${REPORTS_DIR}"
echo ""

# Function to run Trivy scans
run_trivy_scan() {
    local scan_type="$1"
    local target="$2"
    local output_file="$3"
    local description="$4"
    
    echo -e "${YELLOW}Running ${description}...${NC}"
    
    if trivy --config "$TRIVY_CONFIG" "$scan_type" \
        --format json \
        --output "$output_file" \
        "$target"; then
        echo -e "${GREEN}✓ ${description} completed${NC}"
        
        # Check for vulnerabilities
        if [[ "$scan_type" == "image" ]]; then
            local vuln_count
            vuln_count=$(jq -r '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL" or .Severity == "HIGH")] | length' "$output_file" 2>/dev/null || echo "0")
            
            if [[ "$vuln_count" -gt 0 ]]; then
                echo -e "${RED}⚠ Found $vuln_count HIGH/CRITICAL vulnerabilities${NC}"
                return 1
            else
                echo -e "${GREEN}✓ No HIGH/CRITICAL vulnerabilities found${NC}"
            fi
        fi
        
        return 0
    else
        echo -e "${RED}✗ ${description} failed${NC}"
        return 1
    fi
}

# Function to generate SBOM
generate_sbom() {
    echo -e "${YELLOW}Generating Software Bill of Materials (SBOM)...${NC}"
    
    if trivy image \
        --format spdx-json \
        --output "$REPORTS_DIR/sbom.spdx.json" \
        "$DOCKER_IMAGE:$DOCKER_TAG"; then
        echo -e "${GREEN}✓ SBOM generated successfully${NC}"
        
        # Also generate CycloneDX format
        if trivy image \
            --format cyclonedx \
            --output "$REPORTS_DIR/sbom.cyclonedx.json" \
            "$DOCKER_IMAGE:$DOCKER_TAG"; then
            echo -e "${GREEN}✓ CycloneDX SBOM generated successfully${NC}"
        fi
    else
        echo -e "${RED}✗ SBOM generation failed${NC}"
        return 1
    fi
}

# Function to scan filesystem
scan_filesystem() {
    echo -e "${YELLOW}Scanning filesystem for vulnerabilities...${NC}"
    
    if run_trivy_scan "fs" "." "$REPORTS_DIR/filesystem-scan.json" "Filesystem vulnerability scan"; then
        return 0
    else
        return 1
    fi
}

# Function to scan configuration files
scan_config() {
    echo -e "${YELLOW}Scanning configuration files...${NC}"
    
    if run_trivy_scan "config" "." "$REPORTS_DIR/config-scan.json" "Configuration scan"; then
        return 0
    else
        return 1
    fi
}

# Function to scan for secrets
scan_secrets() {
    echo -e "${YELLOW}Scanning for secrets...${NC}"
    
    if trivy --config "$TRIVY_CONFIG" fs \
        --scanners secret \
        --format json \
        --output "$REPORTS_DIR/secrets-scan.json" \
        .; then
        echo -e "${GREEN}✓ Secret scan completed${NC}"
        
        # Check for secrets
        local secret_count
        secret_count=$(jq -r '[.Results[]?.Secrets[]?] | length' "$REPORTS_DIR/secrets-scan.json" 2>/dev/null || echo "0")
        
        if [[ "$secret_count" -gt 0 ]]; then
            echo -e "${RED}⚠ Found $secret_count potential secrets${NC}"
            return 1
        else
            echo -e "${GREEN}✓ No secrets detected${NC}"
        fi
    else
        echo -e "${RED}✗ Secret scan failed${NC}"
        return 1
    fi
}

# Function to generate HTML report
generate_html_report() {
    echo -e "${YELLOW}Generating HTML security report...${NC}"
    
    # Create a comprehensive HTML report
    cat > "$REPORTS_DIR/security-report.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Container Security Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .critical { background-color: #ffebee; }
        .high { background-color: #fff3e0; }
        .medium { background-color: #f3e5f5; }
        .low { background-color: #e8f5e8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Container Security Report</h1>
        <p>Generated on: $(date)</p>
        <p>Image: ${DOCKER_IMAGE}:${DOCKER_TAG}</p>
    </div>
    
    <div class="section">
        <h2>Scan Summary</h2>
        <p>This report contains the results of comprehensive security scanning including vulnerability assessment, secret detection, configuration analysis, and SBOM generation.</p>
    </div>
    
    <div class="section">
        <h2>Report Files</h2>
        <ul>
            <li><strong>Vulnerability Scan:</strong> <a href="image-scan.json">image-scan.json</a></li>
            <li><strong>Filesystem Scan:</strong> <a href="filesystem-scan.json">filesystem-scan.json</a></li>
            <li><strong>Configuration Scan:</strong> <a href="config-scan.json">config-scan.json</a></li>
            <li><strong>Secret Scan:</strong> <a href="secrets-scan.json">secrets-scan.json</a></li>
            <li><strong>SBOM (SPDX):</strong> <a href="sbom.spdx.json">sbom.spdx.json</a></li>
            <li><strong>SBOM (CycloneDX):</strong> <a href="sbom.cyclonedx.json">sbom.cyclonedx.json</a></li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            <li>Review all HIGH and CRITICAL severity vulnerabilities</li>
            <li>Update base images and dependencies regularly</li>
            <li>Implement automated security scanning in CI/CD pipeline</li>
            <li>Monitor security advisories for dependencies</li>
            <li>Regularly rotate secrets and credentials</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    echo -e "${GREEN}✓ HTML report generated: $REPORTS_DIR/security-report.html${NC}"
}

# Main execution
main() {
    local exit_code=0
    
    # Check if Trivy is installed
    if ! command -v trivy &> /dev/null; then
        echo -e "${RED}Error: Trivy is not installed. Please install Trivy first.${NC}"
        echo "Installation: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        exit 1
    fi
    
    # Check if Docker image exists (if scanning image)
    if [[ "${1:-}" == "image" ]]; then
        if ! docker image inspect "$DOCKER_IMAGE:$DOCKER_TAG" &> /dev/null; then
            echo -e "${RED}Error: Docker image $DOCKER_IMAGE:$DOCKER_TAG not found${NC}"
            echo "Please build the image first: docker build -t $DOCKER_IMAGE:$DOCKER_TAG ."
            exit 1
        fi
        
        # Scan container image
        if ! run_trivy_scan "image" "$DOCKER_IMAGE:$DOCKER_TAG" "$REPORTS_DIR/image-scan.json" "Container image vulnerability scan"; then
            exit_code=1
        fi
        
        # Generate SBOM
        if ! generate_sbom; then
            exit_code=1
        fi
    fi
    
    # Scan filesystem
    if ! scan_filesystem; then
        exit_code=1
    fi
    
    # Scan configuration
    if ! scan_config; then
        exit_code=1
    fi
    
    # Scan for secrets
    if ! scan_secrets; then
        exit_code=1
    fi
    
    # Generate HTML report
    generate_html_report
    
    echo ""
    echo -e "${BLUE}=== Security Scan Complete ===${NC}"
    echo -e "Reports available in: ${REPORTS_DIR}/"
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✓ All security scans passed${NC}"
    else
        echo -e "${RED}⚠ Security issues found - review reports${NC}"
    fi
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"