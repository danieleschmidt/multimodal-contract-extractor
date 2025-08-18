"""Elastic Cloud Orchestration Framework for Auto-Scaling Legal AI Infrastructure."""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers."""
    
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"


class InstanceType(Enum):
    """Cloud instance types for different workloads."""
    
    CPU_OPTIMIZED = "cpu_optimized"
    MEMORY_OPTIMIZED = "memory_optimized"
    GPU_ACCELERATED = "gpu_accelerated"
    GENERAL_PURPOSE = "general_purpose"
    BURSTABLE = "burstable"
    SPOT_INSTANCE = "spot_instance"


class ScalingTrigger(Enum):
    """Triggers for auto-scaling decisions."""
    
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    REQUEST_QUEUE_LENGTH = "request_queue_length"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    CUSTOM_METRIC = "custom_metric"
    PREDICTIVE = "predictive"
    SCHEDULE_BASED = "schedule_based"


class WorkloadPattern(Enum):
    """Different workload patterns for optimization."""
    
    STEADY_STATE = "steady_state"
    SPIKY = "spiky"
    PERIODIC = "periodic"
    GROWING = "growing"
    DECLINING = "declining"
    UNPREDICTABLE = "unpredictable"


@dataclass
class CloudResource:
    """Represents a cloud resource instance."""
    
    instance_id: str
    instance_type: InstanceType
    provider: CloudProvider
    region: str
    availability_zone: str
    cpu_cores: int
    memory_gb: float
    gpu_count: int
    storage_gb: float
    hourly_cost: float
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration."""
    
    name: str
    trigger: ScalingTrigger
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_adjustment: int
    scale_down_adjustment: int
    cooldown_period: float
    min_instances: int
    max_instances: int
    target_instance_type: InstanceType
    enabled: bool = True
    evaluation_periods: int = 2
    last_scaling_time: float = 0


@dataclass
class WorkloadForecast:
    """Workload forecasting results."""
    
    timestamp: float
    forecast_horizon_hours: int
    predicted_cpu_usage: List[float]
    predicted_memory_usage: List[float]
    predicted_request_rate: List[float]
    confidence_interval: Tuple[float, float]
    pattern: WorkloadPattern
    recommended_instances: int


class PredictiveScaler:
    """Predictive scaling based on historical patterns and ML forecasting."""
    
    def __init__(self):
        self.historical_metrics: deque = deque(maxlen=10000)
        self.workload_patterns: Dict[str, WorkloadPattern] = {}
        self.forecast_cache: Dict[str, WorkloadForecast] = {}
        
    def record_metrics(
        self,
        timestamp: float,
        cpu_usage: float,
        memory_usage: float,
        request_rate: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record metrics for pattern analysis."""
        self.historical_metrics.append({
            "timestamp": timestamp,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "request_rate": request_rate,
            "tags": tags or {}
        })
    
    def detect_workload_pattern(self, lookback_hours: int = 24) -> WorkloadPattern:
        """Detect workload pattern from historical data."""
        if len(self.historical_metrics) < 100:
            return WorkloadPattern.UNPREDICTABLE
        
        # Get recent metrics
        cutoff_time = time.time() - (lookback_hours * 3600)
        recent_metrics = [
            m for m in self.historical_metrics
            if m["timestamp"] > cutoff_time
        ]
        
        if len(recent_metrics) < 50:
            return WorkloadPattern.UNPREDICTABLE
        
        # Analyze patterns
        cpu_values = [m["cpu_usage"] for m in recent_metrics]
        cpu_mean = np.mean(cpu_values)
        cpu_std = np.std(cpu_values)
        
        # Calculate trend
        timestamps = [m["timestamp"] for m in recent_metrics]
        cpu_trend = np.corrcoef(timestamps, cpu_values)[0, 1]
        
        # Detect periodicity
        cpu_fft = np.fft.fft(cpu_values)
        cpu_power = np.abs(cpu_fft) ** 2
        dominant_freq_idx = np.argmax(cpu_power[1:len(cpu_power)//2]) + 1
        periodicity_strength = cpu_power[dominant_freq_idx] / np.sum(cpu_power)
        
        # Pattern classification
        if cpu_std / cpu_mean < 0.1:  # Low variance
            return WorkloadPattern.STEADY_STATE
        elif cpu_std / cpu_mean > 0.5:  # High variance
            if periodicity_strength > 0.3:
                return WorkloadPattern.PERIODIC
            else:
                return WorkloadPattern.SPIKY
        elif cpu_trend > 0.5:
            return WorkloadPattern.GROWING
        elif cpu_trend < -0.5:
            return WorkloadPattern.DECLINING
        elif periodicity_strength > 0.2:
            return WorkloadPattern.PERIODIC
        else:
            return WorkloadPattern.UNPREDICTABLE
    
    def generate_forecast(self, forecast_horizon_hours: int = 24) -> WorkloadForecast:
        """Generate workload forecast for the specified horizon."""
        if len(self.historical_metrics) < 200:
            # Insufficient data for forecasting
            return WorkloadForecast(
                timestamp=time.time(),
                forecast_horizon_hours=forecast_horizon_hours,
                predicted_cpu_usage=[50.0] * forecast_horizon_hours,
                predicted_memory_usage=[60.0] * forecast_horizon_hours,
                predicted_request_rate=[100.0] * forecast_horizon_hours,
                confidence_interval=(0.3, 0.7),
                pattern=WorkloadPattern.UNPREDICTABLE,
                recommended_instances=2
            )
        
        pattern = self.detect_workload_pattern()
        
        # Simple forecasting based on pattern
        recent_metrics = list(self.historical_metrics)[-100:]
        avg_cpu = np.mean([m["cpu_usage"] for m in recent_metrics])
        avg_memory = np.mean([m["memory_usage"] for m in recent_metrics])
        avg_requests = np.mean([m["request_rate"] for m in recent_metrics])
        
        if pattern == WorkloadPattern.STEADY_STATE:
            predicted_cpu = [avg_cpu] * forecast_horizon_hours
            predicted_memory = [avg_memory] * forecast_horizon_hours
            predicted_requests = [avg_requests] * forecast_horizon_hours
            confidence = (0.8, 0.9)
            
        elif pattern == WorkloadPattern.GROWING:
            growth_rate = 1.02  # 2% hourly growth
            predicted_cpu = [avg_cpu * (growth_rate ** i) for i in range(forecast_horizon_hours)]
            predicted_memory = [avg_memory * (growth_rate ** i) for i in range(forecast_horizon_hours)]
            predicted_requests = [avg_requests * (growth_rate ** i) for i in range(forecast_horizon_hours)]
            confidence = (0.6, 0.8)
            
        elif pattern == WorkloadPattern.PERIODIC:
            # Simulate daily pattern
            daily_pattern = [0.3, 0.2, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.2, 1.1, 1.0, 0.9,
                           0.8, 0.9, 1.0, 1.1, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.3]
            
            predicted_cpu = []
            predicted_memory = []
            predicted_requests = []
            
            for i in range(forecast_horizon_hours):
                hour_of_day = (i % 24)
                multiplier = daily_pattern[hour_of_day]
                predicted_cpu.append(avg_cpu * multiplier)
                predicted_memory.append(avg_memory * multiplier)
                predicted_requests.append(avg_requests * multiplier)
            
            confidence = (0.7, 0.85)
            
        else:  # SPIKY or UNPREDICTABLE
            # Add noise to average
            noise_factor = 0.3
            predicted_cpu = [avg_cpu * (1 + np.random.normal(0, noise_factor)) 
                           for _ in range(forecast_horizon_hours)]
            predicted_memory = [avg_memory * (1 + np.random.normal(0, noise_factor)) 
                              for _ in range(forecast_horizon_hours)]
            predicted_requests = [avg_requests * (1 + np.random.normal(0, noise_factor)) 
                                for _ in range(forecast_horizon_hours)]
            confidence = (0.4, 0.6)
        
        # Calculate recommended instances
        max_predicted_cpu = max(predicted_cpu)
        max_predicted_memory = max(predicted_memory)
        
        # Simple instance calculation (assuming 100% CPU = 1 instance)
        cpu_instances = int(np.ceil(max_predicted_cpu / 80))  # 80% target utilization
        memory_instances = int(np.ceil(max_predicted_memory / 80))
        recommended_instances = max(cpu_instances, memory_instances, 1)
        
        return WorkloadForecast(
            timestamp=time.time(),
            forecast_horizon_hours=forecast_horizon_hours,
            predicted_cpu_usage=predicted_cpu,
            predicted_memory_usage=predicted_memory,
            predicted_request_rate=predicted_requests,
            confidence_interval=confidence,
            pattern=pattern,
            recommended_instances=recommended_instances
        )


class CloudResourceManager:
    """Manages cloud resources across different providers."""
    
    def __init__(self):
        self.active_resources: Dict[str, CloudResource] = {}
        self.resource_pools: Dict[CloudProvider, List[CloudResource]] = defaultdict(list)
        self.cost_tracking: Dict[str, float] = defaultdict(float)
        
    async def provision_instance(
        self,
        instance_type: InstanceType,
        provider: CloudProvider,
        region: str,
        tags: Optional[Dict[str, str]] = None
    ) -> CloudResource:
        """Provision a new cloud instance."""
        instance_id = f"{provider.value}_{instance_type.value}_{int(time.time())}"
        
        # Simulate instance specifications based on type
        specs = self._get_instance_specs(instance_type)
        
        resource = CloudResource(
            instance_id=instance_id,
            instance_type=instance_type,
            provider=provider,
            region=region,
            availability_zone=f"{region}a",  # Simplified
            cpu_cores=specs["cpu_cores"],
            memory_gb=specs["memory_gb"],
            gpu_count=specs["gpu_count"],
            storage_gb=specs["storage_gb"],
            hourly_cost=specs["hourly_cost"],
            status="pending",
            tags=tags or {}
        )
        
        # Simulate provisioning delay
        await asyncio.sleep(0.1)
        
        resource.status = "running"
        self.active_resources[instance_id] = resource
        self.resource_pools[provider].append(resource)
        
        logger.info(f"Provisioned instance: {instance_id} ({instance_type.value})")
        return resource
    
    async def terminate_instance(self, instance_id: str) -> bool:
        """Terminate a cloud instance."""
        if instance_id not in self.active_resources:
            return False
        
        resource = self.active_resources[instance_id]
        
        # Calculate final cost
        runtime_hours = (time.time() - resource.created_at) / 3600
        final_cost = runtime_hours * resource.hourly_cost
        self.cost_tracking[instance_id] = final_cost
        
        # Remove from active resources
        del self.active_resources[instance_id]
        
        # Remove from resource pool
        self.resource_pools[resource.provider] = [
            r for r in self.resource_pools[resource.provider] 
            if r.instance_id != instance_id
        ]
        
        logger.info(f"Terminated instance: {instance_id} (cost: ${final_cost:.2f})")
        return True
    
    def _get_instance_specs(self, instance_type: InstanceType) -> Dict[str, Any]:
        """Get instance specifications based on type."""
        specs = {
            InstanceType.CPU_OPTIMIZED: {
                "cpu_cores": 8, "memory_gb": 16.0, "gpu_count": 0, 
                "storage_gb": 100.0, "hourly_cost": 0.50
            },
            InstanceType.MEMORY_OPTIMIZED: {
                "cpu_cores": 4, "memory_gb": 32.0, "gpu_count": 0, 
                "storage_gb": 100.0, "hourly_cost": 0.80
            },
            InstanceType.GPU_ACCELERATED: {
                "cpu_cores": 16, "memory_gb": 64.0, "gpu_count": 4, 
                "storage_gb": 200.0, "hourly_cost": 3.00
            },
            InstanceType.GENERAL_PURPOSE: {
                "cpu_cores": 4, "memory_gb": 16.0, "gpu_count": 0, 
                "storage_gb": 100.0, "hourly_cost": 0.40
            },
            InstanceType.BURSTABLE: {
                "cpu_cores": 2, "memory_gb": 4.0, "gpu_count": 0, 
                "storage_gb": 50.0, "hourly_cost": 0.15
            },
            InstanceType.SPOT_INSTANCE: {
                "cpu_cores": 8, "memory_gb": 16.0, "gpu_count": 0, 
                "storage_gb": 100.0, "hourly_cost": 0.20
            }
        }
        
        return specs.get(instance_type, specs[InstanceType.GENERAL_PURPOSE])
    
    def get_total_cost(self) -> float:
        """Get total cost across all resources."""
        # Active resource costs
        active_cost = 0.0
        current_time = time.time()
        
        for resource in self.active_resources.values():
            runtime_hours = (current_time - resource.created_at) / 3600
            active_cost += runtime_hours * resource.hourly_cost
        
        # Historical costs
        historical_cost = sum(self.cost_tracking.values())
        
        return active_cost + historical_cost
    
    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get current resource utilization summary."""
        if not self.active_resources:
            return {"total_instances": 0, "total_cost": 0.0}
        
        total_instances = len(self.active_resources)
        total_cpu_cores = sum(r.cpu_cores for r in self.active_resources.values())
        total_memory_gb = sum(r.memory_gb for r in self.active_resources.values())
        total_gpu_count = sum(r.gpu_count for r in self.active_resources.values())
        
        # Group by instance type
        by_type = defaultdict(int)
        for resource in self.active_resources.values():
            by_type[resource.instance_type.value] += 1
        
        # Group by provider
        by_provider = defaultdict(int)
        for resource in self.active_resources.values():
            by_provider[resource.provider.value] += 1
        
        return {
            "total_instances": total_instances,
            "total_cpu_cores": total_cpu_cores,
            "total_memory_gb": total_memory_gb,
            "total_gpu_count": total_gpu_count,
            "by_instance_type": dict(by_type),
            "by_provider": dict(by_provider),
            "total_cost": self.get_total_cost()
        }


class ElasticCloudOrchestrator:
    """Main orchestrator for elastic cloud operations."""
    
    def __init__(self):
        self.resource_manager = CloudResourceManager()
        self.predictive_scaler = PredictiveScaler()
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.metrics_buffer: deque = deque(maxlen=1000)
        
        # Default scaling policies
        self._setup_default_policies()
        
    def _setup_default_policies(self) -> None:
        """Setup default auto-scaling policies."""
        # CPU-based scaling
        self.scaling_policies["cpu_scaling"] = ScalingPolicy(
            name="cpu_scaling",
            trigger=ScalingTrigger.CPU_UTILIZATION,
            scale_up_threshold=75.0,
            scale_down_threshold=25.0,
            scale_up_adjustment=2,
            scale_down_adjustment=1,
            cooldown_period=300.0,  # 5 minutes
            min_instances=1,
            max_instances=20,
            target_instance_type=InstanceType.GENERAL_PURPOSE
        )
        
        # Memory-based scaling
        self.scaling_policies["memory_scaling"] = ScalingPolicy(
            name="memory_scaling",
            trigger=ScalingTrigger.MEMORY_UTILIZATION,
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            scale_up_adjustment=1,
            scale_down_adjustment=1,
            cooldown_period=600.0,  # 10 minutes
            min_instances=1,
            max_instances=15,
            target_instance_type=InstanceType.MEMORY_OPTIMIZED
        )
        
        # Response time-based scaling
        self.scaling_policies["latency_scaling"] = ScalingPolicy(
            name="latency_scaling",
            trigger=ScalingTrigger.RESPONSE_TIME,
            scale_up_threshold=2000.0,  # 2 seconds
            scale_down_threshold=500.0,  # 0.5 seconds
            scale_up_adjustment=3,
            scale_down_adjustment=1,
            cooldown_period=180.0,  # 3 minutes
            min_instances=2,
            max_instances=50,
            target_instance_type=InstanceType.CPU_OPTIMIZED
        )
    
    async def record_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        response_time: float,
        request_rate: float,
        error_rate: float = 0.0,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record system metrics for scaling decisions."""
        timestamp = time.time()
        
        metrics = {
            "timestamp": timestamp,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "response_time": response_time,
            "request_rate": request_rate,
            "error_rate": error_rate,
            "tags": tags or {}
        }
        
        self.metrics_buffer.append(metrics)
        
        # Record for predictive scaling
        self.predictive_scaler.record_metrics(
            timestamp, cpu_usage, memory_usage, request_rate, tags
        )
        
        # Evaluate scaling policies
        await self._evaluate_scaling_policies(metrics)
    
    async def _evaluate_scaling_policies(self, current_metrics: Dict[str, Any]) -> None:
        """Evaluate all scaling policies against current metrics."""
        for policy_name, policy in self.scaling_policies.items():
            if not policy.enabled:
                continue
            
            await self._evaluate_single_policy(policy, current_metrics)
    
    async def _evaluate_single_policy(
        self, policy: ScalingPolicy, current_metrics: Dict[str, Any]
    ) -> None:
        """Evaluate a single scaling policy."""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - policy.last_scaling_time < policy.cooldown_period:
            return
        
        # Get metric value based on trigger
        metric_value = self._get_metric_value(policy.trigger, current_metrics)
        if metric_value is None:
            return
        
        # Get recent metric values for evaluation
        recent_metrics = [
            m for m in self.metrics_buffer
            if current_time - m["timestamp"] < 300  # Last 5 minutes
        ]
        
        if len(recent_metrics) < policy.evaluation_periods:
            return
        
        # Calculate average over evaluation periods
        recent_values = [
            self._get_metric_value(policy.trigger, m) 
            for m in recent_metrics[-policy.evaluation_periods:]
        ]
        recent_values = [v for v in recent_values if v is not None]
        
        if not recent_values:
            return
        
        avg_value = np.mean(recent_values)
        current_instances = len(self.resource_manager.active_resources)
        
        scaling_action = None
        adjustment = 0
        
        # Scale up condition
        if avg_value > policy.scale_up_threshold and current_instances < policy.max_instances:
            scaling_action = "scale_up"
            adjustment = min(
                policy.scale_up_adjustment,
                policy.max_instances - current_instances
            )
            
        # Scale down condition
        elif avg_value < policy.scale_down_threshold and current_instances > policy.min_instances:
            scaling_action = "scale_down"
            adjustment = min(
                policy.scale_down_adjustment,
                current_instances - policy.min_instances
            )
        
        if scaling_action and adjustment > 0:
            await self._execute_scaling_action(policy, scaling_action, adjustment, avg_value)
    
    def _get_metric_value(self, trigger: ScalingTrigger, metrics: Dict[str, Any]) -> Optional[float]:
        """Extract metric value based on trigger type."""
        if trigger == ScalingTrigger.CPU_UTILIZATION:
            return metrics.get("cpu_usage")
        elif trigger == ScalingTrigger.MEMORY_UTILIZATION:
            return metrics.get("memory_usage")
        elif trigger == ScalingTrigger.RESPONSE_TIME:
            return metrics.get("response_time")
        elif trigger == ScalingTrigger.REQUEST_QUEUE_LENGTH:
            return metrics.get("request_rate")  # Simplified
        elif trigger == ScalingTrigger.ERROR_RATE:
            return metrics.get("error_rate")
        
        return None
    
    async def _execute_scaling_action(
        self,
        policy: ScalingPolicy,
        action: str,
        adjustment: int,
        trigger_value: float
    ) -> None:
        """Execute scaling action (scale up or down)."""
        try:
            if action == "scale_up":
                # Provision new instances
                for i in range(adjustment):
                    await self.resource_manager.provision_instance(
                        instance_type=policy.target_instance_type,
                        provider=CloudProvider.AWS,  # Default to AWS
                        region="us-east-1",
                        tags={"scaling_policy": policy.name, "auto_scaled": "true"}
                    )
            
            elif action == "scale_down":
                # Terminate instances (oldest first)
                active_instances = list(self.resource_manager.active_resources.values())
                active_instances.sort(key=lambda r: r.created_at)
                
                for i in range(min(adjustment, len(active_instances))):
                    await self.resource_manager.terminate_instance(active_instances[i].instance_id)
            
            # Record scaling event
            scaling_event = {
                "timestamp": time.time(),
                "policy_name": policy.name,
                "action": action,
                "adjustment": adjustment,
                "trigger_value": trigger_value,
                "threshold": policy.scale_up_threshold if action == "scale_up" else policy.scale_down_threshold,
                "instances_after": len(self.resource_manager.active_resources)
            }
            
            self.scaling_history.append(scaling_event)
            policy.last_scaling_time = time.time()
            
            logger.info(f"Scaling action executed: {policy.name} - {action} by {adjustment}")
            
        except Exception as e:
            logger.error(f"Scaling action failed for {policy.name}: {e}")
    
    async def enable_predictive_scaling(self, forecast_horizon_hours: int = 6) -> None:
        """Enable predictive scaling based on workload forecasting."""
        try:
            forecast = self.predictive_scaler.generate_forecast(forecast_horizon_hours)
            
            # Make scaling decisions based on forecast
            current_instances = len(self.resource_manager.active_resources)
            recommended_instances = forecast.recommended_instances
            
            if recommended_instances > current_instances:
                # Proactive scale up
                scale_up_count = min(
                    recommended_instances - current_instances,
                    20 - current_instances  # Max 20 instances
                )
                
                for i in range(scale_up_count):
                    await self.resource_manager.provision_instance(
                        instance_type=InstanceType.GENERAL_PURPOSE,
                        provider=CloudProvider.AWS,
                        region="us-east-1",
                        tags={"scaling_type": "predictive", "forecast_based": "true"}
                    )
                
                # Record predictive scaling event
                self.scaling_history.append({
                    "timestamp": time.time(),
                    "policy_name": "predictive_scaling",
                    "action": "predictive_scale_up",
                    "adjustment": scale_up_count,
                    "pattern": forecast.pattern.value,
                    "confidence": forecast.confidence_interval,
                    "instances_after": len(self.resource_manager.active_resources)
                })
                
                logger.info(f"Predictive scaling: scaled up by {scale_up_count} instances")
                
        except Exception as e:
            logger.error(f"Predictive scaling failed: {e}")
    
    def create_scaling_policy(
        self,
        name: str,
        trigger: ScalingTrigger,
        scale_up_threshold: float,
        scale_down_threshold: float,
        scale_up_adjustment: int,
        scale_down_adjustment: int,
        min_instances: int,
        max_instances: int,
        target_instance_type: InstanceType,
        cooldown_period: float = 300.0
    ) -> None:
        """Create a custom scaling policy."""
        policy = ScalingPolicy(
            name=name,
            trigger=trigger,
            scale_up_threshold=scale_up_threshold,
            scale_down_threshold=scale_down_threshold,
            scale_up_adjustment=scale_up_adjustment,
            scale_down_adjustment=scale_down_adjustment,
            cooldown_period=cooldown_period,
            min_instances=min_instances,
            max_instances=max_instances,
            target_instance_type=target_instance_type
        )
        
        self.scaling_policies[name] = policy
        logger.info(f"Created scaling policy: {name}")
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestration status."""
        # Resource utilization
        utilization = self.resource_manager.get_resource_utilization()
        
        # Recent scaling events
        recent_events = [
            event for event in self.scaling_history
            if time.time() - event["timestamp"] < 3600  # Last hour
        ]
        
        # Workload pattern
        pattern = self.predictive_scaler.detect_workload_pattern()
        
        # Policy status
        policy_status = {
            name: {
                "enabled": policy.enabled,
                "last_scaling": policy.last_scaling_time,
                "trigger": policy.trigger.value
            }
            for name, policy in self.scaling_policies.items()
        }
        
        return {
            "resource_utilization": utilization,
            "recent_scaling_events": len(recent_events),
            "workload_pattern": pattern.value,
            "active_policies": len([p for p in self.scaling_policies.values() if p.enabled]),
            "policy_status": policy_status,
            "total_scaling_events": len(self.scaling_history)
        }


# Global cloud orchestrator instance
cloud_orchestrator = ElasticCloudOrchestrator()


async def record_system_metrics(
    cpu_usage: float,
    memory_usage: float,
    response_time: float,
    request_rate: float,
    error_rate: float = 0.0,
    tags: Optional[Dict[str, str]] = None
) -> None:
    """Record system metrics for auto-scaling."""
    await cloud_orchestrator.record_metrics(
        cpu_usage, memory_usage, response_time, request_rate, error_rate, tags
    )


async def enable_predictive_scaling(forecast_horizon_hours: int = 6) -> None:
    """Enable predictive scaling with specified forecast horizon."""
    await cloud_orchestrator.enable_predictive_scaling(forecast_horizon_hours)


def get_cloud_orchestrator() -> ElasticCloudOrchestrator:
    """Get the global cloud orchestrator instance."""
    return cloud_orchestrator