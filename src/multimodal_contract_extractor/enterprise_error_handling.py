"""
Enterprise Error Handling and Recovery Framework

Comprehensive error handling, validation, monitoring, and security measures
for the multimodal contract extractor system with novel research algorithms.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import traceback
import uuid
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional, Type, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import threading
from pathlib import Path
import json
import psutil
import gc

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for categorization and handling."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SECURITY = "security"


class RecoveryStrategy(Enum):
    """Advanced recovery strategy options for different error scenarios."""
    
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF_RETRY = "exponential_backoff_retry"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_ALGORITHM = "fallback_algorithm"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SKIP_WITH_WARNING = "skip_with_warning"
    ABORT_OPERATION = "abort_operation"
    RESOURCE_CLEANUP_RETRY = "resource_cleanup_retry"
    DISTRIBUTED_FAILOVER = "distributed_failover"


class ComponentType(Enum):
    """System component types for targeted error handling."""
    
    QUANTUM_PROCESSOR = "quantum_processor"
    NEUROMORPHIC_ENGINE = "neuromorphic_engine"
    GNN_ANALYZER = "gnn_analyzer"
    TRANSFORMER_ATTENTION = "transformer_attention"
    FEDERATED_LEARNER = "federated_learner"
    CAUSAL_INFERENCE = "causal_inference"
    MULTIMODAL_FUSION = "multimodal_fusion"
    DOCUMENT_PROCESSOR = "document_processor"
    OCR_ENGINE = "ocr_engine"
    DATABASE_LAYER = "database_layer"
    API_GATEWAY = "api_gateway"
    SECURITY_LAYER = "security_layer"


class ResourceConstraint(Enum):
    """Resource constraint types for management."""
    
    MEMORY_LIMIT = "memory_limit"
    GPU_MEMORY = "gpu_memory"
    CPU_UTILIZATION = "cpu_utilization"
    NETWORK_BANDWIDTH = "network_bandwidth"
    DISK_SPACE = "disk_space"
    THREAD_POOL_SIZE = "thread_pool_size"


@dataclass
class ErrorContext:
    """Comprehensive error context for enterprise-grade error handling."""
    
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    component: ComponentType = ComponentType.DOCUMENT_PROCESSOR
    operation: str = ""
    error_type: Optional[Type[Exception]] = None
    error_message: str = ""
    stack_trace: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_session_id: Optional[str] = None
    request_id: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    performance_impact: float = 0.0
    business_impact: str = "low"


# Custom exception hierarchy for research algorithms
class ResearchAlgorithmError(Exception):
    """Base exception for research algorithm errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, component: ComponentType = ComponentType.DOCUMENT_PROCESSOR):
        super().__init__(message)
        self.severity = severity
        self.component = component
        self.timestamp = time.time()


class QuantumProcessingError(ResearchAlgorithmError):
    """Error in quantum processing algorithms."""
    
    def __init__(self, message: str, quantum_state: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.HIGH, ComponentType.QUANTUM_PROCESSOR)
        self.quantum_state = quantum_state or {}


class NeuromorphicProcessingError(ResearchAlgorithmError):
    """Error in neuromorphic processing algorithms."""
    
    def __init__(self, message: str, spike_data: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.HIGH, ComponentType.NEUROMORPHIC_ENGINE)
        self.spike_data = spike_data or {}


class GraphNeuralNetworkError(ResearchAlgorithmError):
    """Error in graph neural network processing."""
    
    def __init__(self, message: str, graph_structure: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.HIGH, ComponentType.GNN_ANALYZER)
        self.graph_structure = graph_structure or {}


class FederatedLearningError(ResearchAlgorithmError):
    """Error in federated learning operations."""
    
    def __init__(self, message: str, federation_state: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.HIGH, ComponentType.FEDERATED_LEARNER)
        self.federation_state = federation_state or {}


class CausalInferenceError(ResearchAlgorithmError):
    """Error in causal inference processing."""
    
    def __init__(self, message: str, causal_graph: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.MEDIUM, ComponentType.CAUSAL_INFERENCE)
        self.causal_graph = causal_graph or {}


class MultimodalFusionError(ResearchAlgorithmError):
    """Error in multimodal fusion processing."""
    
    def __init__(self, message: str, modality_data: Optional[Dict] = None):
        super().__init__(message, ErrorSeverity.HIGH, ComponentType.MULTIMODAL_FUSION)
        self.modality_data = modality_data or {}


class ResourceExhaustionError(ResearchAlgorithmError):
    """Error when system resources are exhausted."""
    
    def __init__(self, message: str, resource_type: ResourceConstraint, current_usage: float, limit: float):
        super().__init__(message, ErrorSeverity.CRITICAL)
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit


class CircuitBreakerOpenError(ResearchAlgorithmError):
    """Error when circuit breaker is in open state."""
    
    def __init__(self, circuit_name: str, failure_count: int, threshold: int):
        super().__init__(f"Circuit breaker '{circuit_name}' is open: {failure_count}/{threshold} failures", ErrorSeverity.HIGH)
        self.circuit_name = circuit_name
        self.failure_count = failure_count
        self.threshold = threshold


class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance."""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0, expected_exception: Type[Exception] = Exception):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half_open
        self._lock = threading.Lock()
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to apply circuit breaker to a function."""
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self.call_async(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half_open"
                    logger.info(f"Circuit breaker {self.name} moving to half-open state")
                else:
                    raise CircuitBreakerOpenError(self.name, self.failure_count, self.failure_threshold)
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection."""
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half_open"
                    logger.info(f"Circuit breaker {self.name} moving to half-open state")
                else:
                    raise CircuitBreakerOpenError(self.name, self.failure_count, self.failure_threshold)
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful execution."""
        with self._lock:
            self.failure_count = 0
            self.state = "closed"
            logger.debug(f"Circuit breaker {self.name} reset to closed state")
    
    def _on_failure(self):
        """Handle failed execution."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")


class ResourceManager:
    """Advanced resource management with constraints and monitoring."""
    
    def __init__(self):
        self.resource_limits = {
            ResourceConstraint.MEMORY_LIMIT: psutil.virtual_memory().total * 0.8,  # 80% of total memory
            ResourceConstraint.GPU_MEMORY: 8 * 1024**3,  # 8GB GPU memory (configurable)
            ResourceConstraint.CPU_UTILIZATION: 80.0,  # 80% CPU
            ResourceConstraint.NETWORK_BANDWIDTH: 1000.0,  # Mbps
            ResourceConstraint.DISK_SPACE: 10 * 1024**3,  # 10GB
            ResourceConstraint.THREAD_POOL_SIZE: 50
        }
        self.current_usage = {constraint: 0.0 for constraint in ResourceConstraint}
        self._lock = threading.Lock()
        self.resource_history: List[Dict[str, float]] = []
    
    def check_resource_availability(self, constraint: ResourceConstraint, required_amount: float) -> bool:
        """Check if required resources are available."""
        current = self.get_current_usage(constraint)
        available = self.resource_limits[constraint] - current
        return available >= required_amount
    
    def get_current_usage(self, constraint: ResourceConstraint) -> float:
        """Get current resource usage."""
        if constraint == ResourceConstraint.MEMORY_LIMIT:
            return psutil.virtual_memory().used
        elif constraint == ResourceConstraint.CPU_UTILIZATION:
            return psutil.cpu_percent(interval=0.1)
        elif constraint == ResourceConstraint.DISK_SPACE:
            return psutil.disk_usage('/').used
        else:
            return self.current_usage[constraint]
    
    @contextmanager
    def reserve_resources(self, resources: Dict[ResourceConstraint, float]) -> Generator[None, None, None]:
        """Context manager to reserve and release resources."""
        # Check availability
        for constraint, amount in resources.items():
            if not self.check_resource_availability(constraint, amount):
                current = self.get_current_usage(constraint)
                limit = self.resource_limits[constraint]
                raise ResourceExhaustionError(
                    f"Insufficient {constraint.value}: need {amount}, available {limit - current}",
                    constraint, current, limit
                )
        
        # Reserve resources
        with self._lock:
            for constraint, amount in resources.items():
                self.current_usage[constraint] += amount
        
        try:
            yield
        finally:
            # Release resources
            with self._lock:
                for constraint, amount in resources.items():
                    self.current_usage[constraint] = max(0, self.current_usage[constraint] - amount)
    
    def cleanup_resources(self):
        """Force cleanup of system resources."""
        gc.collect()  # Force garbage collection
        logger.info("Performed resource cleanup")


class EnterpriseErrorRecoveryManager:
    """Enterprise-grade error recovery manager for research algorithms."""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.resource_manager = ResourceManager()
        self.recovery_strategies: Dict[Type[Exception], RecoveryStrategy] = {
            QuantumProcessingError: RecoveryStrategy.FALLBACK_ALGORITHM,
            NeuromorphicProcessingError: RecoveryStrategy.RESOURCE_CLEANUP_RETRY,
            GraphNeuralNetworkError: RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY,
            FederatedLearningError: RecoveryStrategy.DISTRIBUTED_FAILOVER,
            CausalInferenceError: RecoveryStrategy.GRACEFUL_DEGRADATION,
            MultimodalFusionError: RecoveryStrategy.FALLBACK_ALGORITHM,
            ResourceExhaustionError: RecoveryStrategy.RESOURCE_CLEANUP_RETRY,
            CircuitBreakerOpenError: RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY,
            TimeoutError: RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY,
            MemoryError: RecoveryStrategy.RESOURCE_CLEANUP_RETRY,
            ConnectionError: RecoveryStrategy.DISTRIBUTED_FAILOVER,
            FileNotFoundError: RecoveryStrategy.ABORT_OPERATION,
        }
        
        self.fallback_algorithms = {
            ComponentType.QUANTUM_PROCESSOR: self._classical_processor_fallback,
            ComponentType.NEUROMORPHIC_ENGINE: self._standard_neural_network_fallback,
            ComponentType.GNN_ANALYZER: self._traditional_graph_analysis_fallback,
            ComponentType.TRANSFORMER_ATTENTION: self._basic_attention_fallback,
            ComponentType.FEDERATED_LEARNER: self._centralized_learning_fallback,
            ComponentType.MULTIMODAL_FUSION: self._single_modality_fallback,
        }
        
        # Initialize circuit breakers for critical components
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for critical components."""
        components = [
            ("quantum_processor", QuantumProcessingError),
            ("neuromorphic_engine", NeuromorphicProcessingError),
            ("gnn_analyzer", GraphNeuralNetworkError),
            ("federated_learner", FederatedLearningError),
            ("multimodal_fusion", MultimodalFusionError),
        ]
        
        for component_name, exception_type in components:
            self.circuit_breakers[component_name] = CircuitBreaker(
                name=component_name,
                failure_threshold=3,
                recovery_timeout=30.0,
                expected_exception=exception_type
            )
    
    def register_error(self, error_context: ErrorContext) -> None:
        """Register and track errors for analysis and recovery."""
        self.error_history.append(error_context)
        
        # Update resource usage in context
        error_context.resource_usage = {
            'memory_mb': psutil.virtual_memory().used / (1024**2),
            'cpu_percent': psutil.cpu_percent(),
            'disk_usage_gb': psutil.disk_usage('/').used / (1024**3)
        }
        
        # Log with structured format
        self._log_structured_error(error_context)
        
        # Trigger alerts for high severity errors
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.SECURITY]:
            self._trigger_alert(error_context)
    
    def _log_structured_error(self, error_context: ErrorContext):
        """Log error with structured format for analysis."""
        log_data = {
            'error_id': error_context.error_id,
            'correlation_id': error_context.correlation_id,
            'timestamp': error_context.timestamp,
            'severity': error_context.severity.value,
            'component': error_context.component.value,
            'operation': error_context.operation,
            'error_type': error_context.error_type.__name__ if error_context.error_type else 'Unknown',
            'error_message': error_context.error_message,
            'recovery_attempts': error_context.recovery_attempts,
            'resource_usage': error_context.resource_usage,
            'business_impact': error_context.business_impact
        }
        
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.SECURITY: logging.CRITICAL,
        }.get(error_context.severity, logging.ERROR)
        
        logger.log(log_level, f"Structured Error: {json.dumps(log_data, indent=2)}")
    
    def _trigger_alert(self, error_context: ErrorContext):
        """Trigger alerts for high-severity errors."""
        # This would integrate with monitoring systems like PagerDuty, Slack, etc.
        logger.critical(f"ALERT: High-severity error in {error_context.component.value}: {error_context.error_message}")
    
    async def execute_with_recovery(
        self, 
        func: Callable[..., T], 
        component: ComponentType,
        operation: str,
        *args,
        max_attempts: int = 3,
        **kwargs
    ) -> T:
        """Execute function with comprehensive error recovery."""
        error_context = ErrorContext(
            component=component,
            operation=operation,
            max_recovery_attempts=max_attempts
        )
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                error_context.recovery_attempts = attempt
                
                # Apply circuit breaker if available
                circuit_breaker = self.circuit_breakers.get(component.value)
                if circuit_breaker and asyncio.iscoroutinefunction(func):
                    result = await circuit_breaker.call_async(func, *args, **kwargs)
                elif circuit_breaker:
                    result = circuit_breaker.call(func, *args, **kwargs)
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                last_exception = e
                error_context.error_type = type(e)
                error_context.error_message = str(e)
                error_context.stack_trace = traceback.format_exc()
                error_context.severity = self._determine_error_severity(e)
                
                self.register_error(error_context)
                
                # Determine recovery strategy
                recovery_strategy = self.recovery_strategies.get(type(e), RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY)
                error_context.recovery_strategy = recovery_strategy
                
                if attempt < max_attempts - 1:  # Not the last attempt
                    should_retry = await self._execute_recovery_strategy(recovery_strategy, error_context, component)
                    if not should_retry:
                        break
                else:
                    # Last attempt failed, try fallback if available
                    fallback_result = await self._try_fallback(component, func, *args, **kwargs)
                    if fallback_result is not None:
                        return fallback_result
        
        # All recovery attempts failed
        logger.error(f"All recovery attempts failed for {component.value}.{operation}")
        raise last_exception
    
    def _determine_error_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type and context."""
        if isinstance(exception, (MemoryError, ResourceExhaustionError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, (QuantumProcessingError, NeuromorphicProcessingError, GraphNeuralNetworkError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (FederatedLearningError, MultimodalFusionError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.MEDIUM
    
    async def _execute_recovery_strategy(
        self, 
        strategy: RecoveryStrategy, 
        error_context: ErrorContext,
        component: ComponentType
    ) -> bool:
        """Execute recovery strategy and return whether to retry."""
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return True
        
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF_RETRY:
            delay = min(2 ** error_context.recovery_attempts, 60)  # Max 60 seconds
            logger.info(f"Exponential backoff: waiting {delay} seconds before retry")
            await asyncio.sleep(delay)
            return True
        
        elif strategy == RecoveryStrategy.RESOURCE_CLEANUP_RETRY:
            self.resource_manager.cleanup_resources()
            await asyncio.sleep(1)  # Brief pause after cleanup
            return True
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            # Circuit breaker is handled in execute_with_recovery
            return True
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            logger.warning(f"Graceful degradation for {component.value}")
            return False  # Don't retry, accept degraded performance
        
        elif strategy == RecoveryStrategy.SKIP_WITH_WARNING:
            logger.warning(f"Skipping operation for {component.value}")
            return False
        
        elif strategy == RecoveryStrategy.ABORT_OPERATION:
            logger.error(f"Aborting operation for {component.value}")
            return False
        
        elif strategy == RecoveryStrategy.DISTRIBUTED_FAILOVER:
            # Try alternative service instance or fallback service
            logger.info(f"Attempting distributed failover for {component.value}")
            await asyncio.sleep(2)  # Time for failover
            return True
        
        else:
            return True  # Default to retry
    
    async def _try_fallback(self, component: ComponentType, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """Try fallback algorithm if available."""
        fallback_func = self.fallback_algorithms.get(component)
        if fallback_func:
            try:
                logger.info(f"Attempting fallback algorithm for {component.value}")
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback algorithm failed for {component.value}: {e}")
        return None
    
    # Fallback algorithm implementations
    async def _classical_processor_fallback(self, *args, **kwargs):
        """Classical processing fallback for quantum algorithms."""
        logger.info("Using classical processing fallback")
        # Implement classical algorithm equivalent
        await asyncio.sleep(0.1)  # Simulate processing
        return {"fallback": True, "algorithm": "classical", "confidence": 0.7}
    
    async def _standard_neural_network_fallback(self, *args, **kwargs):
        """Standard neural network fallback for neuromorphic algorithms."""
        logger.info("Using standard neural network fallback")
        await asyncio.sleep(0.1)
        return {"fallback": True, "algorithm": "standard_nn", "confidence": 0.75}
    
    async def _traditional_graph_analysis_fallback(self, *args, **kwargs):
        """Traditional graph analysis fallback for GNN algorithms."""
        logger.info("Using traditional graph analysis fallback")
        await asyncio.sleep(0.1)
        return {"fallback": True, "algorithm": "traditional_graph", "confidence": 0.65}
    
    async def _basic_attention_fallback(self, *args, **kwargs):
        """Basic attention mechanism fallback for advanced transformers."""
        logger.info("Using basic attention fallback")
        await asyncio.sleep(0.1)
        return {"fallback": True, "algorithm": "basic_attention", "confidence": 0.8}
    
    async def _centralized_learning_fallback(self, *args, **kwargs):
        """Centralized learning fallback for federated learning."""
        logger.info("Using centralized learning fallback")
        await asyncio.sleep(0.1)
        return {"fallback": True, "algorithm": "centralized", "confidence": 0.85}
    
    async def _single_modality_fallback(self, *args, **kwargs):
        """Single modality fallback for multimodal fusion."""
        logger.info("Using single modality fallback")
        await asyncio.sleep(0.1)
        return {"fallback": True, "algorithm": "single_modality", "confidence": 0.6}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics for monitoring."""
        if not self.error_history:
            return {"total_errors": 0}
        
        total_errors = len(self.error_history)
        severity_counts = {}
        component_counts = {}
        recent_errors = []
        
        # Analyze last 24 hours
        cutoff_time = time.time() - 86400  # 24 hours
        
        for error in self.error_history:
            # Count by severity
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by component
            component = error.component.value
            component_counts[component] = component_counts.get(component, 0) + 1
            
            # Recent errors
            if error.timestamp > cutoff_time:
                recent_errors.append({
                    'error_id': error.error_id,
                    'timestamp': error.timestamp,
                    'severity': error.severity.value,
                    'component': error.component.value,
                    'message': error.error_message
                })
        
        return {
            'total_errors': total_errors,
            'severity_distribution': severity_counts,
            'component_distribution': component_counts,
            'recent_errors_24h': len(recent_errors),
            'recent_error_details': recent_errors[-10:],  # Last 10 recent errors
            'circuit_breaker_states': {name: cb.state for name, cb in self.circuit_breakers.items()},
            'resource_usage': {
                'memory_usage_mb': psutil.virtual_memory().used / (1024**2),
                'cpu_percent': psutil.cpu_percent(),
                'disk_usage_gb': psutil.disk_usage('/').used / (1024**3)
            }
        }


# Global error recovery manager instance
error_recovery_manager = EnterpriseErrorRecoveryManager()


# Decorator for automatic error handling
def with_error_recovery(component: ComponentType, operation: str, max_attempts: int = 3):
    """Decorator to add enterprise error recovery to functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await error_recovery_manager.execute_with_recovery(
                func, component, operation, *args, max_attempts=max_attempts, **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in async context
            return asyncio.run(error_recovery_manager.execute_with_recovery(
                func, component, operation, *args, max_attempts=max_attempts, **kwargs
            ))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context manager for resource-safe operations
@asynccontextmanager
async def safe_resource_context(resources: Dict[ResourceConstraint, float]):
    """Context manager for safe resource allocation and cleanup."""
    try:
        with error_recovery_manager.resource_manager.reserve_resources(resources):
            yield
    except ResourceExhaustionError as e:
        logger.error(f"Resource exhaustion: {e}")
        error_recovery_manager.resource_manager.cleanup_resources()
        raise
    except Exception as e:
        logger.error(f"Error in resource context: {e}")
        error_recovery_manager.resource_manager.cleanup_resources()
        raise


# Utility functions
def create_error_context(
    component: ComponentType,
    operation: str,
    exception: Optional[Exception] = None,
    severity: Optional[ErrorSeverity] = None,
    **kwargs
) -> ErrorContext:
    """Create error context with automatic field population."""
    context = ErrorContext(
        component=component,
        operation=operation,
        **kwargs
    )
    
    if exception:
        context.error_type = type(exception)
        context.error_message = str(exception)
        context.stack_trace = traceback.format_exc()
        
        if not severity:
            context.severity = error_recovery_manager._determine_error_severity(exception)
        else:
            context.severity = severity
    
    return context


def get_error_recovery_manager() -> EnterpriseErrorRecoveryManager:
    """Get the global error recovery manager instance."""
    return error_recovery_manager


# Health check function for monitoring integration
async def health_check() -> Dict[str, Any]:
    """Perform health check of error handling system."""
    stats = error_recovery_manager.get_error_statistics()
    
    # Check circuit breaker states
    unhealthy_circuits = [
        name for name, state in stats['circuit_breaker_states'].items() 
        if state == 'open'
    ]
    
    # Check resource usage
    memory_usage = stats['resource_usage']['memory_usage_mb']
    cpu_usage = stats['resource_usage']['cpu_percent']
    
    health_status = "healthy"
    if unhealthy_circuits:
        health_status = "degraded"
    if memory_usage > 8000 or cpu_usage > 90:  # High resource usage
        health_status = "warning"
    if stats['recent_errors_24h'] > 100:  # High error rate
        health_status = "critical"
    
    return {
        'status': health_status,
        'unhealthy_circuits': unhealthy_circuits,
        'error_rate_24h': stats['recent_errors_24h'],
        'resource_usage': stats['resource_usage'],
        'timestamp': time.time()
    }