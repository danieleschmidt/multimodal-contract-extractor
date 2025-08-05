"""
Advanced error tracking and monitoring system.
Structured error collection, analysis, and alerting.
"""

import hashlib
import json
import logging
import os
import threading
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.stdlib import StdlibIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATA = "data"
    NETWORK = "network"
    USER_INPUT = "user_input"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Contextual information for error tracking."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ErrorEvent:
    """Structured error event."""
    id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[ErrorContext] = None
    fingerprint: Optional[str] = None
    count: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        if self.context:
            data['context'] = self.context.to_dict()
        return data


class ErrorTrackingConfig:
    """Configuration for error tracking."""

    def __init__(self):
        # Sentry configuration
        self.sentry_dsn = os.getenv('SENTRY_DSN')
        self.sentry_enabled = os.getenv('SENTRY_ENABLED', 'false').lower() == 'true'
        self.sentry_environment = os.getenv('SENTRY_ENVIRONMENT', 'development')
        self.sentry_release = os.getenv('SENTRY_RELEASE')
        self.sentry_sample_rate = float(os.getenv('SENTRY_SAMPLE_RATE', '1.0'))

        # Local storage configuration
        self.local_storage_enabled = os.getenv('LOCAL_ERROR_STORAGE', 'true').lower() == 'true'
        self.storage_directory = os.getenv('ERROR_STORAGE_DIR', 'monitoring/errors')
        self.max_local_errors = int(os.getenv('MAX_LOCAL_ERRORS', '1000'))

        # Filtering configuration
        self.min_severity = ErrorSeverity(os.getenv('MIN_ERROR_SEVERITY', 'info'))
        self.ignored_exceptions = os.getenv('IGNORED_EXCEPTIONS', '').split(',')
        self.rate_limit_window = int(os.getenv('ERROR_RATE_LIMIT_WINDOW', '60'))  # seconds
        self.rate_limit_count = int(os.getenv('ERROR_RATE_LIMIT_COUNT', '10'))

        # Alerting configuration
        self.alert_enabled = os.getenv('ERROR_ALERTS_ENABLED', 'false').lower() == 'true'
        self.alert_webhook_url = os.getenv('ERROR_ALERT_WEBHOOK_URL')
        self.alert_threshold = int(os.getenv('ERROR_ALERT_THRESHOLD', '5'))


class ErrorTracker:
    """Advanced error tracking and monitoring system."""

    def __init__(self, config: Optional[ErrorTrackingConfig] = None):
        self.config = config or ErrorTrackingConfig()
        self.logger = logging.getLogger(__name__)
        self.initialized = False

        # Local storage
        self.storage_path = Path(self.config.storage_directory)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Error cache for deduplication
        self.error_cache: Dict[str, ErrorEvent] = {}
        self.cache_lock = threading.Lock()

        # Rate limiting
        self.rate_limit_cache: Dict[str, List[datetime]] = {}

        # Load existing errors
        self._load_local_errors()

    def initialize(self) -> bool:
        """Initialize error tracking."""
        try:
            # Initialize Sentry if available and configured
            if self.config.sentry_enabled and self.config.sentry_dsn and SENTRY_AVAILABLE:
                self._setup_sentry()

            # Setup custom exception handler
            self._setup_exception_handler()

            self.initialized = True
            self.logger.info("Error tracking initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize error tracking: {e}")
            return False

    def _setup_sentry(self) -> None:
        """Setup Sentry integration."""
        sentry_sdk.init(
            dsn=self.config.sentry_dsn,
            environment=self.config.sentry_environment,
            release=self.config.sentry_release,
            sample_rate=self.config.sentry_sample_rate,
            integrations=[
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                StdlibIntegration(),
            ],
            before_send=self._sentry_before_send,
        )
        self.logger.info("Sentry error tracking initialized")

    def _sentry_before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter events before sending to Sentry."""
        # Apply custom filtering logic
        if 'exception' in event:
            exception_type = event['exception']['values'][0]['type']
            if exception_type in self.config.ignored_exceptions:
                return None

        return event

    def _setup_exception_handler(self) -> None:
        """Setup global exception handler."""
        import sys

        original_excepthook = sys.excepthook

        def custom_excepthook(exc_type, exc_value, exc_traceback):
            # Track the exception
            self.track_exception(
                exc_value,
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM
            )

            # Call original handler
            original_excepthook(exc_type, exc_value, exc_traceback)

        sys.excepthook = custom_excepthook

    def track_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.APPLICATION,
        context: Optional[ErrorContext] = None,
        exception: Optional[Exception] = None
    ) -> str:
        """Track an error event."""
        # Create error event
        error_event = self._create_error_event(
            message=message,
            severity=severity,
            category=category,
            context=context,
            exception=exception
        )

        # Check rate limiting
        if self._is_rate_limited(error_event.fingerprint):
            return error_event.id

        # Store and process error
        self._process_error_event(error_event)

        return error_event.id

    def track_exception(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        category: ErrorCategory = ErrorCategory.APPLICATION,
        context: Optional[ErrorContext] = None
    ) -> str:
        """Track an exception."""
        return self.track_error(
            message=str(exception),
            severity=severity,
            category=category,
            context=context,
            exception=exception
        )

    def _create_error_event(
        self,
        message: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[ErrorContext],
        exception: Optional[Exception]
    ) -> ErrorEvent:
        """Create an error event."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate unique ID
        error_id = hashlib.md5(f"{timestamp}:{message}".encode()).hexdigest()[:12]

        # Extract exception information
        exception_type = None
        stack_trace = None
        if exception:
            exception_type = type(exception).__name__
            stack_trace = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))

        # Generate fingerprint for deduplication
        fingerprint_data = f"{exception_type or 'error'}:{message}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()

        return ErrorEvent(
            id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=message,
            exception_type=exception_type,
            stack_trace=stack_trace,
            context=context,
            fingerprint=fingerprint,
            first_seen=timestamp,
            last_seen=timestamp
        )

    def _process_error_event(self, error_event: ErrorEvent) -> None:
        """Process and store error event."""
        with self.cache_lock:
            # Check for existing error with same fingerprint
            if error_event.fingerprint in self.error_cache:
                existing_error = self.error_cache[error_event.fingerprint]
                existing_error.count += 1
                existing_error.last_seen = error_event.timestamp
                error_event = existing_error
            else:
                self.error_cache[error_event.fingerprint] = error_event

        # Store locally if enabled
        if self.config.local_storage_enabled:
            self._store_error_locally(error_event)

        # Send to Sentry if enabled
        if self.config.sentry_enabled and SENTRY_AVAILABLE:
            self._send_to_sentry(error_event)

        # Log the error
        self._log_error(error_event)

        # Check for alerting
        if self.config.alert_enabled:
            self._check_alert_conditions(error_event)

    def _store_error_locally(self, error_event: ErrorEvent) -> None:
        """Store error event locally."""
        try:
            error_file = self.storage_path / f"error_{error_event.id}.json"
            with open(error_file, 'w') as f:
                json.dump(error_event.to_dict(), f, indent=2)

            # Cleanup old errors if needed
            self._cleanup_old_errors()

        except Exception as e:
            self.logger.error(f"Failed to store error locally: {e}")

    def _send_to_sentry(self, error_event: ErrorEvent) -> None:
        """Send error to Sentry."""
        try:
            with sentry_sdk.push_scope() as scope:
                # Set context
                if error_event.context:
                    scope.set_context("error_context", error_event.context.to_dict())

                # Set tags
                scope.set_tag("error.category", error_event.category.value)
                scope.set_tag("error.severity", error_event.severity.value)

                # Set fingerprint
                scope.fingerprint = [error_event.fingerprint]

                # Capture exception or message
                if error_event.exception_type and error_event.stack_trace:
                    sentry_sdk.capture_message(
                        error_event.message,
                        level=self._severity_to_sentry_level(error_event.severity)
                    )
                else:
                    sentry_sdk.capture_message(
                        error_event.message,
                        level=self._severity_to_sentry_level(error_event.severity)
                    )

        except Exception as e:
            self.logger.error(f"Failed to send error to Sentry: {e}")

    def _severity_to_sentry_level(self, severity: ErrorSeverity) -> str:
        """Convert severity to Sentry level."""
        mapping = {
            ErrorSeverity.CRITICAL: 'error',
            ErrorSeverity.HIGH: 'error',
            ErrorSeverity.MEDIUM: 'warning',
            ErrorSeverity.LOW: 'info',
            ErrorSeverity.INFO: 'info',
        }
        return mapping.get(severity, 'error')

    def _log_error(self, error_event: ErrorEvent) -> None:
        """Log error event."""
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.INFO,
        }.get(error_event.severity, logging.ERROR)

        extra_info = {
            'error_id': error_event.id,
            'category': error_event.category.value,
            'fingerprint': error_event.fingerprint,
            'count': error_event.count
        }

        if error_event.context:
            extra_info.update(error_event.context.to_dict())

        self.logger.log(
            log_level,
            f"[{error_event.category.value.upper()}] {error_event.message}",
            extra=extra_info
        )

    def _is_rate_limited(self, fingerprint: str) -> bool:
        """Check if error is rate limited."""
        now = datetime.now(timezone.utc)
        window_start = now.timestamp() - self.config.rate_limit_window

        if fingerprint not in self.rate_limit_cache:
            self.rate_limit_cache[fingerprint] = []

        # Clean old entries
        self.rate_limit_cache[fingerprint] = [
            ts for ts in self.rate_limit_cache[fingerprint]
            if ts.timestamp() > window_start
        ]

        # Check rate limit
        if len(self.rate_limit_cache[fingerprint]) >= self.config.rate_limit_count:
            return True

        # Add current timestamp
        self.rate_limit_cache[fingerprint].append(now)
        return False

    def _check_alert_conditions(self, error_event: ErrorEvent) -> None:
        """Check if error should trigger an alert."""
        # Simple alerting based on error count
        if error_event.count >= self.config.alert_threshold:
            self._send_alert(error_event)

    def _send_alert(self, error_event: ErrorEvent) -> None:
        """Send error alert."""
        if not self.config.alert_webhook_url:
            return

        try:
            import requests

            alert_data = {
                'error_id': error_event.id,
                'message': error_event.message,
                'severity': error_event.severity.value,
                'category': error_event.category.value,
                'count': error_event.count,
                'first_seen': error_event.first_seen,
                'last_seen': error_event.last_seen
            }

            response = requests.post(
                self.config.alert_webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()

        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")

    def _load_local_errors(self) -> None:
        """Load existing local errors."""
        try:
            error_files = list(self.storage_path.glob("error_*.json"))

            for error_file in error_files:
                try:
                    with open(error_file) as f:
                        error_data = json.load(f)

                    # Reconstruct error event
                    context = None
                    if error_data.get('context'):
                        context = ErrorContext(**error_data['context'])

                    error_event = ErrorEvent(
                        id=error_data['id'],
                        timestamp=error_data['timestamp'],
                        severity=ErrorSeverity(error_data['severity']),
                        category=ErrorCategory(error_data['category']),
                        message=error_data['message'],
                        exception_type=error_data.get('exception_type'),
                        stack_trace=error_data.get('stack_trace'),
                        context=context,
                        fingerprint=error_data.get('fingerprint'),
                        count=error_data.get('count', 1),
                        first_seen=error_data.get('first_seen'),
                        last_seen=error_data.get('last_seen'),
                        resolved=error_data.get('resolved', False)
                    )

                    self.error_cache[error_event.fingerprint] = error_event

                except Exception as e:
                    self.logger.warning(f"Failed to load error file {error_file}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to load local errors: {e}")

    def _cleanup_old_errors(self) -> None:
        """Cleanup old error files."""
        try:
            error_files = sorted(
                self.storage_path.glob("error_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            if len(error_files) > self.config.max_local_errors:
                for error_file in error_files[self.config.max_local_errors:]:
                    error_file.unlink()

        except Exception as e:
            self.logger.error(f"Failed to cleanup old errors: {e}")

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self.cache_lock:
            total_errors = len(self.error_cache)
            total_occurrences = sum(error.count for error in self.error_cache.values())

            # Group by severity
            severity_stats = {}
            for severity in ErrorSeverity:
                count = sum(1 for error in self.error_cache.values() if error.severity == severity)
                severity_stats[severity.value] = count

            # Group by category
            category_stats = {}
            for category in ErrorCategory:
                count = sum(1 for error in self.error_cache.values() if error.category == category)
                category_stats[category.value] = count

            return {
                'total_unique_errors': total_errors,
                'total_occurrences': total_occurrences,
                'by_severity': severity_stats,
                'by_category': category_stats,
                'cache_size': len(self.error_cache)
            }

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors."""
        with self.cache_lock:
            sorted_errors = sorted(
                self.error_cache.values(),
                key=lambda x: x.last_seen,
                reverse=True
            )

            return [error.to_dict() for error in sorted_errors[:limit]]


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance."""
    global _error_tracker

    if _error_tracker is None:
        _error_tracker = ErrorTracker()
        _error_tracker.initialize()

    return _error_tracker


def track_error(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.APPLICATION,
    context: Optional[ErrorContext] = None
) -> str:
    """Track an error."""
    return get_error_tracker().track_error(message, severity, category, context)


def track_exception(
    exception: Exception,
    severity: ErrorSeverity = ErrorSeverity.HIGH,
    category: ErrorCategory = ErrorCategory.APPLICATION,
    context: Optional[ErrorContext] = None
) -> str:
    """Track an exception."""
    return get_error_tracker().track_exception(exception, severity, category, context)


# Decorator for automatic exception tracking
def track_exceptions(
    severity: ErrorSeverity = ErrorSeverity.HIGH,
    category: ErrorCategory = ErrorCategory.APPLICATION,
    reraise: bool = True
):
    """Decorator for automatic exception tracking."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    operation=f"{func.__module__}.{func.__name__}",
                    component=func.__module__
                )

                track_exception(e, severity, category, context)

                if reraise:
                    raise

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize error tracking
    error_tracker = get_error_tracker()

    # Test error tracking
    try:
        raise ValueError("Test exception")
    except Exception as e:
        context = ErrorContext(
            user_id="test_user",
            operation="test_operation",
            additional_data={"test": True}
        )

        error_id = track_exception(
            e,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.APPLICATION,
            context=context
        )

        print(f"Tracked error: {error_id}")

    # Get error stats
    stats = error_tracker.get_error_stats()
    print(f"Error stats: {stats}")

    # Get recent errors
    recent = error_tracker.get_recent_errors(limit=5)
    print(f"Recent errors: {len(recent)}")
