"""
Policy as Code framework for automated compliance checking.
Implements governance policies as executable code with automated enforcement.
"""

import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PolicySeverity(Enum):
    """Policy violation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PolicyCategory(Enum):
    """Policy categories for organization."""
    SECURITY = "security"
    COMPLIANCE = "compliance"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    LICENSING = "licensing"
    DEPENDENCY = "dependency"
    DEPLOYMENT = "deployment"


@dataclass
class PolicyViolation:
    """Represents a policy violation."""
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    category: PolicyCategory
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        return data


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    policy_id: str
    passed: bool
    violations: List[PolicyViolation]
    execution_time: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'policy_id': self.policy_id,
            'passed': self.passed,
            'violations': [v.to_dict() for v in self.violations],
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }


class Policy:
    """Base class for governance policies."""

    def __init__(
        self,
        policy_id: str,
        name: str,
        description: str,
        category: PolicyCategory,
        severity: PolicySeverity = PolicySeverity.WARNING,
        enabled: bool = True
    ):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity
        self.enabled = enabled
        self.logger = logging.getLogger(f"{__name__}.{policy_id}")

    def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        """Evaluate the policy against the given context."""
        if not self.enabled:
            return PolicyResult(
                policy_id=self.policy_id,
                passed=True,
                violations=[],
                execution_time=0.0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        start_time = datetime.now()
        violations = []

        try:
            violations = self._check_policy(context)
        except Exception as e:
            self.logger.error(f"Policy evaluation failed: {e}")
            violations = [PolicyViolation(
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.ERROR,
                category=self.category,
                message=f"Policy evaluation failed: {str(e)}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )]

        execution_time = (datetime.now() - start_time).total_seconds()

        return PolicyResult(
            policy_id=self.policy_id,
            passed=len(violations) == 0,
            violations=violations,
            execution_time=execution_time,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _check_policy(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        """Override this method to implement policy logic."""
        raise NotImplementedError("Subclasses must implement _check_policy")


class SecurityPolicy(Policy):
    """Security-related governance policies."""

    def __init__(self, policy_id: str, name: str, description: str, **kwargs):
        super().__init__(
            policy_id=policy_id,
            name=name,
            description=description,
            category=PolicyCategory.SECURITY,
            severity=PolicySeverity.ERROR,
            **kwargs
        )


class CompliancePolicy(Policy):
    """Compliance-related governance policies."""

    def __init__(self, policy_id: str, name: str, description: str, **kwargs):
        super().__init__(
            policy_id=policy_id,
            name=name,
            description=description,
            category=PolicyCategory.COMPLIANCE,
            severity=PolicySeverity.WARNING,
            **kwargs
        )


# Specific Policy Implementations

class NoSecretsInCodePolicy(SecurityPolicy):
    """Policy to prevent secrets in source code."""

    def __init__(self):
        super().__init__(
            policy_id="security.no_secrets_in_code",
            name="No Secrets in Code",
            description="Source code must not contain hardcoded secrets, API keys, or passwords"
        )

        # Common secret patterns
        self.secret_patterns = [
            (r'(?i)api[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9]{20,}', 'API Key'),
            (r'(?i)secret[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9]{20,}', 'Secret Key'),
            (r'(?i)password["\'\s]*[:=]["\'\s]*[a-zA-Z0-9]{8,}', 'Password'),
            (r'(?i)token["\'\s]*[:=]["\'\s]*[a-zA-Z0-9]{20,}', 'Token'),
            (r'-----BEGIN PRIVATE KEY-----', 'Private Key'),
            (r'(?i)aws[_-]?access[_-]?key[_-]?id["\'\s]*[:=]["\'\s]*[A-Z0-9]{20}', 'AWS Access Key'),
            (r'(?i)aws[_-]?secret[_-]?access[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9+/]{40}', 'AWS Secret Key'),
        ]

    def _check_policy(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []
        source_files = context.get('source_files', [])

        for file_path in source_files:
            if self._is_excluded_file(file_path):
                continue

            try:
                with open(file_path, encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern, secret_type in self.secret_patterns:
                        if re.search(pattern, line):
                            violations.append(PolicyViolation(
                                policy_id=self.policy_id,
                                policy_name=self.name,
                                severity=self.severity,
                                category=self.category,
                                message=f"Potential {secret_type} found in source code",
                                file_path=str(file_path),
                                line_number=line_num,
                                details={'pattern': pattern, 'line': line.strip()},
                                timestamp=datetime.now(timezone.utc).isoformat()
                            ))

            except Exception as e:
                self.logger.warning(f"Could not scan file {file_path}: {e}")

        return violations

    def _is_excluded_file(self, file_path: str) -> bool:
        """Check if file should be excluded from scanning."""
        excluded_patterns = [
            r'.*\.git/.*',
            r'.*node_modules/.*',
            r'.*__pycache__/.*',
            r'.*\.pyc$',
            r'.*test.*',
            r'.*example.*',
            r'.*\.md$',
            r'.*\.txt$',
        ]

        for pattern in excluded_patterns:
            if re.match(pattern, str(file_path), re.IGNORECASE):
                return True
        return False


class RequiredFilesPolicy(CompliancePolicy):
    """Policy to ensure required files are present."""

    def __init__(self):
        super().__init__(
            policy_id="compliance.required_files",
            name="Required Files Present",
            description="Repository must contain all required files"
        )

        self.required_files = [
            'README.md',
            'LICENSE',
            'SECURITY.md',
            'CONTRIBUTING.md',
            'CODE_OF_CONDUCT.md',
            '.gitignore',
            'requirements.txt',
            'pyproject.toml'
        ]

    def _check_policy(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []
        repository_root = Path(context.get('repository_root', '.'))

        for required_file in self.required_files:
            file_path = repository_root / required_file
            if not file_path.exists():
                violations.append(PolicyViolation(
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    severity=self.severity,
                    category=self.category,
                    message=f"Required file missing: {required_file}",
                    file_path=str(file_path),
                    details={'required_file': required_file},
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

        return violations


class DependencyLicensePolicy(CompliancePolicy):
    """Policy to check dependency licenses."""

    def __init__(self):
        super().__init__(
            policy_id="compliance.dependency_licenses",
            name="Dependency License Compliance",
            description="All dependencies must have approved licenses"
        )

        # Approved open source licenses
        self.approved_licenses = [
            'MIT',
            'Apache-2.0',
            'BSD-2-Clause',
            'BSD-3-Clause',
            'ISC',
            'Python Software Foundation License'
        ]

        # Prohibited licenses
        self.prohibited_licenses = [
            'GPL-2.0',
            'GPL-3.0',
            'AGPL-1.0',
            'AGPL-3.0',
            'CPAL-1.0'
        ]

    def _check_policy(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []

        # Check Python dependencies if pip-licenses is available
        try:
            result = subprocess.run(
                ['pip-licenses', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                dependencies = json.loads(result.stdout)

                for dep in dependencies:
                    license_name = dep.get('License', 'Unknown')
                    package_name = dep.get('Name', 'Unknown')

                    if license_name in self.prohibited_licenses:
                        violations.append(PolicyViolation(
                            policy_id=self.policy_id,
                            policy_name=self.name,
                            severity=PolicySeverity.ERROR,
                            category=self.category,
                            message=f"Prohibited license detected: {package_name} uses {license_name}",
                            details={
                                'package': package_name,
                                'license': license_name,
                                'version': dep.get('Version', 'Unknown')
                            },
                            timestamp=datetime.now(timezone.utc).isoformat()
                        ))
                    elif license_name not in self.approved_licenses and license_name != 'Unknown':
                        violations.append(PolicyViolation(
                            policy_id=self.policy_id,
                            policy_name=self.name,
                            severity=PolicySeverity.WARNING,
                            category=self.category,
                            message=f"Unapproved license detected: {package_name} uses {license_name}",
                            details={
                                'package': package_name,
                                'license': license_name,
                                'version': dep.get('Version', 'Unknown')
                            },
                            timestamp=datetime.now(timezone.utc).isoformat()
                        ))

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # pip-licenses not available or failed, skip this check
            pass

        return violations


class CodeQualityPolicy(Policy):
    """Code quality governance policy."""

    def __init__(self):
        super().__init__(
            policy_id="quality.code_standards",
            name="Code Quality Standards",
            description="Code must meet minimum quality standards",
            category=PolicyCategory.QUALITY,
            severity=PolicySeverity.WARNING
        )

        self.min_test_coverage = 80.0  # Minimum test coverage percentage
        self.max_function_lines = 50    # Maximum lines per function
        self.max_file_lines = 500       # Maximum lines per file

    def _check_policy(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        violations = []

        # Check test coverage
        coverage_data = context.get('test_coverage')
        if coverage_data and coverage_data < self.min_test_coverage:
            violations.append(PolicyViolation(
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=self.severity,
                category=self.category,
                message=f"Test coverage below minimum: {coverage_data:.1f}% < {self.min_test_coverage}%",
                details={'current_coverage': coverage_data, 'minimum_coverage': self.min_test_coverage},
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

        # Check file and function sizes
        source_files = context.get('source_files', [])
        for file_path in source_files:
            if str(file_path).endswith('.py'):
                violations.extend(self._check_python_file_quality(file_path))

        return violations

    def _check_python_file_quality(self, file_path: str) -> List[PolicyViolation]:
        """Check Python file for quality issues."""
        violations = []

        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            # Check file length
            if len(lines) > self.max_file_lines:
                violations.append(PolicyViolation(
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    severity=self.severity,
                    category=self.category,
                    message=f"File too long: {len(lines)} lines > {self.max_file_lines}",
                    file_path=file_path,
                    details={'actual_lines': len(lines), 'max_lines': self.max_file_lines},
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

            # Check function lengths (simple heuristic)
            in_function = False
            function_start = 0
            function_name = ""

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                if stripped.startswith('def ') and ':' in stripped:
                    if in_function and (line_num - function_start) > self.max_function_lines:
                        violations.append(PolicyViolation(
                            policy_id=self.policy_id,
                            policy_name=self.name,
                            severity=self.severity,
                            category=self.category,
                            message=f"Function too long: {function_name} has {line_num - function_start} lines > {self.max_function_lines}",
                            file_path=file_path,
                            line_number=function_start,
                            details={'function_name': function_name, 'actual_lines': line_num - function_start, 'max_lines': self.max_function_lines},
                            timestamp=datetime.now(timezone.utc).isoformat()
                        ))

                    in_function = True
                    function_start = line_num
                    function_name = stripped.split('(')[0].replace('def ', '').strip()

                elif stripped and not stripped.startswith(' ') and not stripped.startswith('\t') and in_function:
                    # End of function (next top-level statement)
                    if (line_num - function_start) > self.max_function_lines:
                        violations.append(PolicyViolation(
                            policy_id=self.policy_id,
                            policy_name=self.name,
                            severity=self.severity,
                            category=self.category,
                            message=f"Function too long: {function_name} has {line_num - function_start} lines > {self.max_function_lines}",
                            file_path=file_path,
                            line_number=function_start,
                            details={'function_name': function_name, 'actual_lines': line_num - function_start, 'max_lines': self.max_function_lines},
                            timestamp=datetime.now(timezone.utc).isoformat()
                        ))
                    in_function = False

        except Exception as e:
            self.logger.warning(f"Could not check file quality for {file_path}: {e}")

        return violations


class PolicyEngine:
    """Main policy engine for governance automation."""

    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.policies: Dict[str, Policy] = {}
        self.config = self._load_config(config_file)

        # Register default policies
        self._register_default_policies()

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_file and Path(config_file).exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_file}: {e}")

        # Default configuration
        return {
            'enabled_policies': [],  # Empty means all policies enabled
            'disabled_policies': [],
            'policy_settings': {}
        }

    def _register_default_policies(self) -> None:
        """Register default governance policies."""
        default_policies = [
            NoSecretsInCodePolicy(),
            RequiredFilesPolicy(),
            DependencyLicensePolicy(),
            CodeQualityPolicy(),
        ]

        for policy in default_policies:
            self.register_policy(policy)

    def register_policy(self, policy: Policy) -> None:
        """Register a policy with the engine."""
        # Check if policy should be disabled
        if policy.policy_id in self.config.get('disabled_policies', []):
            policy.enabled = False

        # Check if only specific policies are enabled
        enabled_policies = self.config.get('enabled_policies', [])
        if enabled_policies and policy.policy_id not in enabled_policies:
            policy.enabled = False

        self.policies[policy.policy_id] = policy
        self.logger.info(f"Registered policy: {policy.policy_id} (enabled: {policy.enabled})")

    def evaluate_policies(self, context: Dict[str, Any]) -> Dict[str, PolicyResult]:
        """Evaluate all registered policies."""
        results = {}

        for policy_id, policy in self.policies.items():
            self.logger.info(f"Evaluating policy: {policy_id}")
            try:
                result = policy.evaluate(context)
                results[policy_id] = result

                if not result.passed:
                    self.logger.warning(f"Policy {policy_id} failed with {len(result.violations)} violations")

            except Exception as e:
                self.logger.error(f"Failed to evaluate policy {policy_id}: {e}")
                results[policy_id] = PolicyResult(
                    policy_id=policy_id,
                    passed=False,
                    violations=[PolicyViolation(
                        policy_id=policy_id,
                        policy_name=policy.name,
                        severity=PolicySeverity.ERROR,
                        category=policy.category,
                        message=f"Policy evaluation error: {str(e)}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )],
                    execution_time=0.0,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

        return results

    def generate_compliance_report(self, results: Dict[str, PolicyResult]) -> Dict[str, Any]:
        """Generate a comprehensive compliance report."""
        total_policies = len(results)
        passed_policies = sum(1 for r in results.values() if r.passed)
        failed_policies = total_policies - passed_policies

        total_violations = sum(len(r.violations) for r in results.values())

        # Group violations by severity
        violations_by_severity = {severity.value: 0 for severity in PolicySeverity}
        violations_by_category = {category.value: 0 for category in PolicyCategory}

        all_violations = []
        for result in results.values():
            for violation in result.violations:
                all_violations.append(violation.to_dict())
                violations_by_severity[violation.severity.value] += 1
                violations_by_category[violation.category.value] += 1

        # Calculate compliance score
        compliance_score = (passed_policies / total_policies * 100) if total_policies > 0 else 100

        # Determine overall status
        if violations_by_severity[PolicySeverity.CRITICAL.value] > 0:
            overall_status = "critical"
        elif violations_by_severity[PolicySeverity.ERROR.value] > 0:
            overall_status = "non-compliant"
        elif violations_by_severity[PolicySeverity.WARNING.value] > 0:
            overall_status = "warnings"
        else:
            overall_status = "compliant"

        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': overall_status,
            'compliance_score': compliance_score,
            'summary': {
                'total_policies': total_policies,
                'passed_policies': passed_policies,
                'failed_policies': failed_policies,
                'total_violations': total_violations
            },
            'violations_by_severity': violations_by_severity,
            'violations_by_category': violations_by_category,
            'policy_results': {policy_id: result.to_dict() for policy_id, result in results.items()},
            'violations': all_violations
        }

    def save_report(self, report: Dict[str, Any], output_file: str) -> None:
        """Save compliance report to file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"Compliance report saved to {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save report to {output_file}: {e}")


def collect_repository_context(repository_root: str = ".") -> Dict[str, Any]:
    """Collect context information about the repository."""
    root_path = Path(repository_root)

    # Find source files
    source_files = []
    for pattern in ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.go', '**/*.rs']:
        source_files.extend(root_path.glob(pattern))

    # Filter out common non-source directories
    excluded_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache', 'dist', 'build'}
    source_files = [f for f in source_files if not any(part in excluded_dirs for part in f.parts)]

    # Get test coverage if available
    test_coverage = None
    coverage_file = root_path / 'coverage.xml'
    if coverage_file.exists():
        try:
            # Simple coverage extraction (could be more sophisticated)
            with open(coverage_file) as f:
                content = f.read()
                if 'line-rate=' in content:
                    import re
                    match = re.search(r'line-rate="([0-9.]+)"', content)
                    if match:
                        test_coverage = float(match.group(1)) * 100
        except Exception:
            pass

    return {
        'repository_root': str(root_path.absolute()),
        'source_files': [str(f) for f in source_files],
        'test_coverage': test_coverage,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Policy as Code Governance Engine')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output', default='governance/compliance_report.json', help='Output report file')
    parser.add_argument('--repository', default='.', help='Repository root path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Initialize policy engine
    engine = PolicyEngine(args.config)

    # Collect repository context
    print("Collecting repository context...")
    context = collect_repository_context(args.repository)
    print(f"Found {len(context['source_files'])} source files")

    # Evaluate policies
    print("Evaluating governance policies...")
    results = engine.evaluate_policies(context)

    # Generate report
    print("Generating compliance report...")
    report = engine.generate_compliance_report(results)

    # Save report
    engine.save_report(report, args.output)

    # Print summary
    print("\nCompliance Report Summary:")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Compliance Score: {report['compliance_score']:.1f}%")
    print(f"Total Policies: {report['summary']['total_policies']}")
    print(f"Passed: {report['summary']['passed_policies']}")
    print(f"Failed: {report['summary']['failed_policies']}")
    print(f"Total Violations: {report['summary']['total_violations']}")

    if report['summary']['total_violations'] > 0:
        print("\nViolations by Severity:")
        for severity, count in report['violations_by_severity'].items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")

    # Exit with appropriate code
    if report['overall_status'] in ['critical', 'non-compliant']:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
