"""High-level extraction functions that bridge OCR detection with structured output."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .adaptive_processing import process_with_adaptive_pipeline
from .advanced_classification import classify_clause_advanced, identify_contract_type
from .advanced_error_handling import (
    ContractProcessingError,
    ErrorSeverity,
    with_error_handling,
)
from .clause_detection import detect_clauses
from .comprehensive_validation import ValidationLevel, validate_extraction_result
from .config import get_config
from .document import Document, load_document, stream_document
from .enterprise_security import ThreatLevel, get_audit_logger, get_threat_detector
from .metrics import (
    PROCESSING_TIME,
    record_clauses_detected,
    record_document_processed,
    record_pages_processed,
)
from .neuromorphic_engine import analyze_with_neuromorphic_computing
from .performance_optimization import (
    OptimizationStrategy,
    optimize_performance,
)
from .quantum_analysis import analyze_with_quantum_computing

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@optimize_performance(
    cache_key=None,  # Auto-generate based on file path and settings
    cache_ttl=3600.0,  # Cache for 1 hour
    enable_parallel=True,
    optimization_strategy=OptimizationStrategy.ADAPTIVE
)
@with_error_handling(
    component="extraction",
    operation="extract_from_document",
    severity=ErrorSeverity.HIGH,
    max_retries=2,
    retry_delay=2.0
)
def extract_from_document(file_path: Path, *,
                         language_code: str | None = None,
                         enable_advanced_classification: bool = True,
                         enable_adaptive_processing: bool = True,
                         enable_neuromorphic_analysis: bool = True,
                         enable_quantum_analysis: bool = True,
                         validation_level: ValidationLevel = ValidationLevel.STANDARD,
                         enable_security_scanning: bool = True) -> dict[str, Any]:
    """Extract clauses from a document and return structured JSON-compatible data.

    This function provides the main extraction pipeline that:
    1. Loads the document
    2. Detects clauses using OCR with multi-language support
    3. Performs advanced clause classification for specialized contract types
    4. Formats the output to match the documented JSON structure

    Parameters
    ----------
    file_path : Path
        Path to the document to process
    language_code : str, optional
        Specific language code to use for processing. If None, language will be auto-detected.
    enable_advanced_classification : bool
        Whether to enable advanced clause classification for specialized contract types.
    enable_adaptive_processing : bool
        Whether to enable adaptive processing pipeline for low-confidence extractions.
    enable_neuromorphic_analysis : bool
        Whether to enable neuromorphic computing analysis for advanced pattern recognition.
    enable_quantum_analysis : bool
        Whether to enable quantum-inspired analysis for complex clause relationships.
    validation_level : ValidationLevel
        Level of validation to perform on extraction results.
    enable_security_scanning : bool
        Whether to perform security scanning on input files.

    Returns
    -------
    Dict[str, Any]
        Structured extraction result matching the documented JSON format
    """
    # Record processing time with Prometheus histogram
    with PROCESSING_TIME.time():
        start_time = time.perf_counter()

        # Initialize security and audit logging
        audit_logger = get_audit_logger() if enable_security_scanning else None
        threat_detector = get_threat_detector() if enable_security_scanning else None

        try:
            # Security scanning
            if enable_security_scanning:
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="document_processing_started",
                        severity=ThreatLevel.INFO,
                        resource=str(file_path),
                        action="extract_from_document",
                        outcome="started"
                    )

                if threat_detector:
                    # Scan file for threats
                    threat_scan = threat_detector.scan_file(file_path)
                    if threat_scan["risk_score"] > 0.5:
                        if audit_logger:
                            audit_logger.log_security_event(
                                event_type="high_risk_file_detected",
                                severity=ThreatLevel.HIGH,
                                resource=str(file_path),
                                action="threat_scan",
                                outcome="threat_detected",
                                details=threat_scan
                            )
                        logger.warning("High-risk file detected: %s", threat_scan)
                        # Continue processing but log the risk

            logger.info("Starting extraction for %s", file_path.name)

            # Adaptive document loading: use streaming for large files to optimize memory usage
            document = _load_document_adaptive(file_path)

            # Use adaptive processing pipeline if enabled
            if enable_adaptive_processing:
                adaptive_result = process_with_adaptive_pipeline(
                    document,
                    language_code=language_code or "en"
                )
                clauses = adaptive_result.final_clauses

                # Log adaptive processing results
                logger.info(
                    "Adaptive processing completed: strategy=%s, improvement=%s, attempts=%d",
                    adaptive_result.processing_strategy,
                    adaptive_result.improvement_achieved,
                    len(adaptive_result.attempts_made)
                )
            else:
                clauses = detect_clauses(document, language_code=language_code)

            # Perform advanced classification if enabled
            if enable_advanced_classification:
                clauses = _enhance_clauses_with_advanced_classification(clauses, language_code or "en")

            processing_time = time.perf_counter() - start_time

            # Record metrics
            record_pages_processed(len(document.pages))

            # Count clauses by type for metrics
            clause_counts = {}
            for clause in clauses:
                clause_counts[clause.type] = clause_counts.get(clause.type, 0) + 1

            if clause_counts:
                record_clauses_detected(clause_counts)

            # Record successful processing
            record_document_processed("success")

            result = _build_extraction_result(document, clauses, processing_time, enable_advanced_classification)

            # Add adaptive processing metadata if it was used
            if enable_adaptive_processing and 'adaptive_result' in locals():
                result["metadata"]["adaptive_processing"] = {
                    "strategy_used": adaptive_result.processing_strategy,
                    "improvement_achieved": adaptive_result.improvement_achieved,
                    "total_attempts": len(adaptive_result.attempts_made),
                    "consensus_confidence": round(adaptive_result.consensus_confidence, 3),
                    "processing_time": round(adaptive_result.total_processing_time, 2)
                }

            # Perform neuromorphic analysis if enabled
            if enable_neuromorphic_analysis:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    neuromorphic_result = loop.run_until_complete(
                        analyze_with_neuromorphic_computing(
                            result["document_info"],
                            result["clauses"]
                        )
                    )
                    result["metadata"]["neuromorphic_analysis"] = neuromorphic_result
                    logger.info("Neuromorphic analysis completed with %d neural spikes",
                              neuromorphic_result.get("total_spikes", 0))

                    loop.close()
                except Exception as e:
                    logger.warning("Neuromorphic analysis failed: %s", e)
                    result["metadata"]["neuromorphic_analysis"] = {"error": str(e)}

            # Perform quantum analysis if enabled
            if enable_quantum_analysis:
                try:
                    if 'loop' not in locals():
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    quantum_result = loop.run_until_complete(
                        analyze_with_quantum_computing(
                            result["clauses"],
                            enable_entanglement=True,
                            enable_interference=True
                        )
                    )
                    result["metadata"]["quantum_analysis"] = quantum_result
                    logger.info("Quantum analysis completed with %.3f confidence",
                              quantum_result.get("quantum_confidence", 0.0))

                    if 'loop' in locals():
                        loop.close()
                except Exception as e:
                    logger.warning("Quantum analysis failed: %s", e)
                    result["metadata"]["quantum_analysis"] = {"error": str(e)}

            # Perform comprehensive validation
            try:
                validation_report = validate_extraction_result(result, validation_level)
                result["metadata"]["validation"] = {
                    "validation_id": validation_report.validation_id,
                    "level": validation_report.validation_level.value,
                    "success_rate": validation_report.success_rate,
                    "is_valid": validation_report.is_valid,
                    "total_checks": validation_report.total_checks,
                    "warning_count": len(validation_report.warning_issues),
                    "error_count": len(validation_report.failed_issues),
                    "critical_count": len(validation_report.critical_issues),
                    "execution_time": validation_report.execution_time
                }

                if not validation_report.is_valid:
                    logger.warning(
                        "Validation issues found: %d errors, %d critical",
                        len(validation_report.failed_issues),
                        len(validation_report.critical_issues)
                    )

                    if audit_logger:
                        audit_logger.log_security_event(
                            event_type="validation_issues_found",
                            severity=ThreatLevel.MEDIUM if validation_report.has_critical_issues else ThreatLevel.LOW,
                            resource=str(file_path),
                            action="validation",
                            outcome="issues_detected",
                            details={
                                "error_count": len(validation_report.failed_issues),
                                "critical_count": len(validation_report.critical_issues)
                            }
                        )

                logger.info("Validation completed with %.1f%% success rate",
                          validation_report.success_rate * 100)

            except Exception as e:
                logger.error("Validation failed: %s", e)
                result["metadata"]["validation"] = {"error": str(e)}

            # Final security audit log
            if audit_logger:
                audit_logger.log_security_event(
                    event_type="document_processing_completed",
                    severity=ThreatLevel.INFO,
                    resource=str(file_path),
                    action="extract_from_document",
                    outcome="success",
                    details={
                        "clauses_extracted": len(clauses),
                        "processing_time": processing_time,
                        "features_enabled": {
                            "neuromorphic": enable_neuromorphic_analysis,
                            "quantum": enable_quantum_analysis,
                            "validation": validation_level.value
                        }
                    }
                )

            logger.info(
                "Extraction completed for %s: %d clauses found in %.2fs",
                file_path.name,
                len(clauses),
                processing_time,
            )

            return result

        except Exception as e:
            # Record failed processing
            record_document_processed("error")

            # Security audit log for failure
            if audit_logger:
                audit_logger.log_security_event(
                    event_type="document_processing_failed",
                    severity=ThreatLevel.HIGH,
                    resource=str(file_path),
                    action="extract_from_document",
                    outcome="failure",
                    details={"error": str(e), "error_type": type(e).__name__}
                )

            logger.exception("Extraction failed for %s: %s", file_path.name, e)

            # Wrap in ContractProcessingError for better error handling
            if not isinstance(e, ContractProcessingError):
                raise ContractProcessingError(
                    f"Document extraction failed: {str(e)}",
                    ErrorSeverity.HIGH
                ) from e
            raise


def _build_extraction_result(
    document: Document, clauses: list, processing_time: float
) -> dict[str, Any]:
    """Build the structured extraction result.

    Parameters
    ----------
    document : Document
        The processed document
    clauses : list
        Detected clauses
    processing_time : float
        Processing time in seconds

    Returns
    -------
    Dict[str, Any]
        Structured extraction result
    """
    # Calculate overall confidence (simple average for now)
    if clauses:
        overall_confidence = sum(
            _calculate_clause_confidence(clause) for clause in clauses
        ) / len(clauses)
    else:
        overall_confidence = (
            1.0  # High confidence when no clauses found means OCR worked
        )

    # Identify contract type using advanced classification if enabled
    document_type = _infer_document_type(clauses)
    contract_type_scores = {}

    if enable_advanced_classification:
        clause_tuples = [(clause.type, clause.text) for clause in clauses]
        contract_type_scores = identify_contract_type(clause_tuples)

        # Override document type with highest scoring contract type if confident enough
        if contract_type_scores:
            best_type = max(contract_type_scores.keys(), key=lambda k: contract_type_scores[k])
            if contract_type_scores[best_type] > 0.6:
                document_type = best_type

    # Build document info
    document_info = {
        "filename": document.path.name,
        "pages": len(document.pages),
        "processing_time": round(processing_time, 2),
        "overall_confidence": round(overall_confidence, 2),
        "document_type": document_type,
    }

    # Add contract type scores if advanced classification was used
    if enable_advanced_classification and contract_type_scores:
        document_info["contract_type_scores"] = {
            k: round(v, 3) for k, v in contract_type_scores.items() if v > 0.1
        }

    # Build result in documented JSON format
    return {
        "document_info": document_info,
        "clauses": [
            {
                "id": clause.id
                or f"clause_{i:03d}",  # Use clause ID if available, fallback to generated
                "type": clause.type,
                "text": clause.text,
                "page": clause.page,
                "coordinates": clause.coordinates
                if clause.coordinates is not None
                else [],
                "confidence": clause.confidence
                if hasattr(clause, "confidence")
                else _calculate_clause_confidence(clause),
                "key_terms": clause.key_terms
                if hasattr(clause, "key_terms")
                else _extract_key_terms(clause),
                # Add advanced classification results if available
                **(_get_advanced_clause_data(clause) if enable_advanced_classification
                   and hasattr(clause, 'advanced_classification') else {})
            }
            for i, clause in enumerate(clauses, 1)
        ],
        "metadata": {
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": "v0.1.0-ocr-multilang",
            "processing_method": "ocr_keyword_detection" + ("_advanced" if enable_advanced_classification else "") + ("_adaptive" if enable_adaptive_processing else "") + ("_neuromorphic" if enable_neuromorphic_analysis else "") + ("_quantum" if enable_quantum_analysis else ""),
            "features_enabled": {
                "multi_language_support": True,
                "advanced_classification": enable_advanced_classification,
                "adaptive_processing": enable_adaptive_processing,
                "neuromorphic_analysis": enable_neuromorphic_analysis,
                "quantum_analysis": enable_quantum_analysis,
            }
        },
    }


def _calculate_clause_confidence(clause) -> float:
    """Calculate confidence score for a detected clause.

    For now, this is a simple heuristic based on text length and type.
    In the future, this could integrate ML-based confidence scoring.
    """
    # Base confidence for keyword detection
    config = get_config()
    base_confidence = config.extraction.base_confidence_score

    # Bonus for longer text (more context)
    length_bonus = min(0.15, len(clause.text) / config.extraction.length_bonus_divisor)

    # Bonus for specific clause types that are easier to detect
    type_bonus = {
        "confidentiality": 0.05,
        "termination": 0.03,
        "payment_terms": 0.02,
    }.get(clause.type, 0.0)

    confidence = base_confidence + length_bonus + type_bonus
    return round(min(confidence, config.extraction.max_confidence_cap), 2)


def _extract_key_terms(clause) -> list[str]:
    """Extract key terms from clause text for highlighting."""
    # Simple extraction based on common legal terms
    # In the future, this could use NLP for better term extraction
    text_lower = clause.text.lower()

    key_terms = []

    # Look for monetary amounts
    import re

    money_pattern = r"\$[\d,]+(?:\.\d{2})?"
    money_matches = re.findall(money_pattern, clause.text)
    key_terms.extend(money_matches)

    # Look for time periods
    time_pattern = r"\b\d+\s*(?:days?|weeks?|months?|years?)\b"
    time_matches = re.findall(time_pattern, clause.text, re.IGNORECASE)
    key_terms.extend(time_matches)

    # Add clause-specific terms
    clause_keywords = {
        "confidentiality": ["confidential", "proprietary", "non-disclosure"],
        "termination": ["terminate", "termination", "end", "expire"],
        "payment_terms": ["payment", "compensation", "salary", "fee"],
        "liability": ["liable", "liability", "damages", "responsible"],
        "governing_law": ["governing law", "jurisdiction", "governed by"],
        "dispute_resolution": ["dispute", "arbitration", "mediation", "court"],
    }

    if clause.type in clause_keywords:
        for keyword in clause_keywords[clause.type]:
            if keyword in text_lower:
                # Find the actual case from original text
                start_idx = text_lower.find(keyword)
                if start_idx >= 0:
                    actual_term = clause.text[start_idx : start_idx + len(keyword)]
                    key_terms.append(actual_term)

    return list(set(key_terms))  # Remove duplicates


def _infer_document_type(clauses) -> str:
    """Infer document type based on detected clause types with enhanced logic."""
    if not clauses:
        return "unknown"

    clause_types = {clause.type for clause in clauses}

    # Enhanced heuristics for document type classification
    # Check for specialized contract types first
    if "licensing" in clause_types or "intellectual_property" in clause_types:
        return "licensing_agreement"
    if "merger_acquisition" in clause_types:
        return "merger_acquisition"
    if "trade_agreement" in clause_types or ("import" in str(clauses).lower() and "export" in str(clauses).lower()):
        return "trade_agreement"

    # Traditional classification logic
    if "confidentiality" in clause_types and len(clause_types) <= 3:
        return "nda"
    if "payment_terms" in clause_types and "termination" in clause_types:
        # Check for employment-specific terms
        all_text = " ".join([clause.text.lower() for clause in clauses])
        if any(term in all_text for term in ["employee", "employer", "salary", "wages"]):
            return "employment_agreement"
        else:
            return "service_agreement"
    if "liability" in clause_types and "governing_law" in clause_types:
        return "service_agreement"
    if "lease" in str(clauses).lower() or "rent" in str(clauses).lower():
        return "lease_agreement"

    return "general_contract"


def _load_document_adaptive(file_path: Path) -> Document:
    """Load document using adaptive strategy based on file size.

    For large files (> 10MB), use streaming to manage memory usage.
    For smaller files, use standard loading for faster access.

    Parameters
    ----------
    file_path : Path
        Path to the document to load

    Returns
    -------
    Document
        Loaded document object
    """
    # Define size threshold for streaming
    config = get_config()
    SIZE_THRESHOLD = (
        config.extraction.file_size_threshold_mb * 1024 * 1024
    )  # Convert MB to bytes

    try:
        file_size = file_path.stat().st_size

        if file_path.suffix.lower() == ".pdf" and file_size > SIZE_THRESHOLD:
            logger.info(
                "Large PDF detected (%d MB), using streaming approach",
                file_size // (1024 * 1024),
            )
            # Use streaming for large PDFs
            pages = list(
                stream_document(
                    file_path, chunk_size=config.extraction.streaming_chunk_size
                )
            )
            return Document(path=file_path, pages=pages)
        logger.debug("Using standard loading for file size: %d bytes", file_size)
        return load_document(file_path)

    except OSError as e:
        logger.warning(
            "Could not determine file size, falling back to standard loading: %s", e
        )
        return load_document(file_path)


def _enhance_clauses_with_advanced_classification(clauses: list, language_code: str) -> list:
    """Enhance clauses with advanced classification results."""
    enhanced_clauses = []

    for clause in clauses:
        # Perform advanced classification
        advanced_result = classify_clause_advanced(
            clause.text, clause.type, language_code
        )

        # Store advanced classification results on the clause object
        clause.advanced_classification = advanced_result

        # Update confidence if advanced classification provides higher confidence
        if advanced_result.confidence > clause.confidence:
            clause.confidence = advanced_result.confidence

        enhanced_clauses.append(clause)

    return enhanced_clauses


def _get_advanced_clause_data(clause) -> dict[str, Any]:
    """Extract advanced classification data from a clause object."""
    if not hasattr(clause, 'advanced_classification'):
        return {}

    advanced = clause.advanced_classification
    return {
        "legal_significance": advanced.legal_significance,
        "contract_types": advanced.contract_types,
        "keywords_matched": advanced.keywords_matched,
        "context_indicators": advanced.context_indicators,
        "advanced_confidence": round(advanced.confidence, 3),
    }
