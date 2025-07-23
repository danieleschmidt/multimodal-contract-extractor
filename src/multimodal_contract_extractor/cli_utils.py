from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from .security import sanitize_request_id

if TYPE_CHECKING:
    import argparse

SUPPORTED_FORMATS = {"json", "xml", "csv"}


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared CLI options to ``parser``."""
    parser.add_argument(
        "--output-format",
        "--format",
        default="json",
        help="Output format: json, xml, or csv",
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
