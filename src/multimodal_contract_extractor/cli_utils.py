from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from .security import sanitize_request_id

if TYPE_CHECKING:
    import argparse

# Import dynamically to check availability
def get_supported_formats():
    """Get supported formats based on available dependencies."""
    from .serialization import get_supported_formats
    return set(get_supported_formats())

SUPPORTED_FORMATS = {"json", "xml", "csv", "yaml", "toml"}  # All possible formats


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared CLI options to ``parser``."""
    parser.add_argument(
        "--output-format",
        "--format",
        default="json",
        help="Output format: json, xml, csv, yaml, or toml (depending on installed dependencies)",
    )
    parser.add_argument(
        "--include-coordinates",
        action="store_true",
        help="Include coordinates in CSV output",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Output logs in JSON format",
    )
    parser.add_argument(
        "--metrics-file",
        default=None,
        help="Path to write metrics file",
    )
    parser.add_argument(
        "--metrics-format",
        default="prometheus",
        choices=["prometheus", "json"],
        help="Metrics output format: prometheus (default) or json",
    )


class _RequestIdFilter(logging.Filter):
    def __init__(self, request_id: str) -> None:
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        record.request_id = self.request_id
        return True


def setup_logging(
    level: str = "info", *, json_logs: bool = False, request_id: str | None = None
) -> logging.Logger:
    """Configure and return a module-level logger."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.handlers.clear()
    fmt = "%(levelname)s:%(name)s:%(message)s"
    if json_logs:
        fmt = '{"level":"%(levelname)s","name":"%(name)s","message":"%(message)s","request_id":"%(request_id)s"}'
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    rid = sanitize_request_id(request_id or "-")
    handler.addFilter(_RequestIdFilter(rid))
    logger.setLevel(numeric)
    logger.addHandler(handler)
    return logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe version of ``name``."""
    clean = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", clean)


def build_output_path(base: str | None, fmt: str) -> Path:
    """Construct a sanitized output path for CLI commands."""
    if base:
        path = Path(base)
        if path.suffix == "":
            path = path.with_suffix(f".{fmt}")
        if not path.parent.exists():
            msg = f"Output directory not found: {path.parent}"
            raise FileNotFoundError(msg)
    else:
        path = Path(f"result.{fmt}")

    return path.parent / sanitize_filename(path.name)


def process_single_document(file_path: str, output_path: str = None, output_format: str = "json", format: str = None) -> dict:
    """Process a single document and return extraction results.
    
    Args:
        file_path: Path to the document to process
        output_path: Optional output file path
        output_format: Output format (json, xml, csv, yaml, toml)
        format: Alias for output_format (for compatibility)
        
    Returns:
        Dictionary containing extraction results
    """
    from . import extract_from_document, load_document, save_results

    # Use format if provided (for compatibility)
    if format is not None:
        output_format = format

    # Load and process document
    document = load_document(file_path)
    result = extract_from_document(document)

    # Save results if output path specified
    if output_path:
        save_results(result, output_path, output_format)

    # Return as dictionary
    from dataclasses import asdict
    return asdict(result)
