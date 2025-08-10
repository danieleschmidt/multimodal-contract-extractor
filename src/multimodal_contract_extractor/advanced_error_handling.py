"""Advanced Error Handling and Recovery System.

This module implements comprehensive error handling, recovery mechanisms,
and fault tolerance for the multimodal contract extraction system.
Provides graceful degradation, automatic retry logic, and detailed error reporting.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for categorization."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy options for different error types."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    error_id: str
    timestamp: float
    severity: ErrorSeverity
    component: str
    operation: str
    error_type: Type[Exception]
    error_message: str
    stack_trace: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY


class ContractProcessingError(Exception):
    """Base exception for contract processing errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.severity = severity
        self.timestamp = time.time()


class DocumentLoadError(ContractProcessingError):
    """Error loading or parsing document."""
    pass


class OCRProcessingError(ContractProcessingError):
    """Error during OCR processing."""
    pass


class ClauseExtractionError(ContractProcessingError):
    """Error during clause extraction."""
    pass


class NeuromorphicAnalysisError(ContractProcessingError):
    """Error during neuromorphic analysis."""
    pass


class QuantumAnalysisError(ContractProcessingError):
    """Error during quantum analysis."""
    pass


class ValidationError(ContractProcessingError):
    """Error during validation."""
    pass


class ErrorRecoveryManager:
    """Manages error recovery strategies and fallback mechanisms."""

    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[Type[Exception], RecoveryStrategy] = {
            DocumentLoadError: RecoveryStrategy.RETRY,
            OCRProcessingError: RecoveryStrategy.FALLBACK,
            ClauseExtractionError: RecoveryStrategy.GRACEFUL_DEGRADATION,
            NeuromorphicAnalysisError: RecoveryStrategy.SKIP,
            QuantumAnalysisError: RecoveryStrategy.SKIP,
            ValidationError: RecoveryStrategy.RETRY,
            FileNotFoundError: RecoveryStrategy.ABORT,
            MemoryError: RecoveryStrategy.GRACEFUL_DEGRADATION,
            TimeoutError: RecoveryStrategy.RETRY,
        }
        self.fallback_processors = {}

    def register_error(self, error_context: ErrorContext) -> None:
        """Register an error for tracking and analysis."""
        self.error_history.append(error_context)

        # Log error with appropriate level
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(error_context.severity, logging.ERROR)

        logger.log(
            log_level,
            "Error in %s.%s: %s (ID: %s, Severity: %s)",
            error_context.component,
            error_context.operation,
            error_context.error_message,
            error_context.error_id,
            error_context.severity.value
        )

    def get_recovery_strategy(self, error_type: Type[Exception]) -> RecoveryStrategy:
        """Get recovery strategy for a specific error type."""
        return self.recovery_strategies.get(error_type, RecoveryStrategy.RETRY)

    def should_retry(self, error_context: ErrorContext) -> bool:
        """Determine if an error should be retried."""
        strategy = self.get_recovery_strategy(error_context.error_type)

        if strategy != RecoveryStrategy.RETRY:
            return False

        return error_context.recovery_attempts < error_context.max_recovery_attempts

    def register_fallback_processor(
        self,
        error_type: Type[Exception],
        fallback_func: Callable
    ) -> None:
        """Register a fallback processor for a specific error type."""
        self.fallback_processors[error_type] = fallback_func

    def get_fallback_processor(self, error_type: Type[Exception]) -> Optional[Callable]:
        """Get fallback processor for an error type."""
        return self.fallback_processors.get(error_type)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns."""
        if not self.error_history:
            return {"total_errors": 0}

        error_counts = {}
        severity_counts = {}
        component_errors = {}

        for error in self.error_history:
            # Count by error type
            error_type = error.error_type.__name__
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

            # Count by severity
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count by component
            component_errors[error.component] = component_errors.get(error.component, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "severity_counts": severity_counts,
            "component_errors": component_errors,
            "avg_recovery_attempts": sum(e.recovery_attempts for e in self.error_history) / len(self.error_history),
            "most_common_error": max(error_counts.keys(), key=error_counts.get) if error_counts else None
        }


# Global error recovery manager
_error_manager: Optional[ErrorRecoveryManager] = None


def get_error_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager."""
    global _error_manager
    if _error_manager is None:
        _error_manager = ErrorRecoveryManager()
    return _error_manager


def with_error_handling(
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    enable_fallback: bool = True
):
    """Decorator for comprehensive error handling."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            error_manager = get_error_manager()

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    error_id = f"{component}_{operation}_{int(time.time())}"

                    error_context = ErrorContext(
                        error_id=error_id,
                        timestamp=time.time(),
                        severity=severity,
                        component=component,
                        operation=operation,
                        error_type=type(e),
                        error_message=str(e),
                        stack_trace=traceback.format_exc(),
                        context_data={
                            "args": str(args)[:500],  # Limit size
                            "kwargs": str(kwargs)[:500]
                        },
                        recovery_attempts=attempt,
                        max_recovery_attempts=max_retries
                    )

                    error_manager.register_error(error_context)

                    # Check if we should retry
                    if attempt < max_retries and error_manager.should_retry(error_context):
                        logger.info(
                            "Retrying %s.%s (attempt %d/%d) after error: %s",
                            component, operation, attempt + 1, max_retries, str(e)
                        )
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue

                    # Try fallback processor
                    if enable_fallback:
                        fallback = error_manager.get_fallback_processor(type(e))
                        if fallback:
                            logger.info(
                                "Using fallback processor for %s.%s after error: %s",
                                component, operation, str(e)
                            )
                            try:
                                return fallback(*args, **kwargs)
                            except Exception as fallback_error:
                                logger.error(
                                    "Fallback processor failed: %s",
                                    str(fallback_error)
                                )

                    # If we get here, all retries and fallbacks failed
                    raise

            # This should never be reached
            raise RuntimeError("Unexpected error in retry logic")

        return wrapper
    return decorator


def with_async_error_handling(
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    enable_fallback: bool = True
):
    """Decorator for comprehensive async error handling."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            error_manager = get_error_manager()

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    error_id = f"{component}_{operation}_{int(time.time())}"

                    error_context = ErrorContext(
                        error_id=error_id,
                        timestamp=time.time(),
                        severity=severity,
                        component=component,
                        operation=operation,
                        error_type=type(e),
                        error_message=str(e),
                        stack_trace=traceback.format_exc(),
                        context_data={
                            "args": str(args)[:500],
                            "kwargs": str(kwargs)[:500]
                        },
                        recovery_attempts=attempt,
                        max_recovery_attempts=max_retries
                    )

                    error_manager.register_error(error_context)

                    # Check if we should retry
                    if attempt < max_retries and error_manager.should_retry(error_context):
                        logger.info(
                            "Retrying %s.%s (attempt %d/%d) after error: %s",
                            component, operation, attempt + 1, max_retries, str(e)
                        )
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue

                    # Try fallback processor
                    if enable_fallback:
                        fallback = error_manager.get_fallback_processor(type(e))
                        if fallback:
                            logger.info(
                                "Using fallback processor for %s.%s after error: %s",
                                component, operation, str(e)
                            )
                            try:
                                if asyncio.iscoroutinefunction(fallback):
                                    return await fallback(*args, **kwargs)
                                else:
                                    return fallback(*args, **kwargs)
                            except Exception as fallback_error:
                                logger.error(
                                    "Fallback processor failed: %s",
                                    str(fallback_error)
                                )

                    # If we get here, all retries and fallbacks failed
                    raise

            # This should never be reached
            raise RuntimeError("Unexpected error in async retry logic")

        return wrapper
    return decorator


@contextmanager
def error_boundary(
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    suppress_errors: bool = False,
    default_return: Any = None
) -> Generator[ErrorContext, None, None]:
    """Context manager for error boundary with optional error suppression."""

    error_context = ErrorContext(
        error_id=f"{component}_{operation}_{int(time.time())}",
        timestamp=time.time(),
        severity=severity,
        component=component,
        operation=operation,
        error_type=Exception,
        error_message="",
        stack_trace="",
    )

    try:
        yield error_context

    except Exception as e:
        error_context.error_type = type(e)
        error_context.error_message = str(e)
        error_context.stack_trace = traceback.format_exc()

        error_manager = get_error_manager()
        error_manager.register_error(error_context)

        if not suppress_errors:
            raise

        logger.warning(
            "Error suppressed in %s.%s: %s",
            component, operation, str(e)
        )


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise self.expected_exception("Circuit breaker is open")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except self.expected_exception:
                self._on_failure()
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                "Circuit breaker opened after %d failures",
                self.failure_count
            )


class BulkheadPattern:
    """Bulkhead pattern for resource isolation."""

    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_operations = 0
        self.max_concurrent = max_concurrent

    async def __aenter__(self):
        await self.semaphore.acquire()
        self.active_operations += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()
        self.active_operations -= 1

    def get_utilization(self) -> float:
        """Get current resource utilization."""
        return self.active_operations / self.max_concurrent


# Pre-configured bulkheads for different operations
document_processing_bulkhead = BulkheadPattern(max_concurrent=5)
neuromorphic_analysis_bulkhead = BulkheadPattern(max_concurrent=3)
quantum_analysis_bulkhead = BulkheadPattern(max_concurrent=2)


class HealthChecker:
    """System health monitoring and checking."""

    def __init__(self):
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.last_check_results: Dict[str, Dict[str, Any]] = {}

    def register_health_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """Register a health check function."""
        self.health_checks[name] = check_func

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        overall_health = True

        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                is_healthy = check_func()
                check_time = time.time() - start_time

                results[name] = {
                    "healthy": is_healthy,
                    "check_time": round(check_time, 3),
                    "timestamp": time.time()
                }

                if not is_healthy:
                    overall_health = False

            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "check_time": 0,
                    "timestamp": time.time()
                }
                overall_health = False

        self.last_check_results = results

        return {
            "overall_health": overall_health,
            "checks": results,
            "timestamp": time.time()
        }

    def get_last_results(self) -> Dict[str, Any]:
        """Get results from the last health check."""
        return self.last_check_results


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


class ErrorHandlingConfig(BaseModel):
    """Configuration for error handling system."""

    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, gt=0.0, le=60.0)
    enable_fallback: bool = True
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=50)
    circuit_breaker_timeout: float = Field(default=60.0, gt=0.0, le=3600.0)
    enable_bulkhead: bool = True
    max_concurrent_operations: int = Field(default=10, ge=1, le=100)
    enable_health_checks: bool = True
    health_check_interval: float = Field(default=30.0, gt=0.0, le=3600.0)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda x: round(x, 3)
        }
