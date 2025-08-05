"""Processing result models for contract extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ProcessingStatus(Enum):
    """Status of document processing."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(Enum):
    """Stages of the processing pipeline."""

    VALIDATION = "validation"
    PREPROCESSING = "preprocessing"
    OCR_EXTRACTION = "ocr_extraction"
    CLAUSE_DETECTION = "clause_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    VALIDATION_FINAL = "validation_final"
    SERIALIZATION = "serialization"


@dataclass
class ValidationResult:
    """Result of document validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_size_bytes: Optional[int] = None
    file_type: Optional[str] = None
    pages_detected: Optional[int] = None

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'file_size_bytes': self.file_size_bytes,
            'file_type': self.file_type,
            'pages_detected': self.pages_detected,
        }


@dataclass
class ProcessingMetrics:
    """Metrics collected during processing."""

    # Timing metrics
    total_time_seconds: float = 0.0
    stage_times: Dict[str, float] = field(default_factory=dict)

    # Quality metrics
    ocr_confidence: float = 0.0
    clause_detection_confidence: float = 0.0
    overall_confidence: float = 0.0

    # Content metrics
    pages_processed: int = 0
    text_extracted_chars: int = 0
    clauses_detected: int = 0
    entities_extracted: int = 0

    # Performance metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    def add_stage_time(self, stage: ProcessingStage, time_seconds: float) -> None:
        """Add timing for a processing stage."""
        self.stage_times[stage.value] = time_seconds
        self.total_time_seconds += time_seconds

    def calculate_overall_confidence(self) -> None:
        """Calculate overall confidence from component confidences."""
        confidences = []

        if self.ocr_confidence > 0:
            confidences.append(self.ocr_confidence)
        if self.clause_detection_confidence > 0:
            confidences.append(self.clause_detection_confidence)

        if confidences:
            self.overall_confidence = sum(confidences) / len(confidences)
        else:
            self.overall_confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'total_time_seconds': self.total_time_seconds,
            'stage_times': self.stage_times,
            'ocr_confidence': self.ocr_confidence,
            'clause_detection_confidence': self.clause_detection_confidence,
            'overall_confidence': self.overall_confidence,
            'pages_processed': self.pages_processed,
            'text_extracted_chars': self.text_extracted_chars,
            'clauses_detected': self.clauses_detected,
            'entities_extracted': self.entities_extracted,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
        }


@dataclass
class ProcessingError:
    """Represents an error that occurred during processing."""

    stage: ProcessingStage
    error_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stack_trace: Optional[str] = None
    recoverable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'stage': self.stage.value,
            'error_type': self.error_type,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'stack_trace': self.stack_trace,
            'recoverable': self.recoverable,
        }


@dataclass
class ProcessingResult:
    """Complete result of document processing operation."""

    # Identifiers
    id: UUID = field(default_factory=uuid4)
    document_path: Optional[str] = None

    # Status and timing
    status: ProcessingStatus = ProcessingStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Results
    validation: Optional[ValidationResult] = None
    metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    contract: Optional[Any] = None  # Contract object
    extracted_data: Dict[str, Any] = field(default_factory=dict)

    # Error handling
    errors: List[ProcessingError] = field(default_factory=list)
    current_stage: ProcessingStage = ProcessingStage.VALIDATION

    # Configuration
    processing_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize processing result."""
        if self.validation is None:
            self.validation = ValidationResult(is_valid=True)

    def set_status(self, status: ProcessingStatus) -> None:
        """Update processing status."""
        self.status = status
        if status in {ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED}:
            self.completed_at = datetime.utcnow()

    def add_error(self, stage: ProcessingStage, error_type: str, message: str,
                  stack_trace: Optional[str] = None, recoverable: bool = False) -> None:
        """Add a processing error."""
        error = ProcessingError(
            stage=stage,
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            recoverable=recoverable
        )
        self.errors.append(error)

        # Set status to failed if error is not recoverable
        if not recoverable:
            self.set_status(ProcessingStatus.FAILED)

    def has_errors(self) -> bool:
        """Check if there are any processing errors."""
        return bool(self.errors)

    def has_non_recoverable_errors(self) -> bool:
        """Check if there are any non-recoverable errors."""
        return any(not error.recoverable for error in self.errors)

    def get_processing_time(self) -> Optional[float]:
        """Get total processing time in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return (
            self.status == ProcessingStatus.COMPLETED and
            not self.has_non_recoverable_errors() and
            self.validation and
            self.validation.is_valid
        )

    def get_success_rate(self) -> float:
        """Calculate success rate based on completed stages."""
        total_stages = len(ProcessingStage)

        if self.status == ProcessingStatus.COMPLETED:
            return 1.0
        elif self.status == ProcessingStatus.FAILED:
            # Calculate based on how far we got
            completed_stages = len(self.metrics.stage_times)
            return completed_stages / total_stages
        else:
            return 0.0

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the processing result."""
        summary = {
            'id': str(self.id),
            'status': self.status.value,
            'success': self.is_successful(),
            'success_rate': self.get_success_rate(),
            'document_path': self.document_path,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time_seconds': self.get_processing_time(),
            'current_stage': self.current_stage.value,
            'errors_count': len(self.errors),
            'has_warnings': bool(self.validation and self.validation.warnings),
        }

        # Add metrics summary
        if self.metrics:
            summary.update({
                'pages_processed': self.metrics.pages_processed,
                'clauses_detected': self.metrics.clauses_detected,
                'overall_confidence': self.metrics.overall_confidence,
                'total_time_seconds': self.metrics.total_time_seconds,
            })

        # Add validation summary
        if self.validation:
            summary.update({
                'validation_passed': self.validation.is_valid,
                'file_type': self.validation.file_type,
                'file_size_mb': round(self.validation.file_size_bytes / (1024 * 1024), 2) if self.validation.file_size_bytes else None,
            })

        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to complete dictionary representation."""
        return {
            'id': str(self.id),
            'document_path': self.document_path,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'validation': self.validation.to_dict() if self.validation else None,
            'metrics': self.metrics.to_dict(),
            'contract': self.contract.to_dict() if self.contract and hasattr(self.contract, 'to_dict') else None,
            'extracted_data': self.extracted_data,
            'errors': [error.to_dict() for error in self.errors],
            'current_stage': self.current_stage.value,
            'processing_config': self.processing_config,
            'summary': self.generate_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessingResult:
        """Create ProcessingResult from dictionary."""
        # Parse dates
        started_at = datetime.fromisoformat(data['started_at'])
        completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None

        # Parse validation
        validation = None
        if data.get('validation'):
            validation = ValidationResult(**data['validation'])

        # Parse metrics
        metrics = ProcessingMetrics()
        if data.get('metrics'):
            metrics_data = data['metrics']
            metrics.total_time_seconds = metrics_data.get('total_time_seconds', 0.0)
            metrics.stage_times = metrics_data.get('stage_times', {})
            metrics.ocr_confidence = metrics_data.get('ocr_confidence', 0.0)
            metrics.clause_detection_confidence = metrics_data.get('clause_detection_confidence', 0.0)
            metrics.overall_confidence = metrics_data.get('overall_confidence', 0.0)
            metrics.pages_processed = metrics_data.get('pages_processed', 0)
            metrics.text_extracted_chars = metrics_data.get('text_extracted_chars', 0)
            metrics.clauses_detected = metrics_data.get('clauses_detected', 0)
            metrics.entities_extracted = metrics_data.get('entities_extracted', 0)
            metrics.memory_usage_mb = metrics_data.get('memory_usage_mb', 0.0)
            metrics.cpu_usage_percent = metrics_data.get('cpu_usage_percent', 0.0)

        # Parse errors
        errors = []
        for error_data in data.get('errors', []):
            error = ProcessingError(
                stage=ProcessingStage(error_data['stage']),
                error_type=error_data['error_type'],
                message=error_data['message'],
                timestamp=datetime.fromisoformat(error_data['timestamp']),
                stack_trace=error_data.get('stack_trace'),
                recoverable=error_data.get('recoverable', False),
            )
            errors.append(error)

        return cls(
            id=UUID(data['id']),
            document_path=data.get('document_path'),
            status=ProcessingStatus(data['status']),
            started_at=started_at,
            completed_at=completed_at,
            validation=validation,
            metrics=metrics,
            extracted_data=data.get('extracted_data', {}),
            errors=errors,
            current_stage=ProcessingStage(data.get('current_stage', 'validation')),
            processing_config=data.get('processing_config', {}),
        )
