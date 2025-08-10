"""Comprehensive Validation System for Contract Processing.

This module implements multi-layered validation including schema validation,
business rule validation, data quality checks, semantic validation,
and cross-reference validation for contract processing workflows.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import jsonschema
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation levels for different types of checks."""

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    ENTERPRISE = "enterprise"


class ValidationResult(Enum):
    """Validation result status."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    issue_id: str
    level: ValidationResult
    validator_name: str
    field_path: str
    message: str
    suggested_fix: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""

    validation_id: str
    timestamp: float
    validation_level: ValidationLevel
    total_checks: int
    passed_checks: int
    warning_issues: List[ValidationIssue] = field(default_factory=list)
    failed_issues: List[ValidationIssue] = field(default_factory=list)
    critical_issues: List[ValidationIssue] = field(default_factory=list)
    execution_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_checks == 0:
            return 1.0
        return self.passed_checks / self.total_checks

    @property
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.critical_issues) > 0

    @property
    def is_valid(self) -> bool:
        """Check if validation passed overall."""
        return len(self.failed_issues) == 0 and len(self.critical_issues) == 0


class SchemaValidator:
    """JSON Schema validation for contract data structures."""

    def __init__(self):
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load validation schemas."""
        return {
            "extraction_result": {
                "type": "object",
                "required": ["document_info", "clauses", "metadata"],
                "properties": {
                    "document_info": {
                        "type": "object",
                        "required": ["filename", "pages", "processing_time", "overall_confidence"],
                        "properties": {
                            "filename": {"type": "string", "minLength": 1},
                            "pages": {"type": "integer", "minimum": 1},
                            "processing_time": {"type": "number", "minimum": 0},
                            "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "document_type": {"type": "string"}
                        }
                    },
                    "clauses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "type", "text", "page", "confidence"],
                            "properties": {
                                "id": {"type": "string", "minLength": 1},
                                "type": {"type": "string", "minLength": 1},
                                "text": {"type": "string", "minLength": 1},
                                "page": {"type": "integer", "minimum": 1},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "coordinates": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 4,
                                    "maxItems": 4
                                },
                                "key_terms": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "required": ["extraction_timestamp", "model_version", "processing_method"],
                        "properties": {
                            "extraction_timestamp": {"type": "string", "format": "date-time"},
                            "model_version": {"type": "string", "minLength": 1},
                            "processing_method": {"type": "string", "minLength": 1}
                        }
                    }
                }
            },
            "clause": {
                "type": "object",
                "required": ["id", "type", "text", "confidence"],
                "properties": {
                    "id": {"type": "string", "minLength": 1, "maxLength": 100},
                    "type": {
                        "type": "string",
                        "enum": [
                            "confidentiality", "termination", "payment_terms", "liability",
                            "governing_law", "dispute_resolution", "intellectual_property",
                            "non_compete", "force_majeure", "amendment", "severability"
                        ]
                    },
                    "text": {"type": "string", "minLength": 10, "maxLength": 10000},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            },
            "document_info": {
                "type": "object",
                "required": ["filename", "pages"],
                "properties": {
                    "filename": {
                        "type": "string",
                        "pattern": r"^[^<>:\"/\\|?*]+\.[a-zA-Z0-9]{1,10}$"
                    },
                    "pages": {"type": "integer", "minimum": 1, "maximum": 10000},
                    "file_size": {"type": "integer", "minimum": 1},
                    "processing_time": {"type": "number", "minimum": 0, "maximum": 3600}
                }
            }
        }

    def validate(self, data: Any, schema_name: str) -> List[ValidationIssue]:
        """Validate data against a schema."""
        issues = []

        if schema_name not in self.schemas:
            issues.append(ValidationIssue(
                issue_id=f"schema_{int(time.time())}",
                level=ValidationResult.CRITICAL,
                validator_name="SchemaValidator",
                field_path="schema",
                message=f"Unknown schema: {schema_name}",
                suggested_fix=f"Available schemas: {', '.join(self.schemas.keys())}"
            ))
            return issues

        schema = self.schemas[schema_name]

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            issues.append(ValidationIssue(
                issue_id=f"schema_{int(time.time())}",
                level=ValidationResult.FAILED,
                validator_name="SchemaValidator",
                field_path=".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root",
                message=e.message,
                suggested_fix=self._generate_schema_fix_suggestion(e),
                context={"schema_path": ".".join(str(p) for p in e.schema_path)}
            ))
        except jsonschema.SchemaError as e:
            issues.append(ValidationIssue(
                issue_id=f"schema_{int(time.time())}",
                level=ValidationResult.CRITICAL,
                validator_name="SchemaValidator",
                field_path="schema_definition",
                message=f"Schema definition error: {e.message}",
                suggested_fix="Check schema definition for syntax errors"
            ))

        return issues

    def _generate_schema_fix_suggestion(self, error: jsonschema.ValidationError) -> str:
        """Generate suggestion for fixing schema validation errors."""
        if "is not of type" in error.message:
            expected_type = error.schema.get("type", "unknown")
            return f"Convert value to {expected_type}"
        elif "is a required property" in error.message:
            missing_prop = error.message.split("'")[1]
            return f"Add required property: {missing_prop}"
        elif "is not one of" in error.message:
            enum_values = error.schema.get("enum", [])
            return f"Use one of: {', '.join(map(str, enum_values))}"
        elif "is too short" in error.message:
            min_length = error.schema.get("minLength", 1)
            return f"Ensure minimum length of {min_length}"
        elif "is too long" in error.message:
            max_length = error.schema.get("maxLength", 100)
            return f"Ensure maximum length of {max_length}"
        else:
            return "Check value format and constraints"


class BusinessRuleValidator:
    """Validates business rules and logical constraints."""

    def __init__(self):
        self.rules = self._load_business_rules()

    def _load_business_rules(self) -> Dict[str, Callable[[Any], List[ValidationIssue]]]:
        """Load business rule validation functions."""
        return {
            "clause_consistency": self._validate_clause_consistency,
            "confidence_thresholds": self._validate_confidence_thresholds,
            "text_quality": self._validate_text_quality,
            "coordinate_validity": self._validate_coordinates,
            "duplicate_detection": self._validate_duplicates,
            "semantic_coherence": self._validate_semantic_coherence,
            "completeness_check": self._validate_completeness
        }

    def validate(self, data: Any, rule_names: Optional[List[str]] = None) -> List[ValidationIssue]:
        """Validate data against business rules."""
        issues = []
        rules_to_check = rule_names or list(self.rules.keys())

        for rule_name in rules_to_check:
            if rule_name in self.rules:
                rule_issues = self.rules[rule_name](data)
                issues.extend(rule_issues)
            else:
                issues.append(ValidationIssue(
                    issue_id=f"rule_{int(time.time())}",
                    level=ValidationResult.WARNING,
                    validator_name="BusinessRuleValidator",
                    field_path="rules",
                    message=f"Unknown business rule: {rule_name}",
                    suggested_fix=f"Available rules: {', '.join(self.rules.keys())}"
                ))

        return issues

    def _validate_clause_consistency(self, data: Any) -> List[ValidationIssue]:
        """Validate consistency between clauses."""
        issues = []

        if not isinstance(data, dict) or "clauses" not in data:
            return issues

        clauses = data["clauses"]
        if not isinstance(clauses, list):
            return issues

        # Check for conflicting clauses
        termination_clauses = []
        payment_clauses = []

        for clause in clauses:
            if isinstance(clause, dict):
                clause_type = clause.get("type", "")
                if clause_type == "termination":
                    termination_clauses.append(clause)
                elif clause_type == "payment_terms":
                    payment_clauses.append(clause)

        # Check for conflicting termination terms
        if len(termination_clauses) > 1:
            issues.append(ValidationIssue(
                issue_id=f"consistency_{int(time.time())}",
                level=ValidationResult.WARNING,
                validator_name="BusinessRuleValidator",
                field_path="clauses.termination",
                message=f"Multiple termination clauses found ({len(termination_clauses)})",
                suggested_fix="Review termination clauses for consistency"
            ))

        return issues

    def _validate_confidence_thresholds(self, data: Any) -> List[ValidationIssue]:
        """Validate confidence scores meet business thresholds."""
        issues = []

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                low_confidence_clauses = []

                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict) and "confidence" in clause:
                        confidence = clause["confidence"]
                        if isinstance(confidence, (int, float)) and confidence < 0.5:
                            low_confidence_clauses.append((i, confidence))

                if low_confidence_clauses:
                    issues.append(ValidationIssue(
                        issue_id=f"confidence_{int(time.time())}",
                        level=ValidationResult.WARNING,
                        validator_name="BusinessRuleValidator",
                        field_path="clauses.confidence",
                        message=f"{len(low_confidence_clauses)} clauses have low confidence (<0.5)",
                        suggested_fix="Review and potentially re-process low confidence clauses",
                        context={"low_confidence_indices": [i for i, _ in low_confidence_clauses]}
                    ))

        return issues

    def _validate_text_quality(self, data: Any) -> List[ValidationIssue]:
        """Validate text quality of extracted clauses."""
        issues = []

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict) and "text" in clause:
                        text = clause["text"]
                        if isinstance(text, str):
                            # Check for suspicious patterns
                            if len(text) < 20:
                                issues.append(ValidationIssue(
                                    issue_id=f"text_quality_{i}_{int(time.time())}",
                                    level=ValidationResult.WARNING,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}].text",
                                    message="Clause text is very short",
                                    suggested_fix="Verify OCR accuracy for this clause"
                                ))

                            # Check for excessive special characters
                            special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text)
                            if special_char_ratio > 0.3:
                                issues.append(ValidationIssue(
                                    issue_id=f"text_quality_{i}_{int(time.time())}",
                                    level=ValidationResult.WARNING,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}].text",
                                    message="High ratio of special characters in text",
                                    suggested_fix="Check for OCR errors or encoding issues"
                                ))

        return issues

    def _validate_coordinates(self, data: Any) -> List[ValidationIssue]:
        """Validate coordinate data."""
        issues = []

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict) and "coordinates" in clause:
                        coords = clause["coordinates"]
                        if isinstance(coords, list) and len(coords) == 4:
                            # Check coordinate validity (assuming page coordinates)
                            if not all(isinstance(c, (int, float)) and c >= 0 for c in coords):
                                issues.append(ValidationIssue(
                                    issue_id=f"coords_{i}_{int(time.time())}",
                                    level=ValidationResult.FAILED,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}].coordinates",
                                    message="Invalid coordinate values",
                                    suggested_fix="Ensure coordinates are non-negative numbers"
                                ))

                            # Check coordinate order (x1, y1, x2, y2)
                            if len(coords) == 4 and coords[2] <= coords[0]:
                                issues.append(ValidationIssue(
                                    issue_id=f"coords_order_{i}_{int(time.time())}",
                                    level=ValidationResult.WARNING,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}].coordinates",
                                    message="Coordinate ordering may be incorrect",
                                    suggested_fix="Ensure coordinates follow (x1, y1, x2, y2) format"
                                ))

        return issues

    def _validate_duplicates(self, data: Any) -> List[ValidationIssue]:
        """Detect duplicate clauses."""
        issues = []

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                seen_texts = {}

                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict) and "text" in clause:
                        text = clause["text"]
                        if isinstance(text, str):
                            # Normalize text for comparison
                            normalized_text = re.sub(r'\s+', ' ', text.strip().lower())

                            if normalized_text in seen_texts:
                                issues.append(ValidationIssue(
                                    issue_id=f"duplicate_{i}_{int(time.time())}",
                                    level=ValidationResult.WARNING,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}].text",
                                    message=f"Duplicate text found (similar to clause {seen_texts[normalized_text]})",
                                    suggested_fix="Remove duplicate clauses or verify uniqueness"
                                ))
                            else:
                                seen_texts[normalized_text] = i

        return issues

    def _validate_semantic_coherence(self, data: Any) -> List[ValidationIssue]:
        """Validate semantic coherence of clauses."""
        issues = []

        # This is a simplified semantic check
        # In production, this would use NLP models

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict):
                        clause_type = clause.get("type", "")
                        clause_text = clause.get("text", "").lower()

                        # Simple keyword-based semantic check
                        type_keywords = {
                            "payment_terms": ["payment", "pay", "compensation", "salary", "fee"],
                            "termination": ["terminate", "end", "expire", "cancel"],
                            "confidentiality": ["confidential", "non-disclosure", "secret"],
                            "liability": ["liable", "responsibility", "damages"]
                        }

                        if clause_type in type_keywords:
                            expected_keywords = type_keywords[clause_type]
                            if not any(keyword in clause_text for keyword in expected_keywords):
                                issues.append(ValidationIssue(
                                    issue_id=f"semantic_{i}_{int(time.time())}",
                                    level=ValidationResult.WARNING,
                                    validator_name="BusinessRuleValidator",
                                    field_path=f"clauses[{i}]",
                                    message=f"Clause type '{clause_type}' doesn't match text content",
                                    suggested_fix="Review clause classification accuracy"
                                ))

        return issues

    def _validate_completeness(self, data: Any) -> List[ValidationIssue]:
        """Validate document completeness."""
        issues = []

        if isinstance(data, dict):
            # Check for essential contract elements
            if "clauses" in data:
                clauses = data["clauses"]
                if isinstance(clauses, list):
                    clause_types = {clause.get("type") for clause in clauses if isinstance(clause, dict)}

                    # Essential clause types for contracts
                    essential_types = {"payment_terms", "termination"}
                    missing_types = essential_types - clause_types

                    if missing_types:
                        issues.append(ValidationIssue(
                            issue_id=f"completeness_{int(time.time())}",
                            level=ValidationResult.WARNING,
                            validator_name="BusinessRuleValidator",
                            field_path="clauses",
                            message=f"Missing essential clause types: {', '.join(missing_types)}",
                            suggested_fix="Verify document completeness or OCR accuracy"
                        ))

        return issues


class DataQualityValidator:
    """Validates data quality metrics and patterns."""

    def __init__(self):
        self.quality_metrics = {
            "completeness": self._check_completeness,
            "accuracy": self._check_accuracy,
            "consistency": self._check_consistency,
            "timeliness": self._check_timeliness,
            "validity": self._check_validity
        }

    def validate(self, data: Any) -> List[ValidationIssue]:
        """Validate data quality."""
        issues = []

        for metric_name, check_func in self.quality_metrics.items():
            metric_issues = check_func(data)
            issues.extend(metric_issues)

        return issues

    def _check_completeness(self, data: Any) -> List[ValidationIssue]:
        """Check data completeness."""
        issues = []

        if isinstance(data, dict):
            required_fields = ["document_info", "clauses", "metadata"]
            missing_fields = []

            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)

            if missing_fields:
                issues.append(ValidationIssue(
                    issue_id=f"completeness_{int(time.time())}",
                    level=ValidationResult.FAILED,
                    validator_name="DataQualityValidator",
                    field_path="root",
                    message=f"Missing required fields: {', '.join(missing_fields)}",
                    suggested_fix="Ensure all required fields are populated"
                ))

        return issues

    def _check_accuracy(self, data: Any) -> List[ValidationIssue]:
        """Check data accuracy indicators."""
        issues = []

        if isinstance(data, dict) and "document_info" in data:
            doc_info = data["document_info"]
            if isinstance(doc_info, dict):
                confidence = doc_info.get("overall_confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < 0.7:
                    issues.append(ValidationIssue(
                        issue_id=f"accuracy_{int(time.time())}",
                        level=ValidationResult.WARNING,
                        validator_name="DataQualityValidator",
                        field_path="document_info.overall_confidence",
                        message=f"Low overall confidence score: {confidence}",
                        suggested_fix="Review extraction accuracy and consider re-processing"
                    ))

        return issues

    def _check_consistency(self, data: Any) -> List[ValidationIssue]:
        """Check data consistency."""
        issues = []

        # Check consistency between document pages and clause pages
        if isinstance(data, dict):
            doc_pages = data.get("document_info", {}).get("pages", 0)
            clause_pages = set()

            clauses = data.get("clauses", [])
            if isinstance(clauses, list):
                for clause in clauses:
                    if isinstance(clause, dict) and "page" in clause:
                        clause_pages.add(clause["page"])

                max_clause_page = max(clause_pages) if clause_pages else 0
                if max_clause_page > doc_pages:
                    issues.append(ValidationIssue(
                        issue_id=f"consistency_{int(time.time())}",
                        level=ValidationResult.FAILED,
                        validator_name="DataQualityValidator",
                        field_path="clauses.page",
                        message=f"Clause page {max_clause_page} exceeds document pages {doc_pages}",
                        suggested_fix="Check page numbering consistency"
                    ))

        return issues

    def _check_timeliness(self, data: Any) -> List[ValidationIssue]:
        """Check data timeliness."""
        issues = []

        if isinstance(data, dict) and "metadata" in data:
            metadata = data["metadata"]
            if isinstance(metadata, dict) and "extraction_timestamp" in metadata:
                timestamp_str = metadata["extraction_timestamp"]
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_seconds = (datetime.now(timestamp.tzinfo) - timestamp).total_seconds()

                    # Warn if data is older than 24 hours
                    if age_seconds > 86400:
                        issues.append(ValidationIssue(
                            issue_id=f"timeliness_{int(time.time())}",
                            level=ValidationResult.WARNING,
                            validator_name="DataQualityValidator",
                            field_path="metadata.extraction_timestamp",
                            message=f"Data is {age_seconds/3600:.1f} hours old",
                            suggested_fix="Consider re-extracting for current data"
                        ))
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        issue_id=f"timeliness_{int(time.time())}",
                        level=ValidationResult.FAILED,
                        validator_name="DataQualityValidator",
                        field_path="metadata.extraction_timestamp",
                        message="Invalid timestamp format",
                        suggested_fix="Use ISO format timestamp"
                    ))

        return issues

    def _check_validity(self, data: Any) -> List[ValidationIssue]:
        """Check data validity."""
        issues = []

        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
            if isinstance(clauses, list):
                for i, clause in enumerate(clauses):
                    if isinstance(clause, dict):
                        # Check ID format
                        clause_id = clause.get("id", "")
                        if not isinstance(clause_id, str) or not clause_id:
                            issues.append(ValidationIssue(
                                issue_id=f"validity_{i}_{int(time.time())}",
                                level=ValidationResult.FAILED,
                                validator_name="DataQualityValidator",
                                field_path=f"clauses[{i}].id",
                                message="Invalid or missing clause ID",
                                suggested_fix="Ensure all clauses have valid string IDs"
                            ))

        return issues


class ComprehensiveValidator:
    """Main validator that orchestrates all validation types."""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.schema_validator = SchemaValidator()
        self.business_rule_validator = BusinessRuleValidator()
        self.data_quality_validator = DataQualityValidator()

    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Perform comprehensive validation."""
        start_time = time.time()
        validation_id = f"validation_{int(start_time)}"

        all_issues = []
        total_checks = 0

        # Schema validation
        if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT, ValidationLevel.ENTERPRISE]:
            schema_issues = self.schema_validator.validate(data, "extraction_result")
            all_issues.extend(schema_issues)
            total_checks += 1

        # Business rule validation
        if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.ENTERPRISE]:
            business_issues = self.business_rule_validator.validate(data)
            all_issues.extend(business_issues)
            total_checks += len(self.business_rule_validator.rules)

        # Data quality validation
        if self.validation_level == ValidationLevel.ENTERPRISE:
            quality_issues = self.data_quality_validator.validate(data)
            all_issues.extend(quality_issues)
            total_checks += len(self.data_quality_validator.quality_metrics)

        # Categorize issues
        warning_issues = [issue for issue in all_issues if issue.level == ValidationResult.WARNING]
        failed_issues = [issue for issue in all_issues if issue.level == ValidationResult.FAILED]
        critical_issues = [issue for issue in all_issues if issue.level == ValidationResult.CRITICAL]

        passed_checks = total_checks - len(failed_issues) - len(critical_issues)

        execution_time = time.time() - start_time

        report = ValidationReport(
            validation_id=validation_id,
            timestamp=start_time,
            validation_level=self.validation_level,
            total_checks=total_checks,
            passed_checks=passed_checks,
            warning_issues=warning_issues,
            failed_issues=failed_issues,
            critical_issues=critical_issues,
            execution_time=execution_time
        )

        logger.info(
            "Validation completed: ID=%s, Level=%s, Success=%.1f%%, Issues=%d",
            validation_id,
            self.validation_level.value,
            report.success_rate * 100,
            len(all_issues)
        )

        return report


def validate_extraction_result(
    result: Dict[str, Any],
    validation_level: ValidationLevel = ValidationLevel.STANDARD
) -> ValidationReport:
    """Convenience function to validate extraction results."""
    validator = ComprehensiveValidator(validation_level)
    return validator.validate(result)


class ValidationConfig(BaseModel):
    """Configuration for validation system."""

    validation_level: ValidationLevel = ValidationLevel.STANDARD
    enable_schema_validation: bool = True
    enable_business_rules: bool = True
    enable_data_quality_checks: bool = True
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_validation_time: float = Field(default=30.0, gt=0.0)
    strict_schema_compliance: bool = False
    custom_business_rules: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
