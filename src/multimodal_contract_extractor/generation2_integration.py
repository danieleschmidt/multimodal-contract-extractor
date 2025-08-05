"""
Generation 2 Integration Module

This module integrates all Generation 2 "Make it Robust" enhancements with the existing
Generation 1 features, providing a unified, production-ready interface for enterprise
deployment with comprehensive error handling, security, monitoring, and resilience.
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .data_validation import (
    get_validation_manager,
)
from .enhanced_config import get_enhanced_config
from .enhanced_monitoring import get_logger, get_monitoring_manager, track_performance
from .enhanced_security import (
    PermissionType,
    SecurityContext,
    get_security_manager,
)

# Generation 1 imports
from .extraction import extract_from_document
from .health import get_health_status
from .infrastructure import cached, get_cache, get_infrastructure_manager
from .metrics import record_document_processed, record_pages_processed

# Generation 2 imports
from .resilience import (
    CircuitBreakerConfig,
    RetryConfig,
    get_resilience_manager,
)
from .security import SecurityError, validate_file_input

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Enhanced processing result with comprehensive metadata."""

    # Core results
    success: bool
    clauses: List[Dict[str, Any]]
    confidence_score: float

    # Processing metadata
    processing_time_seconds: float
    pages_processed: int
    document_type: str
    file_size_bytes: int

    # Generation 2 metadata
    validation_report: Optional[Dict[str, Any]] = None
    security_checks: Optional[Dict[str, Any]] = None
    cache_hit: bool = False
    resilience_applied: bool = False
    monitoring_trace_id: Optional[str] = None

    # Error information
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class Generation2ContractExtractor:
    """
    Production-ready contract extractor with Generation 2 enhancements.
    
    This class integrates all Generation 1 functionality with Generation 2 robustness
    features including resilience, security, validation, monitoring, and infrastructure.
    """

    def __init__(self):
        self.config = get_enhanced_config()

        # Initialize Generation 2 managers
        self.resilience_manager = get_resilience_manager()
        self.security_manager = get_security_manager()
        self.validation_manager = get_validation_manager()
        self.monitoring_manager = get_monitoring_manager()
        self.infrastructure_manager = get_infrastructure_manager()

        # Setup resilience components
        self._setup_resilience()

        # Initialize monitoring
        self.logger = get_logger("contract_extractor")

        # Performance metrics
        self.total_extractions = 0
        self.successful_extractions = 0
        self.cached_extractions = 0

        self.logger.info("Generation 2 Contract Extractor initialized")

    def _setup_resilience(self):
        """Setup resilience patterns for the extractor."""
        # Circuit breaker for file processing
        if self.config.resilience.circuit_breaker_enabled:
            cb_config = CircuitBreakerConfig(
                failure_threshold=self.config.resilience.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.resilience.circuit_breaker_recovery_timeout,
                expected_failure_rate=self.config.resilience.circuit_breaker_expected_failure_rate
            )
            self.resilience_manager.register_circuit_breaker("file_processing", cb_config)

        # Retry manager for extraction operations
        if self.config.resilience.retry_enabled:
            retry_config = RetryConfig(
                max_attempts=self.config.resilience.retry_max_attempts,
                initial_delay=self.config.resilience.retry_initial_delay,
                max_delay=self.config.resilience.retry_max_delay,
                backoff_multiplier=self.config.resilience.retry_backoff_multiplier,
                jitter=self.config.resilience.retry_jitter_enabled
            )
            self.resilience_manager.register_retry_manager("extraction", retry_config)

    @track_performance("contract_extraction")
    def extract_from_file(
        self,
        file_path: Union[str, Path],
        security_context: Optional[SecurityContext] = None,
        output_format: str = "json",
        enable_caching: bool = True,
        validation_strict: bool = False
    ) -> ProcessingResult:
        """
        Extract clauses from a contract file with full Generation 2 enhancements.
        
        Args:
            file_path: Path to the contract file
            security_context: Security context for authorization
            output_format: Output format (json, xml, csv)
            enable_caching: Whether to use caching
            validation_strict: Whether to use strict validation
            
        Returns:
            ProcessingResult with comprehensive metadata
        """
        start_time = time.time()
        file_path = Path(file_path)
        self.total_extractions += 1

        # Initialize result
        result = ProcessingResult(
            success=False,
            clauses=[],
            confidence_score=0.0,
            processing_time_seconds=0.0,
            pages_processed=0,
            document_type="unknown",
            file_size_bytes=0
        )

        try:
            with self.logger.operation_context(
                "contract_extraction",
                user_id=security_context.user_id if security_context else None,
                file_path=str(file_path)
            ):
                # Step 1: Security validation and authorization
                result.security_checks = self._perform_security_checks(file_path, security_context)
                if not result.security_checks["valid"]:
                    result.errors.extend(result.security_checks["issues"])
                    return result

                # Step 2: File validation and integrity checks
                result.validation_report = self._perform_validation(file_path, validation_strict)
                if not result.validation_report["valid"] and validation_strict:
                    result.errors.append("File validation failed in strict mode")
                    return result
                elif not result.validation_report["valid"]:
                    result.warnings.append("File validation warnings detected")

                # Step 3: Check cache if enabled
                cache_key = None
                if enable_caching and self.config.infrastructure.caching_enabled:
                    cache_key = self._generate_cache_key(file_path)
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        result = cached_result
                        result.cache_hit = True
                        self.cached_extractions += 1
                        self.logger.info("Retrieved result from cache", cache_key=cache_key)
                        return result

                # Step 4: Resilient extraction with circuit breaker and retry
                extraction_result = self._perform_resilient_extraction(file_path)

                # Step 5: Process extraction results
                result.clauses = extraction_result.get("clauses", [])
                result.confidence_score = extraction_result.get("confidence_score", 0.0)
                result.pages_processed = extraction_result.get("pages_processed", 0)
                result.document_type = extraction_result.get("document_type", "contract")
                result.file_size_bytes = file_path.stat().st_size
                result.resilience_applied = extraction_result.get("resilience_applied", False)
                result.success = True

                # Step 6: Cache the result if enabled
                if enable_caching and cache_key and self.config.infrastructure.caching_enabled:
                    self._store_in_cache(cache_key, result)

                # Step 7: Record metrics
                self._record_metrics(result)

                self.successful_extractions += 1
                self.logger.info(
                    "Contract extraction completed successfully",
                    clauses_found=len(result.clauses),
                    confidence_score=result.confidence_score,
                    processing_time=result.processing_time_seconds
                )

        except Exception as e:
            self.logger.error("Contract extraction failed", error=e)
            result.errors.append(str(e))
            result.success = False

            # Record error metrics
            self.monitoring_manager.get_metrics_collector().record_error(
                "contract_extractor", type(e).__name__
            )

        finally:
            result.processing_time_seconds = time.time() - start_time

            # Get trace ID for correlation
            trace_id = self.monitoring_manager.get_profiler().get_active_profiles()
            if trace_id:
                result.monitoring_trace_id = trace_id.get("contract_extraction")

        return result

    def _perform_security_checks(
        self,
        file_path: Path,
        security_context: Optional[SecurityContext]
    ) -> Dict[str, Any]:
        """Perform comprehensive security checks."""
        security_result = {
            "valid": True,
            "issues": [],
            "checks_performed": []
        }

        try:
            # Basic file validation (Generation 1)
            validated_path = validate_file_input(file_path)
            security_result["checks_performed"].append("basic_file_validation")

            # Enhanced security validation (Generation 2)
            if self.config.security.virus_scanning_enabled:
                validation_result = self.security_manager.validate_file_upload(
                    validated_path, security_context
                )
                security_result["checks_performed"].append("virus_scanning")

                if not validation_result["valid"]:
                    security_result["valid"] = False
                    security_result["issues"].extend(validation_result["issues"])

            # Rate limiting check
            if self.config.security.rate_limiting_enabled and security_context:
                identifier = security_context.ip_address or security_context.user_id or "anonymous"
                allowed, rate_info = self.security_manager.check_rate_limit(identifier)
                security_result["checks_performed"].append("rate_limiting")

                if not allowed:
                    security_result["valid"] = False
                    security_result["issues"].append(f"Rate limit exceeded: {rate_info}")

            # Authorization check
            if security_context:
                # Check if user has read permission for document processing
                from .enhanced_security import check_authorization
                if not check_authorization(security_context, PermissionType.READ):
                    security_result["valid"] = False
                    security_result["issues"].append("Insufficient permissions for document processing")
                security_result["checks_performed"].append("authorization")

        except SecurityError as e:
            security_result["valid"] = False
            security_result["issues"].append(str(e))
            self.logger.warning("Security validation failed", error=str(e))

        return security_result

    def _perform_validation(self, file_path: Path, strict: bool = False) -> Dict[str, Any]:
        """Perform comprehensive data validation."""
        if not self.config.validation.file_integrity_checks_enabled:
            return {"valid": True, "message": "Validation disabled"}

        try:
            # File integrity validation
            validation_report = self.validation_manager.validate_file(file_path)

            return {
                "valid": validation_report.valid,
                "result": validation_report.result.value,
                "issues_count": len(validation_report.issues),
                "validation_time": validation_report.validation_time_seconds,
                "integrity_checks": len(validation_report.integrity_checks)
            }

        except Exception as e:
            self.logger.error("Validation failed", error=e)
            return {
                "valid": not strict,  # Fail in strict mode, warn in normal mode
                "error": str(e)
            }

    def _generate_cache_key(self, file_path: Path) -> str:
        """Generate a cache key for the file."""
        import hashlib

        # Include file path, size, and modification time
        file_stat = file_path.stat()
        key_data = f"{file_path}:{file_stat.st_size}:{file_stat.st_mtime}"

        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[ProcessingResult]:
        """Get result from cache."""
        cache = get_cache()
        if cache:
            return cache.get(cache_key)
        return None

    def _store_in_cache(self, cache_key: str, result: ProcessingResult) -> None:
        """Store result in cache."""
        cache = get_cache()
        if cache:
            # Don't cache the full result object, just the essential data
            cache_data = {
                "success": result.success,
                "clauses": result.clauses,
                "confidence_score": result.confidence_score,
                "pages_processed": result.pages_processed,
                "document_type": result.document_type,
                "file_size_bytes": result.file_size_bytes,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            cache.put(cache_key, cache_data, ttl=self.config.infrastructure.cache_ttl_seconds)

    def _perform_resilient_extraction(self, file_path: Path) -> Dict[str, Any]:
        """Perform document extraction with resilience patterns."""

        def extraction_operation():
            """Core extraction operation."""
            # Use Generation 1 extraction logic
            extraction_result = extract_from_document(Path(file_path))

            # Enhance with additional metadata
            result = {
                "clauses": extraction_result.get("clauses", []),
                "confidence_score": extraction_result.get("confidence", 0.0),
                "pages_processed": extraction_result.get("pages", 1),
                "document_type": "contract",
                "resilience_applied": False
            }

            return result

        # Apply resilience patterns if enabled
        try:
            if (self.config.resilience.circuit_breaker_enabled or
                self.config.resilience.retry_enabled):

                result = self.resilience_manager.execute_resilient_operation(
                    extraction_operation,
                    "document_extraction",
                    circuit_breaker_name="file_processing" if self.config.resilience.circuit_breaker_enabled else None,
                    retry_manager_name="extraction" if self.config.resilience.retry_enabled else None
                )
                result["resilience_applied"] = True
                return result
            else:
                return extraction_operation()

        except Exception as e:
            self.logger.error("Resilient extraction failed", error=e)
            raise

    def _record_metrics(self, result: ProcessingResult) -> None:
        """Record processing metrics."""
        # Generation 1 metrics
        record_document_processed("success" if result.success else "error")
        record_pages_processed(result.pages_processed)

        # Generation 2 metrics
        metrics_collector = self.monitoring_manager.get_metrics_collector()
        metrics_collector.record_document_processing(
            result.document_type,
            result.processing_time_seconds,
            "success" if result.success else "error"
        )

        # Custom metrics
        if hasattr(metrics_collector, 'clauses_extracted'):
            metrics_collector.clauses_extracted.labels(
                document_type=result.document_type
            ).inc(len(result.clauses))

    @cached(cache_name="default", ttl=3600)
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ["pdf", "png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        # Generation 1 health
        gen1_health = get_health_status()

        # Generation 2 health
        gen2_health = self.monitoring_manager.health_check()
        infrastructure_health = self.infrastructure_manager.get_system_status()

        # Combine health information
        overall_healthy = (
            gen1_health["status"] == "healthy" and
            gen2_health["healthy"] and
            infrastructure_health["infrastructure_ready"]
        )

        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "generation1": gen1_health,
            "generation2": gen2_health,
            "infrastructure": infrastructure_health["health"],
            "performance_stats": {
                "total_extractions": self.total_extractions,
                "successful_extractions": self.successful_extractions,
                "success_rate": (
                    self.successful_extractions / self.total_extractions
                    if self.total_extractions > 0 else 0
                ),
                "cached_extractions": self.cached_extractions,
                "cache_hit_rate": (
                    self.cached_extractions / self.total_extractions
                    if self.total_extractions > 0 else 0
                )
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_metrics(self, format: str = "prometheus") -> str:
        """Get all metrics in specified format."""
        return self.monitoring_manager.export_metrics(format)

    def create_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """Create a system backup."""
        # Define important paths to backup
        backup_paths = [
            Path("data"),  # Data directory
            Path("logs"),  # Log files
            Path("config.yml"),  # Configuration
        ]

        # Filter existing paths
        existing_paths = [p for p in backup_paths if p.exists()]

        return self.infrastructure_manager.create_backup(existing_paths, backup_name)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "health": self.get_health_status(),
            "infrastructure": self.infrastructure_manager.get_system_status(),
            "security": self.security_manager.get_security_status(),
            "resilience": self.resilience_manager.get_system_status(),
            "validation": self.validation_manager.get_validation_stats(),
            "monitoring": self.monitoring_manager.get_system_status(),
            "configuration": {
                "environment": self.config.environment,
                "debug_enabled": self.config.debug_enabled,
                "feature_flags": self.config.feature_flags
            }
        }


# Global instance
_generation2_extractor: Optional[Generation2ContractExtractor] = None


def get_generation2_extractor() -> Generation2ContractExtractor:
    """Get the global Generation 2 contract extractor instance."""
    global _generation2_extractor
    if _generation2_extractor is None:
        _generation2_extractor = Generation2ContractExtractor()
    return _generation2_extractor


# Convenience functions for backwards compatibility
def robust_extract_from_file(
    file_path: Union[str, Path],
    security_context: Optional[SecurityContext] = None,
    **kwargs
) -> ProcessingResult:
    """
    Extract clauses from file with full Generation 2 robustness.
    
    This is the main entry point for production contract extraction.
    """
    extractor = get_generation2_extractor()
    return extractor.extract_from_file(file_path, security_context, **kwargs)


def get_robust_health_status() -> Dict[str, Any]:
    """Get comprehensive health status."""
    extractor = get_generation2_extractor()
    return extractor.get_health_status()


def create_system_backup(backup_name: str = None) -> Dict[str, Any]:
    """Create a system backup."""
    extractor = get_generation2_extractor()
    return extractor.create_backup(backup_name)


# Enhanced decorators for backwards compatibility
def with_generation2_features(
    enable_caching: bool = True,
    enable_validation: bool = True,
    enable_monitoring: bool = True
):
    """Decorator to add Generation 2 features to existing functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            extractor = get_generation2_extractor()

            # Add monitoring
            if enable_monitoring:
                with extractor.logger.operation_context(f"{func.__name__}_operation"):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper
    return decorator


# Example integration with Generation 1 functions
@with_generation2_features()
def enhanced_extract_clauses_from_document(
    file_path: str,
    security_context: Optional[SecurityContext] = None
) -> Dict[str, Any]:
    """Enhanced version of the original extract_clauses_from_document function."""
    return robust_extract_from_file(file_path, security_context).clauses


# System initialization
def initialize_generation2_system() -> None:
    """Initialize the complete Generation 2 system."""
    logger = get_logger("system_init")

    try:
        # Initialize extractor (this initializes all subsystems)
        extractor = get_generation2_extractor()

        # Verify system health
        health = extractor.get_health_status()

        if health["overall_status"] == "healthy":
            logger.info("Generation 2 system initialized successfully")
        else:
            logger.warning("Generation 2 system initialized with health issues", health_status=health)

        # Log system capabilities
        logger.info(
            "System capabilities enabled",
            resilience=extractor.config.resilience.circuit_breaker_enabled,
            security=extractor.config.security.virus_scanning_enabled,
            monitoring=extractor.config.monitoring.structured_logging_enabled,
            caching=extractor.config.infrastructure.caching_enabled,
            validation=extractor.config.validation.file_integrity_checks_enabled
        )

    except Exception as e:
        logger.critical("Failed to initialize Generation 2 system", error=e)
        raise


# Shutdown procedure
def shutdown_generation2_system() -> None:
    """Gracefully shutdown the Generation 2 system."""
    logger = get_logger("system_shutdown")

    try:
        extractor = get_generation2_extractor()

        # Create final backup if enabled
        if extractor.config.infrastructure.backup_enabled:
            backup_result = extractor.create_backup("shutdown_backup")
            logger.info("Shutdown backup created", backup_result=backup_result)

        # Cleanup infrastructure
        extractor.infrastructure_manager.get_system_status()  # Final status check

        # Final metrics export
        if extractor.config.monitoring.metrics_enabled:
            metrics = extractor.get_metrics()
            logger.info(f"Final metrics exported: {len(metrics.split('\n'))} lines")

        logger.info("Generation 2 system shutdown completed successfully")

    except Exception as e:
        logger.error("Error during system shutdown", error=e)


if __name__ == "__main__":
    # Example usage
    import tempfile

    # Initialize system
    initialize_generation2_system()

    # Create test security context
    security_context = SecurityContext(
        user_id="test_user",
        permissions={PermissionType.READ, PermissionType.WRITE},
        authenticated=True
    )

    # Test extraction with a dummy file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4\n%dummy PDF content\n%%EOF")
        tmp_path = Path(tmp_file.name)

    try:
        # Perform robust extraction
        result = robust_extract_from_file(tmp_path, security_context)
        print(f"Extraction result: success={result.success}, clauses={len(result.clauses)}")
        print(f"Processing time: {result.processing_time_seconds:.3f}s")
        print(f"Cache hit: {result.cache_hit}")
        print(f"Resilience applied: {result.resilience_applied}")

        # Get system status
        status = get_robust_health_status()
        print(f"System health: {status['overall_status']}")

        # Create backup
        backup_result = create_system_backup("test_backup")
        print(f"Backup created: {backup_result.get('success', False)}")

    finally:
        tmp_path.unlink()  # Cleanup
        shutdown_generation2_system()
