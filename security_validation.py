#!/usr/bin/env python3
"""Security validation script for the multimodal contract extractor."""

import os
import sys
import re
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class SecurityValidator:
    """Validates security aspects of the codebase."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.src_path = self.root_path / "src"
        self.issues = []
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all security validations."""
        print("🔒 Running Security Validation...")
        
        results = {
            "hardcoded_secrets": self.check_hardcoded_secrets(),
            "unsafe_functions": self.check_unsafe_functions(),
            "sql_injection": self.check_sql_injection_risks(),
            "file_permissions": self.check_file_permissions(),
            "import_security": self.check_import_security(),
            "input_validation": self.check_input_validation(),
            "crypto_usage": self.check_crypto_usage(),
            "total_issues": len(self.issues)
        }
        
        return results
    
    def check_hardcoded_secrets(self) -> List[Dict[str, str]]:
        """Check for hardcoded secrets and credentials."""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded_password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "hardcoded_api_key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded_secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "hardcoded_token"),
            (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', "potential_base64_secret"),
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip test files and documentation examples
                        if "test" not in str(py_file) and "example" not in match.group():
                            issues.append({
                                "file": str(py_file),
                                "line": content[:match.start()].count('\n') + 1,
                                "type": issue_type,
                                "severity": "high"
                            })
                            self.issues.append(f"{issue_type} in {py_file}")
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
                
        return issues
    
    def check_unsafe_functions(self) -> List[Dict[str, str]]:
        """Check for usage of unsafe functions."""
        unsafe_patterns = [
            (r'eval\s*\(', "eval_usage"),
            (r'exec\s*\(', "exec_usage"),
            (r'__import__\s*\(', "dynamic_import"),
            (r'subprocess\.call\(.*shell\s*=\s*True', "shell_injection"),
            (r'os\.system\s*\(', "os_system_usage"),
            (r'pickle\.loads?\s*\(', "pickle_usage"),
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in unsafe_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        issues.append({
                            "file": str(py_file),
                            "line": content[:match.start()].count('\n') + 1,
                            "type": issue_type,
                            "severity": "high" if issue_type in ["eval_usage", "exec_usage"] else "medium"
                        })
                        self.issues.append(f"{issue_type} in {py_file}")
            except Exception:
                continue
                
        return issues
    
    def check_sql_injection_risks(self) -> List[Dict[str, str]]:
        """Check for potential SQL injection vulnerabilities."""
        sql_patterns = [
            (r'execute\s*\(\s*["\'][^"\']*\%', "string_formatting_sql"),
            (r'execute\s*\(\s*f["\']', "f_string_sql"),
            (r'query\s*\(\s*["\'][^"\']*\%', "string_formatting_query"),
            (r'sql\s*=\s*["\'][^"\']*\%', "string_formatting_sql_var"),
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in sql_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        issues.append({
                            "file": str(py_file),
                            "line": content[:match.start()].count('\n') + 1,
                            "type": issue_type,
                            "severity": "high"
                        })
                        self.issues.append(f"{issue_type} in {py_file}")
            except Exception:
                continue
                
        return issues
    
    def check_file_permissions(self) -> List[Dict[str, str]]:
        """Check for overly permissive file operations."""
        permission_patterns = [
            (r'open\s*\([^)]*["\']w["\'][^)]*\)', "write_file_operation"),
            (r'chmod\s*\([^)]*0o7', "overly_permissive_chmod"),
            (r'tempfile\..*\(.*mode\s*=\s*["\'].*7', "permissive_temp_file"),
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in permission_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Only flag if not using secure patterns
                        if "0o600" not in match.group() and "mode=0o600" not in match.group():
                            issues.append({
                                "file": str(py_file),
                                "line": content[:match.start()].count('\n') + 1,
                                "type": issue_type,
                                "severity": "medium"
                            })
            except Exception:
                continue
                
        return issues
    
    def check_import_security(self) -> List[Dict[str, str]]:
        """Check for potentially dangerous imports."""
        dangerous_imports = [
            "imp",  # Deprecated import mechanism
            "importlib.util",  # Dynamic imports
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if alias.name in dangerous_imports:
                                        issues.append({
                                            "file": str(py_file),
                                            "line": node.lineno,
                                            "type": f"dangerous_import_{alias.name}",
                                            "severity": "medium"
                                        })
                            elif isinstance(node, ast.ImportFrom):
                                if node.module in dangerous_imports:
                                    issues.append({
                                        "file": str(py_file),
                                        "line": node.lineno,
                                        "type": f"dangerous_import_{node.module}",
                                        "severity": "medium"
                                    })
                    except SyntaxError:
                        continue
            except Exception:
                continue
                
        return issues
    
    def check_input_validation(self) -> List[Dict[str, str]]:
        """Check for missing input validation."""
        issues = []
        
        # Look for functions that accept external input
        validation_patterns = [
            (r'def\s+\w+\([^)]*file_path[^)]*\):', "file_path_param"),
            (r'def\s+\w+\([^)]*user_input[^)]*\):', "user_input_param"),
            (r'def\s+\w+\([^)]*url[^)]*\):', "url_param"),
        ]
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in validation_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Check if validation exists in the function
                        func_start = match.start()
                        # Look for the next function or end of file
                        next_func = re.search(r'\ndef\s+', content[func_start + 100:])
                        func_end = func_start + 100 + next_func.start() if next_func else len(content)
                        func_body = content[func_start:func_end]
                        
                        # Check for validation patterns
                        has_validation = any([
                            'validate' in func_body.lower(),
                            'check' in func_body.lower(),
                            'sanitize' in func_body.lower(),
                            'isinstance' in func_body,
                            'raise ValueError' in func_body,
                            'raise TypeError' in func_body,
                        ])
                        
                        if not has_validation and 'test_' not in str(py_file):
                            issues.append({
                                "file": str(py_file),
                                "line": content[:match.start()].count('\n') + 1,
                                "type": f"missing_validation_{issue_type}",
                                "severity": "medium"
                            })
            except Exception:
                continue
                
        return issues
    
    def check_crypto_usage(self) -> List[Dict[str, str]]:
        """Check for weak cryptographic practices."""
        crypto_patterns = [
            (r'md5\s*\(', "weak_hash_md5"),
            (r'sha1\s*\(', "weak_hash_sha1"),
            (r'random\.random\s*\(', "weak_random"),
            (r'DES', "weak_cipher_des"),
            (r'RC4', "weak_cipher_rc4"),
        ]
        
        issues = []
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, issue_type in crypto_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        issues.append({
                            "file": str(py_file),
                            "line": content[:match.start()].count('\n') + 1,
                            "type": issue_type,
                            "severity": "high" if "weak_hash" in issue_type else "medium"
                        })
                        self.issues.append(f"{issue_type} in {py_file}")
            except Exception:
                continue
                
        return issues
    
    def print_report(self, results: Dict[str, Any]):
        """Print security validation report."""
        print("\n🔒 SECURITY VALIDATION REPORT")
        print("=" * 50)
        
        total_issues = results["total_issues"]
        
        if total_issues == 0:
            print("✅ No security issues found!")
        else:
            print(f"⚠️  Found {total_issues} potential security issues:")
            
            for category, issues in results.items():
                if category != "total_issues" and issues:
                    print(f"\n{category.replace('_', ' ').title()}:")
                    for issue in issues[:5]:  # Show first 5 issues per category
                        severity_icon = "🔴" if issue["severity"] == "high" else "🟡"
                        print(f"  {severity_icon} {issue['type']} in {issue['file']}:{issue['line']}")
                    
                    if len(issues) > 5:
                        print(f"  ... and {len(issues) - 5} more issues")
        
        # Security score
        max_score = 100
        deduction = min(total_issues * 2, 50)  # Max 50% deduction
        security_score = max_score - deduction
        
        print(f"\n🛡️  Security Score: {security_score}/100")
        
        if security_score >= 90:
            print("✅ Excellent security posture")
        elif security_score >= 70:
            print("⚠️  Good security, minor issues to address")
        elif security_score >= 50:
            print("🟡 Fair security, several issues need attention")
        else:
            print("🔴 Poor security, immediate attention required")
            
        return security_score


def main():
    """Run security validation."""
    validator = SecurityValidator()
    results = validator.validate_all()
    score = validator.print_report(results)
    
    # Exit with error code if security score is too low
    if score < 70:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()