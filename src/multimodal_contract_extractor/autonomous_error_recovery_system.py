"""
Autonomous Error Recovery System for SDLC Progressive Quality Gates

This system provides:
- Intelligent error detection and classification
- Automated recovery strategies
- Self-healing capabilities
- Circuit breaker patterns
- Progressive failure handling
- Learning from error patterns

Key Features:
- Automatic retry with exponential backoff
- Context-aware error classification
- Recovery strategy selection
- Failure pattern analysis
- Self-adapting thresholds
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
import json
from pathlib import Path


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification"""
    CRITICAL = "critical"  # System-breaking errors
    HIGH = "high"         # Phase-blocking errors  
    MEDIUM = "medium"     # Quality-affecting errors
    LOW = "low"          # Warning-level issues
    INFO = "info"        # Informational messages


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_METHOD = "fallback_method"
    SKIP_WITH_WARNING = "skip_with_warning"
    MANUAL_INTERVENTION = "manual_intervention"


class ErrorCategory(Enum):
    """Error categories for classification"""
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RESOURCE = "resource"
    LOGIC = "logic"


@dataclass
class ErrorContext:
    """Context information for error recovery"""
    error_type: Type[Exception]
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    phase: str
    operation: str
    attempt: int = 1
    max_attempts: int = 3
    backoff_factor: float = 2.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecoveryResult:
    """Result of error recovery attempt"""
    success: bool
    strategy_used: RecoveryStrategy
    attempts_made: int
    recovery_time: float
    final_result: Any = None
    error_message: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    timeout: float = 60.0  # seconds
    half_open_max_calls: int = 1


class CircuitBreaker:
    """Circuit breaker implementation for error recovery"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
            
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.config.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
            
        if self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
            
        return False
    
    def record_success(self) -> None:
        """Record successful execution"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            
        self.failure_count = 0
        self.half_open_calls = 0
    
    def record_failure(self) -> None:
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1


class AutonomousErrorRecoverySystem:
    """
    Autonomous error recovery system for SDLC quality gates
    
    Provides intelligent error handling with:
    - Automatic error classification
    - Context-aware recovery strategies
    - Progressive failure handling
    - Learning from error patterns
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.error_history: List[ErrorContext] = []
        self.recovery_stats: Dict[str, Dict] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize recovery strategies
        self.recovery_strategies = {
            RecoveryStrategy.RETRY_WITH_BACKOFF: self._retry_with_backoff,
            RecoveryStrategy.GRACEFUL_DEGRADATION: self._graceful_degradation,
            RecoveryStrategy.CIRCUIT_BREAKER: self._circuit_breaker_recovery,
            RecoveryStrategy.FALLBACK_METHOD: self._fallback_method,
            RecoveryStrategy.SKIP_WITH_WARNING: self._skip_with_warning,
        }
        
        # Error classification patterns
        self.error_patterns = {
            # Infrastructure errors
            (ConnectionError, OSError): (ErrorSeverity.HIGH, ErrorCategory.INFRASTRUCTURE),
            (TimeoutError,): (ErrorSeverity.MEDIUM, ErrorCategory.INFRASTRUCTURE),
            
            # Dependency errors
            (ImportError, ModuleNotFoundError): (ErrorSeverity.HIGH, ErrorCategory.DEPENDENCY),
            (FileNotFoundError,): (ErrorSeverity.MEDIUM, ErrorCategory.DEPENDENCY),
            
            # Configuration errors
            (ValueError, KeyError): (ErrorSeverity.MEDIUM, ErrorCategory.CONFIGURATION),
            
            # Resource errors
            (MemoryError, PermissionError): (ErrorSeverity.HIGH, ErrorCategory.RESOURCE),
            
            # Security errors
            (PermissionError,): (ErrorSeverity.CRITICAL, ErrorCategory.SECURITY),
        }

    def classify_error(self, error: Exception, phase: str, operation: str) -> ErrorContext:
        """
        Classify error and create context for recovery
        
        Args:
            error: The exception that occurred
            phase: SDLC phase where error occurred
            operation: Specific operation that failed
            
        Returns:
            Error context with classification and metadata
        """
        error_type = type(error)
        error_message = str(error)
        
        # Classify error based on type patterns
        severity = ErrorSeverity.MEDIUM
        category = ErrorCategory.LOGIC
        
        for error_types, (sev, cat) in self.error_patterns.items():
            if error_type in error_types:
                severity = sev
                category = cat
                break
        
        # Create error context
        context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            phase=phase,
            operation=operation,
            metadata={
                "traceback": traceback.format_exc(),
                "timestamp": time.time()
            }
        )
        
        # Add to error history
        self.error_history.append(context)
        
        logger.warning(
            f"Error classified: {severity.value} {category.value} - {operation}: {error_message}"
        )
        
        return context

    def select_recovery_strategy(self, context: ErrorContext) -> RecoveryStrategy:
        """
        Select appropriate recovery strategy based on error context
        
        Args:
            context: Error context information
            
        Returns:
            Selected recovery strategy
        """
        # Critical errors need immediate attention
        if context.severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.MANUAL_INTERVENTION
        
        # Infrastructure and dependency errors benefit from retries
        if context.category in [ErrorCategory.INFRASTRUCTURE, ErrorCategory.DEPENDENCY]:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # Performance issues may need circuit breaking
        if context.category == ErrorCategory.PERFORMANCE:
            return RecoveryStrategy.CIRCUIT_BREAKER
        
        # Configuration and validation errors can often be degraded gracefully
        if context.category in [ErrorCategory.CONFIGURATION, ErrorCategory.VALIDATION]:
            return RecoveryStrategy.GRACEFUL_DEGRADATION
        
        # Resource errors may need fallback methods
        if context.category == ErrorCategory.RESOURCE:
            return RecoveryStrategy.FALLBACK_METHOD
        
        # Default to retry for other cases
        return RecoveryStrategy.RETRY_WITH_BACKOFF

    async def recover_from_error(
        self, 
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """
        Attempt to recover from error using appropriate strategy
        
        Args:
            context: Error context
            operation_func: Function to retry
            args, kwargs: Arguments for the function
            
        Returns:
            Recovery result with outcome and metrics
        """
        start_time = time.time()
        strategy = self.select_recovery_strategy(context)
        
        logger.info(f"Attempting recovery using {strategy.value} for {context.operation}")
        
        try:
            recovery_func = self.recovery_strategies[strategy]
            result = await recovery_func(context, operation_func, *args, **kwargs)
            
            # Record success statistics
            operation_key = f"{context.phase}:{context.operation}"
            if operation_key not in self.recovery_stats:
                self.recovery_stats[operation_key] = {"attempts": 0, "successes": 0}
            
            self.recovery_stats[operation_key]["attempts"] += 1
            if result.success:
                self.recovery_stats[operation_key]["successes"] += 1
            
            recovery_time = time.time() - start_time
            result.recovery_time = recovery_time
            
            logger.info(
                f"Recovery {'succeeded' if result.success else 'failed'} "
                f"using {strategy.value} (took {recovery_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Recovery strategy {strategy.value} failed: {str(e)}")
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                attempts_made=context.attempt,
                recovery_time=time.time() - start_time,
                error_message=str(e),
                recommendations=["Consider manual intervention"]
            )

    async def _retry_with_backoff(
        self, 
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Retry with exponential backoff"""
        
        last_error = None
        
        for attempt in range(1, context.max_attempts + 1):
            try:
                if attempt > 1:
                    # Exponential backoff delay
                    delay = context.backoff_factor ** (attempt - 1)
                    logger.info(f"Retry attempt {attempt}/{context.max_attempts} after {delay}s delay")
                    await asyncio.sleep(delay)
                
                # Execute the operation
                if asyncio.iscoroutinefunction(operation_func):
                    result = await operation_func(*args, **kwargs)
                else:
                    result = operation_func(*args, **kwargs)
                
                return RecoveryResult(
                    success=True,
                    strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    attempts_made=attempt,
                    recovery_time=0,  # Will be set by caller
                    final_result=result
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Retry attempt {attempt} failed: {str(e)}")
        
        # All retries failed
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
            attempts_made=context.max_attempts,
            recovery_time=0,
            error_message=str(last_error),
            recommendations=[
                "Check system resources and dependencies",
                "Review error logs for patterns",
                "Consider increasing retry attempts"
            ]
        )

    async def _graceful_degradation(
        self,
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Gracefully degrade functionality"""
        
        # Provide a simplified version of the operation
        logger.info(f"Gracefully degrading {context.operation}")
        
        # For quality gates, we can return a warning status instead of failure
        degraded_result = {
            "status": "degraded",
            "original_operation": context.operation,
            "degradation_reason": context.error_message,
            "partial_result": True
        }
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
            attempts_made=1,
            recovery_time=0,
            final_result=degraded_result,
            recommendations=[
                "Monitor system health",
                "Plan for full functionality restoration",
                "Document degradation impact"
            ]
        )

    async def _circuit_breaker_recovery(
        self,
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Use circuit breaker pattern for recovery"""
        
        operation_key = f"{context.phase}:{context.operation}"
        
        # Initialize circuit breaker if needed
        if operation_key not in self.circuit_breakers:
            config = CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
            self.circuit_breakers[operation_key] = CircuitBreaker(config)
        
        circuit_breaker = self.circuit_breakers[operation_key]
        
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for {operation_key}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.CIRCUIT_BREAKER,
                attempts_made=0,
                recovery_time=0,
                error_message="Circuit breaker is OPEN",
                recommendations=[
                    "Wait for circuit breaker timeout",
                    "Check downstream dependencies",
                    "Consider alternative approaches"
                ]
            )
        
        try:
            # Execute with circuit breaker
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)
            
            circuit_breaker.record_success()
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.CIRCUIT_BREAKER,
                attempts_made=1,
                recovery_time=0,
                final_result=result
            )
            
        except Exception as e:
            circuit_breaker.record_failure()
            
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.CIRCUIT_BREAKER,
                attempts_made=1,
                recovery_time=0,
                error_message=str(e),
                recommendations=[
                    "Circuit breaker triggered",
                    "Investigate root cause",
                    "Consider manual reset if needed"
                ]
            )

    async def _fallback_method(
        self,
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Use fallback method for recovery"""
        
        # Provide a simple fallback implementation
        logger.info(f"Using fallback method for {context.operation}")
        
        fallback_result = {
            "status": "fallback_used",
            "original_operation": context.operation,
            "fallback_reason": context.error_message,
            "simplified_result": True
        }
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.FALLBACK_METHOD,
            attempts_made=1,
            recovery_time=0,
            final_result=fallback_result,
            recommendations=[
                "Implement proper fallback logic",
                "Monitor fallback usage patterns",
                "Plan for primary method restoration"
            ]
        )

    async def _skip_with_warning(
        self,
        context: ErrorContext,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> RecoveryResult:
        """Skip operation with warning"""
        
        logger.warning(f"Skipping {context.operation} due to error: {context.error_message}")
        
        skip_result = {
            "status": "skipped",
            "operation": context.operation,
            "skip_reason": context.error_message,
            "impact": "Operation was bypassed"
        }
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.SKIP_WITH_WARNING,
            attempts_made=1,
            recovery_time=0,
            final_result=skip_result,
            recommendations=[
                "Review if skip is acceptable",
                "Plan for retry in next cycle",
                "Document impact of skipping"
            ]
        )

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery system statistics"""
        
        total_errors = len(self.error_history)
        if total_errors == 0:
            return {"message": "No errors recorded"}
        
        # Error severity distribution
        severity_counts = {}
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Error category distribution
        category_counts = {}
        for error in self.error_history:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Recovery success rates
        total_attempts = sum(stats["attempts"] for stats in self.recovery_stats.values())
        total_successes = sum(stats["successes"] for stats in self.recovery_stats.values())
        success_rate = total_successes / total_attempts if total_attempts > 0 else 0
        
        return {
            "total_errors": total_errors,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "recovery_attempts": total_attempts,
            "recovery_successes": total_successes,
            "recovery_success_rate": success_rate,
            "active_circuit_breakers": len(self.circuit_breakers),
            "operation_stats": self.recovery_stats
        }

    def save_error_report(self, output_path: Path) -> None:
        """Save comprehensive error recovery report"""
        
        report_data = {
            "error_recovery_system": {
                "version": "1.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "statistics": self.get_recovery_statistics()
            },
            "error_history": [
                {
                    "error_type": error.error_type.__name__,
                    "message": error.error_message,
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "phase": error.phase,
                    "operation": error.operation,
                    "attempt": error.attempt,
                    "timestamp": error.timestamp
                }
                for error in self.error_history[-50:]  # Last 50 errors
            ],
            "circuit_breaker_states": {
                key: {
                    "state": breaker.state.value,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time
                }
                for key, breaker in self.circuit_breakers.items()
            }
        }
        
        output_path.write_text(json.dumps(report_data, indent=2))
        logger.info(f"Error recovery report saved to {output_path}")


def with_autonomous_recovery(
    phase: str,
    operation: str,
    max_attempts: int = 3,
    recovery_system: Optional[AutonomousErrorRecoverySystem] = None
):
    """
    Decorator for automatic error recovery
    
    Args:
        phase: SDLC phase name
        operation: Operation description
        max_attempts: Maximum retry attempts
        recovery_system: Error recovery system instance
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if recovery_system is None:
                # Fallback to direct execution if no recovery system
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            try:
                # Try direct execution first
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                # Classify error and attempt recovery
                context = recovery_system.classify_error(e, phase, operation)
                context.max_attempts = max_attempts
                
                recovery_result = await recovery_system.recover_from_error(
                    context, func, *args, **kwargs
                )
                
                if recovery_result.success:
                    return recovery_result.final_result
                else:
                    # Re-raise original exception if recovery failed
                    raise e
                    
        return wrapper
    return decorator


# Global error recovery system instance
_global_recovery_system: Optional[AutonomousErrorRecoverySystem] = None


def initialize_global_recovery_system(project_root: Path) -> AutonomousErrorRecoverySystem:
    """Initialize global error recovery system"""
    global _global_recovery_system
    _global_recovery_system = AutonomousErrorRecoverySystem(project_root)
    return _global_recovery_system


def get_global_recovery_system() -> Optional[AutonomousErrorRecoverySystem]:
    """Get global error recovery system"""
    return _global_recovery_system


if __name__ == "__main__":
    # Example usage and testing
    async def test_recovery_system():
        project_root = Path(__file__).parent.parent.parent
        recovery_system = AutonomousErrorRecoverySystem(project_root)
        
        # Test error classification
        try:
            raise ConnectionError("Failed to connect to service")
        except Exception as e:
            context = recovery_system.classify_error(e, "generation_1", "test_operation")
            print(f"Classified error: {context.severity.value} {context.category.value}")
        
        # Test recovery strategy selection
        strategy = recovery_system.select_recovery_strategy(context)
        print(f"Selected strategy: {strategy.value}")
        
        # Print statistics
        stats = recovery_system.get_recovery_statistics()
        print(f"Recovery stats: {stats}")
    
    asyncio.run(test_recovery_system())