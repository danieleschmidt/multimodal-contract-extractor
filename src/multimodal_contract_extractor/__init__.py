"""Core package for the Multimodal Contract Extractor."""

__version__ = "0.1.0"

from .adaptive_processing import (
    AdaptiveProcessingResult,
    ProcessingAttempt,
    process_with_adaptive_pipeline,
)
from .advanced_classification import (
    classify_clause_advanced,
    get_all_contract_types,
    identify_contract_type,
    is_specialized_contract_type,
)
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
from .language_detection import (
    detect_document_language,
    get_language_config,
    get_supported_languages,
    is_language_supported,
)
from .security import (
    SecurityError,
    sanitize_file_path,
    validate_file_input,
    validate_output_path,
)
from .serialization import (
    DocumentInfo,
    ExtractionResult,
    export_to_file,
    get_format_info,
    get_supported_formats,
    serialize_to_csv,
    serialize_to_json,
    serialize_to_toml,
    serialize_to_xml,
    serialize_to_yaml,
    serialize_with_validation,
    validate_extraction_result,
)
from .websocket_server import (
    CollaborationMessage,
    ProcessingProgressTracker,
    ProcessingStatus,
    WebSocketManager,
    start_websocket_server,
    websocket_manager,
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
    "detect_document_language",
    "extract_from_document",
    "get_config",
    "get_language_config",
    "get_supported_languages",
    "is_language_supported",
    "classify_clause_advanced",
    "identify_contract_type",
    "get_all_contract_types",
    "is_specialized_contract_type",
    "process_with_adaptive_pipeline",
    "AdaptiveProcessingResult",
    "ProcessingAttempt",
    "WebSocketManager",
    "ProcessingStatus",
    "CollaborationMessage",
    "ProcessingProgressTracker",
    "websocket_manager",
    "start_websocket_server",
    "load_config",
    "load_document",
    "reload_config",
    "sanitize_file_path",
    "serialize_to_csv",
    "serialize_to_json",
    "serialize_to_xml",
    "serialize_to_yaml",
    "serialize_to_toml",
    "serialize_with_validation",
    "validate_extraction_result",
    "get_supported_formats",
    "get_format_info",
    "export_to_file",
    "stream_document",
    "validate_file_input",
    "validate_output_path",
]
