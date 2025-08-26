#!/usr/bin/env python3
"""
Comprehensive Security Scanning Suite
Advanced security analysis for the autonomous SDLC system with
vulnerability detection, code analysis, and compliance validation.
"""

import os
import re
import ast
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto


class VulnerabilityLevel(Enum):
    """Vulnerability severity levels"""
    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class SecurityCategory(Enum):
    """Security vulnerability categories"""
    INJECTION = auto()
    BROKEN_AUTHENTICATION = auto()
    SENSITIVE_DATA_EXPOSURE = auto()
    XML_EXTERNAL_ENTITIES = auto()
    BROKEN_ACCESS_CONTROL = auto()
    SECURITY_MISCONFIGURATION = auto()
    XSS = auto()
    INSECURE_DESERIALIZATION = auto()
    USING_COMPONENTS_WITH_KNOWN_VULNERABILITIES = auto()
    INSUFFICIENT_LOGGING = auto()
    CRYPTOGRAPHIC_ISSUES = auto()
    CODE_QUALITY = auto()


@dataclass
class SecurityFinding:
    """Security finding/vulnerability"""
    finding_id: str
    title: str
    description: str
    severity: VulnerabilityLevel
    category: SecurityCategory
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cve_references: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityReport:
    """Comprehensive security report"""
    scan_id: str
    timestamp: datetime
    total_files_scanned: int
    total_findings: int
    findings_by_severity: Dict[VulnerabilityLevel, int]
    findings_by_category: Dict[SecurityCategory, int]
    findings: List[SecurityFinding]
    overall_security_score: float
    compliance_status: Dict[str, bool]
    recommendations: List[str]


class SecurityPatternAnalyzer:
    """Advanced security pattern analyzer"""
    
    def __init__(self):
        # Vulnerability patterns
        self.vulnerability_patterns = {
            # SQL Injection patterns
            'sql_injection': [
                r'(\bexecute\s*\(.*\+.*\))',
                r'(\bquery\s*\(.*\%.*\))',
                r'(cursor\.execute\s*\(.*\+.*\))',
                r'(\bSELECT.*\+.*FROM)',
                r'(\bINSERT.*\+.*VALUES)',
                r'(\bUPDATE.*\+.*SET)',
                r'(\bDELETE.*\+.*WHERE)',
            ],
            
            # Command Injection patterns
            'command_injection': [
                r'(os\.system\s*\(.*\+)',
                r'(subprocess\.call\s*\(.*\+)',
                r'(subprocess\.run\s*\(.*\+)',
                r'(os\.popen\s*\(.*\+)',
                r'(eval\s*\(.*\+)',
                r'(exec\s*\(.*\+)',
            ],
            
            # Path Traversal patterns
            'path_traversal': [
                r'(open\s*\(.*\.\..*\))',
                r'(file\s*\(.*\.\..*\))',
                r'(readlines\s*\(.*\.\..*\))',
                r'(\.\./|\.\.\\\)',
            ],
            
            # Insecure Cryptography
            'weak_crypto': [
                r'(\bMD5\b)',
                r'(\bSHA1\b)',
                r'(\bDES\b)',
                r'(\bRC4\b)',
                r'(hashlib\.md5)',
                r'(hashlib\.sha1)',
                r'(random\.random)',
            ],
            
            # Hard-coded secrets
            'hardcoded_secrets': [
                r'(password\s*=\s*["\'][^"\']{3,}["\'])',
                r'(api_key\s*=\s*["\'][^"\']{10,}["\'])',
                r'(secret\s*=\s*["\'][^"\']{8,}["\'])',
                r'(token\s*=\s*["\'][^"\']{20,}["\'])',
                r'(key\s*=\s*["\'][^"\']{16,}["\'])',
            ],
            
            # Insecure Network Communication
            'insecure_network': [
                r'(http://)',
                r'(urllib\.request\.urlopen\s*\(\s*["\']http://)',
                r'(requests\.get\s*\(\s*["\']http://)',
                r'(ssl\.CERT_NONE)',
                r'(verify=False)',
            ],
            
            # Unsafe Deserialization
            'unsafe_deserialization': [
                r'(pickle\.loads)',
                r'(cPickle\.loads)',
                r'(marshal\.loads)',
                r'(eval\s*\(.*input)',
            ],
            
            # Information Disclosure
            'info_disclosure': [
                r'(print\s*\(.*password)',
                r'(print\s*\(.*secret)',
                r'(print\s*\(.*token)',
                r'(logging\..*password)',
                r'(logging\..*secret)',
                r'(traceback\.print_exc)',
            ],
        }
        
        # Secure coding patterns (good practices)
        self.secure_patterns = {
            'parameterized_queries': [
                r'(cursor\.execute\s*\(.*\?\s*,)',
                r'(cursor\.execute\s*\(.*%s.*,)',
            ],
            'input_validation': [
                r'(re\.match\s*\()',
                r'(isinstance\s*\()',
                r'(len\s*\(.*\)\s*[<>]=?\s*\d+)',
            ],
            'secure_random': [
                r'(secrets\.token_)',
                r'(os\.urandom)',
                r'(random\.SystemRandom)',
            ],
            'secure_crypto': [
                r'(hashlib\.sha256)',
                r'(hashlib\.sha512)',
                r'(cryptography\.)',
                r'(Fernet\.)',
            ],
        }
    
    def analyze_file(self, file_path: Path) -> List[SecurityFinding]:
        """Analyze a single file for security vulnerabilities"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based analysis
            for vuln_type, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        finding = self._create_finding(
                            vuln_type, match, file_path, line_num, line_content
                        )
                        findings.append(finding)
            
            # AST-based analysis for Python files
            if file_path.suffix == '.py':
                ast_findings = self._analyze_ast(file_path, content)
                findings.extend(ast_findings)
            
        except Exception as e:
            # Create finding for files that can't be analyzed
            finding = SecurityFinding(
                finding_id=f"scan_error_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                title="File Analysis Error",
                description=f"Could not analyze file: {str(e)}",
                severity=VulnerabilityLevel.INFO,
                category=SecurityCategory.CODE_QUALITY,
                file_path=str(file_path),
                line_number=0,
                code_snippet="",
                recommendation="Ensure file is properly formatted and accessible"
            )
            findings.append(finding)
        
        return findings
    
    def _create_finding(self, vuln_type: str, match, file_path: Path, 
                       line_num: int, line_content: str) -> SecurityFinding:
        """Create a security finding from a pattern match"""
        finding_id = hashlib.md5(f"{file_path}:{line_num}:{match.group()}".encode()).hexdigest()[:12]
        
        # Map vulnerability types to categories and severities
        vuln_mapping = {
            'sql_injection': (SecurityCategory.INJECTION, VulnerabilityLevel.HIGH),
            'command_injection': (SecurityCategory.INJECTION, VulnerabilityLevel.CRITICAL),
            'path_traversal': (SecurityCategory.BROKEN_ACCESS_CONTROL, VulnerabilityLevel.HIGH),
            'weak_crypto': (SecurityCategory.CRYPTOGRAPHIC_ISSUES, VulnerabilityLevel.MEDIUM),
            'hardcoded_secrets': (SecurityCategory.SENSITIVE_DATA_EXPOSURE, VulnerabilityLevel.HIGH),
            'insecure_network': (SecurityCategory.SECURITY_MISCONFIGURATION, VulnerabilityLevel.MEDIUM),
            'unsafe_deserialization': (SecurityCategory.INSECURE_DESERIALIZATION, VulnerabilityLevel.HIGH),
            'info_disclosure': (SecurityCategory.SENSITIVE_DATA_EXPOSURE, VulnerabilityLevel.MEDIUM),
        }
        
        category, severity = vuln_mapping.get(vuln_type, (SecurityCategory.CODE_QUALITY, VulnerabilityLevel.LOW))
        
        # Generate descriptions and recommendations
        descriptions = {
            'sql_injection': "Potential SQL injection vulnerability detected",
            'command_injection': "Potential command injection vulnerability detected",
            'path_traversal': "Potential path traversal vulnerability detected",
            'weak_crypto': "Weak cryptographic algorithm or hash function detected",
            'hardcoded_secrets': "Hard-coded sensitive information detected",
            'insecure_network': "Insecure network communication detected",
            'unsafe_deserialization': "Potentially unsafe deserialization detected",
            'info_disclosure': "Potential information disclosure detected",
        }
        
        recommendations = {
            'sql_injection': "Use parameterized queries or prepared statements",
            'command_injection': "Use subprocess with shell=False or validate input strictly",
            'path_traversal': "Validate and sanitize file paths, use os.path.join()",
            'weak_crypto': "Use strong cryptographic algorithms like SHA-256, SHA-512, or AES",
            'hardcoded_secrets': "Store sensitive information in environment variables or secure vaults",
            'insecure_network': "Use HTTPS/TLS for all network communications",
            'unsafe_deserialization': "Use safe serialization formats like JSON, validate input data",
            'info_disclosure': "Avoid logging or printing sensitive information",
        }
        
        return SecurityFinding(
            finding_id=finding_id,
            title=vuln_type.replace('_', ' ').title(),
            description=descriptions.get(vuln_type, f"{vuln_type} vulnerability detected"),
            severity=severity,
            category=category,
            file_path=str(file_path),
            line_number=line_num,
            code_snippet=line_content.strip(),
            recommendation=recommendations.get(vuln_type, "Review and remediate this security issue"),
            confidence=0.8  # Pattern-based detection confidence
        )
    
    def _analyze_ast(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """Analyze Python AST for security issues"""
        findings = []
        
        try:
            tree = ast.parse(content)
            
            # Analyze function calls for security issues
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    finding = self._analyze_function_call(node, file_path, content)
                    if finding:
                        findings.append(finding)
                
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    finding = self._analyze_import(node, file_path, content)
                    if finding:
                        findings.append(finding)
        
        except SyntaxError as e:
            # Create finding for syntax errors
            finding = SecurityFinding(
                finding_id=f"syntax_error_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                title="Syntax Error",
                description=f"Syntax error in Python file: {str(e)}",
                severity=VulnerabilityLevel.LOW,
                category=SecurityCategory.CODE_QUALITY,
                file_path=str(file_path),
                line_number=getattr(e, 'lineno', 0),
                code_snippet="",
                recommendation="Fix syntax errors in the code"
            )
            findings.append(finding)
        
        return findings
    
    def _analyze_function_call(self, node: ast.Call, file_path: Path, content: str) -> Optional[SecurityFinding]:
        """Analyze function calls for security issues"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check for dangerous functions
            dangerous_functions = {
                'eval': (VulnerabilityLevel.CRITICAL, "Code injection via eval()"),
                'exec': (VulnerabilityLevel.CRITICAL, "Code injection via exec()"),
                'input': (VulnerabilityLevel.MEDIUM, "Potential code injection via input()"),
                'compile': (VulnerabilityLevel.HIGH, "Dynamic code compilation"),
            }
            
            if func_name in dangerous_functions:
                severity, description = dangerous_functions[func_name]
                
                return SecurityFinding(
                    finding_id=f"ast_{func_name}_{node.lineno}",
                    title=f"Dangerous Function: {func_name}()",
                    description=description,
                    severity=severity,
                    category=SecurityCategory.INJECTION,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    code_snippet=self._get_line_from_content(content, node.lineno),
                    recommendation=f"Avoid using {func_name}() or ensure input is properly validated",
                    confidence=0.9
                )
        
        return None
    
    def _analyze_import(self, node, file_path: Path, content: str) -> Optional[SecurityFinding]:
        """Analyze imports for potentially insecure modules"""
        insecure_modules = {
            'pickle': (VulnerabilityLevel.MEDIUM, "Pickle can execute arbitrary code during deserialization"),
            'cPickle': (VulnerabilityLevel.MEDIUM, "cPickle can execute arbitrary code"),
            'marshal': (VulnerabilityLevel.MEDIUM, "Marshal can be unsafe for untrusted data"),
            'shelve': (VulnerabilityLevel.LOW, "Shelve uses pickle internally"),
        }
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in insecure_modules:
                    severity, description = insecure_modules[alias.name]
                    
                    return SecurityFinding(
                        finding_id=f"import_{alias.name}_{node.lineno}",
                        title=f"Potentially Insecure Import: {alias.name}",
                        description=description,
                        severity=severity,
                        category=SecurityCategory.INSECURE_DESERIALIZATION,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        code_snippet=self._get_line_from_content(content, node.lineno),
                        recommendation=f"Use safer alternatives to {alias.name} or ensure input is trusted",
                        confidence=0.7
                    )
        
        elif isinstance(node, ast.ImportFrom) and node.module in insecure_modules:
            severity, description = insecure_modules[node.module]
            
            return SecurityFinding(
                finding_id=f"import_{node.module}_{node.lineno}",
                title=f"Potentially Insecure Import: {node.module}",
                description=description,
                severity=severity,
                category=SecurityCategory.INSECURE_DESERIALIZATION,
                file_path=str(file_path),
                line_number=node.lineno,
                code_snippet=self._get_line_from_content(content, node.lineno),
                recommendation=f"Use safer alternatives to {node.module} or ensure input is trusted",
                confidence=0.7
            )
        
        return None
    
    def _get_line_from_content(self, content: str, line_num: int) -> str:
        """Get a specific line from content"""
        lines = content.split('\n')
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1].strip()
        return ""


class ComplianceChecker:
    """Security compliance checker"""
    
    def __init__(self):
        self.compliance_frameworks = {
            'OWASP_TOP_10': self._check_owasp_top_10,
            'NIST_CYBERSECURITY': self._check_nist_cybersecurity,
            'ISO_27001': self._check_iso_27001,
            'SOC_2': self._check_soc_2,
        }
    
    def check_compliance(self, findings: List[SecurityFinding]) -> Dict[str, bool]:
        """Check compliance against various frameworks"""
        compliance_results = {}
        
        for framework, check_function in self.compliance_frameworks.items():
            compliance_results[framework] = check_function(findings)
        
        return compliance_results
    
    def _check_owasp_top_10(self, findings: List[SecurityFinding]) -> bool:
        """Check OWASP Top 10 compliance"""
        critical_categories = [
            SecurityCategory.INJECTION,
            SecurityCategory.BROKEN_AUTHENTICATION,
            SecurityCategory.SENSITIVE_DATA_EXPOSURE,
            SecurityCategory.BROKEN_ACCESS_CONTROL,
            SecurityCategory.SECURITY_MISCONFIGURATION,
            SecurityCategory.XSS,
            SecurityCategory.INSECURE_DESERIALIZATION,
        ]
        
        # Check for critical/high severity findings in OWASP categories
        critical_findings = [
            f for f in findings 
            if f.severity in [VulnerabilityLevel.CRITICAL, VulnerabilityLevel.HIGH]
            and f.category in critical_categories
        ]
        
        return len(critical_findings) == 0
    
    def _check_nist_cybersecurity(self, findings: List[SecurityFinding]) -> bool:
        """Check NIST Cybersecurity Framework compliance"""
        # Basic compliance check - no critical vulnerabilities
        critical_findings = [
            f for f in findings 
            if f.severity == VulnerabilityLevel.CRITICAL
        ]
        
        return len(critical_findings) == 0
    
    def _check_iso_27001(self, findings: List[SecurityFinding]) -> bool:
        """Check ISO 27001 compliance"""
        # Check for information security controls
        info_security_categories = [
            SecurityCategory.SENSITIVE_DATA_EXPOSURE,
            SecurityCategory.CRYPTOGRAPHIC_ISSUES,
            SecurityCategory.INSUFFICIENT_LOGGING,
        ]
        
        high_findings = [
            f for f in findings 
            if f.severity in [VulnerabilityLevel.HIGH, VulnerabilityLevel.CRITICAL]
            and f.category in info_security_categories
        ]
        
        return len(high_findings) == 0
    
    def _check_soc_2(self, findings: List[SecurityFinding]) -> bool:
        """Check SOC 2 compliance"""
        # Security, availability, and confidentiality controls
        soc2_categories = [
            SecurityCategory.BROKEN_ACCESS_CONTROL,
            SecurityCategory.SENSITIVE_DATA_EXPOSURE,
            SecurityCategory.SECURITY_MISCONFIGURATION,
        ]
        
        high_findings = [
            f for f in findings 
            if f.severity in [VulnerabilityLevel.HIGH, VulnerabilityLevel.CRITICAL]
            and f.category in soc2_categories
        ]
        
        return len(high_findings) <= 2  # Allow up to 2 high findings


class SecurityScanner:
    """Main security scanner orchestrator"""
    
    def __init__(self, scan_directory: str = "src"):
        self.scan_directory = Path(scan_directory)
        self.pattern_analyzer = SecurityPatternAnalyzer()
        self.compliance_checker = ComplianceChecker()
        
        # File extensions to scan
        self.scan_extensions = {'.py', '.js', '.ts', '.java', '.php', '.rb', '.go', '.rs'}
        
        # Files to exclude from scanning
        self.exclude_patterns = {
            '__pycache__',
            '.git',
            '.pytest_cache',
            'node_modules',
            '.venv',
            'venv',
            '.env'
        }
    
    def scan_project(self) -> SecurityReport:
        """Perform comprehensive security scan of directory"""
        print(f"🔍 Starting comprehensive security scan of {self.scan_directory}")
        print("=" * 70)
        
        scan_id = hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        start_time = datetime.utcnow()
        
        all_findings = []
        files_scanned = 0
        
        # Scan all relevant files
        for file_path in self._get_scannable_files():
            print(f"Scanning: {file_path}")
            
            findings = self.pattern_analyzer.analyze_file(file_path)
            all_findings.extend(findings)
            files_scanned += 1
        
        # Calculate statistics
        findings_by_severity = {level: 0 for level in VulnerabilityLevel}
        findings_by_category = {category: 0 for category in SecurityCategory}
        
        for finding in all_findings:
            findings_by_severity[finding.severity] += 1
            findings_by_category[finding.category] += 1
        
        # Calculate security score
        security_score = self._calculate_security_score(all_findings, files_scanned)
        
        # Check compliance
        compliance_status = self.compliance_checker.check_compliance(all_findings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_findings)
        
        report = SecurityReport(
            scan_id=scan_id,
            timestamp=start_time,
            total_files_scanned=files_scanned,
            total_findings=len(all_findings),
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category,
            findings=all_findings,
            overall_security_score=security_score,
            compliance_status=compliance_status,
            recommendations=recommendations
        )
        
        return report
    
    def _get_scannable_files(self) -> List[Path]:
        """Get list of files to scan"""
        files = []
        
        def should_include_path(path: Path) -> bool:
            # Check if any part of the path matches exclude patterns
            for part in path.parts:
                if any(exclude in part for exclude in self.exclude_patterns):
                    return False
            return True
        
        for file_path in self.scan_directory.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in self.scan_extensions and
                should_include_path(file_path)):
                files.append(file_path)
        
        return files
    
    def _calculate_security_score(self, findings: List[SecurityFinding], files_scanned: int) -> float:
        """Calculate overall security score (0-100)"""
        if files_scanned == 0:
            return 100.0
        
        # Weight findings by severity
        severity_weights = {
            VulnerabilityLevel.CRITICAL: -50,
            VulnerabilityLevel.HIGH: -20,
            VulnerabilityLevel.MEDIUM: -10,
            VulnerabilityLevel.LOW: -5,
            VulnerabilityLevel.INFO: -1,
        }
        
        total_penalty = sum(severity_weights[finding.severity] for finding in findings)
        
        # Base score starts at 100
        base_score = 100.0
        
        # Apply penalties
        security_score = base_score + total_penalty
        
        # Normalize to 0-100 range
        security_score = max(0.0, min(100.0, security_score))
        
        return security_score
    
    def _generate_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Count findings by category
        category_counts = {}
        for finding in findings:
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1
        
        # Generate recommendations based on most common issues
        if category_counts.get(SecurityCategory.INJECTION, 0) > 0:
            recommendations.append(
                "Implement input validation and use parameterized queries to prevent injection attacks"
            )
        
        if category_counts.get(SecurityCategory.SENSITIVE_DATA_EXPOSURE, 0) > 0:
            recommendations.append(
                "Remove hard-coded secrets and implement secure credential management"
            )
        
        if category_counts.get(SecurityCategory.CRYPTOGRAPHIC_ISSUES, 0) > 0:
            recommendations.append(
                "Upgrade to strong cryptographic algorithms and secure random number generation"
            )
        
        if category_counts.get(SecurityCategory.INSECURE_DESERIALIZATION, 0) > 0:
            recommendations.append(
                "Use safe serialization formats and validate all deserialized data"
            )
        
        if category_counts.get(SecurityCategory.SECURITY_MISCONFIGURATION, 0) > 0:
            recommendations.append(
                "Review and harden security configurations, enable TLS/HTTPS everywhere"
            )
        
        # General recommendations
        if len(findings) > 0:
            recommendations.extend([
                "Implement a Security Development Lifecycle (SDL)",
                "Regular security training for development team",
                "Automated security scanning in CI/CD pipeline",
                "Regular penetration testing and security audits"
            ])
        
        return recommendations[:10]  # Limit to top 10 recommendations


def generate_security_report(report: SecurityReport):
    """Generate human-readable security report"""
    print("\n" + "=" * 70)
    print(f"🔒 COMPREHENSIVE SECURITY SCAN REPORT")
    print("=" * 70)
    
    print(f"\n📊 SCAN SUMMARY")
    print(f"Scan ID: {report.scan_id}")
    print(f"Timestamp: {report.timestamp.isoformat()}")
    print(f"Files Scanned: {report.total_files_scanned}")
    print(f"Total Findings: {report.total_findings}")
    print(f"Overall Security Score: {report.overall_security_score:.1f}/100")
    
    print(f"\n📈 FINDINGS BY SEVERITY")
    for severity, count in report.findings_by_severity.items():
        if count > 0:
            emoji = {
                VulnerabilityLevel.CRITICAL: "🚨",
                VulnerabilityLevel.HIGH: "🔴", 
                VulnerabilityLevel.MEDIUM: "🟡",
                VulnerabilityLevel.LOW: "🟢",
                VulnerabilityLevel.INFO: "ℹ️"
            }
            print(f"{emoji[severity]} {severity.name}: {count}")
    
    print(f"\n🏷️ FINDINGS BY CATEGORY")
    for category, count in report.findings_by_category.items():
        if count > 0:
            print(f"• {category.name.replace('_', ' ')}: {count}")
    
    print(f"\n📋 COMPLIANCE STATUS")
    for framework, compliant in report.compliance_status.items():
        status = "✅ COMPLIANT" if compliant else "❌ NON-COMPLIANT"
        print(f"{framework.replace('_', ' ')}: {status}")
    
    if report.findings:
        print(f"\n🔍 TOP SECURITY FINDINGS")
        
        # Sort by severity and show top 10
        sorted_findings = sorted(report.findings, 
                               key=lambda f: f.severity.value, 
                               reverse=True)[:10]
        
        for i, finding in enumerate(sorted_findings, 1):
            print(f"\n{i}. {finding.title}")
            print(f"   Severity: {finding.severity.name}")
            print(f"   File: {finding.file_path}:{finding.line_number}")
            print(f"   Description: {finding.description}")
            print(f"   Code: {finding.code_snippet}")
            print(f"   Recommendation: {finding.recommendation}")
    
    print(f"\n💡 SECURITY RECOMMENDATIONS")
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"{i}. {recommendation}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL SECURITY ASSESSMENT")
    if report.overall_security_score >= 90:
        print("✅ EXCELLENT - Minimal security issues detected")
    elif report.overall_security_score >= 70:
        print("⚠️  GOOD - Some security improvements recommended")
    elif report.overall_security_score >= 50:
        print("🟡 MODERATE - Several security issues need attention")
    else:
        print("🚨 POOR - Critical security issues require immediate attention")
    
    print("=" * 70)


def save_security_report_json(report: SecurityReport, filename: str = None):
    """Save security report to JSON file"""
    if filename is None:
        filename = f"security_scan_report_{report.scan_id}.json"
    
    # Convert report to JSON-serializable format
    report_data = {
        'scan_id': report.scan_id,
        'timestamp': report.timestamp.isoformat(),
        'total_files_scanned': report.total_files_scanned,
        'total_findings': report.total_findings,
        'overall_security_score': report.overall_security_score,
        'findings_by_severity': {k.name: v for k, v in report.findings_by_severity.items()},
        'findings_by_category': {k.name: v for k, v in report.findings_by_category.items()},
        'compliance_status': report.compliance_status,
        'recommendations': report.recommendations,
        'findings': [
            {
                'finding_id': f.finding_id,
                'title': f.title,
                'description': f.description,
                'severity': f.severity.name,
                'category': f.category.name,
                'file_path': f.file_path,
                'line_number': f.line_number,
                'code_snippet': f.code_snippet,
                'recommendation': f.recommendation,
                'confidence': f.confidence,
                'cve_references': f.cve_references,
                'metadata': f.metadata
            }
            for f in report.findings
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"📄 Security report saved to: {filename}")


def main():
    """Main security scanning execution"""
    print("🛡️  Comprehensive Security Scanner for Autonomous SDLC v6.0")
    print("Advanced vulnerability detection and compliance validation\n")
    
    # Initialize scanner
    scanner = SecurityScanner("src")
    
    # Perform security scan
    start_time = datetime.utcnow()
    report = scanner.scan_project()
    scan_duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Generate reports
    generate_security_report(report)
    save_security_report_json(report)
    
    print(f"\n⏱️  Security scan completed in {scan_duration:.2f} seconds")
    
    # Return exit code based on security score
    if report.overall_security_score >= 80:
        print("🎉 SECURITY SCAN PASSED")
        return 0
    elif report.overall_security_score >= 60:
        print("⚠️  SECURITY SCAN PASSED WITH WARNINGS")  
        return 1
    else:
        print("❌ SECURITY SCAN FAILED - Critical issues detected")
        return 2


if __name__ == "__main__":
    sys.exit(main())