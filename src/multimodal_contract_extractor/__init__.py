"""Core package for the Multimodal Contract Extractor."""

__version__ = "0.1.0"

from .document import Document, DocumentPage, load_document, stream_document
from .clause_detection import Clause, detect_clauses
from .serialization import (
    DocumentInfo,
    ExtractionResult,
    serialize_to_json,
    serialize_to_xml,
    serialize_to_csv,
)

__all__ = [
    "Document",
    "DocumentPage",
    "load_document",
    "stream_document",
    "Clause",
    "detect_clauses",
    "DocumentInfo",
    "ExtractionResult",
    "serialize_to_json",
    "serialize_to_xml",
    "serialize_to_csv",
    "__version__",
]
