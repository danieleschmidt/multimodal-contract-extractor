"""
Advanced error handling and resilience framework for production-ready operation.

This module provides comprehensive error handling, retry mechanisms, circuit breakers,
graceful degradation, and recovery strategies for robust operation in enterprise environments.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import threading
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class RetryStrategy(Enum):
    """Retry strategy types."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CUSTOM = "custom"


class FailureCategory(Enum):
    """Failure categories for classification."""
    TRANSIENT = "transient"  # Temporary failures that might succeed on retry
    PERMANENT = "permanent"  # Permanent failures that won't succeed on retry
    TIMEOUT = "timeout"     # Timeout-related failures
    RESOURCE = "resource"   # Resource exhaustion failures
    NETWORK = "network"     # Network-related failures
    SECURITY = "security"   # Security-related failures
    DATA = "data"          # Data validation/corruption failures
    UNKNOWN = "unknown"    # Unknown failure type


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()
    custom_delay_func: Optional[Callable[[int], float]] = None

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_failure_rate: float = 0.5
    minimum_request_threshold: int = 10
    half_open_max_calls: int = 3
    sliding_window_size: int = 100

    def __post_init__(self):
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if not 0 <= self.expected_failure_rate <= 1:
            raise ValueError("expected_failure_rate must be between 0 and 1")


@dataclass
class FailureInfo:
    """Information about a failure."""
    timestamp: datetime
    exception: Exception
    category: FailureCategory
    operation: str
    attempt: int
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None

    def __post_init__(self):
        if self.stack_trace is None:
            self.stack_trace = ''.join(traceback.format_exception(
                type(self.exception), self.exception, self.exception.__traceback__
            ))


class FailureClassifier:
    """Classifier for categorizing failures."""

    # Default exception classifications
    TRANSIENT_EXCEPTIONS = (
        ConnectionError,
        TimeoutError,
        OSError,  # Including network errors
    )

    PERMANENT_EXCEPTIONS = (
        ValueError,
        TypeError,
        AttributeError,
        ImportError,
        NotImplementedError,
    )

    TIMEOUT_EXCEPTIONS = (
        TimeoutError,
        asyncio.TimeoutError,
    )

    RESOURCE_EXCEPTIONS = (
        MemoryError,
        OSError,  # Can include disk full, etc.
    )

    @classmethod
    def classify_failure(cls, exception: Exception, context: Dict[str, Any] = None) -> FailureCategory:
        """Classify a failure based on exception type and context."""
        context = context or {}

        # Check for timeout exceptions first
        if isinstance(exception, cls.TIMEOUT_EXCEPTIONS):
            return FailureCategory.TIMEOUT

        # Check for resource exceptions
        if isinstance(exception, cls.RESOURCE_EXCEPTIONS):
            return FailureCategory.RESOURCE

        # Check for permanent exceptions
        if isinstance(exception, cls.PERMANENT_EXCEPTIONS):
            return FailureCategory.PERMANENT

        # Check for transient exceptions
        if isinstance(exception, cls.TRANSIENT_EXCEPTIONS):
            return FailureCategory.TRANSIENT

        # Check for security-related exceptions
        if "security" in str(exception).lower() or "permission" in str(exception).lower():
            return FailureCategory.SECURITY

        # Check for data-related exceptions
        if "data" in str(exception).lower() or "validation" in str(exception).lower():
            return FailureCategory.DATA

        # Check for network-related exceptions
        if "network" in str(exception).lower() or "connection" in str(exception).lower():
            return FailureCategory.NETWORK

        # Default to unknown
        return FailureCategory.UNKNOWN


class CircuitBreaker:
    """Circuit breaker implementation for handling cascading failures."""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_call_count = 0
        self.request_history: List[bool] = []  # True for success, False for failure
        self._lock = threading.Lock()

        # Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.state_gauge = Gauge(
                'circuit_breaker_state',
                'Circuit breaker state (0=closed, 1=open, 2=half_open)',
                ['name']
            )
            self.failure_counter = Counter(
                'circuit_breaker_failures_total',
                'Total circuit breaker failures',
                ['name', 'category']
            )
            self.call_counter = Counter(
                'circuit_breaker_calls_total',
                'Total circuit breaker calls',
                ['name', 'result']
            )

    def _update_metrics(self):
        """Update Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        state_value = {
            CircuitBreakerState.CLOSED: 0,
            CircuitBreakerState.OPEN: 1,
            CircuitBreakerState.HALF_OPEN: 2
        }[self.state]

        self.state_gauge.labels(name=self.name).set(state_value)

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        if self.last_failure_time is None:
            return True

        time_since_last_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_last_failure.total_seconds() >= self.config.recovery_timeout

    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            self.success_count += 1
            self.request_history.append(True)

            # Trim history to sliding window size
            if len(self.request_history) > self.config.sliding_window_size:
                self.request_history.pop(0)

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_call_count += 1
                # If we've had enough successful calls in half-open, close the circuit
                if self.half_open_call_count >= self.config.half_open_max_calls:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.half_open_call_count = 0
                    logger.info(f"Circuit breaker {self.name} closed after successful recovery")

            if PROMETHEUS_AVAILABLE:
                self.call_counter.labels(name=self.name, result='success').inc()

            self._update_metrics()

    def _record_failure(self, exception: Exception):
        """Record a failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now(timezone.utc)
            self.request_history.append(False)

            # Trim history to sliding window size
            if len(self.request_history) > self.config.sliding_window_size:
                self.request_history.pop(0)

            # Classify the failure
            failure_category = FailureClassifier.classify_failure(exception)

            if PROMETHEUS_AVAILABLE:
                self.call_counter.labels(name=self.name, result='failure').inc()
                self.failure_counter.labels(name=self.name, category=failure_category.value).inc()

            # Check if we should open the circuit
            if (self.state == CircuitBreakerState.CLOSED and
                len(self.request_history) >= self.config.minimum_request_threshold):

                recent_failures = sum(1 for result in self.request_history if not result)
                failure_rate = recent_failures / len(self.request_history)

                if (failure_rate >= self.config.expected_failure_rate or
                    self.failure_count >= self.config.failure_threshold):

                    self.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker {self.name} opened due to failure rate: {failure_rate:.2%}")

            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Failure in half-open state, go back to open
                self.state = CircuitBreakerState.OPEN
                self.half_open_call_count = 0
                logger.warning(f"Circuit breaker {self.name} reopened after failure in half-open state")

            self._update_metrics()

    @contextmanager
    def call(self):
        """Context manager for circuit breaker calls."""
        # Check if we should attempt a reset
        if self._should_attempt_reset():
            with self._lock:
                if self.state == CircuitBreakerState.OPEN:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_call_count = 0
                    logger.info(f"Circuit breaker {self.name} entering half-open state")

        # Check current state
        if self.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is open")

        # Allow the call to proceed
        try:
            yield
            self._record_success()
        except Exception as e:
            self._record_failure(e)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        with self._lock:
            total_requests = len(self.request_history)
            failures = sum(1 for result in self.request_history if not result)
            success_rate = (total_requests - failures) / total_requests if total_requests > 0 else 0

            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "success_rate": success_rate,
                "total_requests": total_requests,
                "half_open_call_count": self.half_open_call_count,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "expected_failure_rate": self.config.expected_failure_rate
                }
            }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class RetryManager:
    """Advanced retry manager with multiple strategies."""

    def __init__(self, config: RetryConfig):
        self.config = config

        if PROMETHEUS_AVAILABLE:
            self.retry_counter = Counter(
                'retry_attempts_total',
                'Total retry attempts',
                ['operation', 'attempt', 'result']
            )
            self.retry_histogram = Histogram(
                'retry_duration_seconds',
                'Time spent in retry operations',
                ['operation']
            )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt."""
        if self.config.strategy == RetryStrategy.CUSTOM and self.config.custom_delay_func:
            base_delay = self.config.custom_delay_func(attempt)
        elif self.config.strategy == RetryStrategy.FIXED:
            base_delay = self.config.initial_delay
        elif self.config.strategy == RetryStrategy.LINEAR:
            base_delay = self.config.initial_delay * attempt
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            base_delay = self.config.initial_delay * (self.config.backoff_multiplier ** (attempt - 1))
        else:
            base_delay = self.config.initial_delay

        # Apply jitter if enabled
        if self.config.jitter:
            import random
            jitter_factor = random.uniform(0.5, 1.5)
            base_delay *= jitter_factor

        # Respect maximum delay
        return min(base_delay, self.config.max_delay)

    def _is_retryable(self, exception: Exception) -> bool:
        """Check if an exception is retryable."""
        # Check non-retryable exceptions first
        if isinstance(exception, self.config.non_retryable_exceptions):
            return False

        # Check retryable exceptions
        if isinstance(exception, self.config.retryable_exceptions):
            return True

        # Check based on failure classification
        category = FailureClassifier.classify_failure(exception)
        return category in [FailureCategory.TRANSIENT, FailureCategory.TIMEOUT, FailureCategory.NETWORK]

    def execute_with_retry(self, operation: Callable[[], T], operation_name: str = "unknown") -> T:
        """Execute an operation with retry logic."""
        start_time = time.time()
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if PROMETHEUS_AVAILABLE:
                    with self.retry_histogram.labels(operation=operation_name).time():
                        result = operation()
                else:
                    result = operation()

                if PROMETHEUS_AVAILABLE:
                    self.retry_counter.labels(
                        operation=operation_name,
                        attempt=str(attempt),
                        result='success'
                    ).inc()

                if attempt > 1:
                    logger.info(f"Operation {operation_name} succeeded on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e

                if PROMETHEUS_AVAILABLE:
                    self.retry_counter.labels(
                        operation=operation_name,
                        attempt=str(attempt),
                        result='failure'
                    ).inc()

                # Check if this is the last attempt
                if attempt >= self.config.max_attempts:
                    logger.error(f"Operation {operation_name} failed after {attempt} attempts: {e}")
                    break

                # Check if exception is retryable
                if not self._is_retryable(e):
                    logger.error(f"Operation {operation_name} failed with non-retryable exception: {e}")
                    break

                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                logger.warning(f"Operation {operation_name} failed on attempt {attempt}, retrying in {delay:.2f}s: {e}")
                time.sleep(delay)

        # All attempts exhausted
        raise RetryExhaustedError(
            f"Operation {operation_name} failed after {self.config.max_attempts} attempts",
            self.config.max_attempts,
            last_exception
        )


class GracefulDegradationManager:
    """Manager for graceful degradation strategies."""

    def __init__(self):
        self.degradation_strategies: Dict[str, Callable] = {}
        self.active_degradations: Dict[str, datetime] = {}
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.degradation_gauge = Gauge(
                'graceful_degradation_active',
                'Active graceful degradations',
                ['service', 'strategy']
            )

    def register_strategy(self, service_name: str, strategy: Callable):
        """Register a degradation strategy for a service."""
        self.degradation_strategies[service_name] = strategy
        logger.info(f"Registered degradation strategy for service: {service_name}")

    def activate_degradation(self, service_name: str, reason: str = ""):
        """Activate graceful degradation for a service."""
        with self._lock:
            if service_name not in self.active_degradations:
                self.active_degradations[service_name] = datetime.now(timezone.utc)
                logger.warning(f"Activated graceful degradation for {service_name}: {reason}")

                if PROMETHEUS_AVAILABLE:
                    self.degradation_gauge.labels(
                        service=service_name,
                        strategy='active'
                    ).set(1)

    def deactivate_degradation(self, service_name: str):
        """Deactivate graceful degradation for a service."""
        with self._lock:
            if service_name in self.active_degradations:
                del self.active_degradations[service_name]
                logger.info(f"Deactivated graceful degradation for {service_name}")

                if PROMETHEUS_AVAILABLE:
                    self.degradation_gauge.labels(
                        service=service_name,
                        strategy='active'
                    ).set(0)

    def is_degraded(self, service_name: str) -> bool:
        """Check if a service is currently degraded."""
        return service_name in self.active_degradations

    def execute_with_degradation(self, service_name: str, primary_operation: Callable[[], T],
                                context: Dict[str, Any] = None) -> T:
        """Execute operation with potential graceful degradation."""
        context = context or {}

        if self.is_degraded(service_name) and service_name in self.degradation_strategies:
            logger.info(f"Using degraded mode for service: {service_name}")
            return self.degradation_strategies[service_name](context)

        return primary_operation()

    def get_status(self) -> Dict[str, Any]:
        """Get current degradation status."""
        with self._lock:
            return {
                "active_degradations": {
                    service: activation_time.isoformat()
                    for service, activation_time in self.active_degradations.items()
                },
                "registered_strategies": list(self.degradation_strategies.keys()),
                "total_active": len(self.active_degradations)
            }


class ResilienceManager:
    """Central manager for resilience patterns."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_managers: Dict[str, RetryManager] = {}
        self.degradation_manager = GracefulDegradationManager()
        self.failure_history: List[FailureInfo] = []
        self._lock = threading.Lock()

        # Keep only recent failures
        self.max_failure_history = 1000

        if PROMETHEUS_AVAILABLE:
            self.resilience_operations = Counter(
                'resilience_operations_total',
                'Total resilience operations',
                ['operation', 'pattern', 'result']
            )

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Register a circuit breaker."""
        circuit_breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = circuit_breaker
        logger.info(f"Registered circuit breaker: {name}")
        return circuit_breaker

    def register_retry_manager(self, name: str, config: RetryConfig) -> RetryManager:
        """Register a retry manager."""
        retry_manager = RetryManager(config)
        self.retry_managers[name] = retry_manager
        logger.info(f"Registered retry manager: {name}")
        return retry_manager

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self.circuit_breakers.get(name)

    def get_retry_manager(self, name: str) -> Optional[RetryManager]:
        """Get a retry manager by name."""
        return self.retry_managers.get(name)

    def record_failure(self, operation: str, exception: Exception, context: Dict[str, Any] = None):
        """Record a failure for analysis."""
        failure_info = FailureInfo(
            timestamp=datetime.now(timezone.utc),
            exception=exception,
            category=FailureClassifier.classify_failure(exception, context),
            operation=operation,
            attempt=context.get('attempt', 1) if context else 1,
            context=context or {}
        )

        with self._lock:
            self.failure_history.append(failure_info)

            # Trim history if needed
            if len(self.failure_history) > self.max_failure_history:
                self.failure_history = self.failure_history[-self.max_failure_history:]

        logger.error(f"Recorded failure for operation {operation}: {exception}")

    def execute_resilient_operation(
        self,
        operation: Callable[[], T],
        operation_name: str,
        circuit_breaker_name: Optional[str] = None,
        retry_manager_name: Optional[str] = None,
        degradation_service: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> T:
        """Execute an operation with full resilience patterns."""
        context = context or {}
        start_time = time.time()

        try:
            # Get resilience components
            circuit_breaker = self.circuit_breakers.get(circuit_breaker_name) if circuit_breaker_name else None
            retry_manager = self.retry_managers.get(retry_manager_name) if retry_manager_name else None

            # Define the operation with circuit breaker if available
            def protected_operation():
                if circuit_breaker:
                    with circuit_breaker.call():
                        return operation()
                else:
                    return operation()

            # Execute with retry if available
            if retry_manager:
                result = retry_manager.execute_with_retry(protected_operation, operation_name)
            else:
                result = protected_operation()

            if PROMETHEUS_AVAILABLE:
                self.resilience_operations.labels(
                    operation=operation_name,
                    pattern='full',
                    result='success'
                ).inc()

            return result

        except (CircuitBreakerOpenError, RetryExhaustedError) as e:
            # Try graceful degradation if available
            if degradation_service:
                try:
                    logger.warning(f"Attempting graceful degradation for {operation_name}: {e}")
                    self.degradation_manager.activate_degradation(degradation_service, str(e))

                    def degraded_operation():
                        return operation()  # This might be replaced with a degraded version

                    result = self.degradation_manager.execute_with_degradation(
                        degradation_service, degraded_operation, context
                    )

                    if PROMETHEUS_AVAILABLE:
                        self.resilience_operations.labels(
                            operation=operation_name,
                            pattern='degraded',
                            result='success'
                        ).inc()

                    return result

                except Exception as degradation_error:
                    logger.error(f"Graceful degradation also failed for {operation_name}: {degradation_error}")
                    self.record_failure(operation_name, degradation_error, context)
                    raise

            # Record the failure
            self.record_failure(operation_name, e, context)

            if PROMETHEUS_AVAILABLE:
                self.resilience_operations.labels(
                    operation=operation_name,
                    pattern='full',
                    result='failure'
                ).inc()

            raise

        except Exception as e:
            self.record_failure(operation_name, e, context)
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system resilience status."""
        with self._lock:
            # Analyze recent failures
            recent_failures = [
                f for f in self.failure_history
                if (datetime.now(timezone.utc) - f.timestamp).total_seconds() < 3600  # Last hour
            ]

            failure_by_category = {}
            for failure in recent_failures:
                category = failure.category.value
                failure_by_category[category] = failure_by_category.get(category, 0) + 1

            return {
                "circuit_breakers": {
                    name: cb.get_status() for name, cb in self.circuit_breakers.items()
                },
                "degradation": self.degradation_manager.get_status(),
                "failure_analysis": {
                    "total_failures": len(self.failure_history),
                    "recent_failures": len(recent_failures),
                    "failures_by_category": failure_by_category,
                    "most_common_failures": [
                        f.operation for f in recent_failures[:10]
                    ]
                },
                "registered_components": {
                    "circuit_breakers": len(self.circuit_breakers),
                    "retry_managers": len(self.retry_managers),
                    "degradation_strategies": len(self.degradation_manager.degradation_strategies)
                }
            }


# Global resilience manager instance
_resilience_manager: Optional[ResilienceManager] = None


def get_resilience_manager() -> ResilienceManager:
    """Get the global resilience manager instance."""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = ResilienceManager()
    return _resilience_manager


# Convenience decorators
def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker protection to a function."""
    def decorator(func: Callable) -> Callable:
        manager = get_resilience_manager()

        if name not in manager.circuit_breakers:
            cb_config = config or CircuitBreakerConfig()
            manager.register_circuit_breaker(name, cb_config)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            circuit_breaker = manager.circuit_breakers[name]
            with circuit_breaker.call():
                return func(*args, **kwargs)

        return wrapper
    return decorator


def with_retry(name: str, config: Optional[RetryConfig] = None):
    """Decorator to add retry logic to a function."""
    def decorator(func: Callable) -> Callable:
        manager = get_resilience_manager()

        if name not in manager.retry_managers:
            retry_config = config or RetryConfig()
            manager.register_retry_manager(name, retry_config)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = manager.retry_managers[name]
            return retry_manager.execute_with_retry(
                lambda: func(*args, **kwargs),
                f"{func.__module__}.{func.__name__}"
            )

        return wrapper
    return decorator


def with_resilience(
    circuit_breaker: Optional[str] = None,
    retry_manager: Optional[str] = None,
    degradation_service: Optional[str] = None
):
    """Decorator to add full resilience patterns to a function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_resilience_manager()
            return manager.execute_resilient_operation(
                lambda: func(*args, **kwargs),
                f"{func.__module__}.{func.__name__}",
                circuit_breaker,
                retry_manager,
                degradation_service
            )

        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import random

    # Example of using the resilience framework
    manager = get_resilience_manager()

    # Register circuit breaker
    cb_config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=10.0)
    manager.register_circuit_breaker("test_service", cb_config)

    # Register retry manager
    retry_config = RetryConfig(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    manager.register_retry_manager("test_retry", retry_config)

    # Example operation that might fail
    def unreliable_operation():
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("Simulated network failure")
        return "Success!"

    # Test resilient execution
    try:
        result = manager.execute_resilient_operation(
            unreliable_operation,
            "test_operation",
            circuit_breaker_name="test_service",
            retry_manager_name="test_retry"
        )
        print(f"Operation succeeded: {result}")
    except Exception as e:
        print(f"Operation failed: {e}")

    # Print system status
    status = manager.get_system_status()
    print(f"System status: {status}")
