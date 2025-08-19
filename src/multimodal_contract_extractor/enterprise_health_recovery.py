"""
Enterprise Health Checks and Recovery System

Comprehensive health monitoring, self-healing capabilities, dependency monitoring,
and chaos engineering tests for the multimodal contract extractor system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union, Awaitable
import threading
from pathlib import Path
import uuid
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

import numpy as np
from pydantic import BaseModel

from .enterprise_error_handling import ComponentType, ErrorSeverity, EnterpriseErrorRecoveryManager
from .enterprise_monitoring import EnterpriseMonitoringSystem
from .enhanced_enterprise_security import EnhancedEnterpriseSecurityManager, SecurityContext

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DependencyType(Enum):
    """Types of system dependencies."""
    
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    NETWORK_SERVICE = "network_service"
    QUEUE_SERVICE = "queue_service"
    CACHE_SERVICE = "cache_service"
    ML_MODEL_SERVICE = "ml_model_service"
    RESEARCH_ALGORITHM = "research_algorithm"


class RecoveryAction(Enum):
    """Types of recovery actions."""
    
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    FAILOVER_TO_BACKUP = "failover_to_backup"
    SCALE_UP_RESOURCES = "scale_up_resources"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    ENABLE_CIRCUIT_BREAKER = "enable_circuit_breaker"
    RESET_CONNECTION_POOL = "reset_connection_pool"
    GARBAGE_COLLECTION = "garbage_collection"
    ALGORITHM_FALLBACK = "algorithm_fallback"
    MANUAL_INTERVENTION = "manual_intervention"


class ChaosExperimentType(Enum):
    """Types of chaos engineering experiments."""
    
    CPU_STRESS = "cpu_stress"
    MEMORY_PRESSURE = "memory_pressure"
    NETWORK_LATENCY = "network_latency"
    SERVICE_FAILURE = "service_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    ALGORITHM_ERROR_INJECTION = "algorithm_error_injection"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATABASE_SLOWDOWN = "database_slowdown"


@dataclass
class HealthCheck:
    """Individual health check definition."""
    
    name: str
    component: ComponentType
    check_function: Callable[[], Awaitable[Dict[str, Any]]]
    interval_seconds: float = 30.0
    timeout_seconds: float = 10.0
    critical: bool = False
    enabled: bool = True
    dependencies: Set[str] = field(default_factory=set)
    recovery_actions: List[RecoveryAction] = field(default_factory=list)


@dataclass
class HealthCheckResult:
    """Result of a health check execution."""
    
    check_name: str
    component: ComponentType
    status: HealthStatus
    timestamp: float = field(default_factory=time.time)
    duration_seconds: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Dependency:
    """System dependency definition."""
    
    name: str
    type: DependencyType
    endpoint: Optional[str] = None
    timeout_seconds: float = 5.0
    critical: bool = True
    health_check_url: Optional[str] = None
    expected_response: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryPlan:
    """Recovery plan for unhealthy components."""
    
    component: ComponentType
    actions: List[RecoveryAction]
    estimated_recovery_time: float = 60.0
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    rollback_plan: Optional[List[RecoveryAction]] = None


@dataclass
class ChaosExperiment:
    """Chaos engineering experiment definition."""
    
    name: str
    type: ChaosExperimentType
    target_components: List[ComponentType]
    duration_seconds: float = 300.0  # 5 minutes
    intensity: float = 0.5  # 0.0 to 1.0
    safety_checks: List[str] = field(default_factory=list)
    recovery_validation: bool = True


class AlgorithmHealthMonitor:
    """Specialized health monitor for research algorithms."""
    
    def __init__(self):
        self.algorithm_baselines: Dict[str, Dict[str, float]] = {}
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.anomaly_thresholds: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()
        
        # Default anomaly detection thresholds
        self.default_thresholds = {
            'accuracy_degradation': 0.05,  # 5% degradation
            'latency_increase': 2.0,  # 2x latency increase
            'memory_increase': 1.5,  # 1.5x memory increase
            'error_rate_increase': 0.1  # 10% error rate increase
        }
    
    def set_algorithm_baseline(self, algorithm_name: str, baseline_metrics: Dict[str, float]):
        """Set baseline performance metrics for an algorithm."""
        with self._lock:
            self.algorithm_baselines[algorithm_name] = baseline_metrics
            logger.info(f"Set baseline metrics for {algorithm_name}: {baseline_metrics}")
    
    async def check_algorithm_health(self, algorithm_name: str) -> HealthCheckResult:
        """Check health of a specific research algorithm."""
        start_time = time.time()
        
        try:
            # Get recent performance data
            with self._lock:
                history = self.performance_history.get(algorithm_name, [])
            
            if not history:
                return HealthCheckResult(
                    check_name=f"algorithm_{algorithm_name}",
                    component=ComponentType.QUANTUM_PROCESSOR,  # Default
                    status=HealthStatus.UNKNOWN,
                    details={"reason": "no_performance_data"}
                )
            
            # Analyze recent performance (last 10 executions)
            recent_data = history[-10:]
            baseline = self.algorithm_baselines.get(algorithm_name, {})
            
            # Calculate current metrics
            current_metrics = self._calculate_current_metrics(recent_data)
            
            # Detect anomalies
            anomalies = self._detect_algorithm_anomalies(algorithm_name, current_metrics, baseline)
            
            # Determine health status
            status = self._determine_algorithm_health_status(anomalies)
            
            return HealthCheckResult(
                check_name=f"algorithm_{algorithm_name}",
                component=ComponentType.QUANTUM_PROCESSOR,
                status=status,
                duration_seconds=time.time() - start_time,
                details={
                    "anomalies": anomalies,
                    "current_metrics": current_metrics,
                    "baseline_metrics": baseline,
                    "data_points": len(recent_data)
                },
                metrics=current_metrics
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name=f"algorithm_{algorithm_name}",
                component=ComponentType.QUANTUM_PROCESSOR,
                status=HealthStatus.CRITICAL,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                details={"error": str(e)}
            )
    
    def _calculate_current_metrics(self, recent_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate current performance metrics from recent data."""
        if not recent_data:
            return {}
        
        metrics = {}
        
        # Calculate averages for key metrics
        for metric_name in ['accuracy', 'latency', 'memory_usage', 'error_rate']:
            values = [data.get(metric_name, 0) for data in recent_data if metric_name in data]
            if values:
                metrics[metric_name] = statistics.mean(values)
                metrics[f"{metric_name}_std"] = statistics.stdev(values) if len(values) > 1 else 0
        
        return metrics
    
    def _detect_algorithm_anomalies(
        self, 
        algorithm_name: str, 
        current_metrics: Dict[str, float], 
        baseline: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in algorithm performance."""
        anomalies = []
        thresholds = self.anomaly_thresholds.get(algorithm_name, self.default_thresholds)
        
        # Check accuracy degradation
        if 'accuracy' in current_metrics and 'accuracy' in baseline:
            degradation = baseline['accuracy'] - current_metrics['accuracy']
            if degradation > thresholds.get('accuracy_degradation', 0.05):
                anomalies.append({
                    'type': 'accuracy_degradation',
                    'severity': 'high' if degradation > 0.1 else 'medium',
                    'current': current_metrics['accuracy'],
                    'baseline': baseline['accuracy'],
                    'degradation': degradation
                })
        
        # Check latency increase
        if 'latency' in current_metrics and 'latency' in baseline:
            increase_ratio = current_metrics['latency'] / baseline['latency'] if baseline['latency'] > 0 else 1
            if increase_ratio > thresholds.get('latency_increase', 2.0):
                anomalies.append({
                    'type': 'latency_increase',
                    'severity': 'high' if increase_ratio > 3.0 else 'medium',
                    'current': current_metrics['latency'],
                    'baseline': baseline['latency'],
                    'increase_ratio': increase_ratio
                })
        
        # Check memory usage increase
        if 'memory_usage' in current_metrics and 'memory_usage' in baseline:
            increase_ratio = current_metrics['memory_usage'] / baseline['memory_usage'] if baseline['memory_usage'] > 0 else 1
            if increase_ratio > thresholds.get('memory_increase', 1.5):
                anomalies.append({
                    'type': 'memory_increase',
                    'severity': 'high' if increase_ratio > 2.0 else 'medium',
                    'current': current_metrics['memory_usage'],
                    'baseline': baseline['memory_usage'],
                    'increase_ratio': increase_ratio
                })
        
        # Check error rate increase
        if 'error_rate' in current_metrics and 'error_rate' in baseline:
            increase = current_metrics['error_rate'] - baseline['error_rate']
            if increase > thresholds.get('error_rate_increase', 0.1):
                anomalies.append({
                    'type': 'error_rate_increase',
                    'severity': 'critical' if increase > 0.2 else 'high',
                    'current': current_metrics['error_rate'],
                    'baseline': baseline['error_rate'],
                    'increase': increase
                })
        
        return anomalies
    
    def _determine_algorithm_health_status(self, anomalies: List[Dict[str, Any]]) -> HealthStatus:
        """Determine overall health status based on anomalies."""
        if not anomalies:
            return HealthStatus.HEALTHY
        
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'medium')
            severity_counts[severity] += 1
        
        if severity_counts['critical'] > 0:
            return HealthStatus.CRITICAL
        elif severity_counts['high'] > 2:
            return HealthStatus.CRITICAL
        elif severity_counts['high'] > 0:
            return HealthStatus.UNHEALTHY
        elif severity_counts['medium'] > 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.DEGRADED
    
    def record_algorithm_execution(self, algorithm_name: str, execution_data: Dict[str, Any]):
        """Record algorithm execution data for health monitoring."""
        with self._lock:
            if algorithm_name not in self.performance_history:
                self.performance_history[algorithm_name] = []
            
            execution_data['timestamp'] = time.time()
            self.performance_history[algorithm_name].append(execution_data)
            
            # Keep only recent history (last 1000 executions)
            if len(self.performance_history[algorithm_name]) > 1000:
                self.performance_history[algorithm_name] = self.performance_history[algorithm_name][-1000:]


class DependencyHealthMonitor:
    """Monitor health of system dependencies."""
    
    def __init__(self):
        self.dependencies: Dict[str, Dependency] = {}
        self.dependency_status: Dict[str, HealthCheckResult] = {}
        self._lock = threading.Lock()
    
    def register_dependency(self, dependency: Dependency):
        """Register a system dependency for monitoring."""
        with self._lock:
            self.dependencies[dependency.name] = dependency
        logger.info(f"Registered dependency: {dependency.name} ({dependency.type.value})")
    
    async def check_dependency_health(self, dependency_name: str) -> HealthCheckResult:
        """Check health of a specific dependency."""
        with self._lock:
            dependency = self.dependencies.get(dependency_name)
        
        if not dependency:
            return HealthCheckResult(
                check_name=f"dependency_{dependency_name}",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=HealthStatus.UNKNOWN,
                error_message=f"Dependency {dependency_name} not found"
            )
        
        start_time = time.time()
        
        try:
            # Perform dependency-specific health check
            if dependency.type == DependencyType.DATABASE:
                result = await self._check_database_health(dependency)
            elif dependency.type == DependencyType.EXTERNAL_API:
                result = await self._check_api_health(dependency)
            elif dependency.type == DependencyType.FILE_SYSTEM:
                result = await self._check_filesystem_health(dependency)
            elif dependency.type == DependencyType.NETWORK_SERVICE:
                result = await self._check_network_service_health(dependency)
            elif dependency.type == DependencyType.CACHE_SERVICE:
                result = await self._check_cache_health(dependency)
            elif dependency.type == DependencyType.ML_MODEL_SERVICE:
                result = await self._check_ml_service_health(dependency)
            else:
                result = await self._check_generic_dependency(dependency)
            
            result.duration_seconds = time.time() - start_time
            
            # Store result
            with self._lock:
                self.dependency_status[dependency_name] = result
            
            return result
            
        except Exception as e:
            return HealthCheckResult(
                check_name=f"dependency_{dependency_name}",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=HealthStatus.CRITICAL,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                details={"error": str(e), "dependency_type": dependency.type.value}
            )
    
    async def _check_database_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check database dependency health."""
        # Simulate database health check
        await asyncio.sleep(0.1)  # Simulate network latency
        
        # Mock database metrics
        connection_count = random.randint(10, 100)
        query_time = random.uniform(0.001, 0.1)
        
        status = HealthStatus.HEALTHY
        if connection_count > 80:
            status = HealthStatus.DEGRADED
        if query_time > 0.05:
            status = HealthStatus.DEGRADED
        if connection_count > 95 or query_time > 0.1:
            status = HealthStatus.UNHEALTHY
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.DATABASE_LAYER,
            status=status,
            details={
                "connection_count": connection_count,
                "avg_query_time": query_time,
                "database_type": "postgresql"
            },
            metrics={
                "connection_count": connection_count,
                "query_time_ms": query_time * 1000
            }
        )
    
    async def _check_api_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check external API dependency health."""
        await asyncio.sleep(0.05)  # Simulate API call
        
        # Mock API metrics
        response_time = random.uniform(0.1, 2.0)
        success_rate = random.uniform(0.9, 1.0)
        
        status = HealthStatus.HEALTHY
        if response_time > 1.0 or success_rate < 0.98:
            status = HealthStatus.DEGRADED
        if response_time > 2.0 or success_rate < 0.95:
            status = HealthStatus.UNHEALTHY
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.API_GATEWAY,
            status=status,
            details={
                "response_time_seconds": response_time,
                "success_rate": success_rate,
                "endpoint": dependency.endpoint
            },
            metrics={
                "response_time_ms": response_time * 1000,
                "success_rate_percent": success_rate * 100
            }
        )
    
    async def _check_filesystem_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check file system dependency health."""
        try:
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check if path is writable
            test_file = Path("/tmp/health_check_test")
            test_file.write_text("test")
            test_file.unlink()
            
            status = HealthStatus.HEALTHY
            if usage_percent > 80:
                status = HealthStatus.DEGRADED
            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
            
            return HealthCheckResult(
                check_name=f"dependency_{dependency.name}",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=status,
                details={
                    "disk_usage_percent": usage_percent,
                    "total_gb": disk_usage.total / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                    "writable": True
                },
                metrics={
                    "disk_usage_percent": usage_percent,
                    "free_space_gb": disk_usage.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name=f"dependency_{dependency.name}",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=HealthStatus.CRITICAL,
                error_message=str(e)
            )
    
    async def _check_network_service_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check network service dependency health."""
        await asyncio.sleep(0.02)  # Simulate network check
        
        # Mock network metrics
        latency = random.uniform(1, 50)  # ms
        packet_loss = random.uniform(0, 0.05)  # 0-5%
        
        status = HealthStatus.HEALTHY
        if latency > 20 or packet_loss > 0.01:
            status = HealthStatus.DEGRADED
        if latency > 50 or packet_loss > 0.05:
            status = HealthStatus.UNHEALTHY
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.DOCUMENT_PROCESSOR,
            status=status,
            details={
                "latency_ms": latency,
                "packet_loss_percent": packet_loss * 100,
                "endpoint": dependency.endpoint
            },
            metrics={
                "latency_ms": latency,
                "packet_loss_percent": packet_loss * 100
            }
        )
    
    async def _check_cache_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check cache service dependency health."""
        await asyncio.sleep(0.01)
        
        # Mock cache metrics
        hit_rate = random.uniform(0.7, 0.98)
        memory_usage = random.uniform(0.3, 0.9)
        
        status = HealthStatus.HEALTHY
        if hit_rate < 0.8 or memory_usage > 0.8:
            status = HealthStatus.DEGRADED
        if hit_rate < 0.7 or memory_usage > 0.9:
            status = HealthStatus.UNHEALTHY
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.DOCUMENT_PROCESSOR,
            status=status,
            details={
                "hit_rate": hit_rate,
                "memory_usage_percent": memory_usage * 100,
                "cache_type": "redis"
            },
            metrics={
                "hit_rate_percent": hit_rate * 100,
                "memory_usage_percent": memory_usage * 100
            }
        )
    
    async def _check_ml_service_health(self, dependency: Dependency) -> HealthCheckResult:
        """Check ML model service dependency health."""
        await asyncio.sleep(0.1)
        
        # Mock ML service metrics
        model_accuracy = random.uniform(0.85, 0.98)
        inference_time = random.uniform(0.05, 0.5)
        queue_length = random.randint(0, 50)
        
        status = HealthStatus.HEALTHY
        if model_accuracy < 0.9 or inference_time > 0.3 or queue_length > 30:
            status = HealthStatus.DEGRADED
        if model_accuracy < 0.85 or inference_time > 0.5 or queue_length > 50:
            status = HealthStatus.UNHEALTHY
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.QUANTUM_PROCESSOR,
            status=status,
            details={
                "model_accuracy": model_accuracy,
                "inference_time_seconds": inference_time,
                "queue_length": queue_length
            },
            metrics={
                "accuracy_percent": model_accuracy * 100,
                "inference_time_ms": inference_time * 1000,
                "queue_length": queue_length
            }
        )
    
    async def _check_generic_dependency(self, dependency: Dependency) -> HealthCheckResult:
        """Generic dependency health check."""
        await asyncio.sleep(0.05)
        
        return HealthCheckResult(
            check_name=f"dependency_{dependency.name}",
            component=ComponentType.DOCUMENT_PROCESSOR,
            status=HealthStatus.HEALTHY,
            details={
                "type": dependency.type.value,
                "check_type": "generic"
            }
        )
    
    def get_dependency_status(self) -> Dict[str, HealthCheckResult]:
        """Get current status of all dependencies."""
        with self._lock:
            return self.dependency_status.copy()


class SelfHealingManager:
    """Self-healing system that automatically recovers from failures."""
    
    def __init__(self):
        self.recovery_plans: Dict[ComponentType, RecoveryPlan] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.auto_recovery_enabled = True
        self._lock = threading.Lock()
        
        # Initialize default recovery plans
        self._initialize_recovery_plans()
    
    def _initialize_recovery_plans(self):
        """Initialize default recovery plans for components."""
        self.recovery_plans = {
            ComponentType.QUANTUM_PROCESSOR: RecoveryPlan(
                component=ComponentType.QUANTUM_PROCESSOR,
                actions=[
                    RecoveryAction.ALGORITHM_FALLBACK,
                    RecoveryAction.CLEAR_CACHE,
                    RecoveryAction.RESTART_SERVICE
                ],
                estimated_recovery_time=30.0,
                success_criteria={"accuracy": ">0.7", "latency": "<2.0"}
            ),
            ComponentType.NEUROMORPHIC_ENGINE: RecoveryPlan(
                component=ComponentType.NEUROMORPHIC_ENGINE,
                actions=[
                    RecoveryAction.GARBAGE_COLLECTION,
                    RecoveryAction.ALGORITHM_FALLBACK,
                    RecoveryAction.RESTART_SERVICE
                ],
                estimated_recovery_time=45.0,
                success_criteria={"memory_usage": "<80%", "error_rate": "<0.05"}
            ),
            ComponentType.DATABASE_LAYER: RecoveryPlan(
                component=ComponentType.DATABASE_LAYER,
                actions=[
                    RecoveryAction.RESET_CONNECTION_POOL,
                    RecoveryAction.FAILOVER_TO_BACKUP,
                    RecoveryAction.RESTART_SERVICE
                ],
                estimated_recovery_time=60.0,
                success_criteria={"connection_count": "<80", "query_time": "<0.1"}
            ),
            ComponentType.FEDERATED_LEARNER: RecoveryPlan(
                component=ComponentType.FEDERATED_LEARNER,
                actions=[
                    RecoveryAction.ENABLE_CIRCUIT_BREAKER,
                    RecoveryAction.ALGORITHM_FALLBACK,
                    RecoveryAction.RESTART_SERVICE
                ],
                estimated_recovery_time=120.0,
                success_criteria={"participant_count": ">3", "aggregation_success": ">0.9"}
            )
        }
    
    async def execute_recovery(self, component: ComponentType, health_result: HealthCheckResult) -> Dict[str, Any]:
        """Execute recovery plan for an unhealthy component."""
        if not self.auto_recovery_enabled:
            logger.info("Auto-recovery is disabled, skipping recovery")
            return {"status": "skipped", "reason": "auto_recovery_disabled"}
        
        recovery_plan = self.recovery_plans.get(component)
        if not recovery_plan:
            logger.warning(f"No recovery plan found for component {component.value}")
            return {"status": "failed", "reason": "no_recovery_plan"}
        
        recovery_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting recovery for {component.value} (ID: {recovery_id})")
        
        recovery_record = {
            "recovery_id": recovery_id,
            "component": component.value,
            "start_time": start_time,
            "trigger_health_check": {
                "status": health_result.status.value,
                "details": health_result.details,
                "metrics": health_result.metrics
            },
            "plan": recovery_plan,
            "actions_executed": [],
            "success": False,
            "duration": 0.0
        }
        
        try:
            # Execute recovery actions sequentially
            for action in recovery_plan.actions:
                action_start = time.time()
                action_result = await self._execute_recovery_action(action, component)
                action_duration = time.time() - action_start
                
                action_record = {
                    "action": action.value,
                    "result": action_result,
                    "duration": action_duration,
                    "timestamp": action_start
                }
                
                recovery_record["actions_executed"].append(action_record)
                
                if not action_result.get("success", False):
                    logger.warning(f"Recovery action {action.value} failed: {action_result}")
                    # Continue with next action rather than failing completely
                
                # Wait between actions
                await asyncio.sleep(2)
            
            # Validate recovery success
            await asyncio.sleep(5)  # Wait for services to stabilize
            validation_result = await self._validate_recovery(component, recovery_plan.success_criteria)
            
            recovery_record["success"] = validation_result["success"]
            recovery_record["validation"] = validation_result
            recovery_record["duration"] = time.time() - start_time
            
            with self._lock:
                self.recovery_history.append(recovery_record)
            
            if validation_result["success"]:
                logger.info(f"Recovery successful for {component.value} (ID: {recovery_id})")
            else:
                logger.error(f"Recovery failed for {component.value} (ID: {recovery_id})")
            
            return {
                "status": "completed",
                "success": validation_result["success"],
                "recovery_id": recovery_id,
                "duration": recovery_record["duration"],
                "actions_executed": len(recovery_record["actions_executed"]),
                "validation": validation_result
            }
            
        except Exception as e:
            recovery_record["error"] = str(e)
            recovery_record["duration"] = time.time() - start_time
            
            with self._lock:
                self.recovery_history.append(recovery_record)
            
            logger.error(f"Recovery failed for {component.value} (ID: {recovery_id}): {e}")
            return {
                "status": "failed",
                "error": str(e),
                "recovery_id": recovery_id,
                "duration": recovery_record["duration"]
            }
    
    async def _execute_recovery_action(self, action: RecoveryAction, component: ComponentType) -> Dict[str, Any]:
        """Execute a specific recovery action."""
        try:
            if action == RecoveryAction.RESTART_SERVICE:
                return await self._restart_service(component)
            elif action == RecoveryAction.CLEAR_CACHE:
                return await self._clear_cache(component)
            elif action == RecoveryAction.FAILOVER_TO_BACKUP:
                return await self._failover_to_backup(component)
            elif action == RecoveryAction.SCALE_UP_RESOURCES:
                return await self._scale_up_resources(component)
            elif action == RecoveryAction.ENABLE_CIRCUIT_BREAKER:
                return await self._enable_circuit_breaker(component)
            elif action == RecoveryAction.RESET_CONNECTION_POOL:
                return await self._reset_connection_pool(component)
            elif action == RecoveryAction.GARBAGE_COLLECTION:
                return await self._garbage_collection(component)
            elif action == RecoveryAction.ALGORITHM_FALLBACK:
                return await self._algorithm_fallback(component)
            else:
                return {"success": False, "error": f"Unknown action: {action.value}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restart_service(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate service restart."""
        logger.info(f"Restarting service for {component.value}")
        await asyncio.sleep(2)  # Simulate restart time
        return {"success": True, "message": f"Service {component.value} restarted"}
    
    async def _clear_cache(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate cache clearing."""
        logger.info(f"Clearing cache for {component.value}")
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Cache cleared for {component.value}"}
    
    async def _failover_to_backup(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate failover to backup service."""
        logger.info(f"Failing over to backup for {component.value}")
        await asyncio.sleep(1)
        return {"success": True, "message": f"Failed over to backup for {component.value}"}
    
    async def _scale_up_resources(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate resource scaling."""
        logger.info(f"Scaling up resources for {component.value}")
        await asyncio.sleep(3)
        return {"success": True, "message": f"Resources scaled up for {component.value}"}
    
    async def _enable_circuit_breaker(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate circuit breaker activation."""
        logger.info(f"Enabling circuit breaker for {component.value}")
        await asyncio.sleep(0.1)
        return {"success": True, "message": f"Circuit breaker enabled for {component.value}"}
    
    async def _reset_connection_pool(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate connection pool reset."""
        logger.info(f"Resetting connection pool for {component.value}")
        await asyncio.sleep(1)
        return {"success": True, "message": f"Connection pool reset for {component.value}"}
    
    async def _garbage_collection(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate garbage collection."""
        logger.info(f"Running garbage collection for {component.value}")
        import gc
        gc.collect()
        return {"success": True, "message": f"Garbage collection completed for {component.value}"}
    
    async def _algorithm_fallback(self, component: ComponentType) -> Dict[str, Any]:
        """Simulate algorithm fallback."""
        logger.info(f"Switching to fallback algorithm for {component.value}")
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Fallback algorithm activated for {component.value}"}
    
    async def _validate_recovery(self, component: ComponentType, success_criteria: Dict[str, str]) -> Dict[str, Any]:
        """Validate that recovery was successful."""
        # Simulate validation check
        await asyncio.sleep(1)
        
        # Mock validation - in real implementation, this would check actual metrics
        validation_results = {}
        overall_success = True
        
        for criterion, expected in success_criteria.items():
            # Simple mock validation
            if ">" in expected:
                threshold = float(expected.replace(">", ""))
                current_value = threshold + random.uniform(0.1, 0.3)  # Mock value above threshold
                success = current_value > threshold
            elif "<" in expected:
                threshold = float(expected.replace("<", "").replace("%", ""))
                current_value = threshold - random.uniform(0.1, 0.3)  # Mock value below threshold
                success = current_value < threshold
            else:
                success = True  # Default success for other criteria
                current_value = 1.0
            
            validation_results[criterion] = {
                "expected": expected,
                "current": current_value,
                "success": success
            }
            
            if not success:
                overall_success = False
        
        return {
            "success": overall_success,
            "criteria_results": validation_results,
            "component": component.value
        }
    
    def get_recovery_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent recovery history."""
        with self._lock:
            return self.recovery_history[-limit:]
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        with self._lock:
            total_recoveries = len(self.recovery_history)
            successful_recoveries = sum(1 for r in self.recovery_history if r.get("success", False))
            
            if total_recoveries == 0:
                return {
                    "total_recoveries": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0
                }
            
            success_rate = successful_recoveries / total_recoveries
            avg_duration = statistics.mean([r.get("duration", 0) for r in self.recovery_history])
            
            # Component breakdown
            component_stats = {}
            for record in self.recovery_history:
                component = record.get("component", "unknown")
                if component not in component_stats:
                    component_stats[component] = {"total": 0, "successful": 0}
                component_stats[component]["total"] += 1
                if record.get("success", False):
                    component_stats[component]["successful"] += 1
            
            return {
                "total_recoveries": total_recoveries,
                "successful_recoveries": successful_recoveries,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_duration,
                "component_breakdown": component_stats
            }


class ChaosEngineeringManager:
    """Chaos engineering system to test system resilience."""
    
    def __init__(self):
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.experiment_history: List[Dict[str, Any]] = []
        self.safety_enabled = True
        self._lock = threading.Lock()
    
    async def run_chaos_experiment(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Run a chaos engineering experiment."""
        if not self.safety_enabled:
            return {"status": "aborted", "reason": "safety_disabled"}
        
        experiment_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting chaos experiment: {experiment.name} (ID: {experiment_id})")
        
        # Safety checks before starting
        safety_check_result = await self._perform_safety_checks(experiment)
        if not safety_check_result["safe"]:
            return {
                "status": "aborted",
                "reason": "safety_check_failed",
                "safety_results": safety_check_result
            }
        
        experiment_record = {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "type": experiment.type.value,
            "target_components": [c.value for c in experiment.target_components],
            "start_time": start_time,
            "duration_seconds": experiment.duration_seconds,
            "intensity": experiment.intensity,
            "phases": [],
            "success": False,
            "recovery_validated": False
        }
        
        with self._lock:
            self.active_experiments[experiment_id] = experiment
        
        try:
            # Phase 1: Baseline measurement
            baseline_metrics = await self._measure_baseline_metrics(experiment.target_components)
            experiment_record["phases"].append({
                "phase": "baseline",
                "timestamp": time.time(),
                "metrics": baseline_metrics
            })
            
            # Phase 2: Inject chaos
            chaos_result = await self._inject_chaos(experiment)
            experiment_record["phases"].append({
                "phase": "chaos_injection",
                "timestamp": time.time(),
                "result": chaos_result
            })
            
            # Phase 3: Monitor during chaos
            monitoring_task = asyncio.create_task(
                self._monitor_during_chaos(experiment, experiment.duration_seconds)
            )
            
            await asyncio.sleep(experiment.duration_seconds)
            
            # Phase 4: Stop chaos injection
            stop_result = await self._stop_chaos_injection(experiment)
            experiment_record["phases"].append({
                "phase": "chaos_stop",
                "timestamp": time.time(),
                "result": stop_result
            })
            
            # Wait for monitoring to complete
            monitoring_results = await monitoring_task
            experiment_record["monitoring_results"] = monitoring_results
            
            # Phase 5: Recovery validation
            if experiment.recovery_validation:
                recovery_metrics = await self._validate_recovery_after_chaos(experiment.target_components)
                experiment_record["phases"].append({
                    "phase": "recovery_validation",
                    "timestamp": time.time(),
                    "metrics": recovery_metrics
                })
                
                # Compare with baseline
                recovery_success = self._compare_recovery_to_baseline(baseline_metrics, recovery_metrics)
                experiment_record["recovery_validated"] = recovery_success
            
            experiment_record["success"] = True
            experiment_record["end_time"] = time.time()
            experiment_record["total_duration"] = experiment_record["end_time"] - start_time
            
            logger.info(f"Chaos experiment completed: {experiment.name} (ID: {experiment_id})")
            
            return {
                "status": "completed",
                "experiment_id": experiment_id,
                "success": True,
                "recovery_validated": experiment_record["recovery_validated"],
                "duration": experiment_record["total_duration"],
                "phases_completed": len(experiment_record["phases"])
            }
            
        except Exception as e:
            experiment_record["error"] = str(e)
            experiment_record["end_time"] = time.time()
            logger.error(f"Chaos experiment failed: {experiment.name} (ID: {experiment_id}): {e}")
            
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "error": str(e),
                "duration": experiment_record.get("end_time", time.time()) - start_time
            }
            
        finally:
            with self._lock:
                self.active_experiments.pop(experiment_id, None)
                self.experiment_history.append(experiment_record)
    
    async def _perform_safety_checks(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Perform safety checks before running chaos experiment."""
        checks = {
            "system_load_acceptable": True,  # Mock check
            "no_critical_operations": True,  # Mock check
            "backup_systems_available": True,  # Mock check
            "monitoring_active": True  # Mock check
        }
        
        # Simulate safety check
        await asyncio.sleep(0.1)
        
        overall_safe = all(checks.values())
        
        return {
            "safe": overall_safe,
            "checks": checks,
            "timestamp": time.time()
        }
    
    async def _measure_baseline_metrics(self, target_components: List[ComponentType]) -> Dict[str, Any]:
        """Measure baseline metrics before chaos injection."""
        await asyncio.sleep(0.5)  # Simulate measurement time
        
        metrics = {}
        for component in target_components:
            metrics[component.value] = {
                "response_time": random.uniform(0.1, 0.5),
                "error_rate": random.uniform(0.0, 0.01),
                "throughput": random.uniform(100, 1000),
                "cpu_usage": random.uniform(20, 60),
                "memory_usage": random.uniform(30, 70)
            }
        
        return metrics
    
    async def _inject_chaos(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject chaos based on experiment type."""
        logger.info(f"Injecting chaos: {experiment.type.value} with intensity {experiment.intensity}")
        
        if experiment.type == ChaosExperimentType.CPU_STRESS:
            return await self._inject_cpu_stress(experiment.intensity)
        elif experiment.type == ChaosExperimentType.MEMORY_PRESSURE:
            return await self._inject_memory_pressure(experiment.intensity)
        elif experiment.type == ChaosExperimentType.NETWORK_LATENCY:
            return await self._inject_network_latency(experiment.intensity)
        elif experiment.type == ChaosExperimentType.SERVICE_FAILURE:
            return await self._inject_service_failure(experiment)
        elif experiment.type == ChaosExperimentType.ALGORITHM_ERROR_INJECTION:
            return await self._inject_algorithm_errors(experiment)
        else:
            return {"success": True, "message": f"Chaos type {experiment.type.value} simulated"}
    
    async def _inject_cpu_stress(self, intensity: float) -> Dict[str, Any]:
        """Simulate CPU stress injection."""
        await asyncio.sleep(0.1)
        return {"success": True, "message": f"CPU stress injected at {intensity*100}%"}
    
    async def _inject_memory_pressure(self, intensity: float) -> Dict[str, Any]:
        """Simulate memory pressure injection."""
        await asyncio.sleep(0.1)
        return {"success": True, "message": f"Memory pressure injected at {intensity*100}%"}
    
    async def _inject_network_latency(self, intensity: float) -> Dict[str, Any]:
        """Simulate network latency injection."""
        await asyncio.sleep(0.1)
        latency_ms = intensity * 1000  # Scale to milliseconds
        return {"success": True, "message": f"Network latency injected: {latency_ms}ms"}
    
    async def _inject_service_failure(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Simulate service failure injection."""
        await asyncio.sleep(0.1)
        failed_components = random.sample(experiment.target_components, max(1, len(experiment.target_components) // 2))
        return {"success": True, "failed_components": [c.value for c in failed_components]}
    
    async def _inject_algorithm_errors(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Simulate algorithm error injection."""
        await asyncio.sleep(0.1)
        error_rate = experiment.intensity * 0.5  # Up to 50% error rate
        return {"success": True, "message": f"Algorithm errors injected at {error_rate*100}% rate"}
    
    async def _monitor_during_chaos(self, experiment: ChaosExperiment, duration: float) -> Dict[str, Any]:
        """Monitor system during chaos injection."""
        monitoring_results = {
            "start_time": time.time(),
            "duration": duration,
            "samples": []
        }
        
        sample_interval = min(duration / 10, 30)  # Sample every 30s or duration/10
        samples_count = int(duration / sample_interval)
        
        for i in range(samples_count):
            await asyncio.sleep(sample_interval)
            
            sample = {
                "timestamp": time.time(),
                "component_metrics": {}
            }
            
            for component in experiment.target_components:
                # Simulate degraded metrics during chaos
                sample["component_metrics"][component.value] = {
                    "response_time": random.uniform(0.5, 2.0),  # Higher response time
                    "error_rate": random.uniform(0.01, 0.1),  # Higher error rate
                    "throughput": random.uniform(50, 500),  # Lower throughput
                    "cpu_usage": random.uniform(60, 90),  # Higher CPU
                    "memory_usage": random.uniform(70, 95)  # Higher memory
                }
            
            monitoring_results["samples"].append(sample)
        
        return monitoring_results
    
    async def _stop_chaos_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Stop chaos injection."""
        logger.info(f"Stopping chaos injection: {experiment.type.value}")
        await asyncio.sleep(0.1)
        return {"success": True, "message": f"Chaos injection stopped: {experiment.type.value}"}
    
    async def _validate_recovery_after_chaos(self, target_components: List[ComponentType]) -> Dict[str, Any]:
        """Validate system recovery after chaos experiment."""
        # Wait for system to stabilize
        await asyncio.sleep(10)
        
        recovery_metrics = {}
        for component in target_components:
            # Simulate recovery metrics (should be close to baseline)
            recovery_metrics[component.value] = {
                "response_time": random.uniform(0.1, 0.6),
                "error_rate": random.uniform(0.0, 0.02),
                "throughput": random.uniform(90, 1000),
                "cpu_usage": random.uniform(25, 65),
                "memory_usage": random.uniform(35, 75)
            }
        
        return recovery_metrics
    
    def _compare_recovery_to_baseline(self, baseline: Dict[str, Any], recovery: Dict[str, Any]) -> bool:
        """Compare recovery metrics to baseline to validate recovery."""
        tolerance = 0.2  # 20% tolerance
        
        for component in baseline:
            if component not in recovery:
                continue
            
            baseline_metrics = baseline[component]
            recovery_metrics = recovery[component]
            
            for metric_name in baseline_metrics:
                if metric_name not in recovery_metrics:
                    continue
                
                baseline_value = baseline_metrics[metric_name]
                recovery_value = recovery_metrics[metric_name]
                
                # For error rate, recovery should be close to or better than baseline
                if metric_name == "error_rate":
                    if recovery_value > baseline_value * (1 + tolerance):
                        return False
                # For response_time, recovery should be close to baseline
                elif metric_name == "response_time":
                    if abs(recovery_value - baseline_value) / baseline_value > tolerance:
                        return False
                # For throughput, recovery should be close to or better than baseline
                elif metric_name == "throughput":
                    if recovery_value < baseline_value * (1 - tolerance):
                        return False
        
        return True
    
    def get_experiment_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent experiment history."""
        with self._lock:
            return self.experiment_history[-limit:]
    
    def get_active_experiments(self) -> Dict[str, ChaosExperiment]:
        """Get currently active experiments."""
        with self._lock:
            return self.active_experiments.copy()


class EnterpriseHealthRecoverySystem:
    """Comprehensive enterprise health monitoring and recovery system."""
    
    def __init__(self):
        self.algorithm_monitor = AlgorithmHealthMonitor()
        self.dependency_monitor = DependencyHealthMonitor()
        self.self_healing = SelfHealingManager()
        self.chaos_engineering = ChaosEngineeringManager()
        
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_check_results: Dict[str, HealthCheckResult] = {}
        self.monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Initialize default health checks
        self._initialize_default_health_checks()
    
    def _initialize_default_health_checks(self):
        """Initialize default health checks for all components."""
        # System health checks
        self.register_health_check(HealthCheck(
            name="system_resources",
            component=ComponentType.DOCUMENT_PROCESSOR,
            check_function=self._check_system_resources,
            interval_seconds=30.0,
            critical=True
        ))
        
        # Algorithm health checks
        self.register_health_check(HealthCheck(
            name="quantum_processor",
            component=ComponentType.QUANTUM_PROCESSOR,
            check_function=lambda: self.algorithm_monitor.check_algorithm_health("quantum_processor"),
            interval_seconds=60.0,
            critical=False,
            recovery_actions=[RecoveryAction.ALGORITHM_FALLBACK, RecoveryAction.CLEAR_CACHE]
        ))
        
        self.register_health_check(HealthCheck(
            name="neuromorphic_engine",
            component=ComponentType.NEUROMORPHIC_ENGINE,
            check_function=lambda: self.algorithm_monitor.check_algorithm_health("neuromorphic_engine"),
            interval_seconds=60.0,
            critical=False,
            recovery_actions=[RecoveryAction.GARBAGE_COLLECTION, RecoveryAction.ALGORITHM_FALLBACK]
        ))
        
        # Register default dependencies
        self._register_default_dependencies()
    
    def _register_default_dependencies(self):
        """Register default system dependencies."""
        dependencies = [
            Dependency("postgresql_db", DependencyType.DATABASE, "postgresql://localhost:5432", critical=True),
            Dependency("redis_cache", DependencyType.CACHE_SERVICE, "redis://localhost:6379", critical=False),
            Dependency("file_system", DependencyType.FILE_SYSTEM, critical=True),
            Dependency("external_ml_api", DependencyType.ML_MODEL_SERVICE, "https://api.example.com/ml", critical=False)
        ]
        
        for dep in dependencies:
            self.dependency_monitor.register_dependency(dep)
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check."""
        with self._lock:
            self.health_checks[health_check.name] = health_check
        logger.info(f"Registered health check: {health_check.name} for {health_check.component.value}")
    
    async def start_monitoring(self):
        """Start the health monitoring system."""
        if self.monitoring_active:
            logger.warning("Health monitoring is already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting enterprise health monitoring system")
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the health monitoring system."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        logger.info("Stopping enterprise health monitoring system")
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Main health monitoring loop."""
        next_check_times = {}
        
        # Initialize next check times
        for check_name, health_check in self.health_checks.items():
            next_check_times[check_name] = time.time()
        
        while self.monitoring_active:
            try:
                current_time = time.time()
                
                # Check which health checks are due
                checks_to_run = []
                for check_name, health_check in self.health_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    if current_time >= next_check_times.get(check_name, 0):
                        checks_to_run.append((check_name, health_check))
                        next_check_times[check_name] = current_time + health_check.interval_seconds
                
                # Run health checks concurrently
                if checks_to_run:
                    tasks = []
                    for check_name, health_check in checks_to_run:
                        task = asyncio.create_task(self._run_health_check(check_name, health_check))
                        tasks.append(task)
                    
                    # Wait for all checks to complete
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results and trigger recovery if needed
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Health check failed with exception: {result}")
                        elif isinstance(result, HealthCheckResult):
                            await self._process_health_check_result(result)
                
                # Check dependencies periodically
                await self._check_dependencies()
                
                # Sleep for a short interval
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(10)  # Longer sleep on error
    
    async def _run_health_check(self, check_name: str, health_check: HealthCheck) -> HealthCheckResult:
        """Run a single health check."""
        start_time = time.time()
        
        try:
            # Run the health check with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout_seconds
            )
            
            if isinstance(result, HealthCheckResult):
                return result
            elif isinstance(result, dict):
                # Convert dict result to HealthCheckResult
                return HealthCheckResult(
                    check_name=check_name,
                    component=health_check.component,
                    status=HealthStatus(result.get('status', 'healthy')),
                    details=result.get('details', {}),
                    metrics=result.get('metrics', {})
                )
            else:
                # Assume healthy if result is truthy
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                return HealthCheckResult(
                    check_name=check_name,
                    component=health_check.component,
                    status=status
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                check_name=check_name,
                component=health_check.component,
                status=HealthStatus.CRITICAL,
                duration_seconds=time.time() - start_time,
                error_message="Health check timed out",
                details={"timeout_seconds": health_check.timeout_seconds}
            )
        except Exception as e:
            return HealthCheckResult(
                check_name=check_name,
                component=health_check.component,
                status=HealthStatus.CRITICAL,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
                details={"error": str(e)}
            )
    
    async def _process_health_check_result(self, result: HealthCheckResult):
        """Process health check result and trigger recovery if needed."""
        with self._lock:
            self.health_check_results[result.check_name] = result
        
        # Log health check result
        log_level = {
            HealthStatus.HEALTHY: logging.DEBUG,
            HealthStatus.DEGRADED: logging.WARNING,
            HealthStatus.UNHEALTHY: logging.ERROR,
            HealthStatus.CRITICAL: logging.CRITICAL,
            HealthStatus.UNKNOWN: logging.WARNING
        }.get(result.status, logging.INFO)
        
        logger.log(
            log_level,
            f"Health check {result.check_name}: {result.status.value} "
            f"(duration: {result.duration_seconds:.2f}s)"
        )
        
        # Trigger recovery for unhealthy components
        if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
            health_check = self.health_checks.get(result.check_name)
            if health_check and health_check.recovery_actions:
                # Create a recovery plan from the health check
                recovery_plan = RecoveryPlan(
                    component=result.component,
                    actions=health_check.recovery_actions
                )
                
                # Execute recovery asynchronously
                asyncio.create_task(
                    self.self_healing.execute_recovery(result.component, result)
                )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource health."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                status = max(status, HealthStatus.UNHEALTHY)
                issues.append(f"CPU usage high: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = max(status, HealthStatus.DEGRADED)
                issues.append(f"CPU usage elevated: {cpu_percent:.1f}%")
            
            if memory_percent > 95:
                status = HealthStatus.CRITICAL
                issues.append(f"Memory usage critical: {memory_percent:.1f}%")
            elif memory_percent > 85:
                status = max(status, HealthStatus.UNHEALTHY)
                issues.append(f"Memory usage high: {memory_percent:.1f}%")
            elif memory_percent > 75:
                status = max(status, HealthStatus.DEGRADED)
                issues.append(f"Memory usage elevated: {memory_percent:.1f}%")
            
            if disk_percent > 95:
                status = HealthStatus.CRITICAL
                issues.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent > 90:
                status = max(status, HealthStatus.UNHEALTHY)
                issues.append(f"Disk usage high: {disk_percent:.1f}%")
            elif disk_percent > 80:
                status = max(status, HealthStatus.DEGRADED)
                issues.append(f"Disk usage elevated: {disk_percent:.1f}%")
            
            return HealthCheckResult(
                check_name="system_resources",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=status,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "issues": issues
                },
                metrics={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="system_resources",
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=HealthStatus.CRITICAL,
                error_message=str(e)
            )
    
    async def _check_dependencies(self):
        """Check health of all registered dependencies."""
        for dep_name in self.dependency_monitor.dependencies.keys():
            try:
                result = await self.dependency_monitor.check_dependency_health(dep_name)
                
                # Log dependency health
                if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    logger.error(f"Dependency {dep_name} is {result.status.value}: {result.error_message}")
                elif result.status == HealthStatus.DEGRADED:
                    logger.warning(f"Dependency {dep_name} is degraded")
                    
            except Exception as e:
                logger.error(f"Failed to check dependency {dep_name}: {e}")
    
    async def run_health_check_on_demand(self, check_name: str) -> HealthCheckResult:
        """Run a specific health check on demand."""
        health_check = self.health_checks.get(check_name)
        if not health_check:
            return HealthCheckResult(
                check_name=check_name,
                component=ComponentType.DOCUMENT_PROCESSOR,
                status=HealthStatus.UNKNOWN,
                error_message=f"Health check {check_name} not found"
            )
        
        return await self._run_health_check(check_name, health_check)
    
    async def execute_manual_recovery(self, component: ComponentType) -> Dict[str, Any]:
        """Manually trigger recovery for a component."""
        # Create a mock health result for manual recovery
        health_result = HealthCheckResult(
            check_name=f"manual_{component.value}",
            component=component,
            status=HealthStatus.CRITICAL,
            details={"trigger": "manual"}
        )
        
        return await self.self_healing.execute_recovery(component, health_result)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary."""
        with self._lock:
            current_results = self.health_check_results.copy()
        
        # Overall system status
        status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0, "critical": 0, "unknown": 0}
        component_status = {}
        
        for check_name, result in current_results.items():
            status = result.status.value
            status_counts[status] += 1
            component_status[check_name] = {
                "status": status,
                "component": result.component.value,
                "last_check": result.timestamp,
                "duration": result.duration_seconds
            }
        
        # Determine overall health
        if status_counts["critical"] > 0:
            overall_status = "critical"
        elif status_counts["unhealthy"] > 0:
            overall_status = "unhealthy"
        elif status_counts["degraded"] > 0:
            overall_status = "degraded"
        elif status_counts["unknown"] > 2:
            overall_status = "unknown"
        else:
            overall_status = "healthy"
        
        # Get dependency status
        dependency_status = self.dependency_monitor.get_dependency_status()
        
        # Get recovery statistics
        recovery_stats = self.self_healing.get_recovery_statistics()
        
        return {
            "overall_status": overall_status,
            "timestamp": time.time(),
            "monitoring_active": self.monitoring_active,
            "health_checks": {
                "total": len(self.health_checks),
                "status_distribution": status_counts,
                "component_status": component_status
            },
            "dependencies": {
                "total": len(self.dependency_monitor.dependencies),
                "status": {name: result.status.value for name, result in dependency_status.items()}
            },
            "recovery_system": {
                "auto_recovery_enabled": self.self_healing.auto_recovery_enabled,
                "statistics": recovery_stats
            },
            "chaos_engineering": {
                "active_experiments": len(self.chaos_engineering.get_active_experiments()),
                "safety_enabled": self.chaos_engineering.safety_enabled
            }
        }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the entire system."""
        logger.info("Starting comprehensive health check")
        start_time = time.time()
        
        # Run all health checks
        health_check_tasks = []
        for check_name, health_check in self.health_checks.items():
            if health_check.enabled:
                task = asyncio.create_task(self._run_health_check(check_name, health_check))
                health_check_tasks.append((check_name, task))
        
        # Run dependency checks
        dependency_tasks = []
        for dep_name in self.dependency_monitor.dependencies.keys():
            task = asyncio.create_task(self.dependency_monitor.check_dependency_health(dep_name))
            dependency_tasks.append((dep_name, task))
        
        # Wait for all checks to complete
        all_tasks = [task for _, task in health_check_tasks + dependency_tasks]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Process results
        health_results = {}
        dependency_results = {}
        
        for i, (check_name, task) in enumerate(health_check_tasks):
            result = results[i]
            if isinstance(result, HealthCheckResult):
                health_results[check_name] = result
            elif isinstance(result, Exception):
                logger.error(f"Health check {check_name} failed: {result}")
        
        for i, (dep_name, task) in enumerate(dependency_tasks):
            result = results[len(health_check_tasks) + i]
            if isinstance(result, HealthCheckResult):
                dependency_results[dep_name] = result
            elif isinstance(result, Exception):
                logger.error(f"Dependency check {dep_name} failed: {result}")
        
        # Generate comprehensive report
        total_duration = time.time() - start_time
        
        return {
            "comprehensive_check": {
                "timestamp": start_time,
                "duration_seconds": total_duration,
                "health_checks_performed": len(health_results),
                "dependency_checks_performed": len(dependency_results)
            },
            "health_check_results": {
                name: {
                    "status": result.status.value,
                    "component": result.component.value,
                    "duration": result.duration_seconds,
                    "details": result.details,
                    "metrics": result.metrics,
                    "error": result.error_message
                }
                for name, result in health_results.items()
            },
            "dependency_results": {
                name: {
                    "status": result.status.value,
                    "duration": result.duration_seconds,
                    "details": result.details,
                    "metrics": result.metrics,
                    "error": result.error_message
                }
                for name, result in dependency_results.items()
            },
            "summary": self.get_system_health_summary()
        }


# Global health and recovery system instance
health_recovery_system = EnterpriseHealthRecoverySystem()


def get_health_recovery_system() -> EnterpriseHealthRecoverySystem:
    """Get the global health and recovery system instance."""
    return health_recovery_system


# Convenience functions
async def perform_health_check() -> Dict[str, Any]:
    """Perform a quick system health check."""
    return await health_recovery_system.comprehensive_health_check()


async def trigger_recovery(component: ComponentType) -> Dict[str, Any]:
    """Manually trigger recovery for a component."""
    return await health_recovery_system.execute_manual_recovery(component)


async def run_chaos_experiment(experiment: ChaosExperiment) -> Dict[str, Any]:
    """Run a chaos engineering experiment."""
    return await health_recovery_system.chaos_engineering.run_chaos_experiment(experiment)