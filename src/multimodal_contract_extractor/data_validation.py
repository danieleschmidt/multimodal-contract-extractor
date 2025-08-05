"""
Comprehensive data validation and integrity framework.

This module provides deep data validation, schema enforcement, corruption detection,
and integrity verification for all data inputs and outputs in the system.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import re
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from pydantic import BaseModel, ValidationError, validator
    from pydantic.fields import Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """Validation result types."""
    VALID = "valid"
    INVALID = "invalid"
    CORRUPTED = "corrupted"
    INCOMPLETE = "incomplete"
    SUSPICIOUS = "suspicious"


class IntegrityCheckType(Enum):
    """Types of integrity checks."""
    CHECKSUM = "checksum"
    SIGNATURE = "signature"
    STRUCTURE = "structure"
    CONTENT = "content"
    FORMAT = "format"
    SCHEMA = "schema"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: ValidationSeverity
    message: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IntegrityCheckResult:
    """Result of an integrity check."""
    check_type: IntegrityCheckType
    passed: bool
    expected: Optional[str] = None
    actual: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    valid: bool
    result: ValidationResult
    issues: List[ValidationIssue] = field(default_factory=list)
    integrity_checks: List[IntegrityCheckResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_time_seconds: float = 0.0
    validator_version: str = "1.0.0"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_issue(self, severity: ValidationSeverity, message: str,
                  field_path: str = None, **kwargs):
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            severity=severity,
            message=message,
            field_path=field_path,
            **kwargs
        )
        self.issues.append(issue)

        # Update overall validity
        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.valid = False

    def add_integrity_check(self, check_result: IntegrityCheckResult):
        """Add an integrity check result."""
        self.integrity_checks.append(check_result)

        # Update overall validity if check failed
        if not check_result.passed:
            self.add_issue(
                ValidationSeverity.ERROR,
                f"Integrity check failed: {check_result.check_type.value}",
                error_code=f"INTEGRITY_{check_result.check_type.value.upper()}_FAILED"
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation report."""
        issue_counts = {}
        for severity in ValidationSeverity:
            issue_counts[severity.value] = sum(
                1 for issue in self.issues if issue.severity == severity
            )

        integrity_summary = {}
        for check_type in IntegrityCheckType:
            checks = [c for c in self.integrity_checks if c.check_type == check_type]
            if checks:
                integrity_summary[check_type.value] = {
                    "total": len(checks),
                    "passed": sum(1 for c in checks if c.passed),
                    "failed": sum(1 for c in checks if not c.passed)
                }

        return {
            "valid": self.valid,
            "result": self.result.value,
            "total_issues": len(self.issues),
            "issues_by_severity": issue_counts,
            "integrity_checks": integrity_summary,
            "validation_time": self.validation_time_seconds,
            "timestamp": self.timestamp.isoformat()
        }


class BaseValidator(ABC):
    """Base class for all validators."""

    def __init__(self, name: str):
        self.name = name
        self.validation_count = 0
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.validation_counter = Counter(
                f'validator_{name}_validations_total',
                f'Total validations performed by {name} validator',
                ['result']
            )
            self.validation_duration = Histogram(
                f'validator_{name}_duration_seconds',
                f'Time spent in {name} validation'
            )

    @abstractmethod
    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate the given data."""
        pass

    def _start_validation(self) -> float:
        """Start validation timing."""
        with self._lock:
            self.validation_count += 1
        return time.time()

    def _end_validation(self, start_time: float, result: ValidationResult):
        """End validation timing and update metrics."""
        duration = time.time() - start_time

        if PROMETHEUS_AVAILABLE:
            self.validation_counter.labels(result=result.value).inc()
            self.validation_duration.observe(duration)

        return duration


class SchemaValidator(BaseValidator):
    """JSON Schema validator."""

    def __init__(self, schema: Dict[str, Any]):
        super().__init__("schema")
        self.schema = schema
        self.validator = None

        if JSONSCHEMA_AVAILABLE:
            self.validator = jsonschema.Draft7Validator(schema)
        else:
            logger.warning("jsonschema not available, schema validation disabled")

    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate data against JSON schema."""
        start_time = self._start_validation()
        report = ValidationReport()

        if not self.validator:
            report.add_issue(
                ValidationSeverity.WARNING,
                "Schema validation unavailable (jsonschema not installed)"
            )
            report.result = ValidationResult.INCOMPLETE
            report.validation_time_seconds = self._end_validation(start_time, report.result)
            return report

        try:
            # Validate against schema
            errors = list(self.validator.iter_errors(data))

            if not errors:
                report.result = ValidationResult.VALID
            else:
                report.result = ValidationResult.INVALID

                for error in errors:
                    field_path = ".".join(str(p) for p in error.path) if error.path else "root"
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        error.message,
                        field_path=field_path,
                        error_code="SCHEMA_VALIDATION_FAILED"
                    )

            # Add integrity check
            schema_check = IntegrityCheckResult(
                check_type=IntegrityCheckType.SCHEMA,
                passed=len(errors) == 0,
                details={"errors_count": len(errors)}
            )
            report.add_integrity_check(schema_check)

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            report.add_issue(
                ValidationSeverity.CRITICAL,
                f"Schema validation error: {e}",
                error_code="SCHEMA_VALIDATION_ERROR"
            )
            report.result = ValidationResult.CORRUPTED

        report.validation_time_seconds = self._end_validation(start_time, report.result)
        return report


class FileIntegrityValidator(BaseValidator):
    """File integrity validator using checksums and signatures."""

    def __init__(self):
        super().__init__("file_integrity")
        self.supported_algorithms = ['md5', 'sha1', 'sha256', 'sha512']

    def validate(self, file_path: Path, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate file integrity."""
        start_time = self._start_validation()
        report = ValidationReport()
        context = context or {}

        try:
            if not file_path.exists():
                report.add_issue(
                    ValidationSeverity.CRITICAL,
                    f"File does not exist: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
                report.result = ValidationResult.CORRUPTED
                report.validation_time_seconds = self._end_validation(start_time, report.result)
                return report

            # File size check
            file_size = file_path.stat().st_size
            expected_size = context.get('expected_size')
            if expected_size is not None and file_size != expected_size:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"File size mismatch: expected {expected_size}, got {file_size}",
                    expected_value=expected_size,
                    actual_value=file_size,
                    error_code="FILE_SIZE_MISMATCH"
                )

            # Checksum validation
            expected_checksums = context.get('checksums', {})
            actual_checksums = self._calculate_checksums(file_path)

            for algorithm, expected_checksum in expected_checksums.items():
                if algorithm in actual_checksums:
                    actual_checksum = actual_checksums[algorithm]
                    passed = actual_checksum == expected_checksum

                    check_result = IntegrityCheckResult(
                        check_type=IntegrityCheckType.CHECKSUM,
                        passed=passed,
                        expected=expected_checksum,
                        actual=actual_checksum,
                        details={"algorithm": algorithm}
                    )
                    report.add_integrity_check(check_result)

                    if not passed:
                        report.add_issue(
                            ValidationSeverity.ERROR,
                            f"{algorithm.upper()} checksum mismatch",
                            expected_value=expected_checksum,
                            actual_value=actual_checksum,
                            error_code=f"CHECKSUM_{algorithm.upper()}_MISMATCH"
                        )

            # File format validation
            self._validate_file_format(file_path, report)

            # Corruption detection
            self._detect_corruption(file_path, report)

            # Determine overall result
            if report.issues:
                critical_or_error = any(
                    issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
                    for issue in report.issues
                )
                report.result = ValidationResult.CORRUPTED if critical_or_error else ValidationResult.SUSPICIOUS
            else:
                report.result = ValidationResult.VALID

            # Add metadata
            report.metadata.update({
                "file_size": file_size,
                "checksums": actual_checksums,
                "file_extension": file_path.suffix.lower()
            })

        except Exception as e:
            logger.error(f"File integrity validation failed: {e}")
            report.add_issue(
                ValidationSeverity.CRITICAL,
                f"File integrity validation error: {e}",
                error_code="FILE_VALIDATION_ERROR"
            )
            report.result = ValidationResult.CORRUPTED

        report.validation_time_seconds = self._end_validation(start_time, report.result)
        return report

    def _calculate_checksums(self, file_path: Path) -> Dict[str, str]:
        """Calculate file checksums using multiple algorithms."""
        checksums = {}
        hash_objects = {
            'md5': hashlib.md5(),
            'sha1': hashlib.sha1(),
            'sha256': hashlib.sha256(),
            'sha512': hashlib.sha512()
        }

        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    for hash_obj in hash_objects.values():
                        hash_obj.update(chunk)

            for algorithm, hash_obj in hash_objects.items():
                checksums[algorithm] = hash_obj.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate checksums: {e}")

        return checksums

    def _validate_file_format(self, file_path: Path, report: ValidationReport):
        """Validate file format based on magic bytes."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)

            # PDF validation
            if file_path.suffix.lower() == '.pdf':
                if not header.startswith(b'%PDF'):
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        "PDF file does not start with PDF header",
                        error_code="INVALID_PDF_HEADER"
                    )
                else:
                    # Check for PDF trailer
                    with open(file_path, 'rb') as f:
                        f.seek(-1024, 2)  # Read last 1KB
                        tail = f.read()
                        if b'%%EOF' not in tail:
                            report.add_issue(
                                ValidationSeverity.WARNING,
                                "PDF file does not end with proper EOF marker",
                                error_code="MISSING_PDF_EOF"
                            )

            # Image validation
            elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                image_signatures = {
                    b'\x89PNG': 'PNG',
                    b'\xff\xd8\xff': 'JPEG',
                    b'GIF8': 'GIF',
                    b'BM': 'BMP'
                }

                signature_found = False
                for sig, format_name in image_signatures.items():
                    if header.startswith(sig):
                        signature_found = True
                        report.metadata['detected_format'] = format_name
                        break

                if not signature_found:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Invalid image file header for {file_path.suffix}",
                        error_code="INVALID_IMAGE_HEADER"
                    )

            format_check = IntegrityCheckResult(
                check_type=IntegrityCheckType.FORMAT,
                passed=len([i for i in report.issues if 'HEADER' in i.error_code or '']) == 0
            )
            report.add_integrity_check(format_check)

        except Exception as e:
            logger.error(f"File format validation failed: {e}")
            report.add_issue(
                ValidationSeverity.WARNING,
                f"Could not validate file format: {e}",
                error_code="FORMAT_VALIDATION_ERROR"
            )

    def _detect_corruption(self, file_path: Path, report: ValidationReport):
        """Detect potential file corruption."""
        try:
            file_size = file_path.stat().st_size

            # Check for empty files
            if file_size == 0:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "File is empty",
                    error_code="EMPTY_FILE"
                )
                return

            # Check for suspiciously small files
            min_sizes = {
                '.pdf': 100,  # PDF files should be at least 100 bytes
                '.png': 67,   # Smallest possible PNG
                '.jpg': 134,  # Smallest possible JPEG
                '.jpeg': 134,
                '.gif': 43,   # Smallest possible GIF
            }

            ext = file_path.suffix.lower()
            if ext in min_sizes and file_size < min_sizes[ext]:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    f"File unusually small for {ext} format: {file_size} bytes",
                    error_code="SUSPICIOUSLY_SMALL_FILE"
                )

            # Check for null bytes in text-based formats
            if ext in ['.json', '.xml', '.txt', '.csv']:
                with open(file_path, 'rb') as f:
                    sample = f.read(1024)  # Check first 1KB
                    if b'\x00' in sample:
                        report.add_issue(
                            ValidationSeverity.ERROR,
                            "Null bytes found in text file",
                            error_code="NULL_BYTES_IN_TEXT"
                        )

            # Check for compression ratio anomalies (simple heuristic)
            try:
                with open(file_path, 'rb') as f:
                    sample = f.read(8192)  # Sample 8KB
                    compressed = gzip.compress(sample)
                    compression_ratio = len(compressed) / len(sample)

                    # Very low compression ratio might indicate encryption or corruption
                    if compression_ratio > 0.95:
                        report.add_issue(
                            ValidationSeverity.INFO,
                            f"Low compression ratio: {compression_ratio:.2f} (may indicate encryption)",
                            error_code="LOW_COMPRESSION_RATIO"
                        )
            except Exception:
                pass  # Compression check is optional

        except Exception as e:
            logger.error(f"Corruption detection failed: {e}")
            report.add_issue(
                ValidationSeverity.WARNING,
                f"Could not perform corruption detection: {e}",
                error_code="CORRUPTION_CHECK_ERROR"
            )


class DataStructureValidator(BaseValidator):
    """Validator for data structure integrity."""

    def __init__(self):
        super().__init__("data_structure")

    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate data structure integrity."""
        start_time = self._start_validation()
        report = ValidationReport()
        context = context or {}

        try:
            data_type = type(data).__name__
            report.metadata['data_type'] = data_type

            # Dictionary validation
            if isinstance(data, dict):
                self._validate_dict_structure(data, report, context)

            # List validation
            elif isinstance(data, list):
                self._validate_list_structure(data, report, context)

            # String validation
            elif isinstance(data, str):
                self._validate_string_structure(data, report, context)

            # Numeric validation
            elif isinstance(data, (int, float)):
                self._validate_numeric_structure(data, report, context)

            else:
                report.add_issue(
                    ValidationSeverity.INFO,
                    f"Unknown data type for structure validation: {data_type}",
                    error_code="UNKNOWN_DATA_TYPE"
                )

            # Determine result
            has_errors = any(
                issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                for issue in report.issues
            )

            if has_errors:
                report.result = ValidationResult.INVALID
            else:
                report.result = ValidationResult.VALID

        except Exception as e:
            logger.error(f"Data structure validation failed: {e}")
            report.add_issue(
                ValidationSeverity.CRITICAL,
                f"Structure validation error: {e}",
                error_code="STRUCTURE_VALIDATION_ERROR"
            )
            report.result = ValidationResult.CORRUPTED

        report.validation_time_seconds = self._end_validation(start_time, report.result)
        return report

    def _validate_dict_structure(self, data: dict, report: ValidationReport, context: Dict[str, Any]):
        """Validate dictionary structure."""
        required_keys = context.get('required_keys', [])
        optional_keys = context.get('optional_keys', [])
        max_depth = context.get('max_depth', 10)

        # Check required keys
        missing_keys = set(required_keys) - set(data.keys())
        if missing_keys:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Missing required keys: {', '.join(missing_keys)}",
                error_code="MISSING_REQUIRED_KEYS"
            )

        # Check for unexpected keys
        if required_keys or optional_keys:
            allowed_keys = set(required_keys + optional_keys)
            unexpected_keys = set(data.keys()) - allowed_keys
            if unexpected_keys:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    f"Unexpected keys found: {', '.join(unexpected_keys)}",
                    error_code="UNEXPECTED_KEYS"
                )

        # Check nesting depth
        actual_depth = self._calculate_dict_depth(data)
        if actual_depth > max_depth:
            report.add_issue(
                ValidationSeverity.WARNING,
                f"Dictionary nesting too deep: {actual_depth} (max: {max_depth})",
                error_code="EXCESSIVE_NESTING"
            )

        report.metadata.update({
            'key_count': len(data),
            'nesting_depth': actual_depth,
            'keys': list(data.keys())
        })

    def _validate_list_structure(self, data: list, report: ValidationReport, context: Dict[str, Any]):
        """Validate list structure."""
        min_length = context.get('min_length', 0)
        max_length = context.get('max_length', float('inf'))
        expected_type = context.get('expected_item_type')

        # Length validation
        if len(data) < min_length:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"List too short: {len(data)} (min: {min_length})",
                error_code="LIST_TOO_SHORT"
            )

        if len(data) > max_length:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"List too long: {len(data)} (max: {max_length})",
                error_code="LIST_TOO_LONG"
            )

        # Type consistency validation
        if expected_type:
            invalid_items = []
            for i, item in enumerate(data):
                if not isinstance(item, expected_type):
                    invalid_items.append(f"index {i}: {type(item).__name__}")

            if invalid_items:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Invalid item types: {', '.join(invalid_items[:5])}{'...' if len(invalid_items) > 5 else ''}",
                    error_code="INVALID_ITEM_TYPES"
                )

        # Check for duplicates if specified
        if context.get('unique_items', False):
            seen = set()
            duplicates = []
            for i, item in enumerate(data):
                if hashable_item := self._make_hashable(item):
                    if hashable_item in seen:
                        duplicates.append(i)
                    else:
                        seen.add(hashable_item)

            if duplicates:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    f"Duplicate items found at indices: {duplicates[:10]}",
                    error_code="DUPLICATE_ITEMS"
                )

        report.metadata.update({
            'length': len(data),
            'item_types': list(set(type(item).__name__ for item in data))
        })

    def _validate_string_structure(self, data: str, report: ValidationReport, context: Dict[str, Any]):
        """Validate string structure."""
        min_length = context.get('min_length', 0)
        max_length = context.get('max_length', float('inf'))
        pattern = context.get('pattern')
        encoding = context.get('expected_encoding', 'utf-8')

        # Length validation
        if len(data) < min_length:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"String too short: {len(data)} (min: {min_length})",
                error_code="STRING_TOO_SHORT"
            )

        if len(data) > max_length:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"String too long: {len(data)} (max: {max_length})",
                error_code="STRING_TOO_LONG"
            )

        # Pattern validation
        if pattern:
            if not re.match(pattern, data):
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"String does not match required pattern: {pattern}",
                    error_code="PATTERN_MISMATCH"
                )

        # Encoding validation
        try:
            data.encode(encoding)
        except UnicodeEncodeError as e:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"String contains characters not encodable in {encoding}: {e}",
                error_code="ENCODING_ERROR"
            )

        # Check for control characters
        control_chars = [c for c in data if ord(c) < 32 and c not in '\n\r\t']
        if control_chars:
            report.add_issue(
                ValidationSeverity.WARNING,
                f"String contains {len(control_chars)} control characters",
                error_code="CONTROL_CHARACTERS"
            )

        report.metadata.update({
            'length': len(data),
            'encoding': encoding,
            'control_chars_count': len(control_chars)
        })

    def _validate_numeric_structure(self, data: Union[int, float], report: ValidationReport, context: Dict[str, Any]):
        """Validate numeric structure."""
        min_value = context.get('min_value', float('-inf'))
        max_value = context.get('max_value', float('inf'))

        # Range validation
        if data < min_value:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Value too small: {data} (min: {min_value})",
                error_code="VALUE_TOO_SMALL"
            )

        if data > max_value:
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Value too large: {data} (max: {max_value})",
                error_code="VALUE_TOO_LARGE"
            )

        # Special float values
        if isinstance(data, float):
            if data != data:  # NaN check
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "Value is NaN (Not a Number)",
                    error_code="NAN_VALUE"
                )
            elif data == float('inf') or data == float('-inf'):
                report.add_issue(
                    ValidationSeverity.WARNING,
                    f"Value is infinite: {data}",
                    error_code="INFINITE_VALUE"
                )

        report.metadata.update({
            'value': data,
            'type': type(data).__name__
        })

    def _calculate_dict_depth(self, data: dict, current_depth: int = 1) -> int:
        """Calculate maximum nesting depth of a dictionary."""
        if not isinstance(data, dict) or not data:
            return current_depth

        max_depth = current_depth
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def _make_hashable(self, item: Any) -> Optional[Any]:
        """Convert an item to a hashable form for duplicate detection."""
        try:
            if isinstance(item, (list, dict)):
                return json.dumps(item, sort_keys=True)
            else:
                return item
        except (TypeError, ValueError):
            return None


class CompositeValidator:
    """Composite validator that runs multiple validators."""

    def __init__(self, validators: List[BaseValidator]):
        self.validators = validators
        self.validation_count = 0
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.composite_validations = Counter(
                'composite_validator_validations_total',
                'Total composite validations performed',
                ['result']
            )
            self.composite_duration = Histogram(
                'composite_validator_duration_seconds',
                'Time spent in composite validation'
            )

    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Run all validators and combine results."""
        start_time = time.time()

        with self._lock:
            self.validation_count += 1

        composite_report = ValidationReport()
        composite_report.metadata['validator_count'] = len(self.validators)
        composite_report.metadata['individual_reports'] = []

        all_valid = True
        has_critical = False

        for validator in self.validators:
            try:
                individual_report = validator.validate(data, context)

                # Combine issues
                composite_report.issues.extend(individual_report.issues)

                # Combine integrity checks
                composite_report.integrity_checks.extend(individual_report.integrity_checks)

                # Track validity
                if not individual_report.valid:
                    all_valid = False

                if any(issue.severity == ValidationSeverity.CRITICAL for issue in individual_report.issues):
                    has_critical = True

                # Store individual report summary
                composite_report.metadata['individual_reports'].append({
                    'validator': validator.name,
                    'valid': individual_report.valid,
                    'result': individual_report.result.value,
                    'issues_count': len(individual_report.issues),
                    'validation_time': individual_report.validation_time_seconds
                })

            except Exception as e:
                logger.error(f"Validator {validator.name} failed: {e}")
                composite_report.add_issue(
                    ValidationSeverity.CRITICAL,
                    f"Validator {validator.name} failed: {e}",
                    error_code="VALIDATOR_FAILURE"
                )
                all_valid = False
                has_critical = True

        # Determine overall result
        composite_report.valid = all_valid

        if has_critical:
            composite_report.result = ValidationResult.CORRUPTED
        elif not all_valid:
            composite_report.result = ValidationResult.INVALID
        else:
            composite_report.result = ValidationResult.VALID

        # Calculate total validation time
        composite_report.validation_time_seconds = time.time() - start_time

        if PROMETHEUS_AVAILABLE:
            self.composite_validations.labels(result=composite_report.result.value).inc()
            self.composite_duration.observe(composite_report.validation_time_seconds)

        return composite_report


class ValidationManager:
    """Central validation manager."""

    def __init__(self):
        self.validators: Dict[str, BaseValidator] = {}
        self.validation_profiles: Dict[str, CompositeValidator] = {}
        self.validation_history: List[ValidationReport] = []
        self._lock = threading.Lock()
        self.max_history = 1000

        # Register default validators
        self._register_default_validators()

        if PROMETHEUS_AVAILABLE:
            self.total_validations = Counter(
                'validation_manager_total_validations',
                'Total validations performed by manager',
                ['profile', 'result']
            )

    def _register_default_validators(self):
        """Register default validators."""
        # File integrity validator
        self.register_validator("file_integrity", FileIntegrityValidator())

        # Data structure validator
        self.register_validator("data_structure", DataStructureValidator())

        # Create default profiles
        self.create_profile("file_validation", ["file_integrity"])
        self.create_profile("data_validation", ["data_structure"])
        self.create_profile("comprehensive", ["file_integrity", "data_structure"])

    def register_validator(self, name: str, validator: BaseValidator):
        """Register a validator."""
        self.validators[name] = validator
        logger.info(f"Registered validator: {name}")

    def register_schema_validator(self, name: str, schema: Dict[str, Any]):
        """Register a schema validator."""
        validator = SchemaValidator(schema)
        self.register_validator(name, validator)

    def create_profile(self, name: str, validator_names: List[str]):
        """Create a validation profile."""
        validators = []
        for validator_name in validator_names:
            if validator_name in self.validators:
                validators.append(self.validators[validator_name])
            else:
                logger.warning(f"Validator {validator_name} not found for profile {name}")

        if validators:
            self.validation_profiles[name] = CompositeValidator(validators)
            logger.info(f"Created validation profile: {name} with {len(validators)} validators")

    def validate(self, data: Any, profile: str = "comprehensive",
                context: Dict[str, Any] = None) -> ValidationReport:
        """Validate data using a specific profile."""
        if profile not in self.validation_profiles:
            raise ValueError(f"Unknown validation profile: {profile}")

        validator = self.validation_profiles[profile]
        report = validator.validate(data, context)

        # Store in history
        with self._lock:
            self.validation_history.append(report)
            if len(self.validation_history) > self.max_history:
                self.validation_history = self.validation_history[-self.max_history:]

        # Update metrics
        if PROMETHEUS_AVAILABLE:
            self.total_validations.labels(
                profile=profile,
                result=report.result.value
            ).inc()

        logger.info(f"Validation completed: profile={profile}, valid={report.valid}, issues={len(report.issues)}")

        return report

    def validate_file(self, file_path: Path, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate a file using file validation profile."""
        return self.validate(file_path, "file_validation", context)

    def validate_data(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Validate data using data validation profile."""
        return self.validate(data, "data_validation", context)

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        with self._lock:
            total_validations = len(self.validation_history)

            # Count by result
            result_counts = {}
            for result in ValidationResult:
                result_counts[result.value] = sum(
                    1 for report in self.validation_history
                    if report.result == result
                )

            # Count by profile
            profile_counts = {}
            for report in self.validation_history:
                profile = report.metadata.get('profile', 'unknown')
                profile_counts[profile] = profile_counts.get(profile, 0) + 1

            # Recent validation performance
            recent_reports = self.validation_history[-100:]  # Last 100
            avg_validation_time = sum(r.validation_time_seconds for r in recent_reports) / len(recent_reports) if recent_reports else 0

            return {
                "total_validations": total_validations,
                "results": result_counts,
                "profiles": profile_counts,
                "registered_validators": list(self.validators.keys()),
                "available_profiles": list(self.validation_profiles.keys()),
                "average_validation_time": avg_validation_time,
                "history_size": len(self.validation_history)
            }

    def get_recent_validations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent validation reports."""
        with self._lock:
            recent = self.validation_history[-limit:]

        return [report.get_summary() for report in recent]


# Global validation manager instance
_validation_manager: Optional[ValidationManager] = None


def get_validation_manager() -> ValidationManager:
    """Get the global validation manager instance."""
    global _validation_manager
    if _validation_manager is None:
        _validation_manager = ValidationManager()
    return _validation_manager


# Convenience functions
def validate_file(file_path: Path, expected_checksums: Dict[str, str] = None) -> ValidationReport:
    """Validate a file with optional checksum verification."""
    context = {}
    if expected_checksums:
        context['checksums'] = expected_checksums

    manager = get_validation_manager()
    return manager.validate_file(file_path, context)


def validate_data_structure(data: Any, schema: Dict[str, Any] = None, **constraints) -> ValidationReport:
    """Validate data structure with optional schema and constraints."""
    manager = get_validation_manager()

    # If schema provided, create a temporary schema validator
    if schema:
        validator_name = f"temp_schema_{hash(str(schema))}"
        if validator_name not in manager.validators:
            manager.register_schema_validator(validator_name, schema)
            manager.create_profile(f"temp_profile_{validator_name}", ["data_structure", validator_name])
        profile = f"temp_profile_{validator_name}"
    else:
        profile = "data_validation"

    return manager.validate(data, profile, constraints)


# Example usage and testing
if __name__ == "__main__":
    import tempfile

    # Test file validation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        # Validate file
        file_report = validate_file(temp_path)
        print(f"File validation: {file_report.get_summary()}")

        # Test data validation
        test_data = {
            "name": "test",
            "value": 42,
            "items": [1, 2, 3, 4, 5]
        }

        data_report = validate_data_structure(
            test_data,
            min_length=1,
            required_keys=["name", "value"]
        )
        print(f"Data validation: {data_report.get_summary()}")

        # Get validation stats
        manager = get_validation_manager()
        stats = manager.get_validation_stats()
        print(f"Validation stats: {stats}")

    finally:
        temp_path.unlink()  # Clean up
