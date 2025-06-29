import argparse
import logging

SUPPORTED_FORMATS = {"json", "xml", "csv"}


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared CLI options to ``parser``."""
    parser.add_argument(
        "--output-format",
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


def setup_logging(level: str = "info") -> logging.Logger:
    """Configure and return a module-level logger."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(levelname)s:%(name)s:%(message)s")
    return logging.getLogger(__name__)
