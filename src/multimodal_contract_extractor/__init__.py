"""Core package for the Multimodal Contract Extractor."""

__version__ = "0.1.0"

from .clause_detection import Clause, detect_clauses
from .config import (
    Config,
    ConfigValidationError,
    get_config,
    load_config,
    reload_config,
)
from .document import Document, DocumentPage, load_document, stream_document
from .extraction import extract_from_document
from .security import (
    SecurityError,
    sanitize_file_path,
    validate_file_input,
    validate_output_path,
)
from .serialization import (
    DocumentInfo,
    ExtractionResult,
    serialize_to_csv,
    serialize_to_json,
    serialize_to_xml,
)

__all__ = [
    "Clause",
    "Config",
    "ConfigValidationError",
    "Document",
    "DocumentInfo",
    "DocumentPage",
    "ExtractionResult",
    "SecurityError",
    "__version__",
    "detect_clauses",
    "extract_from_document",
    "get_config",
    "load_config",
    "load_document",
    "reload_config",
    "sanitize_file_path",
    "serialize_to_csv",
    "serialize_to_json",
    "serialize_to_xml",
    "stream_document",
    "validate_file_input",
    "validate_output_path",
]
