"""
Real-Time Performance Monitoring with Intelligent Bottleneck Detection and Optimization.

This module provides comprehensive real-time performance monitoring, bottleneck detection,
automated optimization recommendations, and predictive performance analytics for the
distributed contract extraction system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
import concurrent.futures

import numpy as np
import psutil

logger = logging.getLogger(__name__)

# Try to import additional monitoring libraries
try:
    import prometheus_client
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    prometheus_client = None


class PerformanceMetricType(Enum):
    """Types of performance metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    GPU_UTILIZATION = "gpu_utilization"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    CACHE_HIT_RATE = "cache_hit_rate"
    CONCURRENT_REQUESTS = "concurrent_requests"
    RESPONSE_SIZE = "response_size"


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    GPU_BOUND = "gpu_bound"
    CACHE_BOUND = "cache_bound"
    CONCURRENCY_BOUND = "concurrency_bound"
    ALGORITHM_BOUND = "algorithm_bound"
    DATABASE_BOUND = "database_bound"


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""
    SCALE_HORIZONTALLY = "scale_horizontally"
    SCALE_VERTICALLY = "scale_vertically"
    OPTIMIZE_ALGORITHM = "optimize_algorithm"
    INCREASE_CACHE = "increase_cache"
    REDUCE_BATCH_SIZE = "reduce_batch_size"
    INCREASE_BATCH_SIZE = "increase_batch_size"
    ENABLE_COMPRESSION = "enable_compression"
    OPTIMIZE_QUERIES = "optimize_queries"
    INCREASE_PARALLELISM = "increase_parallelism"
    REDUCE_PARALLELISM = "reduce_parallelism"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_id: str
    metric_type: PerformanceMetricType
    value: float
    timestamp: float
    component: str
    operation: str
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BottleneckDetection:
    """Bottleneck detection result."""
    detection_id: str
    bottleneck_type: BottleneckType
    component: str
    severity: AlertSeverity
    confidence: float
    description: str
    affected_metrics: List[str]
    root_cause_analysis: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    duration_seconds: float = 0.0


@dataclass
class PerformanceAlert:
    """Performance alert."""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    component: str
    metric_type: PerformanceMetricType
    current_value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    recommendation_id: str
    strategy: OptimizationStrategy
    component: str
    description: str
    expected_improvement: float
    implementation_effort: str  # 'low', 'medium', 'high'
    risk_level: str  # 'low', 'medium', 'high'
    estimated_cost: float
    priority_score: float
    implementation_steps: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""
    component: str
    metric_type: PerformanceMetricType
    baseline_value: float
    acceptable_deviation: float
    measurement_window: int  # minutes
    confidence_level: float
    last_updated: float = field(default_factory=time.time)


class MetricCollector:
    """Real-time metric collection system."""
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.is_collecting = False
        
        # Metric storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.latest_metrics: Dict[str, PerformanceMetric] = {}
        
        # System monitoring
        self.system_metrics_enabled = True
        self.application_metrics_enabled = True
        
        # Prometheus integration
        if HAS_PROMETHEUS:
            self.prometheus_registry = prometheus_client.CollectorRegistry()
            self.prometheus_metrics = {}
            self._setup_prometheus_metrics()
        
        self.lock = threading.RLock()
        self.collection_task: Optional[asyncio.Task] = None
    
    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics."""
        if not HAS_PROMETHEUS:
            return
        
        try:
            # Create Prometheus metrics
            self.prometheus_metrics = {
                'latency': prometheus_client.Histogram(
                    'operation_latency_seconds',
                    'Operation latency in seconds',
                    ['component', 'operation'],
                    registry=self.prometheus_registry
                ),
                'throughput': prometheus_client.Counter(
                    'operations_total',
                    'Total number of operations',
                    ['component', 'operation', 'status'],
                    registry=self.prometheus_registry
                ),
                'resource_utilization': prometheus_client.Gauge(
                    'resource_utilization_percent',
                    'Resource utilization percentage',
                    ['resource_type', 'component'],
                    registry=self.prometheus_registry
                ),
                'error_rate': prometheus_client.Counter(
                    'errors_total',
                    'Total number of errors',
                    ['component', 'error_type'],
                    registry=self.prometheus_registry
                )
            }
        except Exception as e:
            logger.error(f"Failed to setup Prometheus metrics: {e}")
    
    async def start_collection(self) -> None:
        """Start metric collection."""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Started metric collection")
    
    async def stop_collection(self) -> None:
        """Stop metric collection."""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped metric collection")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self.is_collecting:
            try:
                await asyncio.gather(
                    self._collect_system_metrics(),
                    self._collect_application_metrics(),
                    return_exceptions=True
                )
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Metric collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        if not self.system_metrics_enabled:
            return
        
        try:
            current_time = time.time()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_metric = PerformanceMetric(
                metric_id=f"cpu_{int(current_time * 1000)}",
                metric_type=PerformanceMetricType.CPU_UTILIZATION,
                value=cpu_percent,
                timestamp=current_time,
                component="system",
                operation="cpu_monitoring"
            )
            await self.record_metric(cpu_metric)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_metric = PerformanceMetric(
                metric_id=f"memory_{int(current_time * 1000)}",
                metric_type=PerformanceMetricType.MEMORY_UTILIZATION,
                value=memory.percent,
                timestamp=current_time,
                component="system",
                operation="memory_monitoring"
            )
            await self.record_metric(memory_metric)
            
            # Network I/O metrics
            network_io = psutil.net_io_counters()
            if hasattr(network_io, 'bytes_sent') and hasattr(network_io, 'bytes_recv'):
                # Calculate network throughput (simplified)
                network_throughput = (network_io.bytes_sent + network_io.bytes_recv) / 1024 / 1024  # MB/s
                network_metric = PerformanceMetric(
                    metric_id=f"network_{int(current_time * 1000)}",
                    metric_type=PerformanceMetricType.NETWORK_IO,
                    value=network_throughput,
                    timestamp=current_time,
                    component="system",
                    operation="network_monitoring"
                )
                await self.record_metric(network_metric)
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # Calculate disk throughput (simplified)
                disk_throughput = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024  # MB/s
                disk_metric = PerformanceMetric(
                    metric_id=f"disk_{int(current_time * 1000)}",
                    metric_type=PerformanceMetricType.DISK_IO,
                    value=disk_throughput,
                    timestamp=current_time,
                    component="system",
                    operation="disk_monitoring"
                )
                await self.record_metric(disk_metric)
            
        except Exception as e:
            logger.error(f"System metric collection failed: {e}")
    
    async def _collect_application_metrics(self) -> None:
        """Collect application-specific metrics."""
        if not self.application_metrics_enabled:
            return
        
        try:
            current_time = time.time()
            
            # Simulate application metrics collection
            # In practice, these would come from the actual application
            
            # Queue depth metric (simulated)
            queue_depth = len(asyncio.all_tasks()) if hasattr(asyncio, 'all_tasks') else 0
            queue_metric = PerformanceMetric(
                metric_id=f"queue_{int(current_time * 1000)}",
                metric_type=PerformanceMetricType.QUEUE_DEPTH,
                value=float(queue_depth),
                timestamp=current_time,
                component="application",
                operation="queue_monitoring"
            )
            await self.record_metric(queue_metric)
            
            # Concurrent requests (simulated)
            concurrent_requests = min(queue_depth, 100)  # Cap at 100
            concurrent_metric = PerformanceMetric(
                metric_id=f"concurrent_{int(current_time * 1000)}",
                metric_type=PerformanceMetricType.CONCURRENT_REQUESTS,
                value=float(concurrent_requests),
                timestamp=current_time,
                component="application",
                operation="concurrency_monitoring"
            )
            await self.record_metric(concurrent_metric)
            
        except Exception as e:
            logger.error(f"Application metric collection failed: {e}")
    
    async def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        try:
            with self.lock:
                # Store in memory
                metric_key = f"{metric.component}:{metric.metric_type.value}:{metric.operation}"
                self.metrics[metric_key].append(metric)
                self.latest_metrics[metric_key] = metric
            
            # Update Prometheus metrics if available
            if HAS_PROMETHEUS and hasattr(self, 'prometheus_metrics'):
                await self._update_prometheus_metric(metric)
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    async def _update_prometheus_metric(self, metric: PerformanceMetric) -> None:
        """Update Prometheus metric."""
        try:
            labels = {
                'component': metric.component,
                'operation': metric.operation,
                **metric.labels
            }
            
            if metric.metric_type == PerformanceMetricType.LATENCY:
                if 'latency' in self.prometheus_metrics:
                    self.prometheus_metrics['latency'].labels(**labels).observe(metric.value)
            
            elif metric.metric_type == PerformanceMetricType.THROUGHPUT:
                if 'throughput' in self.prometheus_metrics:
                    self.prometheus_metrics['throughput'].labels(status='success', **labels).inc(metric.value)
            
            elif metric.metric_type in [PerformanceMetricType.CPU_UTILIZATION, 
                                       PerformanceMetricType.MEMORY_UTILIZATION]:
                if 'resource_utilization' in self.prometheus_metrics:
                    resource_type = 'cpu' if metric.metric_type == PerformanceMetricType.CPU_UTILIZATION else 'memory'
                    self.prometheus_metrics['resource_utilization'].labels(
                        resource_type=resource_type, 
                        component=metric.component
                    ).set(metric.value)
            
        except Exception as e:
            logger.error(f"Prometheus metric update failed: {e}")
    
    def get_metrics(self, metric_key: str, since: Optional[float] = None, limit: Optional[int] = None) -> List[PerformanceMetric]:
        """Get metrics for a specific key."""
        with self.lock:
            if metric_key not in self.metrics:
                return []
            
            metrics = list(self.metrics[metric_key])
            
            # Filter by timestamp if specified
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            # Apply limit if specified
            if limit:
                metrics = metrics[-limit:]
            
            return metrics
    
    def get_latest_metric(self, metric_key: str) -> Optional[PerformanceMetric]:
        """Get the latest metric value."""
        with self.lock:
            return self.latest_metrics.get(metric_key)


class BottleneckDetector:
    """Intelligent bottleneck detection system."""
    
    def __init__(self, metric_collector: MetricCollector):
        self.metric_collector = metric_collector
        self.detection_rules: Dict[BottleneckType, Callable] = {
            BottleneckType.CPU_BOUND: self._detect_cpu_bottleneck,
            BottleneckType.MEMORY_BOUND: self._detect_memory_bottleneck,
            BottleneckType.IO_BOUND: self._detect_io_bottleneck,
            BottleneckType.NETWORK_BOUND: self._detect_network_bottleneck,
            BottleneckType.CACHE_BOUND: self._detect_cache_bottleneck,
            BottleneckType.CONCURRENCY_BOUND: self._detect_concurrency_bottleneck,
        }
        
        self.detected_bottlenecks: deque = deque(maxlen=100)
        self.active_bottlenecks: Dict[str, BottleneckDetection] = {}
        
        self.detection_thresholds = {
            'cpu_high': 85.0,
            'memory_high': 90.0,
            'io_high': 80.0,
            'network_high': 80.0,
            'queue_high': 50.0,
            'latency_high': 5.0,
            'error_rate_high': 0.05  # 5%
        }
        
        self.lock = threading.RLock()
    
    async def detect_bottlenecks(self) -> List[BottleneckDetection]:
        """Detect current bottlenecks."""
        detections = []
        
        try:
            # Run all detection rules
            detection_tasks = [
                asyncio.create_task(self._run_detection_rule(bottleneck_type, rule))
                for bottleneck_type, rule in self.detection_rules.items()
            ]
            
            results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, BottleneckDetection):
                    detections.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Bottleneck detection error: {result}")
            
            # Update active bottlenecks
            with self.lock:
                for detection in detections:
                    self.detected_bottlenecks.append(detection)
                    self.active_bottlenecks[detection.detection_id] = detection
                
                # Clean up resolved bottlenecks (simplified logic)
                current_time = time.time()
                expired_keys = [
                    key for key, bottleneck in self.active_bottlenecks.items()
                    if current_time - bottleneck.timestamp > 300  # 5 minutes
                ]
                for key in expired_keys:
                    del self.active_bottlenecks[key]
            
        except Exception as e:
            logger.error(f"Bottleneck detection failed: {e}")
        
        return detections
    
    async def _run_detection_rule(self, bottleneck_type: BottleneckType, rule: Callable) -> Optional[BottleneckDetection]:
        """Run a specific detection rule."""
        try:
            return await rule()
        except Exception as e:
            logger.error(f"Detection rule {bottleneck_type} failed: {e}")
            return None
    
    async def _detect_cpu_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect CPU bottlenecks."""
        try:
            # Get recent CPU metrics
            cpu_metrics = self.metric_collector.get_metrics(
                "system:cpu_utilization:cpu_monitoring",
                since=time.time() - 300,  # Last 5 minutes
                limit=100
            )
            
            if len(cpu_metrics) < 10:
                return None
            
            # Analyze CPU utilization
            cpu_values = [m.value for m in cpu_metrics]
            avg_cpu = statistics.mean(cpu_values)
            max_cpu = max(cpu_values)
            
            # Check for sustained high CPU usage
            if avg_cpu > self.detection_thresholds['cpu_high'] and max_cpu > 95.0:
                # Calculate confidence based on consistency
                high_cpu_count = sum(1 for v in cpu_values if v > self.detection_thresholds['cpu_high'])
                confidence = high_cpu_count / len(cpu_values)
                
                if confidence > 0.7:  # 70% of samples show high CPU
                    return BottleneckDetection(
                        detection_id=f"cpu_bottleneck_{int(time.time())}",
                        bottleneck_type=BottleneckType.CPU_BOUND,
                        component="system",
                        severity=AlertSeverity.HIGH if avg_cpu > 95 else AlertSeverity.MEDIUM,
                        confidence=confidence,
                        description=f"High CPU utilization detected: avg={avg_cpu:.1f}%, max={max_cpu:.1f}%",
                        affected_metrics=["cpu_utilization"],
                        root_cause_analysis={
                            "avg_cpu": avg_cpu,
                            "max_cpu": max_cpu,
                            "samples_above_threshold": high_cpu_count,
                            "total_samples": len(cpu_values),
                            "threshold": self.detection_thresholds['cpu_high']
                        }
                    )
            
        except Exception as e:
            logger.error(f"CPU bottleneck detection failed: {e}")
        
        return None
    
    async def _detect_memory_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect memory bottlenecks."""
        try:
            # Get recent memory metrics
            memory_metrics = self.metric_collector.get_metrics(
                "system:memory_utilization:memory_monitoring",
                since=time.time() - 300,
                limit=100
            )
            
            if len(memory_metrics) < 10:
                return None
            
            memory_values = [m.value for m in memory_metrics]
            avg_memory = statistics.mean(memory_values)
            max_memory = max(memory_values)
            
            if avg_memory > self.detection_thresholds['memory_high']:
                confidence = sum(1 for v in memory_values if v > self.detection_thresholds['memory_high']) / len(memory_values)
                
                if confidence > 0.6:
                    return BottleneckDetection(
                        detection_id=f"memory_bottleneck_{int(time.time())}",
                        bottleneck_type=BottleneckType.MEMORY_BOUND,
                        component="system",
                        severity=AlertSeverity.CRITICAL if avg_memory > 95 else AlertSeverity.HIGH,
                        confidence=confidence,
                        description=f"High memory utilization detected: avg={avg_memory:.1f}%, max={max_memory:.1f}%",
                        affected_metrics=["memory_utilization"],
                        root_cause_analysis={
                            "avg_memory": avg_memory,
                            "max_memory": max_memory,
                            "threshold": self.detection_thresholds['memory_high']
                        }
                    )
            
        except Exception as e:
            logger.error(f"Memory bottleneck detection failed: {e}")
        
        return None
    
    async def _detect_io_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect I/O bottlenecks."""
        try:
            # Get disk I/O metrics
            disk_metrics = self.metric_collector.get_metrics(
                "system:disk_io:disk_monitoring",
                since=time.time() - 300,
                limit=100
            )
            
            if len(disk_metrics) < 10:
                return None
            
            disk_values = [m.value for m in disk_metrics]
            avg_disk_io = statistics.mean(disk_values)
            max_disk_io = max(disk_values)
            
            # Simple I/O bottleneck detection based on high sustained I/O
            if avg_disk_io > self.detection_thresholds['io_high']:
                return BottleneckDetection(
                    detection_id=f"io_bottleneck_{int(time.time())}",
                    bottleneck_type=BottleneckType.IO_BOUND,
                    component="system",
                    severity=AlertSeverity.MEDIUM,
                    confidence=0.7,
                    description=f"High disk I/O detected: avg={avg_disk_io:.1f} MB/s",
                    affected_metrics=["disk_io"],
                    root_cause_analysis={
                        "avg_disk_io": avg_disk_io,
                        "max_disk_io": max_disk_io
                    }
                )
            
        except Exception as e:
            logger.error(f"I/O bottleneck detection failed: {e}")
        
        return None
    
    async def _detect_network_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect network bottlenecks."""
        try:
            network_metrics = self.metric_collector.get_metrics(
                "system:network_io:network_monitoring",
                since=time.time() - 300,
                limit=100
            )
            
            if len(network_metrics) < 10:
                return None
            
            network_values = [m.value for m in network_metrics]
            avg_network_io = statistics.mean(network_values)
            
            if avg_network_io > self.detection_thresholds['network_high']:
                return BottleneckDetection(
                    detection_id=f"network_bottleneck_{int(time.time())}",
                    bottleneck_type=BottleneckType.NETWORK_BOUND,
                    component="system",
                    severity=AlertSeverity.MEDIUM,
                    confidence=0.6,
                    description=f"High network I/O detected: avg={avg_network_io:.1f} MB/s",
                    affected_metrics=["network_io"],
                    root_cause_analysis={
                        "avg_network_io": avg_network_io
                    }
                )
            
        except Exception as e:
            logger.error(f"Network bottleneck detection failed: {e}")
        
        return None
    
    async def _detect_cache_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect cache-related bottlenecks."""
        try:
            # This would typically analyze cache hit rates, cache miss penalties, etc.
            # For now, simulate cache bottleneck detection
            
            # In a real implementation, you would check:
            # - Cache hit rates below acceptable thresholds
            # - High cache miss penalties
            # - Memory pressure affecting cache efficiency
            
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Cache bottleneck detection failed: {e}")
        
        return None
    
    async def _detect_concurrency_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect concurrency bottlenecks."""
        try:
            # Get queue depth metrics
            queue_metrics = self.metric_collector.get_metrics(
                "application:queue_depth:queue_monitoring",
                since=time.time() - 300,
                limit=100
            )
            
            concurrent_metrics = self.metric_collector.get_metrics(
                "application:concurrent_requests:concurrency_monitoring",
                since=time.time() - 300,
                limit=100
            )
            
            if len(queue_metrics) < 5 or len(concurrent_metrics) < 5:
                return None
            
            avg_queue_depth = statistics.mean([m.value for m in queue_metrics])
            avg_concurrent = statistics.mean([m.value for m in concurrent_metrics])
            
            # Detect if queue is consistently high
            if avg_queue_depth > self.detection_thresholds['queue_high']:
                return BottleneckDetection(
                    detection_id=f"concurrency_bottleneck_{int(time.time())}",
                    bottleneck_type=BottleneckType.CONCURRENCY_BOUND,
                    component="application",
                    severity=AlertSeverity.MEDIUM,
                    confidence=0.8,
                    description=f"High queue depth detected: avg={avg_queue_depth:.1f}, concurrent={avg_concurrent:.1f}",
                    affected_metrics=["queue_depth", "concurrent_requests"],
                    root_cause_analysis={
                        "avg_queue_depth": avg_queue_depth,
                        "avg_concurrent": avg_concurrent,
                        "queue_threshold": self.detection_thresholds['queue_high']
                    }
                )
            
        except Exception as e:
            logger.error(f"Concurrency bottleneck detection failed: {e}")
        
        return None
    
    def get_active_bottlenecks(self) -> List[BottleneckDetection]:
        """Get currently active bottlenecks."""
        with self.lock:
            return list(self.active_bottlenecks.values())


class PerformanceOptimizer:
    """Performance optimization recommendation engine."""
    
    def __init__(self, bottleneck_detector: BottleneckDetector):
        self.bottleneck_detector = bottleneck_detector
        self.optimization_strategies: Dict[BottleneckType, List[OptimizationStrategy]] = {
            BottleneckType.CPU_BOUND: [
                OptimizationStrategy.SCALE_HORIZONTALLY,
                OptimizationStrategy.OPTIMIZE_ALGORITHM,
                OptimizationStrategy.INCREASE_PARALLELISM
            ],
            BottleneckType.MEMORY_BOUND: [
                OptimizationStrategy.SCALE_VERTICALLY,
                OptimizationStrategy.INCREASE_CACHE,
                OptimizationStrategy.OPTIMIZE_ALGORITHM
            ],
            BottleneckType.IO_BOUND: [
                OptimizationStrategy.ENABLE_COMPRESSION,
                OptimizationStrategy.INCREASE_CACHE,
                OptimizationStrategy.OPTIMIZE_QUERIES
            ],
            BottleneckType.CONCURRENCY_BOUND: [
                OptimizationStrategy.INCREASE_PARALLELISM,
                OptimizationStrategy.SCALE_HORIZONTALLY,
                OptimizationStrategy.OPTIMIZE_ALGORITHM
            ],
            BottleneckType.CACHE_BOUND: [
                OptimizationStrategy.INCREASE_CACHE,
                OptimizationStrategy.OPTIMIZE_ALGORITHM,
                OptimizationStrategy.ENABLE_COMPRESSION
            ]
        }
        
        self.recommendations: deque = deque(maxlen=100)
    
    async def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on detected bottlenecks."""
        recommendations = []
        
        try:
            active_bottlenecks = self.bottleneck_detector.get_active_bottlenecks()
            
            for bottleneck in active_bottlenecks:
                bottleneck_recommendations = await self._generate_bottleneck_recommendations(bottleneck)
                recommendations.extend(bottleneck_recommendations)
            
            # Sort by priority score
            recommendations.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Store recommendations
            for rec in recommendations:
                self.recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    async def _generate_bottleneck_recommendations(self, bottleneck: BottleneckDetection) -> List[OptimizationRecommendation]:
        """Generate recommendations for a specific bottleneck."""
        recommendations = []
        
        try:
            strategies = self.optimization_strategies.get(bottleneck.bottleneck_type, [])
            
            for strategy in strategies:
                rec = await self._create_recommendation(bottleneck, strategy)
                if rec:
                    recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Bottleneck recommendation generation failed: {e}")
        
        return recommendations
    
    async def _create_recommendation(self, bottleneck: BottleneckDetection, strategy: OptimizationStrategy) -> Optional[OptimizationRecommendation]:
        """Create a specific optimization recommendation."""
        try:
            # Calculate priority score
            severity_multiplier = {
                AlertSeverity.CRITICAL: 1.0,
                AlertSeverity.HIGH: 0.8,
                AlertSeverity.MEDIUM: 0.6,
                AlertSeverity.LOW: 0.4
            }
            
            priority_score = (bottleneck.confidence * severity_multiplier.get(bottleneck.severity, 0.5) * 100)
            
            # Strategy-specific recommendation details
            if strategy == OptimizationStrategy.SCALE_HORIZONTALLY:
                return OptimizationRecommendation(
                    recommendation_id=f"scale_h_{int(time.time())}",
                    strategy=strategy,
                    component=bottleneck.component,
                    description=f"Scale horizontally to address {bottleneck.bottleneck_type.value} bottleneck",
                    expected_improvement=30.0,
                    implementation_effort="medium",
                    risk_level="low",
                    estimated_cost=100.0,
                    priority_score=priority_score,
                    implementation_steps=[
                        "Analyze current scaling configuration",
                        "Add additional worker instances",
                        "Configure load balancing",
                        "Monitor performance impact"
                    ]
                )
            
            elif strategy == OptimizationStrategy.SCALE_VERTICALLY:
                return OptimizationRecommendation(
                    recommendation_id=f"scale_v_{int(time.time())}",
                    strategy=strategy,
                    component=bottleneck.component,
                    description=f"Scale vertically to address {bottleneck.bottleneck_type.value} bottleneck",
                    expected_improvement=25.0,
                    implementation_effort="low",
                    risk_level="low",
                    estimated_cost=50.0,
                    priority_score=priority_score * 0.9,
                    implementation_steps=[
                        "Analyze resource requirements",
                        "Upgrade instance specifications",
                        "Test performance improvements",
                        "Monitor resource utilization"
                    ]
                )
            
            elif strategy == OptimizationStrategy.OPTIMIZE_ALGORITHM:
                return OptimizationRecommendation(
                    recommendation_id=f"algo_opt_{int(time.time())}",
                    strategy=strategy,
                    component=bottleneck.component,
                    description=f"Optimize algorithms to address {bottleneck.bottleneck_type.value} bottleneck",
                    expected_improvement=40.0,
                    implementation_effort="high",
                    risk_level="medium",
                    estimated_cost=0.0,  # Development time, not infrastructure cost
                    priority_score=priority_score * 1.2,  # High impact, prefer this
                    implementation_steps=[
                        "Profile algorithm performance",
                        "Identify optimization opportunities",
                        "Implement algorithmic improvements",
                        "Test and validate improvements"
                    ]
                )
            
            elif strategy == OptimizationStrategy.INCREASE_CACHE:
                return OptimizationRecommendation(
                    recommendation_id=f"cache_inc_{int(time.time())}",
                    strategy=strategy,
                    component=bottleneck.component,
                    description=f"Increase cache size to address {bottleneck.bottleneck_type.value} bottleneck",
                    expected_improvement=35.0,
                    implementation_effort="low",
                    risk_level="low",
                    estimated_cost=25.0,
                    priority_score=priority_score * 1.1,
                    implementation_steps=[
                        "Analyze current cache utilization",
                        "Increase cache size limits",
                        "Optimize cache eviction policies",
                        "Monitor cache performance"
                    ]
                )
            
            elif strategy == OptimizationStrategy.INCREASE_PARALLELISM:
                return OptimizationRecommendation(
                    recommendation_id=f"parallel_inc_{int(time.time())}",
                    strategy=strategy,
                    component=bottleneck.component,
                    description=f"Increase parallelism to address {bottleneck.bottleneck_type.value} bottleneck",
                    expected_improvement=45.0,
                    implementation_effort="medium",
                    risk_level="medium",
                    estimated_cost=20.0,
                    priority_score=priority_score * 1.15,
                    implementation_steps=[
                        "Analyze current parallelism configuration",
                        "Increase worker thread/process count",
                        "Optimize task distribution",
                        "Monitor for diminishing returns"
                    ]
                )
            
            # Add more strategies as needed
            
        except Exception as e:
            logger.error(f"Recommendation creation failed: {e}")
        
        return None


class RealTimePerformanceMonitor:
    """Main real-time performance monitoring system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.monitor_id = f"monitor_{uuid.uuid4().hex[:8]}"
        self.enabled = config.get('enabled', True)
        self.collection_interval = config.get('collection_interval', 1.0)
        self.detection_interval = config.get('detection_interval', 30.0)
        self.optimization_interval = config.get('optimization_interval', 300.0)
        
        # Components
        self.metric_collector = MetricCollector(self.collection_interval)
        self.bottleneck_detector = BottleneckDetector(self.metric_collector)
        self.performance_optimizer = PerformanceOptimizer(self.bottleneck_detector)
        
        # Alerting
        self.alerts: deque = deque(maxlen=1000)
        self.alert_handlers: List[Callable] = []
        
        # Baselines
        self.baselines: Dict[str, PerformanceBaseline] = {}
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False
        
        self.lock = threading.RLock()
    
    async def start(self) -> None:
        """Start the performance monitor."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start metric collection
        await self.metric_collector.start_collection()
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._bottleneck_detection_loop()),
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._alerting_loop())
        ]
        
        logger.info(f"Started real-time performance monitor {self.monitor_id}")
    
    async def stop(self) -> None:
        """Stop the performance monitor."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop metric collection
        await self.metric_collector.stop_collection()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.background_tasks.clear()
        logger.info(f"Stopped real-time performance monitor {self.monitor_id}")
    
    async def _bottleneck_detection_loop(self) -> None:
        """Bottleneck detection loop."""
        while self.is_running:
            try:
                bottlenecks = await self.bottleneck_detector.detect_bottlenecks()
                
                # Generate alerts for new bottlenecks
                for bottleneck in bottlenecks:
                    await self._create_bottleneck_alert(bottleneck)
                
                await asyncio.sleep(self.detection_interval)
                
            except Exception as e:
                logger.error(f"Bottleneck detection loop error: {e}")
                await asyncio.sleep(self.detection_interval)
    
    async def _optimization_loop(self) -> None:
        """Optimization recommendation loop."""
        while self.is_running:
            try:
                recommendations = await self.performance_optimizer.generate_recommendations()
                
                # Log high-priority recommendations
                high_priority_recs = [r for r in recommendations if r.priority_score > 70]
                for rec in high_priority_recs:
                    logger.info(f"High-priority optimization: {rec.strategy.value} for {rec.component} "
                               f"(expected improvement: {rec.expected_improvement}%)")
                
                await asyncio.sleep(self.optimization_interval)
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    async def _alerting_loop(self) -> None:
        """Alerting loop."""
        while self.is_running:
            try:
                # Check metric thresholds and generate alerts
                await self._check_metric_alerts()
                
                await asyncio.sleep(60.0)  # Check every minute
                
            except Exception as e:
                logger.error(f"Alerting loop error: {e}")
                await asyncio.sleep(60.0)
    
    async def _create_bottleneck_alert(self, bottleneck: BottleneckDetection) -> None:
        """Create an alert for a detected bottleneck."""
        try:
            alert = PerformanceAlert(
                alert_id=f"bottleneck_alert_{int(time.time())}",
                severity=bottleneck.severity,
                title=f"{bottleneck.bottleneck_type.value} Bottleneck Detected",
                description=bottleneck.description,
                component=bottleneck.component,
                metric_type=PerformanceMetricType.CPU_UTILIZATION,  # Default
                current_value=bottleneck.confidence * 100,
                threshold=70.0,
                metadata={
                    'bottleneck_id': bottleneck.detection_id,
                    'bottleneck_type': bottleneck.bottleneck_type.value,
                    'root_cause': bottleneck.root_cause_analysis
                }
            )
            
            with self.lock:
                self.alerts.append(alert)
            
            # Notify alert handlers
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
        except Exception as e:
            logger.error(f"Alert creation failed: {e}")
    
    async def _check_metric_alerts(self) -> None:
        """Check metrics against alert thresholds."""
        try:
            # This would check various metrics against their thresholds
            # For now, just log if we have any active bottlenecks
            
            active_bottlenecks = self.bottleneck_detector.get_active_bottlenecks()
            if active_bottlenecks:
                logger.debug(f"Active bottlenecks: {len(active_bottlenecks)}")
            
        except Exception as e:
            logger.error(f"Metric alert check failed: {e}")
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]) -> None:
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def set_baseline(self, component: str, metric_type: PerformanceMetricType, baseline_value: float, acceptable_deviation: float = 0.2) -> None:
        """Set a performance baseline."""
        baseline = PerformanceBaseline(
            component=component,
            metric_type=metric_type,
            baseline_value=baseline_value,
            acceptable_deviation=acceptable_deviation,
            measurement_window=60,
            confidence_level=0.95
        )
        
        baseline_key = f"{component}:{metric_type.value}"
        with self.lock:
            self.baselines[baseline_key] = baseline
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self.lock:
            active_bottlenecks = self.bottleneck_detector.get_active_bottlenecks()
            recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts
            recent_recommendations = list(self.performance_optimizer.recommendations)[-5:]  # Last 5 recommendations
            
            # Get latest metrics
            latest_metrics = {}
            for key, metric in self.metric_collector.latest_metrics.items():
                latest_metrics[key] = {
                    'value': metric.value,
                    'timestamp': metric.timestamp,
                    'component': metric.component,
                    'operation': metric.operation
                }
            
            return {
                'monitor_id': self.monitor_id,
                'enabled': self.enabled,
                'is_running': self.is_running,
                'latest_metrics': latest_metrics,
                'active_bottlenecks': [
                    {
                        'type': b.bottleneck_type.value,
                        'component': b.component,
                        'severity': b.severity.value,
                        'confidence': b.confidence,
                        'description': b.description
                    }
                    for b in active_bottlenecks
                ],
                'recent_alerts': [
                    {
                        'severity': a.severity.value,
                        'title': a.title,
                        'component': a.component,
                        'timestamp': a.timestamp
                    }
                    for a in recent_alerts
                ],
                'recent_recommendations': [
                    {
                        'strategy': r.strategy.value,
                        'component': r.component,
                        'description': r.description,
                        'expected_improvement': r.expected_improvement,
                        'priority_score': r.priority_score
                    }
                    for r in recent_recommendations
                ],
                'baselines_count': len(self.baselines),
                'collection_interval': self.collection_interval,
                'detection_interval': self.detection_interval
            }


# Global performance monitor instance
_performance_monitor: Optional[RealTimePerformanceMonitor] = None


def get_performance_monitor(config: Optional[Dict[str, Any]] = None) -> RealTimePerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = RealTimePerformanceMonitor(config)
    return _performance_monitor


@asynccontextmanager
async def performance_monitoring_context(component: str, operation: str):
    """Context manager for performance monitoring."""
    start_time = time.time()
    monitor = get_performance_monitor()
    
    try:
        yield monitor
    except Exception as e:
        # Record error metric
        error_metric = PerformanceMetric(
            metric_id=f"error_{int(time.time() * 1000)}",
            metric_type=PerformanceMetricType.ERROR_RATE,
            value=1.0,
            timestamp=time.time(),
            component=component,
            operation=operation,
            metadata={'error': str(e)}
        )
        await monitor.metric_collector.record_metric(error_metric)
        raise
    finally:
        # Record latency metric
        end_time = time.time()
        latency = end_time - start_time
        
        latency_metric = PerformanceMetric(
            metric_id=f"latency_{int(end_time * 1000)}",
            metric_type=PerformanceMetricType.LATENCY,
            value=latency,
            timestamp=end_time,
            component=component,
            operation=operation
        )
        await monitor.metric_collector.record_metric(latency_metric)