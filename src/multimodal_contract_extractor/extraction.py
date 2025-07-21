"""High-level extraction functions that bridge OCR detection with structured output."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import logging

from .document import load_document, stream_document, Document
from .clause_detection import detect_clauses
from .config import get_config
from .metrics import (
    record_document_processed, 
    record_clauses_detected, 
    record_pages_processed,
    PROCESSING_TIME
)

logger = logging.getLogger(__name__)


def extract_from_document(file_path: Path) -> Dict[str, Any]:
    """Extract clauses from a document and return structured JSON-compatible data.
    
    This function provides the main extraction pipeline that:
    1. Loads the document
    2. Detects clauses using OCR
    3. Formats the output to match the documented JSON structure
    
    Parameters
    ----------
    file_path : Path
        Path to the document to process
        
    Returns
    -------
    Dict[str, Any]
        Structured extraction result matching the documented JSON format
    """
    # Record processing time with Prometheus histogram
    with PROCESSING_TIME.time():
        start_time = time.perf_counter()
        
        try:
            logger.info("Starting extraction for %s", file_path.name)
            
            # Adaptive document loading: use streaming for large files to optimize memory usage
            document = _load_document_adaptive(file_path)
            clauses = detect_clauses(document)
            
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
            
            result = _build_extraction_result(document, clauses, processing_time)
            
            logger.info(
                "Extraction completed for %s: %d clauses found in %.2fs", 
                file_path.name, len(clauses), processing_time
            )
            
            return result
            
        except Exception as e:
            # Record failed processing
            record_document_processed("error")
            logger.error("Extraction failed for %s: %s", file_path.name, e)
            raise


def _build_extraction_result(document: Document, clauses: list, processing_time: float) -> Dict[str, Any]:
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
        overall_confidence = sum(_calculate_clause_confidence(clause) for clause in clauses) / len(clauses)
    else:
        overall_confidence = 1.0  # High confidence when no clauses found means OCR worked
    
    # Build result in documented JSON format
    result = {
        "document_info": {
            "filename": document.path.name,
            "pages": len(document.pages),
            "processing_time": round(processing_time, 2),
            "overall_confidence": round(overall_confidence, 2),
            "document_type": _infer_document_type(clauses)
        },
        "clauses": [
            {
                "id": f"clause_{i:03d}",
                "type": clause.type,
                "text": clause.text,
                "page": clause.page,
                "coordinates": clause.coordinates,
                "confidence": _calculate_clause_confidence(clause),
                "key_terms": _extract_key_terms(clause)
            }
            for i, clause in enumerate(clauses, 1)
        ],
        "metadata": {
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": "v0.1.0-ocr",
            "processing_method": "ocr_keyword_detection"
        }
    }
    
    return result


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
    money_pattern = r'\$[\d,]+(?:\.\d{2})?'
    money_matches = re.findall(money_pattern, clause.text)
    key_terms.extend(money_matches)
    
    # Look for time periods
    time_pattern = r'\b\d+\s*(?:days?|weeks?|months?|years?)\b'
    time_matches = re.findall(time_pattern, clause.text, re.IGNORECASE)
    key_terms.extend(time_matches)
    
    # Add clause-specific terms
    clause_keywords = {
        "confidentiality": ["confidential", "proprietary", "non-disclosure"],
        "termination": ["terminate", "termination", "end", "expire"],
        "payment_terms": ["payment", "compensation", "salary", "fee"],
        "liability": ["liable", "liability", "damages", "responsible"],
        "governing_law": ["governing law", "jurisdiction", "governed by"],
        "dispute_resolution": ["dispute", "arbitration", "mediation", "court"]
    }
    
    if clause.type in clause_keywords:
        for keyword in clause_keywords[clause.type]:
            if keyword in text_lower:
                # Find the actual case from original text
                start_idx = text_lower.find(keyword)
                if start_idx >= 0:
                    actual_term = clause.text[start_idx:start_idx + len(keyword)]
                    key_terms.append(actual_term)
    
    return list(set(key_terms))  # Remove duplicates


def _infer_document_type(clauses) -> str:
    """Infer document type based on detected clause types."""
    if not clauses:
        return "unknown"
    
    clause_types = set(clause.type for clause in clauses)
    
    # Simple heuristics for document type classification
    if "confidentiality" in clause_types and len(clause_types) <= 3:
        return "nda"
    elif "payment_terms" in clause_types and "termination" in clause_types:
        return "employment_agreement"
    elif "liability" in clause_types and "governing_law" in clause_types:
        return "service_agreement"
    else:
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
    SIZE_THRESHOLD = config.extraction.file_size_threshold_mb * 1024 * 1024  # Convert MB to bytes
    
    try:
        file_size = file_path.stat().st_size
        
        if file_path.suffix.lower() == '.pdf' and file_size > SIZE_THRESHOLD:
            logger.info("Large PDF detected (%d MB), using streaming approach", file_size // (1024 * 1024))
            # Use streaming for large PDFs
            pages = list(stream_document(file_path, chunk_size=config.extraction.streaming_chunk_size))
            document = Document(path=file_path, pages=pages)
            return document
        else:
            logger.debug("Using standard loading for file size: %d bytes", file_size)
            return load_document(file_path)
            
    except (OSError, IOError) as e:
        logger.warning("Could not determine file size, falling back to standard loading: %s", e)
        return load_document(file_path)