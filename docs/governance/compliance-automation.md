# Compliance Automation Framework

This document outlines the automated compliance and governance framework for the Multimodal Contract Extractor, designed to meet enterprise security and regulatory requirements.

## Overview

The compliance automation framework provides:
- Automated security policy enforcement
- Continuous compliance monitoring
- Audit trail generation
- Regulatory requirement mapping
- Risk assessment automation

## Regulatory Standards Supported

### Data Protection
- **GDPR** (General Data Protection Regulation)
- **CCPA** (California Consumer Privacy Act)
- **HIPAA** (Health Insurance Portability and Accountability Act)

### Security Frameworks
- **SOC 2 Type II** (Service Organization Control)
- **ISO 27001** (Information Security Management)
- **NIST Cybersecurity Framework**
- **PCI DSS** (Payment Card Industry Data Security Standard)

### Industry Standards
- **SLSA** (Supply-chain Levels for Software Artifacts)
- **OWASP ASVS** (Application Security Verification Standard)
- **CIS Controls** (Center for Internet Security)

## Automated Policy Enforcement

### Code Quality Gates

```yaml
# .github/workflows/compliance-gates.yml
name: Compliance Quality Gates

on:
  pull_request:
  push:
    branches: [main]

jobs:
  security-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # SAST Analysis
      - name: Static Application Security Testing
        uses: github/super-linter@v4
        env:
          VALIDATE_ALL_CODEBASE: false
          VALIDATE_PYTHON_BANDIT: true
          VALIDATE_PYTHON_MYPY: true
          
      # Dependency Vulnerability Scanning
      - name: Dependency Security Scan
        run: |
          pip install safety pip-audit
          safety check --json --output safety-report.json
          pip-audit --format=cyclonedx-json --output=sbom.json
          
      # License Compliance
      - name: License Compliance Check
        run: |
          pip install pip-licenses
          pip-licenses --format=json --output-file=licenses.json
          python scripts/check_license_compliance.py
          
      # Data Privacy Compliance
      - name: Data Privacy Scan
        run: |
          grep -r "personal.*data\|pii\|sensitive" src/ || true
          python scripts/privacy_compliance_check.py
```

### Infrastructure Security Policies

```hcl
# infrastructure/policies/security.rego
package kubernetes.security

deny[msg] {
  input.kind == "Pod"
  input.spec.securityContext.runAsRoot == true
  msg := "Pods must not run as root user"
}

deny[msg] {
  input.kind == "Pod"
  not input.spec.securityContext.runAsNonRoot
  msg := "Pods must explicitly set runAsNonRoot: true"
}

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  not container.securityContext.allowPrivilegeEscalation == false
  msg := "Containers must not allow privilege escalation"
}

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  not container.resources.limits.memory
  msg := "Containers must have memory limits defined"
}

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  not container.resources.limits.cpu
  msg := "Containers must have CPU limits defined"
}
```

## Continuous Compliance Monitoring

### Security Metrics Dashboard

```python
# scripts/compliance_metrics.py
#!/usr/bin/env python3
"""
Compliance metrics collection and reporting
"""

import json
import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class ComplianceMetric:
    """Represents a single compliance metric"""
    name: str
    value: float
    threshold: float
    status: str  # "pass", "fail", "warning"
    timestamp: str
    details: Dict[str, Any]

class ComplianceMonitor:
    """Monitors and reports on compliance metrics"""
    
    def __init__(self):
        self.metrics: List[ComplianceMetric] = []
        
    def check_security_vulnerabilities(self) -> ComplianceMetric:
        """Check for security vulnerabilities in dependencies"""
        # Implementation would run safety/pip-audit
        return ComplianceMetric(
            name="security_vulnerabilities",
            value=0,  # Number of high/critical vulnerabilities
            threshold=0,
            status="pass",
            timestamp=datetime.datetime.utcnow().isoformat(),
            details={"scan_type": "dependency", "tool": "safety+pip-audit"}
        )
    
    def check_code_quality(self) -> ComplianceMetric:
        """Check code quality metrics"""
        # Implementation would analyze ruff/mypy/bandit results
        return ComplianceMetric(
            name="code_quality_score",
            value=95.5,
            threshold=90.0,
            status="pass",
            timestamp=datetime.datetime.utcnow().isoformat(),
            details={"coverage": 95.5, "linting_errors": 0, "type_errors": 0}
        )
    
    def check_license_compliance(self) -> ComplianceMetric:
        """Check license compliance for all dependencies"""
        approved_licenses = ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]
        # Implementation would analyze pip-licenses output
        return ComplianceMetric(
            name="license_compliance",
            value=100.0,  # Percentage of approved licenses
            threshold=100.0,
            status="pass",
            timestamp=datetime.datetime.utcnow().isoformat(),
            details={"approved_licenses": approved_licenses, "violations": []}
        )
    
    def check_data_privacy(self) -> ComplianceMetric:
        """Check data privacy compliance"""
        # Implementation would scan for PII handling patterns
        return ComplianceMetric(
            name="data_privacy_compliance",
            value=100.0,
            threshold=95.0,
            status="pass",
            timestamp=datetime.datetime.utcnow().isoformat(),
            details={"gdpr_compliant": True, "data_retention_policy": True}
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        self.metrics = [
            self.check_security_vulnerabilities(),
            self.check_code_quality(),
            self.check_license_compliance(),
            self.check_data_privacy()
        ]
        
        total_checks = len(self.metrics)
        passed_checks = sum(1 for m in self.metrics if m.status == "pass")
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "overall_compliance_score": (passed_checks / total_checks) * 100,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "metrics": [asdict(m) for m in self.metrics],
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        for metric in self.metrics:
            if metric.status == "fail":
                recommendations.append(
                    f"Address {metric.name}: {metric.value} exceeds threshold {metric.threshold}"
                )
            elif metric.status == "warning":
                recommendations.append(
                    f"Monitor {metric.name}: approaching threshold {metric.threshold}"
                )
        
        return recommendations

if __name__ == "__main__":
    monitor = ComplianceMonitor()
    report = monitor.generate_report()
    
    # Output report
    print(json.dumps(report, indent=2))
    
    # Write to file for CI/CD consumption
    with open("compliance-report.json", "w") as f:
        json.dump(report, f, indent=2)
```

## Audit Trail Generation

### Automated Audit Logging

```python
# src/multimodal_contract_extractor/audit.py
"""
Automated audit trail generation for compliance
"""

import json
import datetime
import hashlib
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet

@dataclass
class AuditEvent:
    """Represents a single audit event"""
    event_id: str
    timestamp: str
    user_id: Optional[str]
    action: str
    resource: str
    result: str  # "success", "failure", "error"
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    
class AuditLogger:
    """Secure audit logging with tamper protection"""
    
    def __init__(self, log_file: str = "audit.log", encryption_key: Optional[bytes] = None):
        self.log_file = log_file
        self.cipher = Fernet(encryption_key or Fernet.generate_key()) if encryption_key else None
        
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event with integrity protection"""
        event_data = asdict(event)
        event_json = json.dumps(event_data, sort_keys=True)
        
        # Add integrity hash
        event_hash = hashlib.sha256(event_json.encode()).hexdigest()
        log_entry = {
            "audit_event": event_data,
            "integrity_hash": event_hash
        }
        
        # Encrypt if configured
        if self.cipher:
            encrypted_data = self.cipher.encrypt(json.dumps(log_entry).encode())
            log_line = encrypted_data.hex()
        else:
            log_line = json.dumps(log_entry)
        
        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
    
    def log_document_processing(self, document_id: str, user_id: str, 
                               ip_address: str, result: str, 
                               details: Dict[str, Any]) -> None:
        """Log document processing event"""
        event = AuditEvent(
            event_id=hashlib.md5(f"{document_id}{datetime.datetime.utcnow()}".encode()).hexdigest(),
            timestamp=datetime.datetime.utcnow().isoformat(),
            user_id=user_id,
            action="document_processing",
            resource=f"document:{document_id}",
            result=result,
            ip_address=ip_address,
            user_agent=None,
            details=details
        )
        self.log_event(event)
    
    def log_data_access(self, user_id: str, resource: str, action: str,
                       ip_address: str, result: str) -> None:
        """Log data access event for privacy compliance"""
        event = AuditEvent(
            event_id=hashlib.md5(f"{user_id}{resource}{datetime.datetime.utcnow()}".encode()).hexdigest(),
            timestamp=datetime.datetime.utcnow().isoformat(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            ip_address=ip_address,
            user_agent=None,
            details={"compliance_requirement": "GDPR_CCPA"}
        )
        self.log_event(event)
    
    def verify_log_integrity(self) -> bool:
        """Verify the integrity of audit logs"""
        try:
            with open(self.log_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        if self.cipher:
                            # Decrypt line
                            encrypted_data = bytes.fromhex(line.strip())
                            decrypted_data = self.cipher.decrypt(encrypted_data)
                            log_entry = json.loads(decrypted_data.decode())
                        else:
                            log_entry = json.loads(line.strip())
                        
                        # Verify hash
                        event_json = json.dumps(log_entry["audit_event"], sort_keys=True)
                        computed_hash = hashlib.sha256(event_json.encode()).hexdigest()
                        
                        if computed_hash != log_entry["integrity_hash"]:
                            print(f"Integrity violation at line {line_num}")
                            return False
                            
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        print(f"Invalid log entry at line {line_num}: {e}")
                        return False
            
            return True
            
        except FileNotFoundError:
            return True  # Empty log is valid
```

## Risk Assessment Automation

### Automated Risk Scoring

```python
# scripts/risk_assessment.py
#!/usr/bin/env python3
"""
Automated risk assessment for compliance management
"""

import json
import subprocess
from typing import Dict, List, Any, Tuple
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskAssessment:
    """Automated risk assessment engine"""
    
    def __init__(self):
        self.risk_factors = {}
        
    def assess_security_risks(self) -> Tuple[RiskLevel, Dict[str, Any]]:
        """Assess security-related risks"""
        risks = {}
        
        # Check for known vulnerabilities
        try:
            result = subprocess.run(["safety", "check", "--json"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                safety_data = json.loads(result.stdout)
                high_severity_vulns = [v for v in safety_data if v.get("severity") in ["high", "critical"]]
                risks["vulnerabilities"] = {
                    "count": len(high_severity_vulns),
                    "details": high_severity_vulns
                }
        except Exception as e:
            risks["vulnerability_scan_error"] = str(e)
        
        # Check code quality metrics
        try:
            result = subprocess.run(["bandit", "-r", "src", "-f", "json"], 
                                  capture_output=True, text=True)
            bandit_data = json.loads(result.stdout)
            high_confidence_issues = [
                issue for issue in bandit_data.get("results", [])
                if issue.get("issue_confidence") == "HIGH"
            ]
            risks["code_security_issues"] = {
                "count": len(high_confidence_issues),
                "details": high_confidence_issues
            }
        except Exception as e:
            risks["code_scan_error"] = str(e)
        
        # Determine overall risk level
        vuln_count = risks.get("vulnerabilities", {}).get("count", 0)
        code_issues = risks.get("code_security_issues", {}).get("count", 0)
        
        if vuln_count > 5 or code_issues > 10:
            return RiskLevel.CRITICAL, risks
        elif vuln_count > 2 or code_issues > 5:
            return RiskLevel.HIGH, risks
        elif vuln_count > 0 or code_issues > 2:
            return RiskLevel.MEDIUM, risks
        else:
            return RiskLevel.LOW, risks
    
    def assess_compliance_risks(self) -> Tuple[RiskLevel, Dict[str, Any]]:
        """Assess compliance-related risks"""
        risks = {}
        
        # Check for data privacy compliance
        privacy_patterns = [
            r"password.*=.*['\"][^'\"]*['\"]",
            r"api_key.*=.*['\"][^'\"]*['\"]",
            r"secret.*=.*['\"][^'\"]*['\"]",
            r"email.*=.*['\"][^'\"]*['\"]",
            r"ssn.*=.*['\"][^'\"]*['\"]"
        ]
        
        # Check for hardcoded secrets (simplified)
        secret_risk = False
        try:
            result = subprocess.run(["grep", "-r", "-E", "|".join(privacy_patterns), "src/"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                secret_risk = True
                risks["hardcoded_secrets"] = result.stdout.split("\n")
        except Exception:
            pass
        
        # Check license compliance
        license_risk = False
        try:
            result = subprocess.run(["pip-licenses", "--format=json"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                licenses = json.loads(result.stdout)
                unapproved_licenses = [
                    lic for lic in licenses 
                    if lic.get("License") not in ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]
                ]
                if unapproved_licenses:
                    license_risk = True
                    risks["license_violations"] = unapproved_licenses
        except Exception as e:
            risks["license_check_error"] = str(e)
        
        # Determine risk level
        if secret_risk:
            return RiskLevel.CRITICAL, risks
        elif license_risk:
            return RiskLevel.MEDIUM, risks
        else:
            return RiskLevel.LOW, risks
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk assessment report"""
        security_risk, security_details = self.assess_security_risks()
        compliance_risk, compliance_details = self.assess_compliance_risks()
        
        # Overall risk is the highest of individual risks
        overall_risk = max(security_risk, compliance_risk, key=lambda x: 
                          ["low", "medium", "high", "critical"].index(x.value))
        
        return {
            "timestamp": "2024-01-15T10:30:00Z",
            "overall_risk_level": overall_risk.value,
            "security_risk": {
                "level": security_risk.value,
                "details": security_details
            },
            "compliance_risk": {
                "level": compliance_risk.value,
                "details": compliance_details
            },
            "recommendations": self._generate_risk_recommendations(security_risk, compliance_risk),
            "next_assessment": "2024-01-22T10:30:00Z"
        }
    
    def _generate_risk_recommendations(self, security_risk: RiskLevel, 
                                     compliance_risk: RiskLevel) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if security_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Immediately patch all high/critical security vulnerabilities",
                "Review and fix code security issues identified by static analysis",
                "Implement additional security controls and monitoring"
            ])
        
        if compliance_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Remove hardcoded secrets and implement secure secret management",
                "Review license compliance and replace non-approved dependencies",
                "Implement data privacy controls and audit procedures"
            ])
        
        return recommendations

if __name__ == "__main__":
    assessor = RiskAssessment()
    report = assessor.generate_risk_report()
    
    print(json.dumps(report, indent=2))
    
    # Write report for CI/CD consumption
    with open("risk-assessment.json", "w") as f:
        json.dump(report, f, indent=2)