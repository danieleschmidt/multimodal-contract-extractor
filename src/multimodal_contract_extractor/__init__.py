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
from .advanced_error_handling import (
    ErrorRecoveryManager,
    ErrorSeverity,
    get_error_manager,
    with_error_handling,
)
from .clause_detection import Clause, detect_clauses
from .comprehensive_validation import (
    ValidationLevel,
    ValidationReport,
    validate_extraction_result,
)
from .config import (
    Config,
    ConfigValidationError,
    get_config,
    load_config,
    reload_config,
)
from .distributed_computing import (
    ClusterCoordinator,
    DistributedConfig,
    get_distributed_processor,
)
from .document import Document, DocumentPage, load_document, stream_document
from .enterprise_security import (
    EnterpriseSecurityConfig,
    get_audit_logger,
    get_compliance_manager,
    get_encryption_manager,
)
from .extraction import extract_clauses, extract_from_document
from .language_detection import (
    detect_document_language,
    get_language_config,
    get_supported_languages,
    is_language_supported,
)
from .meta_learning_engine import (
    LegalDomain,
    LegalMetaLearningFramework,
    MetaLearningConfig,
    create_meta_learning_framework,
)

# Advanced Research Components (Generation 4+)
from .multimodal_transformer import (
    DocumentElement,
    LegalDocumentAnalyzer,
    MultimodalLegalTransformer,
    SpatialPosition,
    create_legal_document_analyzer,
)
from .neuromorphic_engine import (
    NeuromorphicConfig,
    NeuromorphicProcessor,
    analyze_with_neuromorphic_computing,
    get_neuromorphic_processor,
)
from .performance_optimization import (
    OptimizationStrategy,
    PerformanceConfig,
    get_performance_optimizer,
    optimize_performance,
)
from .quantum_analysis import (
    QuantumConfig,
    QuantumProcessor,
    analyze_with_quantum_computing,
    get_quantum_processor,
)
from .research_publication_framework import (
    ExperimentType,
    PublicationVenue,
    ResearchPublicationFramework,
    create_research_framework,
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
    save_results,
    serialize_to_csv,
    serialize_to_json,
    serialize_to_toml,
    serialize_to_xml,
    serialize_to_yaml,
    serialize_with_validation,
    validate_extraction_result,
)
from .variational_quantum_encoder import (
    QuantumFeatureMap,
    QuantumLegalAnalyzer,
    VariationalQuantumClassifier,
    create_quantum_legal_analyzer,
)
from .version import get_api_version, get_version
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
    "extract_clauses",
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
    "save_results",
    "stream_document",
    "validate_file_input",
    "validate_output_path",
    "analyze_with_neuromorphic_computing",
    "get_neuromorphic_processor",
    "NeuromorphicConfig",
    "NeuromorphicProcessor",
    "analyze_with_quantum_computing",
    "get_quantum_processor",
    "QuantumConfig",
    "QuantumProcessor",
    "ErrorRecoveryManager",
    "ErrorSeverity",
    "get_error_manager",
    "with_error_handling",
    "get_audit_logger",
    "get_encryption_manager",
    "get_compliance_manager",
    "EnterpriseSecurityConfig",
    "validate_extraction_result",
    "ValidationLevel",
    "ValidationReport",
    "get_performance_optimizer",
    "optimize_performance",
    "PerformanceConfig",
    "OptimizationStrategy",
    "get_distributed_processor",
    "DistributedConfig",
    "ClusterCoordinator",
    "get_version",
    "get_api_version",
    # Advanced Research Components
    "MultimodalLegalTransformer",
    "LegalDocumentAnalyzer",
    "create_legal_document_analyzer",
    "SpatialPosition",
    "DocumentElement",
    "QuantumLegalAnalyzer",
    "create_quantum_legal_analyzer",
    "VariationalQuantumClassifier",
    "QuantumFeatureMap",
    "LegalMetaLearningFramework",
    "create_meta_learning_framework",
    "LegalDomain",
    "MetaLearningConfig",
    "ResearchPublicationFramework",
    "create_research_framework",
    "PublicationVenue",
    "ExperimentType",
]
