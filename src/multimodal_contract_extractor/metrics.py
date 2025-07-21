from __future__ import annotations

from pathlib import Path
import resource
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, write_to_textfile, generate_latest

logger = logging.getLogger(__name__)

registry = CollectorRegistry()
PROCESSING_TIME = Histogram("multimodal_contract_processing_time_seconds", "Time spent processing a document", registry=registry)
PAGES_PROCESSED = Counter("multimodal_contract_pages_processed_total", "Total number of document pages processed", registry=registry)
MEMORY_USAGE = Gauge("multimodal_contract_memory_usage_bytes", "Maximum resident set size in bytes", registry=registry)
CLAUSES_DETECTED = Counter("multimodal_contract_clauses_detected_total", "Total number of clauses detected", ["clause_type"], registry=registry)
DOCUMENTS_PROCESSED = Counter("multimodal_contract_documents_processed_total", "Total number of documents processed", ["status"], registry=registry)
OCR_CACHE_HITS = Counter("multimodal_contract_ocr_cache_hits_total", "OCR cache hits", registry=registry)
OCR_CACHE_MISSES = Counter("multimodal_contract_ocr_cache_misses_total", "OCR cache misses", registry=registry)


def record_memory_usage() -> None:
    """Record the current process memory usage in ``MEMORY_USAGE``."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is kilobytes on Linux
    MEMORY_USAGE.set(usage * 1024)


def save_metrics(path: str | Path) -> None:
    """Write collected metrics to ``path`` in Prometheus text format."""
    write_to_textfile(str(path), registry)


def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus text format.
    
    Returns
    -------
    str
        Metrics in Prometheus exposition format
    """
    return generate_latest(registry).decode('utf-8')


def get_dashboard_metrics() -> Dict[str, Any]:
    """Get metrics formatted for dashboard consumption.
    
    Returns
    -------
    Dict[str, Any]
        Structured metrics data for dashboards
    """
    from .health import get_health_status
    
    # Get current metric values
    memory_usage = MEMORY_USAGE._value._value if hasattr(MEMORY_USAGE._value, '_value') else 0
    
    # Calculate processing statistics
    processing_stats = {
        "total_documents": _get_counter_value(DOCUMENTS_PROCESSED),
        "total_pages": _get_counter_value(PAGES_PROCESSED),
        "total_clauses": _get_counter_value(CLAUSES_DETECTED),
        "cache_hit_rate": _calculate_cache_hit_rate(),
        "average_processing_time": _get_average_processing_time(),
        "current_memory_usage": memory_usage
    }
    
    # Get system health
    system_health = get_health_status()
    
    # Get recent activity (placeholder for now)
    recent_activity = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "active_processes": 0,  # Would track active extraction processes
        "queue_length": 0       # Would track processing queue
    }
    
    return {
        "processing_stats": processing_stats,
        "system_health": system_health,
        "recent_activity": recent_activity,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def record_document_processed(status: str = "success") -> None:
    """Record that a document was processed.
    
    Parameters
    ----------
    status : str
        Processing status: 'success', 'error', 'timeout', etc.
    """
    DOCUMENTS_PROCESSED.labels(status=status).inc()


def record_clauses_detected(clause_counts: Dict[str, int]) -> None:
    """Record detected clauses by type.
    
    Parameters
    ----------
    clause_counts : Dict[str, int]
        Count of clauses detected by type
    """
    for clause_type, count in clause_counts.items():
        CLAUSES_DETECTED.labels(clause_type=clause_type).inc(count)


def record_pages_processed(count: int) -> None:
    """Record number of pages processed.
    
    Parameters
    ----------
    count : int
        Number of pages processed
    """
    PAGES_PROCESSED.inc(count)


def record_ocr_cache_hit() -> None:
    """Record an OCR cache hit."""
    OCR_CACHE_HITS.inc()


def record_ocr_cache_miss() -> None:
    """Record an OCR cache miss."""
    OCR_CACHE_MISSES.inc()


def _get_counter_value(counter) -> float:
    """Get the current value of a counter metric."""
    try:
        return counter._value._value if hasattr(counter._value, '_value') else 0
    except AttributeError:
        return 0


def _calculate_cache_hit_rate() -> float:
    """Calculate OCR cache hit rate."""
    hits = _get_counter_value(OCR_CACHE_HITS)
    misses = _get_counter_value(OCR_CACHE_MISSES)
    total = hits + misses
    
    if total == 0:
        return 0.0
    
    return round(hits / total * 100, 2)


def _get_average_processing_time() -> float:
    """Get average processing time from histogram."""
    try:
        # Get histogram data
        if hasattr(PROCESSING_TIME, '_sum') and hasattr(PROCESSING_TIME, '_count'):
            total_time = PROCESSING_TIME._sum._value if hasattr(PROCESSING_TIME._sum, '_value') else 0
            total_count = PROCESSING_TIME._count._value if hasattr(PROCESSING_TIME._count, '_value') else 0
            
            if total_count > 0:
                return round(total_time / total_count, 3)
        
        return 0.0
    except AttributeError:
        return 0.0


def reset_metrics() -> None:
    """Reset all metrics. Useful for testing."""
    global registry
    registry = CollectorRegistry()
    
    # Recreate metrics with new registry
    global PROCESSING_TIME, PAGES_PROCESSED, MEMORY_USAGE, CLAUSES_DETECTED
    global DOCUMENTS_PROCESSED, OCR_CACHE_HITS, OCR_CACHE_MISSES
    
    PROCESSING_TIME = Histogram("multimodal_contract_processing_time_seconds", "Time spent processing a document", registry=registry)
    PAGES_PROCESSED = Counter("multimodal_contract_pages_processed_total", "Total number of document pages processed", registry=registry)
    MEMORY_USAGE = Gauge("multimodal_contract_memory_usage_bytes", "Maximum resident set size in bytes", registry=registry)
    CLAUSES_DETECTED = Counter("multimodal_contract_clauses_detected_total", "Total number of clauses detected", ["clause_type"], registry=registry)
    DOCUMENTS_PROCESSED = Counter("multimodal_contract_documents_processed_total", "Total number of documents processed", ["status"], registry=registry)
    OCR_CACHE_HITS = Counter("multimodal_contract_ocr_cache_hits_total", "OCR cache hits", registry=registry)
    OCR_CACHE_MISSES = Counter("multimodal_contract_ocr_cache_misses_total", "OCR cache misses", registry=registry)
