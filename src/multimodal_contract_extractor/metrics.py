from __future__ import annotations

from pathlib import Path
import resource

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, write_to_textfile

registry = CollectorRegistry()
PROCESSING_TIME = Histogram("processing_time_seconds", "Time spent processing a document", registry=registry)
PAGES_PROCESSED = Counter("pages_processed_total", "Total number of document pages processed", registry=registry)
MEMORY_USAGE = Gauge("max_memory_bytes", "Maximum resident set size in bytes", registry=registry)


def record_memory_usage() -> None:
    """Record the current process memory usage in ``MEMORY_USAGE``."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is kilobytes on Linux
    MEMORY_USAGE.set(usage * 1024)


def save_metrics(path: str | Path) -> None:
    """Write collected metrics to ``path`` in Prometheus text format."""
    write_to_textfile(str(path), registry)
