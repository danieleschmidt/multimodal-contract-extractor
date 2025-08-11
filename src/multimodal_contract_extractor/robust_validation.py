"""Robust validation and error handling for Generation 2."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .config import get_config

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Individual validation issue."""
    severity: ValidationSeverity
    message: str
    field: str = ""
    value: Any = None
    suggestion: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime(2025, 1, 1))

@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    critical_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime(2025, 1, 1))
    
    def add_issue(self, severity: ValidationSeverity, message: str, 
                  field: str = "", value: Any = None, suggestion: str = "") -> None:
        """Add validation issue to report."""
        issue = ValidationIssue(
            severity=severity,
            message=message,
            field=field,
            value=value,
            suggestion=suggestion
        )
        self.issues.append(issue)
        
        if severity == ValidationSeverity.WARNING:
            self.warnings_count += 1
        elif severity == ValidationSeverity.ERROR:
            self.errors_count += 1
            self.valid = False
        elif severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
            self.valid = False

class ExtractionResultValidator:
    """Robust validation for extraction results."""
    
    def __init__(self):
        self.config = get_config()
        
    def validate_extraction_result(self, result: dict[str, Any]) -> ValidationReport:
        """Comprehensive validation of extraction results."""
        report = ValidationReport(valid=True)
        
        # Validate required top-level fields
        self._validate_document_info(result.get('document_info', {}), report)
        self._validate_parties(result.get('parties', []), report)
        self._validate_clauses(result.get('clauses', []), report)
        self._validate_metadata(result.get('metadata', {}), report)
        
        # Cross-validation checks
        self._validate_consistency(result, report)
        
        return report
        
    def _validate_document_info(self, doc_info: dict[str, Any], report: ValidationReport) -> None:
        """Validate document information section."""
        required_fields = ['filename', 'pages', 'processing_time', 'overall_confidence']
        
        for field in required_fields:
            if field not in doc_info:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Missing required field in document_info: {field}",
                    field=f"document_info.{field}"
                )
                continue
                
            value = doc_info[field]
            
            # Field-specific validations
            if field == 'pages' and not isinstance(value, int) or value <= 0:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Pages must be a positive integer, got: {value}",
                    field=f"document_info.{field}",
                    value=value,
                    suggestion="Ensure page count is a positive integer"
                )
                
            elif field == 'processing_time' and (not isinstance(value, (int, float)) or value < 0):
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Processing time must be non-negative number, got: {value}",
                    field=f"document_info.{field}",
                    value=value
                )
                
            elif field == 'overall_confidence':
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Overall confidence must be between 0 and 1, got: {value}",
                        field=f"document_info.{field}",
                        value=value,
                        suggestion="Confidence scores should be normalized between 0 and 1"
                    )
                elif value < 0.5:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"Low overall confidence score: {value:.2f}",
                        field=f"document_info.{field}",
                        value=value,
                        suggestion="Consider manual review for low confidence results"
                    )
                    
    def _validate_parties(self, parties: list[dict[str, Any]], report: ValidationReport) -> None:
        """Validate parties section."""
        if not isinstance(parties, list):
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Parties must be a list, got: {type(parties).__name__}",
                field="parties"
            )
            return
            
        if len(parties) < 2:
            report.add_issue(
                ValidationSeverity.WARNING,
                f"Contract usually has at least 2 parties, found: {len(parties)}",
                field="parties",
                suggestion="Verify if all contract parties were properly identified"
            )
            
        required_party_fields = ['role', 'name']
        
        for i, party in enumerate(parties):
            if not isinstance(party, dict):
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Party {i} must be an object, got: {type(party).__name__}",
                    field=f"parties[{i}]"
                )
                continue
                
            for field in required_party_fields:
                if field not in party or not party[field]:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Missing required field in party {i}: {field}",
                        field=f"parties[{i}].{field}"
                    )
                    
            # Validate party name format
            if 'name' in party and party['name']:
                name = party['name']
                if len(name) < 2:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"Suspiciously short party name: '{name}'",
                        field=f"parties[{i}].name",
                        value=name
                    )
                    
    def _validate_clauses(self, clauses: list[dict[str, Any]], report: ValidationReport) -> None:
        """Validate clauses section."""
        if not isinstance(clauses, list):
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Clauses must be a list, got: {type(clauses).__name__}",
                field="clauses"
            )
            return
            
        if len(clauses) == 0:
            report.add_issue(
                ValidationSeverity.WARNING,
                "No clauses extracted from document",
                field="clauses",
                suggestion="Verify document contains extractable clauses or adjust extraction parameters"
            )
            
        required_clause_fields = ['id', 'type', 'text', 'confidence']
        clause_ids = set()
        
        for i, clause in enumerate(clauses):
            if not isinstance(clause, dict):
                report.add_issue(
                    ValidationSeverity.ERROR,
                    f"Clause {i} must be an object, got: {type(clause).__name__}",
                    field=f"clauses[{i}]"
                )
                continue
                
            # Check required fields
            for field in required_clause_fields:
                if field not in clause:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Missing required field in clause {i}: {field}",
                        field=f"clauses[{i}].{field}"
                    )
                    
            # Validate clause ID uniqueness
            if 'id' in clause:
                clause_id = clause['id']
                if clause_id in clause_ids:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Duplicate clause ID: {clause_id}",
                        field=f"clauses[{i}].id",
                        value=clause_id
                    )
                else:
                    clause_ids.add(clause_id)
                    
            # Validate confidence score
            if 'confidence' in clause:
                confidence = clause['confidence']
                if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Clause confidence must be between 0 and 1, got: {confidence}",
                        field=f"clauses[{i}].confidence",
                        value=confidence
                    )
                elif confidence < 0.6:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"Low confidence clause (ID: {clause.get('id', i)}): {confidence:.2f}",
                        field=f"clauses[{i}].confidence",
                        value=confidence,
                        suggestion="Consider manual review for low confidence clauses"
                    )
                    
            # Validate text content
            if 'text' in clause:
                text = clause['text']
                if not isinstance(text, str):
                    report.add_issue(
                        ValidationSeverity.ERROR,
                        f"Clause text must be string, got: {type(text).__name__}",
                        field=f"clauses[{i}].text"
                    )
                elif len(text.strip()) < 10:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"Suspiciously short clause text: '{text}'",
                        field=f"clauses[{i}].text",
                        value=text
                    )
                    
    def _validate_metadata(self, metadata: dict[str, Any], report: ValidationReport) -> None:
        """Validate metadata section."""
        if not isinstance(metadata, dict):
            report.add_issue(
                ValidationSeverity.ERROR,
                f"Metadata must be an object, got: {type(metadata).__name__}",
                field="metadata"
            )
            return
            
        # Check for required metadata fields
        required_metadata = ['extraction_timestamp', 'model_version']
        
        for field in required_metadata:
            if field not in metadata:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    f"Missing recommended metadata field: {field}",
                    field=f"metadata.{field}",
                    suggestion=f"Include {field} for better traceability"
                )
                
    def _validate_consistency(self, result: dict[str, Any], report: ValidationReport) -> None:
        """Validate internal consistency across sections."""
        # Check if confidence scores are consistent
        doc_confidence = result.get('document_info', {}).get('overall_confidence')
        clauses = result.get('clauses', [])
        
        if doc_confidence is not None and clauses:
            clause_confidences = [
                c.get('confidence', 0) for c in clauses 
                if isinstance(c, dict) and 'confidence' in c
            ]
            
            if clause_confidences:
                avg_clause_confidence = sum(clause_confidences) / len(clause_confidences)
                confidence_diff = abs(doc_confidence - avg_clause_confidence)
                
                if confidence_diff > 0.2:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"Large discrepancy between document confidence ({doc_confidence:.2f}) "
                        f"and average clause confidence ({avg_clause_confidence:.2f})",
                        field="overall_confidence_consistency",
                        suggestion="Review confidence calculation methodology"
                    )

class RobustErrorHandler:
    """Comprehensive error handling and recovery."""
    
    def __init__(self):
        self.config = get_config()
        self.error_counts: dict[str, int] = {}
        
    def handle_extraction_error(self, error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle extraction errors with detailed reporting."""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_report = {
            'error_type': error_type,
            'error_message': str(error),
            'error_count': self.error_counts[error_type],
            'context': context,
            'timestamp': lambda: datetime(2025, 1, 1)().isoformat(),
            'recovery_suggestions': self._get_recovery_suggestions(error_type)
        }
        
        logger.error("Extraction error: %s", error_report)
        
        # Attempt error recovery
        if self._should_retry(error_type):
            error_report['retry_recommended'] = True
            error_report['retry_delay_seconds'] = self._get_retry_delay(error_type)
        else:
            error_report['retry_recommended'] = False
            
        return error_report
        
    def _get_recovery_suggestions(self, error_type: str) -> list[str]:
        """Get context-specific recovery suggestions."""
        suggestions_map = {
            'FileNotFoundError': [
                "Verify file path is correct",
                "Check file permissions",
                "Ensure file has not been moved or deleted"
            ],
            'PermissionError': [
                "Check file read permissions",
                "Run with appropriate user permissions",
                "Verify file is not locked by another process"
            ],
            'ValidationError': [
                "Check input format compliance",
                "Verify required fields are present",
                "Review data types and ranges"
            ],
            'MemoryError': [
                "Reduce processing batch size",
                "Enable document streaming for large files",
                "Increase available system memory"
            ],
            'TimeoutError': [
                "Increase processing timeout limits",
                "Check system resource availability",
                "Consider processing file in smaller chunks"
            ]
        }
        
        return suggestions_map.get(error_type, ["Review error details and system logs"])
        
    def _should_retry(self, error_type: str) -> bool:
        """Determine if error type should be retried."""
        retryable_errors = {
            'TimeoutError', 'ConnectionError', 'TemporaryError',
            'ResourceBusyError', 'ServiceUnavailableError'
        }
        return error_type in retryable_errors
        
    def _get_retry_delay(self, error_type: str) -> float:
        """Get recommended retry delay for error type."""
        delay_map = {
            'TimeoutError': 5.0,
            'ConnectionError': 2.0,
            'ResourceBusyError': 1.0,
            'ServiceUnavailableError': 10.0
        }
        return delay_map.get(error_type, 3.0)

# Global instances for Generation 2
extraction_validator = ExtractionResultValidator()
error_handler = RobustErrorHandler()

def validate_extraction_comprehensive(result: dict[str, Any]) -> ValidationReport:
    """High-level extraction result validation."""
    return extraction_validator.validate_extraction_result(result)

def handle_processing_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
    """High-level error handling."""
    return error_handler.handle_extraction_error(error, context)