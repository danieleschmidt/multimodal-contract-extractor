"""Enterprise Resilience Framework for Mission-Critical Legal AI Operations."""

import asyncio
import json
import logging
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class FailureMode(Enum):
    """Types of failure modes in legal AI systems."""
    
    MODEL_DEGRADATION = "model_degradation"
    DATA_CORRUPTION = "data_corruption"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    SECURITY_BREACH = "security_breach"
    CONFIGURATION_ERROR = "configuration_error"
    HARDWARE_FAILURE = "hardware_failure"


class RecoveryStrategy(Enum):
    """Recovery strategies for different failure scenarios."""
    
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_MODEL = "fallback_model"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAILOVER_CLUSTER = "failover_cluster"
    DATA_RECOVERY = "data_recovery"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    MANUAL_INTERVENTION = "manual_intervention"


class ResilienceLevel(Enum):
    """Levels of system resilience."""
    
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MISSION_CRITICAL = "mission_critical"


@dataclass
class FailureScenario:
    """Definition of a failure scenario and recovery plan."""
    
    id: str
    failure_mode: FailureMode
    description: str
    probability: float
    impact_severity: int  # 1-5 scale
    detection_time: float  # seconds
    recovery_strategy: RecoveryStrategy
    recovery_time_target: float  # seconds (RTO)
    data_loss_target: float  # seconds (RPO)
    automated_recovery: bool = True
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ResilienceEvent:
    """Record of a resilience event (failure or recovery)."""
    
    timestamp: float
    event_type: str  # "failure" or "recovery"
    failure_mode: Optional[FailureMode]
    scenario_id: str
    duration: Optional[float]
    recovery_strategy_used: Optional[RecoveryStrategy]
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker implementation for service protection."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise e


class RetryHandler:
    """Advanced retry handler with exponential backoff and jitter."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                # Add jitter to prevent thundering herd
                if self.jitter:
                    delay += random.uniform(0, delay * 0.1)
                
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception


class FallbackModelManager:
    """Manager for fallback models in case of primary model failure."""
    
    def __init__(self):
        self.fallback_models: Dict[str, Any] = {}
        self.model_priorities: Dict[str, int] = {}
        self.model_health: Dict[str, bool] = {}
    
    def register_fallback_model(
        self, model_name: str, model_instance: Any, priority: int = 1
    ) -> None:
        """Register a fallback model."""
        self.fallback_models[model_name] = model_instance
        self.model_priorities[model_name] = priority
        self.model_health[model_name] = True
        logger.info(f"Registered fallback model: {model_name} (priority: {priority})")
    
    def get_best_available_model(self, exclude_models: Optional[List[str]] = None) -> Optional[Tuple[str, Any]]:
        """Get the best available fallback model."""
        exclude_models = exclude_models or []
        
        # Filter healthy models not in exclude list
        available_models = {
            name: model for name, model in self.fallback_models.items()
            if self.model_health.get(name, False) and name not in exclude_models
        }
        
        if not available_models:
            return None
        
        # Sort by priority (higher priority first)
        sorted_models = sorted(
            available_models.items(),
            key=lambda x: self.model_priorities.get(x[0], 0),
            reverse=True
        )
        
        return sorted_models[0]
    
    def mark_model_unhealthy(self, model_name: str) -> None:
        """Mark a model as unhealthy."""
        if model_name in self.model_health:
            self.model_health[model_name] = False
            logger.warning(f"Marked model as unhealthy: {model_name}")
    
    def mark_model_healthy(self, model_name: str) -> None:
        """Mark a model as healthy."""
        if model_name in self.model_health:
            self.model_health[model_name] = True
            logger.info(f"Marked model as healthy: {model_name}")


class EnterpriseResilienceFramework:
    """Comprehensive resilience framework for enterprise legal AI systems."""
    
    def __init__(self, resilience_level: ResilienceLevel = ResilienceLevel.STANDARD):
        self.resilience_level = resilience_level
        self.failure_scenarios: Dict[str, FailureScenario] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.fallback_manager = FallbackModelManager()
        self.resilience_events: deque = deque(maxlen=1000)
        self.health_checks: Dict[str, Callable] = {}
        self.disaster_recovery_plans: Dict[str, Dict[str, Any]] = {}
        
        # Initialize based on resilience level
        self._initialize_resilience_components()
    
    def _initialize_resilience_components(self) -> None:
        """Initialize resilience components based on level."""
        if self.resilience_level == ResilienceLevel.BASIC:
            self._setup_basic_resilience()
        elif self.resilience_level == ResilienceLevel.STANDARD:
            self._setup_standard_resilience()
        elif self.resilience_level == ResilienceLevel.HIGH:
            self._setup_high_resilience()
        elif self.resilience_level == ResilienceLevel.MISSION_CRITICAL:
            self._setup_mission_critical_resilience()
    
    def _setup_basic_resilience(self) -> None:
        """Setup basic resilience features."""
        # Basic retry for API calls
        self.retry_handlers["api_calls"] = RetryHandler(max_retries=2, base_delay=0.5)
        
        # Simple circuit breaker for external services
        self.circuit_breakers["external_services"] = CircuitBreaker(
            failure_threshold=3, timeout=30.0
        )
    
    def _setup_standard_resilience(self) -> None:
        """Setup standard resilience features."""
        self._setup_basic_resilience()
        
        # Enhanced retry strategies
        self.retry_handlers["model_inference"] = RetryHandler(
            max_retries=3, base_delay=1.0, max_delay=10.0
        )
        
        # Additional circuit breakers
        self.circuit_breakers["database"] = CircuitBreaker(
            failure_threshold=5, timeout=60.0
        )
        
        # Basic failure scenarios
        self._setup_standard_failure_scenarios()
    
    def _setup_high_resilience(self) -> None:
        """Setup high resilience features."""
        self._setup_standard_resilience()
        
        # More aggressive retry policies
        self.retry_handlers["critical_operations"] = RetryHandler(
            max_retries=5, base_delay=0.5, max_delay=30.0, backoff_factor=1.5
        )
        
        # Additional circuit breakers with faster recovery
        self.circuit_breakers["ml_pipeline"] = CircuitBreaker(
            failure_threshold=3, timeout=30.0
        )
        
        # Comprehensive failure scenarios
        self._setup_high_resilience_scenarios()
    
    def _setup_mission_critical_resilience(self) -> None:
        """Setup mission-critical resilience features."""
        self._setup_high_resilience()
        
        # Maximum retry attempts for critical operations
        self.retry_handlers["mission_critical"] = RetryHandler(
            max_retries=10, base_delay=0.1, max_delay=60.0, backoff_factor=1.2
        )
        
        # Aggressive circuit breakers
        self.circuit_breakers["real_time_processing"] = CircuitBreaker(
            failure_threshold=2, timeout=15.0
        )
        
        # Complete failure scenario coverage
        self._setup_mission_critical_scenarios()
    
    def _setup_standard_failure_scenarios(self) -> None:
        """Setup standard failure scenarios."""
        scenarios = [
            FailureScenario(
                id="model_latency_spike",
                failure_mode=FailureMode.MODEL_DEGRADATION,
                description="Model inference latency exceeds acceptable thresholds",
                probability=0.15,
                impact_severity=3,
                detection_time=30.0,
                recovery_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                recovery_time_target=60.0,
                data_loss_target=0.0
            ),
            FailureScenario(
                id="dependency_timeout",
                failure_mode=FailureMode.DEPENDENCY_FAILURE,
                description="External dependency becomes unresponsive",
                probability=0.10,
                impact_severity=2,
                detection_time=15.0,
                recovery_strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                recovery_time_target=30.0,
                data_loss_target=0.0
            )
        ]
        
        for scenario in scenarios:
            self.failure_scenarios[scenario.id] = scenario
    
    def _setup_high_resilience_scenarios(self) -> None:
        """Setup high resilience failure scenarios."""
        self._setup_standard_failure_scenarios()
        
        additional_scenarios = [
            FailureScenario(
                id="model_accuracy_degradation",
                failure_mode=FailureMode.MODEL_DEGRADATION,
                description="Model accuracy drops below acceptable threshold",
                probability=0.08,
                impact_severity=4,
                detection_time=300.0,
                recovery_strategy=RecoveryStrategy.FALLBACK_MODEL,
                recovery_time_target=120.0,
                data_loss_target=0.0
            ),
            FailureScenario(
                id="memory_exhaustion",
                failure_mode=FailureMode.RESOURCE_EXHAUSTION,
                description="System memory usage exceeds safe limits",
                probability=0.12,
                impact_severity=3,
                detection_time=60.0,
                recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                recovery_time_target=180.0,
                data_loss_target=0.0
            )
        ]
        
        for scenario in additional_scenarios:
            self.failure_scenarios[scenario.id] = scenario
    
    def _setup_mission_critical_scenarios(self) -> None:
        """Setup mission-critical failure scenarios."""
        self._setup_high_resilience_scenarios()
        
        critical_scenarios = [
            FailureScenario(
                id="data_center_outage",
                failure_mode=FailureMode.HARDWARE_FAILURE,
                description="Primary data center becomes unavailable",
                probability=0.02,
                impact_severity=5,
                detection_time=10.0,
                recovery_strategy=RecoveryStrategy.FAILOVER_CLUSTER,
                recovery_time_target=300.0,
                data_loss_target=60.0
            ),
            FailureScenario(
                id="security_incident",
                failure_mode=FailureMode.SECURITY_BREACH,
                description="Security breach detected in the system",
                probability=0.05,
                impact_severity=5,
                detection_time=120.0,
                recovery_strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                recovery_time_target=1800.0,
                data_loss_target=0.0,
                automated_recovery=False
            ),
            FailureScenario(
                id="cascading_failure",
                failure_mode=FailureMode.DEPENDENCY_FAILURE,
                description="Multiple system components fail in sequence",
                probability=0.03,
                impact_severity=5,
                detection_time=30.0,
                recovery_strategy=RecoveryStrategy.ROLLBACK_DEPLOYMENT,
                recovery_time_target=600.0,
                data_loss_target=300.0
            )
        ]
        
        for scenario in critical_scenarios:
            self.failure_scenarios[scenario.id] = scenario
    
    async def execute_with_resilience(
        self,
        operation_name: str,
        operation_func: Callable,
        *args,
        fallback_func: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Execute an operation with full resilience protection."""
        start_time = time.time()
        
        try:
            # Apply circuit breaker if configured
            if operation_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[operation_name]
                
                # Apply retry handler if configured
                if operation_name in self.retry_handlers:
                    retry_handler = self.retry_handlers[operation_name]
                    result = await circuit_breaker.call(
                        retry_handler.execute, operation_func, *args, **kwargs
                    )
                else:
                    result = await circuit_breaker.call(operation_func, *args, **kwargs)
            
            # Apply only retry handler if no circuit breaker
            elif operation_name in self.retry_handlers:
                retry_handler = self.retry_handlers[operation_name]
                result = await retry_handler.execute(operation_func, *args, **kwargs)
            
            # Execute directly if no resilience handlers configured
            else:
                if asyncio.iscoroutinefunction(operation_func):
                    result = await operation_func(*args, **kwargs)
                else:
                    result = operation_func(*args, **kwargs)
            
            # Record successful execution
            await self._record_resilience_event(
                event_type="success",
                scenario_id=f"{operation_name}_execution",
                duration=time.time() - start_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Try fallback if available
            if fallback_func:
                try:
                    logger.warning(f"Operation {operation_name} failed, trying fallback: {e}")
                    
                    if asyncio.iscoroutinefunction(fallback_func):
                        result = await fallback_func(*args, **kwargs)
                    else:
                        result = fallback_func(*args, **kwargs)
                    
                    # Record fallback success
                    await self._record_resilience_event(
                        event_type="fallback_success",
                        scenario_id=f"{operation_name}_fallback",
                        duration=time.time() - start_time,
                        success=True,
                        details={"original_error": str(e)}
                    )
                    
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {operation_name}: {fallback_error}")
            
            # Record failure
            await self._record_resilience_event(
                event_type="failure",
                scenario_id=f"{operation_name}_failure",
                duration=time.time() - start_time,
                success=False,
                details={"error": str(e), "error_type": type(e).__name__}
            )
            
            raise e
    
    async def _record_resilience_event(
        self,
        event_type: str,
        scenario_id: str,
        duration: float,
        success: bool,
        failure_mode: Optional[FailureMode] = None,
        recovery_strategy: Optional[RecoveryStrategy] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a resilience event for monitoring and analysis."""
        event = ResilienceEvent(
            timestamp=time.time(),
            event_type=event_type,
            failure_mode=failure_mode,
            scenario_id=scenario_id,
            duration=duration,
            recovery_strategy_used=recovery_strategy,
            success=success,
            details=details or {}
        )
        
        self.resilience_events.append(event)
        logger.info(f"Resilience event recorded: {event_type} for {scenario_id}")
    
    def register_health_check(self, component_name: str, health_check_func: Callable) -> None:
        """Register a health check function for a component."""
        self.health_checks[component_name] = health_check_func
        logger.info(f"Registered health check for: {component_name}")
    
    async def run_health_checks(self) -> Dict[str, bool]:
        """Run all registered health checks."""
        health_status = {}
        
        for component_name, health_check in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(health_check):
                    is_healthy = await health_check()
                else:
                    is_healthy = health_check()
                
                health_status[component_name] = bool(is_healthy)
                
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                health_status[component_name] = False
        
        return health_status
    
    def create_disaster_recovery_plan(
        self, plan_name: str, recovery_steps: List[Dict[str, Any]]
    ) -> None:
        """Create a disaster recovery plan."""
        self.disaster_recovery_plans[plan_name] = {
            "steps": recovery_steps,
            "created_at": time.time(),
            "version": "1.0"
        }
        logger.info(f"Created disaster recovery plan: {plan_name}")
    
    async def execute_disaster_recovery(self, plan_name: str) -> bool:
        """Execute a disaster recovery plan."""
        if plan_name not in self.disaster_recovery_plans:
            logger.error(f"Disaster recovery plan not found: {plan_name}")
            return False
        
        plan = self.disaster_recovery_plans[plan_name]
        logger.info(f"Executing disaster recovery plan: {plan_name}")
        
        try:
            for i, step in enumerate(plan["steps"]):
                step_name = step.get("name", f"step_{i+1}")
                logger.info(f"Executing recovery step: {step_name}")
                
                # Simulate step execution
                await asyncio.sleep(step.get("duration", 1.0))
                
                if step.get("can_fail", False) and random.random() < 0.1:
                    raise Exception(f"Recovery step failed: {step_name}")
            
            logger.info(f"Disaster recovery plan completed successfully: {plan_name}")
            return True
            
        except Exception as e:
            logger.error(f"Disaster recovery plan failed: {plan_name}, error: {e}")
            return False
    
    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get comprehensive resilience metrics."""
        if not self.resilience_events:
            return {"status": "no_data"}
        
        events = list(self.resilience_events)
        total_events = len(events)
        
        # Calculate success rate
        successful_events = sum(1 for event in events if event.success)
        success_rate = successful_events / total_events if total_events > 0 else 0
        
        # Calculate MTBF (Mean Time Between Failures)
        failure_events = [event for event in events if event.event_type == "failure"]
        if len(failure_events) > 1:
            failure_times = [event.timestamp for event in failure_events]
            time_between_failures = [
                failure_times[i] - failure_times[i-1] 
                for i in range(1, len(failure_times))
            ]
            mtbf = np.mean(time_between_failures) if time_between_failures else 0
        else:
            mtbf = 0
        
        # Calculate MTTR (Mean Time To Recovery)
        recovery_events = [event for event in events if "recovery" in event.event_type or "fallback" in event.event_type]
        if recovery_events:
            recovery_times = [event.duration for event in recovery_events if event.duration]
            mttr = np.mean(recovery_times) if recovery_times else 0
        else:
            mttr = 0
        
        # Calculate availability (simplified)
        current_time = time.time()
        total_downtime = sum(
            event.duration for event in events 
            if event.event_type == "failure" and event.duration
        )
        
        if events:
            observation_period = current_time - events[0].timestamp
            availability = max(0, 1 - (total_downtime / observation_period)) if observation_period > 0 else 1
        else:
            availability = 1
        
        return {
            "success_rate": success_rate,
            "total_events": total_events,
            "mtbf_seconds": mtbf,
            "mttr_seconds": mttr,
            "availability": availability,
            "recent_failures": len([e for e in events[-10:] if e.event_type == "failure"]),
            "active_circuit_breakers": sum(
                1 for cb in self.circuit_breakers.values() if cb.state == "open"
            )
        }


# Global resilience framework instance
resilience_framework = EnterpriseResilienceFramework()


async def execute_resilient_operation(
    operation_name: str,
    operation_func: Callable,
    *args,
    fallback_func: Optional[Callable] = None,
    **kwargs
) -> Any:
    """Execute an operation with resilience protection."""
    return await resilience_framework.execute_with_resilience(
        operation_name, operation_func, *args, fallback_func=fallback_func, **kwargs
    )


def get_resilience_framework() -> EnterpriseResilienceFramework:
    """Get the global resilience framework instance."""
    return resilience_framework


def configure_resilience_level(level: ResilienceLevel) -> None:
    """Configure the global resilience level."""
    global resilience_framework
    resilience_framework = EnterpriseResilienceFramework(level)
    logger.info(f"Configured resilience level: {level.value}")