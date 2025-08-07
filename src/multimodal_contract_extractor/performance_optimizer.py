"""Advanced performance optimization engine for neuromorphic and quantum processing.

This module implements intelligent performance optimization, adaptive algorithms,
and scaling strategies for maximum throughput and efficiency.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
import psutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""
    THROUGHPUT_MAXIMIZATION = "throughput_max"
    LATENCY_MINIMIZATION = "latency_min"  
    ENERGY_EFFICIENCY = "energy_efficient"
    BALANCED_PERFORMANCE = "balanced"
    QUALITY_FOCUSED = "quality_focused"
    COST_OPTIMIZATION = "cost_optimized"


class ResourceType(Enum):
    """System resource types for optimization."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    NETWORK = "network"
    STORAGE = "storage"
    QUANTUM_COHERENCE = "quantum_coherence"
    NEUROMORPHIC_SPIKES = "neuromorphic_spikes"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    
    timestamp: float = field(default_factory=time.time)
    throughput_docs_per_second: float = 0.0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    gpu_utilization: float = 0.0
    energy_consumption_watts: float = 0.0
    accuracy_score: float = 0.0
    error_rate: float = 0.0
    quantum_coherence_time: float = 0.0
    neuromorphic_spike_efficiency: float = 0.0
    cost_per_document: float = 0.0
    
    def overall_performance_score(self) -> float:
        """Calculate overall performance score (0-1)."""
        # Normalize and weight different metrics
        throughput_score = min(self.throughput_docs_per_second / 10.0, 1.0)  # Max 10 docs/sec
        latency_score = max(0, 1.0 - (self.average_latency_ms / 30000))  # Max 30s latency
        accuracy_score = self.accuracy_score
        efficiency_score = max(0, 1.0 - (self.energy_consumption_watts / 100))  # Max 100W
        reliability_score = max(0, 1.0 - self.error_rate)
        
        weights = {
            "throughput": 0.25,
            "latency": 0.20,
            "accuracy": 0.25,
            "efficiency": 0.15,
            "reliability": 0.15
        }
        
        score = (
            throughput_score * weights["throughput"] +
            latency_score * weights["latency"] +
            accuracy_score * weights["accuracy"] +
            efficiency_score * weights["efficiency"] +
            reliability_score * weights["reliability"]
        )
        
        return min(max(score, 0.0), 1.0)


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""
    
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED_PERFORMANCE
    target_throughput: float = 5.0  # docs/second
    max_latency_ms: float = 15000  # 15 seconds
    max_energy_watts: float = 50.0
    min_accuracy: float = 0.85
    max_error_rate: float = 0.05
    optimization_interval: float = 60.0  # 1 minute
    adaptation_rate: float = 0.1
    enable_predictive_scaling: bool = True
    enable_dynamic_batching: bool = True
    enable_resource_pooling: bool = True


class ResourceMonitor:
    """Real-time resource monitoring and prediction."""
    
    def __init__(self):
        self.resource_history: Dict[ResourceType, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        self.monitoring_active = False
        self.prediction_models: Dict[ResourceType, Any] = {}
        
    async def start_monitoring(self):
        """Start continuous resource monitoring."""
        self.monitoring_active = True
        logger.info("Started resource monitoring")
        
        while self.monitoring_active:
            await self._collect_resource_metrics()
            await asyncio.sleep(1.0)  # Collect every second
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring_active = False
        logger.info("Stopped resource monitoring")
    
    async def _collect_resource_metrics(self):
        """Collect current resource metrics."""
        timestamp = time.time()
        
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.resource_history[ResourceType.CPU].append((timestamp, cpu_percent))
        
        # Memory utilization
        memory = psutil.virtual_memory()
        self.resource_history[ResourceType.MEMORY].append((timestamp, memory.percent))
        
        # GPU utilization (simulated - would use nvidia-ml-py in real implementation)
        gpu_percent = self._get_gpu_utilization()
        self.resource_history[ResourceType.GPU].append((timestamp, gpu_percent))
        
        # Network utilization
        network_stats = psutil.net_io_counters()
        network_utilization = min(
            (network_stats.bytes_sent + network_stats.bytes_recv) / 1e9, 100.0
        )
        self.resource_history[ResourceType.NETWORK].append((timestamp, network_utilization))
        
        # Storage utilization
        disk_usage = psutil.disk_usage('/').percent
        self.resource_history[ResourceType.STORAGE].append((timestamp, disk_usage))
        
        # Quantum coherence (simulated)
        quantum_coherence = self._get_quantum_coherence()
        self.resource_history[ResourceType.QUANTUM_COHERENCE].append((timestamp, quantum_coherence))
        
        # Neuromorphic spike efficiency (simulated)  
        spike_efficiency = self._get_neuromorphic_efficiency()
        self.resource_history[ResourceType.NEUROMORPHIC_SPIKES].append((timestamp, spike_efficiency))
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization (simulated)."""
        # In real implementation, would use nvidia-ml-py or similar
        return min(psutil.cpu_percent() * 1.2, 100.0)
    
    def _get_quantum_coherence(self) -> float:
        """Get quantum system coherence (simulated)."""
        # Simulate quantum coherence degradation over time
        base_coherence = 85.0
        time_decay = (time.time() % 100) * 0.1
        return max(base_coherence - time_decay, 70.0)
    
    def _get_neuromorphic_efficiency(self) -> float:
        """Get neuromorphic system efficiency (simulated)."""
        # Simulate neuromorphic spike efficiency
        base_efficiency = 80.0
        load_factor = psutil.cpu_percent() * 0.2
        return min(base_efficiency + load_factor, 95.0)
    
    def get_current_utilization(self, resource_type: ResourceType) -> Optional[float]:
        """Get current utilization for resource type."""
        if resource_type not in self.resource_history:
            return None
        
        history = self.resource_history[resource_type]
        if not history:
            return None
        
        return history[-1][1]  # Return latest value
    
    def get_resource_trend(self, resource_type: ResourceType, 
                          window_seconds: float = 60.0) -> Dict[str, float]:
        """Get resource utilization trend."""
        if resource_type not in self.resource_history:
            return {"trend": 0.0, "average": 0.0, "peak": 0.0}
        
        history = self.resource_history[resource_type]
        if len(history) < 2:
            return {"trend": 0.0, "average": 0.0, "peak": 0.0}
        
        current_time = time.time()
        recent_data = [
            (ts, value) for ts, value in history
            if current_time - ts <= window_seconds
        ]
        
        if len(recent_data) < 2:
            return {"trend": 0.0, "average": 0.0, "peak": 0.0}
        
        values = [value for _, value in recent_data]
        times = [ts for ts, _ in recent_data]
        
        # Calculate trend (simple linear regression slope)
        n = len(values)
        sum_xy = sum(t * v for t, v in zip(times, values))
        sum_x = sum(times)
        sum_y = sum(values)
        sum_x2 = sum(t * t for t in times)
        
        if n * sum_x2 - sum_x * sum_x != 0:
            trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            trend = 0.0
        
        return {
            "trend": trend,
            "average": statistics.mean(values),
            "peak": max(values),
            "min": min(values)
        }
    
    def predict_resource_usage(self, resource_type: ResourceType, 
                             future_seconds: float = 60.0) -> Dict[str, float]:
        """Predict future resource usage."""
        trend_data = self.get_resource_trend(resource_type)
        current_usage = self.get_current_utilization(resource_type) or 0.0
        
        # Simple linear extrapolation
        predicted_usage = current_usage + (trend_data["trend"] * future_seconds)
        predicted_usage = max(0.0, min(predicted_usage, 100.0))
        
        # Calculate confidence based on trend stability
        confidence = max(0.5, 1.0 - abs(trend_data["trend"]) * 10)
        
        return {
            "predicted_usage": predicted_usage,
            "confidence": confidence,
            "current_trend": trend_data["trend"]
        }


class AdaptiveOptimizer:
    """Adaptive optimization engine for performance tuning."""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.resource_monitor = ResourceMonitor()
        self.performance_history: deque = deque(maxlen=1000)
        self.optimization_parameters: Dict[str, Any] = {}
        self.active_optimizations: Set[str] = set()
        self._initialize_parameters()
        
    def _initialize_parameters(self):
        """Initialize optimization parameters."""
        self.optimization_parameters = {
            # Batch processing parameters
            "batch_size": 4,
            "batch_timeout_ms": 5000,
            "dynamic_batching": True,
            
            # Resource allocation parameters
            "max_concurrent_tasks": 6,
            "thread_pool_size": 8,
            "process_pool_size": 4,
            
            # Processing mode parameters
            "neuromorphic_threshold": 0.8,
            "quantum_threshold": 0.75,
            "fallback_threshold": 0.6,
            
            # Memory management
            "max_memory_per_task_mb": 512,
            "garbage_collection_interval": 30,
            "cache_size_limit": 1000,
            
            # Quality vs speed tradeoffs
            "accuracy_vs_speed_ratio": 0.7,
            "preprocessing_level": 2,  # 1=basic, 2=standard, 3=intensive
            "postprocessing_level": 2,
            
            # Adaptive parameters
            "learning_rate": 0.05,
            "exploration_rate": 0.1,
            "convergence_threshold": 0.001
        }
    
    async def start_optimization(self):
        """Start the optimization engine."""
        logger.info(f"Starting adaptive optimizer with strategy: {self.config.strategy.value}")
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())
        
        # Start optimization loop
        optimization_task = asyncio.create_task(self._optimization_loop())
        
        return monitor_task, optimization_task
    
    async def stop_optimization(self):
        """Stop the optimization engine."""
        self.resource_monitor.stop_monitoring()
        logger.info("Stopped adaptive optimizer")
    
    async def _optimization_loop(self):
        """Main optimization loop."""
        while self.resource_monitor.monitoring_active:
            try:
                await self._perform_optimization_cycle()
                await asyncio.sleep(self.config.optimization_interval)
            except Exception as e:
                logger.error(f"Optimization cycle failed: {e}")
                await asyncio.sleep(10.0)  # Wait before retrying
    
    async def _perform_optimization_cycle(self):
        """Perform single optimization cycle."""
        logger.debug("Performing optimization cycle")
        
        # Collect current performance metrics
        current_metrics = await self._collect_performance_metrics()
        self.performance_history.append(current_metrics)
        
        # Analyze performance trends
        performance_analysis = self._analyze_performance_trends()
        
        # Determine optimization actions
        optimization_actions = self._determine_optimization_actions(
            current_metrics, performance_analysis
        )
        
        # Apply optimizations
        await self._apply_optimizations(optimization_actions)
        
        # Log optimization results
        self._log_optimization_results(current_metrics, optimization_actions)
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive performance metrics."""
        metrics = PerformanceMetrics()
        
        # System resource metrics
        metrics.cpu_utilization = self.resource_monitor.get_current_utilization(ResourceType.CPU) or 0.0
        metrics.memory_utilization = self.resource_monitor.get_current_utilization(ResourceType.MEMORY) or 0.0
        metrics.gpu_utilization = self.resource_monitor.get_current_utilization(ResourceType.GPU) or 0.0
        
        # Processing-specific metrics
        metrics.quantum_coherence_time = self.resource_monitor.get_current_utilization(
            ResourceType.QUANTUM_COHERENCE
        ) or 0.0
        metrics.neuromorphic_spike_efficiency = self.resource_monitor.get_current_utilization(
            ResourceType.NEUROMORPHIC_SPIKES
        ) or 0.0
        
        # Calculate throughput and latency from recent history
        if len(self.performance_history) >= 2:
            recent_metrics = list(self.performance_history)[-10:]  # Last 10 cycles
            metrics.throughput_docs_per_second = statistics.mean([
                m.throughput_docs_per_second for m in recent_metrics if m.throughput_docs_per_second > 0
            ]) if any(m.throughput_docs_per_second > 0 for m in recent_metrics) else 0.0
            
            metrics.average_latency_ms = statistics.mean([
                m.average_latency_ms for m in recent_metrics if m.average_latency_ms > 0
            ]) if any(m.average_latency_ms > 0 for m in recent_metrics) else 0.0
        
        # Estimate energy consumption based on resource utilization
        metrics.energy_consumption_watts = (
            metrics.cpu_utilization * 0.3 +  # CPU power
            metrics.memory_utilization * 0.1 +  # Memory power  
            metrics.gpu_utilization * 0.5  # GPU power
        )
        
        # Default accuracy and error rate (would be measured from actual processing)
        metrics.accuracy_score = 0.85
        metrics.error_rate = 0.05
        
        return metrics
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(self.performance_history) < 10:
            return {"insufficient_data": True}
        
        recent_metrics = list(self.performance_history)[-20:]  # Last 20 cycles
        
        # Calculate trends
        throughput_values = [m.throughput_docs_per_second for m in recent_metrics]
        latency_values = [m.average_latency_ms for m in recent_metrics]
        cpu_values = [m.cpu_utilization for m in recent_metrics]
        memory_values = [m.memory_utilization for m in recent_metrics]
        
        analysis = {
            "throughput_trend": self._calculate_trend(throughput_values),
            "latency_trend": self._calculate_trend(latency_values),
            "cpu_trend": self._calculate_trend(cpu_values),
            "memory_trend": self._calculate_trend(memory_values),
            "performance_score_trend": self._calculate_trend([
                m.overall_performance_score() for m in recent_metrics
            ]),
            "bottleneck_indicators": self._identify_bottlenecks(recent_metrics),
            "stability_score": self._calculate_stability_score(recent_metrics)
        }
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend statistics for a series of values."""
        if len(values) < 3:
            return {"slope": 0.0, "direction": "stable", "confidence": 0.0}
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        sum_xy = sum(i * v for i, v in zip(x, values))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_x2 = sum(i * i for i in x)
        
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            slope = 0.0
        
        # Determine direction and confidence
        if abs(slope) < 0.001:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # Confidence based on R-squared
        mean_y = sum_y / n
        ss_tot = sum((v - mean_y) ** 2 for v in values)
        intercept = (sum_y - slope * sum_x) / n
        ss_res = sum((v - (slope * i + intercept)) ** 2 for i, v in zip(x, values))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            "slope": slope,
            "direction": direction,
            "confidence": max(0.0, min(r_squared, 1.0))
        }
    
    def _identify_bottlenecks(self, metrics_history: List[PerformanceMetrics]) -> List[str]:
        """Identify system bottlenecks."""
        bottlenecks = []
        
        # Check resource utilization patterns
        avg_cpu = statistics.mean([m.cpu_utilization for m in metrics_history])
        avg_memory = statistics.mean([m.memory_utilization for m in metrics_history])
        avg_gpu = statistics.mean([m.gpu_utilization for m in metrics_history])
        
        if avg_cpu > 85:
            bottlenecks.append("cpu_bound")
        if avg_memory > 85:
            bottlenecks.append("memory_bound")
        if avg_gpu > 85:
            bottlenecks.append("gpu_bound")
        
        # Check processing efficiency
        avg_throughput = statistics.mean([
            m.throughput_docs_per_second for m in metrics_history 
            if m.throughput_docs_per_second > 0
        ]) if any(m.throughput_docs_per_second > 0 for m in metrics_history) else 0
        
        if avg_throughput < 1.0:
            bottlenecks.append("processing_throughput")
        
        # Check latency issues
        avg_latency = statistics.mean([
            m.average_latency_ms for m in metrics_history 
            if m.average_latency_ms > 0
        ]) if any(m.average_latency_ms > 0 for m in metrics_history) else 0
        
        if avg_latency > self.config.max_latency_ms:
            bottlenecks.append("high_latency")
        
        return bottlenecks
    
    def _calculate_stability_score(self, metrics_history: List[PerformanceMetrics]) -> float:
        """Calculate system stability score."""
        if len(metrics_history) < 3:
            return 0.5
        
        # Calculate coefficient of variation for key metrics
        performance_scores = [m.overall_performance_score() for m in metrics_history]
        
        if not performance_scores:
            return 0.5
        
        mean_score = statistics.mean(performance_scores)
        if mean_score == 0:
            return 0.0
        
        stdev_score = statistics.stdev(performance_scores)
        cv = stdev_score / mean_score
        
        # Convert to stability score (lower CV = higher stability)
        stability = max(0.0, 1.0 - cv)
        
        return stability
    
    def _determine_optimization_actions(self, current_metrics: PerformanceMetrics,
                                      analysis: Dict[str, Any]) -> List[str]:
        """Determine optimization actions based on analysis."""
        actions = []
        
        if analysis.get("insufficient_data"):
            return ["collect_more_data"]
        
        # Strategy-specific optimizations
        if self.config.strategy == OptimizationStrategy.THROUGHPUT_MAXIMIZATION:
            actions.extend(self._throughput_optimizations(current_metrics, analysis))
        elif self.config.strategy == OptimizationStrategy.LATENCY_MINIMIZATION:
            actions.extend(self._latency_optimizations(current_metrics, analysis))
        elif self.config.strategy == OptimizationStrategy.ENERGY_EFFICIENCY:
            actions.extend(self._energy_optimizations(current_metrics, analysis))
        elif self.config.strategy == OptimizationStrategy.BALANCED_PERFORMANCE:
            actions.extend(self._balanced_optimizations(current_metrics, analysis))
        
        # Bottleneck-specific optimizations
        bottlenecks = analysis.get("bottleneck_indicators", [])
        for bottleneck in bottlenecks:
            actions.extend(self._bottleneck_optimizations(bottleneck, current_metrics))
        
        return list(set(actions))  # Remove duplicates
    
    def _throughput_optimizations(self, metrics: PerformanceMetrics, 
                                analysis: Dict[str, Any]) -> List[str]:
        """Optimizations for maximizing throughput."""
        actions = []
        
        if metrics.throughput_docs_per_second < self.config.target_throughput:
            actions.extend([
                "increase_batch_size",
                "increase_concurrent_tasks",
                "enable_parallel_processing",
                "optimize_preprocessing"
            ])
        
        if analysis["throughput_trend"]["direction"] == "decreasing":
            actions.extend([
                "reset_caches",
                "garbage_collect",
                "rebalance_load"
            ])
        
        return actions
    
    def _latency_optimizations(self, metrics: PerformanceMetrics,
                             analysis: Dict[str, Any]) -> List[str]:
        """Optimizations for minimizing latency.""" 
        actions = []
        
        if metrics.average_latency_ms > self.config.max_latency_ms:
            actions.extend([
                "reduce_batch_size",
                "increase_preprocessing_threads",
                "enable_fast_mode",
                "reduce_accuracy_for_speed"
            ])
        
        if analysis["latency_trend"]["direction"] == "increasing":
            actions.extend([
                "clear_processing_queues",
                "restart_slow_processors",
                "switch_to_faster_algorithm"
            ])
        
        return actions
    
    def _energy_optimizations(self, metrics: PerformanceMetrics,
                            analysis: Dict[str, Any]) -> List[str]:
        """Optimizations for energy efficiency."""
        actions = []
        
        if metrics.energy_consumption_watts > self.config.max_energy_watts:
            actions.extend([
                "reduce_cpu_frequency",
                "enable_power_saving_mode",
                "reduce_parallel_processing",
                "optimize_algorithm_efficiency"
            ])
        
        return actions
    
    def _balanced_optimizations(self, metrics: PerformanceMetrics,
                              analysis: Dict[str, Any]) -> List[str]:
        """Balanced optimization approach."""
        actions = []
        
        performance_score = metrics.overall_performance_score()
        
        if performance_score < 0.7:
            # Focus on biggest improvement opportunities
            if metrics.throughput_docs_per_second < 2.0:
                actions.append("moderate_batch_increase")
            if metrics.average_latency_ms > 10000:
                actions.append("latency_optimization")
            if metrics.energy_consumption_watts > 30:
                actions.append("energy_optimization")
        
        stability_score = analysis.get("stability_score", 0.5)
        if stability_score < 0.6:
            actions.extend([
                "stabilize_parameters",
                "reduce_parameter_volatility"
            ])
        
        return actions
    
    def _bottleneck_optimizations(self, bottleneck: str,
                                metrics: PerformanceMetrics) -> List[str]:
        """Optimizations for specific bottlenecks."""
        bottleneck_actions = {
            "cpu_bound": [
                "reduce_cpu_intensive_operations",
                "increase_process_pool_size",
                "enable_cpu_affinity_optimization"
            ],
            "memory_bound": [
                "reduce_batch_size",
                "enable_streaming_mode",
                "increase_garbage_collection_frequency",
                "optimize_memory_usage"
            ],
            "gpu_bound": [
                "reduce_gpu_batch_size",
                "optimize_gpu_memory_usage", 
                "balance_cpu_gpu_workload"
            ],
            "processing_throughput": [
                "optimize_algorithm_selection",
                "enable_caching",
                "parallelize_processing_pipeline"
            ],
            "high_latency": [
                "reduce_processing_complexity",
                "enable_early_termination",
                "optimize_critical_path"
            ]
        }
        
        return bottleneck_actions.get(bottleneck, [])
    
    async def _apply_optimizations(self, actions: List[str]):
        """Apply optimization actions."""
        for action in actions:
            try:
                await self._execute_optimization_action(action)
                self.active_optimizations.add(action)
                logger.debug(f"Applied optimization: {action}")
            except Exception as e:
                logger.warning(f"Failed to apply optimization {action}: {e}")
    
    async def _execute_optimization_action(self, action: str):
        """Execute specific optimization action."""
        if action == "increase_batch_size":
            current_size = self.optimization_parameters["batch_size"]
            self.optimization_parameters["batch_size"] = min(current_size + 2, 16)
            
        elif action == "decrease_batch_size":
            current_size = self.optimization_parameters["batch_size"]
            self.optimization_parameters["batch_size"] = max(current_size - 1, 1)
            
        elif action == "increase_concurrent_tasks":
            current_tasks = self.optimization_parameters["max_concurrent_tasks"]
            self.optimization_parameters["max_concurrent_tasks"] = min(current_tasks + 2, 12)
            
        elif action == "reduce_concurrent_tasks":
            current_tasks = self.optimization_parameters["max_concurrent_tasks"]
            self.optimization_parameters["max_concurrent_tasks"] = max(current_tasks - 1, 2)
            
        elif action == "enable_fast_mode":
            self.optimization_parameters["preprocessing_level"] = 1
            self.optimization_parameters["accuracy_vs_speed_ratio"] = 0.3
            
        elif action == "enable_quality_mode":
            self.optimization_parameters["preprocessing_level"] = 3
            self.optimization_parameters["accuracy_vs_speed_ratio"] = 0.9
            
        elif action == "garbage_collect":
            import gc
            gc.collect()
            
        elif action == "reset_caches":
            # Would reset actual caches in real implementation
            pass
            
        elif action == "optimize_memory_usage":
            self.optimization_parameters["max_memory_per_task_mb"] = min(
                self.optimization_parameters["max_memory_per_task_mb"] - 64, 128
            )
            
        # Add more optimization actions as needed
        logger.debug(f"Executed optimization action: {action}")
    
    def _log_optimization_results(self, metrics: PerformanceMetrics, actions: List[str]):
        """Log optimization results."""
        if actions:
            logger.info(f"Applied {len(actions)} optimizations: {actions}")
            logger.info(f"Current performance score: {metrics.overall_performance_score():.3f}")
            logger.debug(f"Throughput: {metrics.throughput_docs_per_second:.2f} docs/s, "
                        f"Latency: {metrics.average_latency_ms:.0f}ms, "
                        f"Energy: {metrics.energy_consumption_watts:.1f}W")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        if not self.performance_history:
            return {"status": "no_data"}
        
        latest_metrics = self.performance_history[-1]
        
        return {
            "strategy": self.config.strategy.value,
            "active_optimizations": list(self.active_optimizations),
            "current_parameters": self.optimization_parameters.copy(),
            "performance_score": latest_metrics.overall_performance_score(),
            "metrics_summary": {
                "throughput": latest_metrics.throughput_docs_per_second,
                "latency_ms": latest_metrics.average_latency_ms,
                "cpu_util": latest_metrics.cpu_utilization,
                "memory_util": latest_metrics.memory_utilization,
                "energy_watts": latest_metrics.energy_consumption_watts
            },
            "resource_trends": {
                ResourceType.CPU.value: self.resource_monitor.get_resource_trend(ResourceType.CPU),
                ResourceType.MEMORY.value: self.resource_monitor.get_resource_trend(ResourceType.MEMORY)
            }
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations for manual review."""
        if not self.performance_history:
            return []
        
        recommendations = []
        latest_metrics = self.performance_history[-1]
        performance_score = latest_metrics.overall_performance_score()
        
        if performance_score < 0.6:
            recommendations.append({
                "priority": "high",
                "category": "performance",
                "title": "Poor Overall Performance",
                "description": f"Current performance score is {performance_score:.2f}",
                "suggested_actions": ["Review system resources", "Consider scaling up", "Optimize algorithms"]
            })
        
        if latest_metrics.average_latency_ms > self.config.max_latency_ms:
            recommendations.append({
                "priority": "high",
                "category": "latency",
                "title": "High Processing Latency",
                "description": f"Average latency {latest_metrics.average_latency_ms:.0f}ms exceeds target {self.config.max_latency_ms:.0f}ms",
                "suggested_actions": ["Reduce batch sizes", "Increase parallel processing", "Optimize critical path"]
            })
        
        if latest_metrics.energy_consumption_watts > self.config.max_energy_watts:
            recommendations.append({
                "priority": "medium",
                "category": "energy",
                "title": "High Energy Consumption",
                "description": f"Energy usage {latest_metrics.energy_consumption_watts:.1f}W exceeds target {self.config.max_energy_watts:.1f}W",
                "suggested_actions": ["Enable power saving modes", "Reduce processing intensity", "Optimize algorithms"]
            })
        
        return recommendations


# Global optimizer instance
_optimizer: Optional[AdaptiveOptimizer] = None


def get_optimizer(config: OptimizationConfig = None) -> AdaptiveOptimizer:
    """Get or create global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        if config is None:
            config = OptimizationConfig()
        _optimizer = AdaptiveOptimizer(config)
    return _optimizer


async def start_performance_optimization(strategy: OptimizationStrategy = OptimizationStrategy.BALANCED_PERFORMANCE):
    """Start performance optimization with specified strategy."""
    config = OptimizationConfig(strategy=strategy)
    optimizer = get_optimizer(config)
    
    monitor_task, optimization_task = await optimizer.start_optimization()
    
    logger.info(f"Performance optimization started with strategy: {strategy.value}")
    
    return optimizer, monitor_task, optimization_task


async def stop_performance_optimization():
    """Stop performance optimization."""
    global _optimizer
    if _optimizer:
        await _optimizer.stop_optimization()
        logger.info("Performance optimization stopped")


def get_performance_status() -> Dict[str, Any]:
    """Get current performance optimization status."""
    global _optimizer
    if _optimizer:
        return _optimizer.get_optimization_status()
    else:
        return {"status": "not_running"}


def get_performance_recommendations() -> List[Dict[str, Any]]:
    """Get performance optimization recommendations."""
    global _optimizer
    if _optimizer:
        return _optimizer.get_optimization_recommendations()
    else:
        return []