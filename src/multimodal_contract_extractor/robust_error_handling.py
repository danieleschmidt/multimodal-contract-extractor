"""
Comprehensive error handling and recovery mechanisms for robust operation.
Generation 2 Enhancement: Reliable error handling with automatic recovery.
"""
from __future__ import annotations

import logging
import time
import traceback
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for specific handling strategies."""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PROCESSING = "processing"
    SECURITY = "security"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Comprehensive error context for debugging and recovery."""
    timestamp: float = field(default_factory=time.time)
    error_id: str = field(default_factory=lambda: f"error_{int(time.time()*1000)}")
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.PROCESSING
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    stacktrace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    recovery_attempted: bool = False


class RobustError(Exception):
    """Base exception class with comprehensive error context."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.PROCESSING,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.context = ErrorContext(
            message=message,
            severity=severity,
            category=category,
            details=context or {},
            stacktrace=traceback.format_exc() if original_exception else None
        )
        self.original_exception = original_exception


class RecoveryStrategy:
    """Base class for error recovery strategies."""

    def can_recover(self, error_context: ErrorContext) -> bool:
        """Check if this strategy can handle the given error."""
        return False

    def recover(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from the error. Returns True if successful."""
        return False


class NetworkRetryStrategy(RecoveryStrategy):
    """Recovery strategy for network-related errors with exponential backoff."""

    def can_recover(self, error_context: ErrorContext) -> bool:
        return (
            error_context.category == ErrorCategory.NETWORK and
            error_context.retry_count < error_context.max_retries
        )

    def recover(self, error_context: ErrorContext) -> bool:
        if not self.can_recover(error_context):
            return False

        # Exponential backoff
        delay = 2 ** error_context.retry_count
        logger.info(f"Network error recovery attempt {error_context.retry_count + 1}, waiting {delay}s")
        time.sleep(delay)
        error_context.retry_count += 1
        error_context.recovery_attempted = True
        return True


class FileSystemRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for filesystem errors."""

    def can_recover(self, error_context: ErrorContext) -> bool:
        return error_context.category == ErrorCategory.FILESYSTEM

    def recover(self, error_context: ErrorContext) -> bool:
        if not self.can_recover(error_context):
            return False

        # Attempt to create missing directories
        if "path" in error_context.details:
            try:
                from pathlib import Path
                path = Path(error_context.details["path"])
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing directory: {path.parent}")
                    error_context.recovery_attempted = True
                    return True
            except Exception as e:
                logger.error(f"Failed to recover filesystem error: {e}")

        return False


class ErrorRecoveryManager:
    """Manages error recovery strategies and handles error classification."""

    def __init__(self):
        self.strategies: List[RecoveryStrategy] = [
            NetworkRetryStrategy(),
            FileSystemRecoveryStrategy(),
        ]
        self.error_history: List[ErrorContext] = []
        self.max_history = 100

    def classify_error(self, exception: Exception) -> ErrorContext:
        """Classify an exception and create appropriate error context."""
        if isinstance(exception, RobustError):
            return exception.context

        # Auto-classify based on exception type and message
        category = ErrorCategory.PROCESSING
        severity = ErrorSeverity.MEDIUM

        error_msg = str(exception).lower()

        if any(term in error_msg for term in ["network", "connection", "timeout", "http"]):
            category = ErrorCategory.NETWORK
        elif any(term in error_msg for term in ["file", "directory", "permission", "path"]):
            category = ErrorCategory.FILESYSTEM
        elif any(term in error_msg for term in ["security", "unauthorized", "forbidden"]):
            category = ErrorCategory.SECURITY
            severity = ErrorSeverity.HIGH
        elif any(term in error_msg for term in ["validation", "invalid", "format"]):
            category = ErrorCategory.VALIDATION
        elif any(term in error_msg for term in ["memory", "system", "resource"]):
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.HIGH

        return ErrorContext(
            message=str(exception),
            severity=severity,
            category=category,
            stacktrace=traceback.format_exc(),
            details={"exception_type": type(exception).__name__}
        )

    def handle_error(self, exception: Exception) -> bool:
        """Handle an error with automatic recovery attempts."""
        error_context = self.classify_error(exception)

        # Add to history
        self.error_history.append(error_context)
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

        # Log the error
        self._log_error(error_context)

        # Attempt recovery
        for strategy in self.strategies:
            if strategy.can_recover(error_context):
                logger.info(f"Attempting recovery with {strategy.__class__.__name__}")
                if strategy.recover(error_context):
                    logger.info("Recovery successful")
                    return True
                else:
                    logger.warning("Recovery failed")

        logger.error("No recovery strategy available for this error")
        return False

    def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level based on severity."""
        log_msg = f"[{error_context.error_id}] {error_context.message}"

        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_msg, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_msg, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_msg, extra={"error_context": error_context})
        else:
            logger.info(log_msg, extra={"error_context": error_context})

    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics about recent errors."""
        if not self.error_history:
            return {"total_errors": 0}

        categories = {}
        severities = {}
        recent_errors = len([e for e in self.error_history if time.time() - e.timestamp < 3600])  # Last hour

        for error in self.error_history:
            categories[error.category.value] = categories.get(error.category.value, 0) + 1
            severities[error.severity.value] = severities.get(error.severity.value, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "recent_errors": recent_errors,
            "categories": categories,
            "severities": severities,
            "recovery_rate": sum(1 for e in self.error_history if e.recovery_attempted) / len(self.error_history)
        }


# Global error manager instance
_error_manager = ErrorRecoveryManager()


def robust_operation(
    max_retries: int = 3,
    backoff_multiplier: float = 1.5,
    expected_exceptions: Optional[List[Type[Exception]]] = None
):
    """Decorator for making operations robust with automatic retry and recovery."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this is an expected exception type
                    if expected_exceptions and not any(isinstance(e, exc_type) for exc_type in expected_exceptions):
                        raise

                    if attempt < max_retries:
                        # Attempt recovery
                        if _error_manager.handle_error(e):
                            continue  # Retry immediately after successful recovery

                        # Exponential backoff
                        delay = backoff_multiplier ** attempt
                        logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"Operation failed after {max_retries} retries: {e}")

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator


@contextmanager
def error_context(operation_name: str, **context_data):
    """Context manager for error handling with automatic logging and recovery."""
    start_time = time.time()
    logger.debug(f"Starting operation: {operation_name}")

    try:
        yield
        duration = time.time() - start_time
        logger.debug(f"Operation completed: {operation_name} (took {duration:.2f}s)")

    except Exception as e:
        duration = time.time() - start_time

        # Enhanced error context
        error_context = ErrorContext(
            message=f"Operation '{operation_name}' failed: {str(e)}",
            details={
                "operation": operation_name,
                "duration": duration,
                **context_data
            }
        )

        # Attempt recovery
        _error_manager.handle_error(e)

        logger.error(f"Operation failed: {operation_name} (took {duration:.2f}s)")
        raise


@asynccontextmanager
async def async_error_context(operation_name: str, **context_data):
    """Async version of error_context."""
    start_time = time.time()
    logger.debug(f"Starting async operation: {operation_name}")

    try:
        yield
        duration = time.time() - start_time
        logger.debug(f"Async operation completed: {operation_name} (took {duration:.2f}s)")

    except Exception as e:
        duration = time.time() - start_time

        # Enhanced error context
        error_context = ErrorContext(
            message=f"Async operation '{operation_name}' failed: {str(e)}",
            details={
                "operation": operation_name,
                "duration": duration,
                **context_data
            }
        )

        # Attempt recovery
        _error_manager.handle_error(e)

        logger.error(f"Async operation failed: {operation_name} (took {duration:.2f}s)")
        raise


def get_error_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager instance."""
    return _error_manager


def health_check_errors() -> Dict[str, Any]:
    """Get error health check information."""
    stats = _error_manager.get_error_stats()

    # Determine health status
    recent_errors = stats.get("recent_errors", 0)
    recovery_rate = stats.get("recovery_rate", 0)

    if recent_errors == 0:
        status = "healthy"
    elif recent_errors < 5 and recovery_rate > 0.8:
        status = "warning"
    elif recent_errors < 20 and recovery_rate > 0.5:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "status": status,
        "error_stats": stats,
        "recovery_strategies": len(_error_manager.strategies)
    }
