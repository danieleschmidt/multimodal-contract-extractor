#!/bin/bash
# Governance and Compliance Automation Script
# Comprehensive governance checking with policy enforcement and audit trail

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GOVERNANCE_DIR="${GOVERNANCE_DIR:-governance}"
REPORTS_DIR="${REPORTS_DIR:-$GOVERNANCE_DIR/reports}"
POLICIES_CONFIG="${POLICIES_CONFIG:-$GOVERNANCE_DIR/policies.json}"
PYTHON_CMD="${PYTHON_CMD:-python}"
REPOSITORY_ROOT="${REPOSITORY_ROOT:-.}"

# Create directories
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}=== Governance and Compliance Check ===${NC}"
echo -e "Governance directory: ${GOVERNANCE_DIR}"
echo -e "Reports directory: ${REPORTS_DIR}"
echo -e "Repository root: ${REPOSITORY_ROOT}"
echo ""

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking governance dependencies...${NC}"
    
    # Check if governance modules are available
    local missing_modules=()
    
    if ! $PYTHON_CMD -c "import json, pathlib, hashlib" 2>/dev/null; then
        missing_modules+=("python standard library components")
    fi
    
    # Check for optional dependencies
    if ! $PYTHON_CMD -c "import pip_licenses" 2>/dev/null; then
        echo -e "${YELLOW}pip-licenses not available - license checking will be limited${NC}"
    fi
    
    if [[ ${#missing_modules[@]} -gt 0 ]]; then
        echo -e "${RED}Missing dependencies: ${missing_modules[*]}${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ All required dependencies available${NC}"
    fi
}

# Function to create default policies configuration
create_default_policies_config() {
    if [[ ! -f "$POLICIES_CONFIG" ]]; then
        echo -e "${YELLOW}Creating default policies configuration...${NC}"
        
        cat > "$POLICIES_CONFIG" << 'EOF'
{
  "enabled_policies": [],
  "disabled_policies": [],
  "policy_settings": {
    "security.no_secrets_in_code": {
      "excluded_files": [
        "**/*test*",
        "**/*example*",  
        "**/*.md",
        "**/docs/**"
      ]
    },
    "compliance.required_files": {
      "required_files": [
        "README.md",
        "LICENSE", 
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        ".gitignore"
      ]
    },
    "quality.code_standards": {
      "min_test_coverage": 80.0,
      "max_function_lines": 50,
      "max_file_lines": 500
    }
  },
  "compliance_frameworks": [
    "SOX",
    "GDPR", 
    "HIPAA",
    "ISO27001"
  ],
  "reporting": {
    "formats": ["json", "html", "csv"],
    "include_recommendations": true,
    "include_audit_trail": true
  }
}
EOF
        echo -e "${GREEN}✓ Default policies configuration created${NC}"
    fi
}

# Function to run policy as code checks
run_policy_checks() {
    echo -e "${YELLOW}Running policy as code checks...${NC}"
    
    local policy_script="$GOVERNANCE_DIR/policy_as_code.py"
    local output_file="$REPORTS_DIR/policy_compliance_$(date +%Y%m%d_%H%M%S).json"
    
    if [[ ! -f "$policy_script" ]]; then
        echo -e "${RED}✗ Policy script not found: $policy_script${NC}"
        return 1
    fi
    
    if $PYTHON_CMD "$policy_script" \
        --config "$POLICIES_CONFIG" \
        --output "$output_file" \
        --repository "$REPOSITORY_ROOT" \
        --verbose; then
        echo -e "${GREEN}✓ Policy checks completed${NC}"
        
        # Display summary
        if command -v jq &> /dev/null && [[ -f "$output_file" ]]; then
            local overall_status
            overall_status=$(jq -r '.overall_status' "$output_file")
            local compliance_score
            compliance_score=$(jq -r '.compliance_score' "$output_file")
            local total_violations
            total_violations=$(jq -r '.summary.total_violations' "$output_file")
            
            echo -e "  Overall Status: $overall_status"
            echo -e "  Compliance Score: ${compliance_score}%"
            echo -e "  Total Violations: $total_violations"
            
            if [[ "$overall_status" != "compliant" ]]; then
                return 1
            fi
        fi
        
        return 0
    else
        echo -e "${RED}✗ Policy checks failed${NC}"
        return 1
    fi
}

# Function to run audit system checks
run_audit_checks() {
    echo -e "${YELLOW}Running audit system checks...${NC}"
    
    local audit_script="$GOVERNANCE_DIR/audit_automation.py"
    
    if [[ ! -f "$audit_script" ]]; then
        echo -e "${YELLOW}⚠ Audit script not found: $audit_script${NC}"
        return 0
    fi
    
    # Test audit system functionality
    if $PYTHON_CMD -c "
import sys
sys.path.insert(0, '$GOVERNANCE_DIR')
from audit_automation import get_audit_logger, AuditEventType, AuditOutcome
import datetime

# Test audit logging
logger = get_audit_logger()

# Log a test event
event_id = logger.log_event(
    event_type=AuditEventType.SYSTEM,
    actor='governance-check',
    action='compliance_check',
    resource='repository',
    outcome=AuditOutcome.SUCCESS,
    details={'test': True}
)

print(f'Test audit event logged: {event_id}')

# Verify integrity
integrity_result = logger.verify_integrity()
print(f'Audit integrity check: {integrity_result[\"status\"]}')

# Generate a basic report
report = logger.generate_compliance_report(
    start_date=datetime.datetime.now() - datetime.timedelta(days=1),
    end_date=datetime.datetime.now()
)

print(f'Generated compliance report with {report[\"total_events\"]} events')
"; then
        echo -e "${GREEN}✓ Audit system operational${NC}"
        return 0
    else
        echo -e "${RED}✗ Audit system checks failed${NC}"
        return 1
    fi
}

# Function to check security configurations
check_security_configs() {
    echo -e "${YELLOW}Checking security configurations...${NC}"
    
    local security_issues=()
    
    # Check for secrets in environment
    if env | grep -i -E "(password|secret|key|token)" | grep -v -E "(PATH|HOME|USER)" >/dev/null 2>&1; then
        security_issues+=("Potential secrets in environment variables")
    fi
    
    # Check file permissions
    local world_writable
    world_writable=$(find "$REPOSITORY_ROOT" -type f -perm -o+w 2>/dev/null | head -5)
    if [[ -n "$world_writable" ]]; then
        security_issues+=("World-writable files detected")
    fi
    
    # Check for unencrypted private keys
    local private_keys
    private_keys=$(find "$REPOSITORY_ROOT" -name "*.pem" -o -name "*.key" -o -name "*_rsa" 2>/dev/null | head -5)
    if [[ -n "$private_keys" ]]; then
        security_issues+=("Private key files detected")
    fi
    
    # Check .git directory permissions
    if [[ -d "$REPOSITORY_ROOT/.git" ]]; then
        local git_perms
        git_perms=$(stat -c "%a" "$REPOSITORY_ROOT/.git" 2>/dev/null || echo "755")
        if [[ "$git_perms" != "755" ]] && [[ "$git_perms" != "750" ]]; then
            security_issues+=("Incorrect .git directory permissions: $git_perms")
        fi
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Security issues detected:${NC}"
        for issue in "${security_issues[@]}"; do
            echo -e "${RED}  - $issue${NC}"
        done
        return 1
    else
        echo -e "${GREEN}✓ No security issues detected${NC}"
        return 0
    fi
}

# Function to validate compliance frameworks
validate_compliance_frameworks() {
    echo -e "${YELLOW}Validating compliance framework requirements...${NC}"
    
    local compliance_issues=()
    
    # SOX (Sarbanes-Oxley) requirements
    if [[ -f "$POLICIES_CONFIG" ]] && command -v jq &> /dev/null; then
        local frameworks
        frameworks=$(jq -r '.compliance_frameworks[]?' "$POLICIES_CONFIG" 2>/dev/null || echo "")
        
        if echo "$frameworks" | grep -q "SOX"; then
            # Check for audit trail
            if [[ ! -d "$GOVERNANCE_DIR/audit_logs" ]]; then
                compliance_issues+=("SOX: Audit trail directory not found")
            fi
            
            # Check for change control documentation
            if [[ ! -f "CHANGELOG.md" ]]; then
                compliance_issues+=("SOX: Change control documentation (CHANGELOG.md) missing")
            fi
        fi
        
        if echo "$frameworks" | grep -q "GDPR"; then
            # Check for privacy policy
            if [[ ! -f "PRIVACY.md" ]] && [[ ! -f "docs/privacy.md" ]]; then
                compliance_issues+=("GDPR: Privacy policy documentation missing")
            fi
        fi
        
        if echo "$frameworks" | grep -q "HIPAA"; then
            # Check for security documentation
            if [[ ! -f "SECURITY.md" ]]; then
                compliance_issues+=("HIPAA: Security documentation missing")
            fi
        fi
    fi
    
    if [[ ${#compliance_issues[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Compliance framework issues:${NC}"
        for issue in "${compliance_issues[@]}"; do
            echo -e "${YELLOW}  - $issue${NC}"
        done
        return 1
    else
        echo -e "${GREEN}✓ Compliance framework requirements satisfied${NC}"
        return 0
    fi
}

# Function to generate comprehensive governance report
generate_governance_report() {
    echo -e "${YELLOW}Generating comprehensive governance report...${NC}"
    
    local report_file="$REPORTS_DIR/governance_report_$(date +%Y%m%d_%H%M%S).json"
    local html_report="${report_file%.json}.html"
    
    # Collect governance data
    local governance_data
    governance_data=$(cat << EOF
{
  "report_metadata": {
    "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "repository": "$REPOSITORY_ROOT",
    "governance_version": "1.0.0"
  },
  "summary": {
    "total_checks": 4,
    "passed_checks": 0,
    "failed_checks": 0,
    "warnings": 0
  },
  "checks": {
    "policy_compliance": {
      "status": "unknown",
      "details": "Policy compliance check results"
    },
    "audit_system": {
      "status": "unknown", 
      "details": "Audit system operational status"
    },
    "security_configuration": {
      "status": "unknown",
      "details": "Security configuration validation"
    },
    "compliance_frameworks": {
      "status": "unknown",
      "details": "Compliance framework validation"
    }
  },
  "recommendations": []
}
EOF
)
    
    echo "$governance_data" > "$report_file"
    
    # Generate HTML report
    cat > "$html_report" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6; 
        }
        .header { 
            background: #f0f0f0; 
            padding: 20px; 
            border-radius: 5px; 
            margin-bottom: 20px;
        }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        .section { margin: 20px 0; }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 10px 0; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        th { background-color: #f2f2f2; }
        .recommendation { 
            background: #e7f3ff; 
            border-left: 4px solid #2196F3; 
            padding: 10px; 
            margin: 10px 0; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Governance and Compliance Report</h1>
        <p><strong>Generated:</strong> $(date)</p>
        <p><strong>Repository:</strong> $REPOSITORY_ROOT</p>
    </div>
    
    <div class="section">
        <h2>📊 Executive Summary</h2>
        <p>This report provides a comprehensive overview of governance and compliance status for the repository.</p>
        
        <table>
            <tr>
                <th>Check Category</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
            <tr>
                <td>Policy Compliance</td>
                <td><span id="policy-status">Pending</span></td>
                <td>Automated policy validation results</td>
            </tr>
            <tr>
                <td>Audit System</td>
                <td><span id="audit-status">Pending</span></td>
                <td>Audit trail and logging system status</td>
            </tr>
            <tr>
                <td>Security Configuration</td>
                <td><span id="security-status">Pending</span></td>
                <td>Security settings and configurations</td>
            </tr>
            <tr>
                <td>Compliance Frameworks</td>
                <td><span id="compliance-status">Pending</span></td>
                <td>Framework-specific requirement validation</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>🔍 Detailed Findings</h2>
        <p>Detailed results for each governance check category.</p>
        
        <h3>Policy Compliance</h3>
        <p>Automated validation of governance policies including security, quality, and compliance requirements.</p>
        
        <h3>Audit System</h3>
        <p>Verification of audit trail capabilities and integrity checking systems.</p>
        
        <h3>Security Configuration</h3>
        <p>Assessment of security configurations, permissions, and potential vulnerabilities.</p>
        
        <h3>Compliance Frameworks</h3>
        <p>Validation against specific regulatory and compliance framework requirements.</p>
    </div>
    
    <div class="section">
        <h2>💡 Recommendations</h2>
        <div class="recommendation">
            <strong>Continuous Monitoring:</strong> Implement automated governance checks in CI/CD pipeline.
        </div>
        <div class="recommendation">
            <strong>Regular Reviews:</strong> Schedule periodic governance and compliance reviews.
        </div>
        <div class="recommendation">
            <strong>Documentation:</strong> Maintain up-to-date governance and compliance documentation.
        </div>
    </div>
    
    <div class="section">
        <h2>📋 Next Steps</h2>
        <ul>
            <li>Address any failed governance checks</li>
            <li>Implement recommended security improvements</li>
            <li>Update compliance documentation as needed</li>
            <li>Schedule regular governance reviews</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    echo -e "${GREEN}✓ Governance report generated${NC}"
    echo -e "  JSON Report: $report_file"
    echo -e "  HTML Report: $html_report"
}

# Function to show governance status summary
show_governance_summary() {
    echo ""
    echo -e "${BLUE}=== Governance Check Summary ===${NC}"
    
    local total_checks=4
    local passed_checks=0
    local failed_checks=0
    local warnings=0
    
    # This would be populated by actual check results
    echo -e "Total Checks: $total_checks"
    echo -e "Passed: ${GREEN}$passed_checks${NC}"
    echo -e "Failed: ${RED}$failed_checks${NC}" 
    echo -e "Warnings: ${YELLOW}$warnings${NC}"
    
    echo ""
    echo -e "Reports available in: $REPORTS_DIR"
}

# Main execution function
main() {
    local mode="${1:-full}"
    local exit_code=0
    
    case "$mode" in
        "policy")
            check_dependencies
            create_default_policies_config
            if ! run_policy_checks; then
                exit_code=1
            fi
            ;;
        "audit")
            check_dependencies
            if ! run_audit_checks; then
                exit_code=1
            fi
            ;;
        "security")
            if ! check_security_configs; then
                exit_code=1
            fi
            ;;
        "compliance")
            if ! validate_compliance_frameworks; then
                exit_code=1
            fi
            ;;
        "report")
            generate_governance_report
            ;;
        "full"|*)
            check_dependencies
            create_default_policies_config
            
            echo ""
            echo -e "${BLUE}Running comprehensive governance checks...${NC}"
            
            # Run all checks
            if ! run_policy_checks; then
                exit_code=1
            fi
            
            if ! run_audit_checks; then
                exit_code=1
            fi
            
            if ! check_security_configs; then
                exit_code=1
            fi
            
            if ! validate_compliance_frameworks; then
                exit_code=1
            fi
            
            # Generate reports
            generate_governance_report
            show_governance_summary
            ;;
    esac
    
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ Governance checks completed successfully${NC}"
    else
        echo -e "${RED}⚠️ Governance issues detected - review reports${NC}"
    fi
    
    exit $exit_code
}

# Usage information
show_usage() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  full        - Run all governance checks (default)"
    echo "  policy      - Run policy compliance checks only"
    echo "  audit       - Run audit system checks only"
    echo "  security    - Run security configuration checks only"
    echo "  compliance  - Run compliance framework validation only"
    echo "  report      - Generate governance report only"
    echo ""
    echo "Environment variables:"
    echo "  GOVERNANCE_DIR    - Governance directory (default: governance)"
    echo "  PYTHON_CMD        - Python command (default: python)"
    echo "  REPOSITORY_ROOT   - Repository root path (default: .)"
}

# Handle command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "${1:-full}"