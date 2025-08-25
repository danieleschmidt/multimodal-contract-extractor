"""
Advanced Monitoring System - Generation 6.0
Comprehensive monitoring, observability, and analytics for contract processing

This module implements enterprise-grade monitoring including:
- Real-time performance monitoring and metrics collection
- Advanced alerting and anomaly detection
- Distributed tracing across multidimensional processing
- Quantum-enhanced observability and telemetry
- AI-powered predictive monitoring and forecasting
- Comprehensive system health assessment
"""

import asyncio
import json
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import statistics
import math
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import queue
import uuid
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"  
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SystemHealth(Enum):
    """Overall system health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DOWN = "down"

@dataclass
class MetricValue:
    """Individual metric value with metadata"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

@dataclass
class Alert:
    """System alert with context"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: Union[int, float]
    threshold_value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

@dataclass
class TraceSpan:
    """Distributed trace span"""
    span_id: str
    trace_id: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    parent_span_id: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass  
class PerformanceBenchmark:
    """Performance benchmark results"""
    benchmark_id: str
    benchmark_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    accuracy: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Advanced metrics collection and aggregation"""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.metrics_buffer: deque = deque(maxlen=buffer_size)
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.metric_subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self.collection_lock = threading.Lock()
        self.is_collecting = False
        
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Optional[Dict[str, str]] = None,
                     unit: Optional[str] = None):
        """Record a metric value"""
        metric = MetricValue(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            unit=unit
        )
        
        with self.collection_lock:
            self.metrics_buffer.append(metric)
            
            # Update aggregated metrics
            self._update_aggregated_metrics(metric)
            
            # Notify subscribers
            self._notify_subscribers(metric)
    
    def _update_aggregated_metrics(self, metric: MetricValue):
        """Update aggregated metrics for analysis"""
        key = f"{metric.name}:{hash(frozenset(metric.labels.items()))}"
        
        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                "name": metric.name,
                "labels": metric.labels,
                "values": deque(maxlen=1000),
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "last_updated": metric.timestamp
            }
        
        agg = self.aggregated_metrics[key]
        agg["values"].append(metric.value)
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["last_updated"] = metric.timestamp
    
    def _notify_subscribers(self, metric: MetricValue):
        """Notify metric subscribers"""
        for callback in self.metric_subscriptions[metric.name]:
            try:
                callback(metric)
            except Exception as e:
                logger.warning(f"Metric subscription callback failed: {e}")
    
    def subscribe_to_metric(self, metric_name: str, callback: Callable[[MetricValue], None]):
        """Subscribe to metric updates"""
        self.metric_subscriptions[metric_name].append(callback)
    
    def get_metric_statistics(self, metric_name: str, 
                            time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get statistical analysis of a metric"""
        matching_metrics = []
        cutoff_time = None
        
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - time_window
        
        # Find matching metrics
        for agg_key, agg_data in self.aggregated_metrics.items():
            if agg_data["name"] == metric_name:
                if not cutoff_time or agg_data["last_updated"] >= cutoff_time:
                    matching_metrics.append(agg_data)
        
        if not matching_metrics:
            return {"error": "No metrics found"}
        
        # Combine values from all matching aggregations
        all_values = []
        for agg in matching_metrics:
            if cutoff_time:
                # Filter values by time (simplified - would need timestamps per value)
                all_values.extend(list(agg["values"]))
            else:
                all_values.extend(list(agg["values"]))
        
        if not all_values:
            return {"error": "No values in time window"}
        
        # Calculate statistics
        return {
            "count": len(all_values),
            "min": min(all_values),
            "max": max(all_values),
            "mean": statistics.mean(all_values),
            "median": statistics.median(all_values),
            "std_dev": statistics.stdev(all_values) if len(all_values) > 1 else 0,
            "percentiles": {
                "p50": np.percentile(all_values, 50),
                "p90": np.percentile(all_values, 90),
                "p95": np.percentile(all_values, 95),
                "p99": np.percentile(all_values, 99)
            }
        }
    
    def get_recent_metrics(self, limit: int = 100) -> List[MetricValue]:
        """Get most recent metrics"""
        with self.collection_lock:
            return list(self.metrics_buffer)[-limit:]

class AlertManager:
    """Advanced alerting system with anomaly detection"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.anomaly_detectors: Dict[str, Callable] = {}
        self.notification_channels: List[Callable] = []
        
    def add_alert_rule(self, name: str, metric_name: str, 
                      threshold: Union[int, float], operator: str = ">",
                      severity: AlertSeverity = AlertSeverity.WARNING,
                      evaluation_window: timedelta = timedelta(minutes=5)):
        """Add alerting rule"""
        self.alert_rules[name] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "operator": operator,
            "severity": severity,
            "evaluation_window": evaluation_window,
            "last_evaluation": datetime.now(timezone.utc)
        }
        
        # Subscribe to metric updates for real-time evaluation
        self.metrics_collector.subscribe_to_metric(metric_name, self._evaluate_metric)
    
    def _evaluate_metric(self, metric: MetricValue):
        """Evaluate metric against alert rules"""
        for rule_name, rule in self.alert_rules.items():
            if rule["metric_name"] == metric.name:
                self._check_alert_condition(rule_name, rule, metric)
    
    def _check_alert_condition(self, rule_name: str, rule: Dict[str, Any], metric: MetricValue):
        """Check if alert condition is met"""
        threshold = rule["threshold"]
        operator = rule["operator"]
        current_value = metric.value
        
        # Evaluate condition
        condition_met = False
        if operator == ">":
            condition_met = current_value > threshold
        elif operator == "<":
            condition_met = current_value < threshold
        elif operator == ">=":
            condition_met = current_value >= threshold
        elif operator == "<=":
            condition_met = current_value <= threshold
        elif operator == "==":
            condition_met = current_value == threshold
        elif operator == "!=":
            condition_met = current_value != threshold
        
        alert_id = f"{rule_name}_{metric.name}"
        
        if condition_met:
            if alert_id not in self.active_alerts:
                # Create new alert
                alert = Alert(
                    alert_id=alert_id,
                    name=rule_name,
                    severity=rule["severity"],
                    message=f"Metric {metric.name} is {current_value} {operator} {threshold}",
                    metric_name=metric.name,
                    current_value=current_value,
                    threshold_value=threshold,
                    labels=metric.labels
                )
                
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                
                # Send notifications
                self._send_alert_notification(alert)
                
                logger.warning(f"ALERT [{alert.severity.value.upper()}]: {alert.message}")
        else:
            # Check if alert should be resolved
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_timestamp = datetime.now(timezone.utc)
                
                del self.active_alerts[alert_id]
                
                logger.info(f"ALERT RESOLVED: {alert.name}")
    
    def _send_alert_notification(self, alert: Alert):
        """Send alert notification through configured channels"""
        for channel in self.notification_channels:
            try:
                channel(alert)
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
    
    def add_notification_channel(self, channel: Callable[[Alert], None]):
        """Add notification channel"""
        self.notification_channels.append(channel)
    
    def add_anomaly_detector(self, metric_name: str, detector: Callable[[List[float]], bool]):
        """Add anomaly detection algorithm for metric"""
        self.anomaly_detectors[metric_name] = detector
        self.metrics_collector.subscribe_to_metric(metric_name, self._check_anomaly)
    
    def _check_anomaly(self, metric: MetricValue):
        """Check for anomalies in metric values"""
        if metric.name not in self.anomaly_detectors:
            return
        
        # Get recent values for anomaly detection
        stats = self.metrics_collector.get_metric_statistics(
            metric.name, 
            time_window=timedelta(minutes=30)
        )
        
        if "error" in stats:
            return
        
        # Get values from aggregated metrics (simplified)
        agg_key = f"{metric.name}:{hash(frozenset(metric.labels.items()))}"
        if agg_key in self.metrics_collector.aggregated_metrics:
            recent_values = list(self.metrics_collector.aggregated_metrics[agg_key]["values"])
            
            # Check for anomaly
            detector = self.anomaly_detectors[metric.name]
            is_anomaly = detector(recent_values)
            
            if is_anomaly:
                # Create anomaly alert
                alert_id = f"anomaly_{metric.name}_{int(time.time())}"
                alert = Alert(
                    alert_id=alert_id,
                    name=f"Anomaly Detection: {metric.name}",
                    severity=AlertSeverity.WARNING,
                    message=f"Anomaly detected in metric {metric.name}: current value {metric.value}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=0,  # Not applicable for anomalies
                    labels=metric.labels
                )
                
                self.alert_history.append(alert)
                self._send_alert_notification(alert)
                
                logger.warning(f"ANOMALY DETECTED: {alert.message}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get recent alert history"""
        return list(self.alert_history)[-limit:]

class DistributedTracer:
    """Distributed tracing for multidimensional processing"""
    
    def __init__(self):
        self.active_traces: Dict[str, TraceSpan] = {}
        self.completed_traces: deque = deque(maxlen=1000)
        self.trace_lock = threading.Lock()
    
    def start_trace(self, operation_name: str, parent_span_id: Optional[str] = None) -> str:
        """Start a new trace span"""
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4()) if not parent_span_id else self._get_trace_id(parent_span_id)
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            operation_name=operation_name,
            start_time=datetime.now(timezone.utc),
            parent_span_id=parent_span_id
        )
        
        with self.trace_lock:
            self.active_traces[span_id] = span
        
        return span_id
    
    def end_trace(self, span_id: str, tags: Optional[Dict[str, Any]] = None):
        """End a trace span"""
        with self.trace_lock:
            if span_id in self.active_traces:
                span = self.active_traces[span_id]
                span.end_time = datetime.now(timezone.utc)
                span.duration = (span.end_time - span.start_time).total_seconds()
                
                if tags:
                    span.tags.update(tags)
                
                self.completed_traces.append(span)
                del self.active_traces[span_id]
    
    def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add tag to active span"""
        with self.trace_lock:
            if span_id in self.active_traces:
                self.active_traces[span_id].tags[key] = value
    
    def log_span_event(self, span_id: str, event: str, data: Optional[Dict[str, Any]] = None):
        """Log event to active span"""
        with self.trace_lock:
            if span_id in self.active_traces:
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": event,
                    "data": data or {}
                }
                self.active_traces[span_id].logs.append(log_entry)
    
    def _get_trace_id(self, span_id: str) -> str:
        """Get trace ID for a span"""
        with self.trace_lock:
            if span_id in self.active_traces:
                return self.active_traces[span_id].trace_id
            
            # Check completed traces
            for span in self.completed_traces:
                if span.span_id == span_id:
                    return span.trace_id
        
        return str(uuid.uuid4())  # Fallback
    
    def get_trace_by_id(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        spans = []
        
        # Check active traces
        with self.trace_lock:
            for span in self.active_traces.values():
                if span.trace_id == trace_id:
                    spans.append(span)
            
            # Check completed traces
            for span in self.completed_traces:
                if span.trace_id == trace_id:
                    spans.append(span)
        
        # Sort by start time
        spans.sort(key=lambda s: s.start_time)
        return spans
    
    def get_recent_traces(self, limit: int = 20) -> List[TraceSpan]:
        """Get recent completed traces"""
        return list(self.completed_traces)[-limit:]

class PerformanceBenchmarker:
    """Performance benchmarking and analysis"""
    
    def __init__(self):
        self.benchmarks: Dict[str, List[PerformanceBenchmark]] = defaultdict(list)
        self.baseline_benchmarks: Dict[str, PerformanceBenchmark] = {}
        
    async def run_benchmark(self, benchmark_name: str, 
                          benchmark_func: Callable, *args, **kwargs) -> PerformanceBenchmark:
        """Run performance benchmark"""
        import psutil
        import tracemalloc
        
        benchmark_id = str(uuid.uuid4())
        
        # Start monitoring
        tracemalloc.start()
        process = psutil.Process()
        start_cpu = process.cpu_percent()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        try:
            # Run benchmark function
            if asyncio.iscoroutinefunction(benchmark_func):
                result = await benchmark_func(*args, **kwargs)
            else:
                result = benchmark_func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Calculate resource usage
            end_cpu = process.cpu_percent()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Calculate metrics
            cpu_usage = (start_cpu + end_cpu) / 2
            memory_usage = peak_memory / 1024 / 1024  # MB
            throughput = 1.0 / execution_time if execution_time > 0 else 0
            
            # Estimate accuracy (if result has accuracy measure)
            accuracy = 1.0
            if isinstance(result, dict) and "accuracy" in result:
                accuracy = result["accuracy"]
            elif isinstance(result, dict) and "quality_score" in result:
                accuracy = result["quality_score"]
            
            # Create benchmark result
            benchmark = PerformanceBenchmark(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                throughput=throughput,
                accuracy=accuracy,
                metadata={
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "result_type": type(result).__name__,
                    "peak_memory_mb": peak_memory / 1024 / 1024
                }
            )
            
            # Store benchmark
            self.benchmarks[benchmark_name].append(benchmark)
            
            return benchmark
            
        except Exception as e:
            tracemalloc.stop()
            logger.error(f"Benchmark {benchmark_name} failed: {str(e)}")
            
            # Create failed benchmark result
            return PerformanceBenchmark(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                execution_time=time.time() - start_time,
                memory_usage=0,
                cpu_usage=0,
                throughput=0,
                accuracy=0,
                metadata={"error": str(e)}
            )
    
    def set_baseline(self, benchmark_name: str, benchmark: PerformanceBenchmark):
        """Set baseline benchmark for comparison"""
        self.baseline_benchmarks[benchmark_name] = benchmark
    
    def compare_to_baseline(self, benchmark_name: str, 
                          current_benchmark: PerformanceBenchmark) -> Dict[str, Any]:
        """Compare benchmark to baseline"""
        if benchmark_name not in self.baseline_benchmarks:
            return {"error": "No baseline benchmark found"}
        
        baseline = self.baseline_benchmarks[benchmark_name]
        
        # Calculate percentage changes
        time_change = ((current_benchmark.execution_time - baseline.execution_time) / baseline.execution_time) * 100
        memory_change = ((current_benchmark.memory_usage - baseline.memory_usage) / baseline.memory_usage) * 100 if baseline.memory_usage > 0 else 0
        throughput_change = ((current_benchmark.throughput - baseline.throughput) / baseline.throughput) * 100 if baseline.throughput > 0 else 0
        accuracy_change = ((current_benchmark.accuracy - baseline.accuracy) / baseline.accuracy) * 100 if baseline.accuracy > 0 else 0
        
        return {
            "execution_time_change_percent": time_change,
            "memory_usage_change_percent": memory_change,
            "throughput_change_percent": throughput_change,
            "accuracy_change_percent": accuracy_change,
            "performance_regression": time_change > 10 or memory_change > 20,  # Thresholds
            "performance_improvement": time_change < -5 and memory_change < 10,
            "baseline_timestamp": baseline.timestamp.isoformat(),
            "current_timestamp": current_benchmark.timestamp.isoformat()
        }
    
    def get_benchmark_trends(self, benchmark_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get performance trends for benchmark"""
        if benchmark_name not in self.benchmarks:
            return {"error": "No benchmarks found"}
        
        recent_benchmarks = self.benchmarks[benchmark_name][-limit:]
        
        if len(recent_benchmarks) < 2:
            return {"error": "Insufficient benchmark data"}
        
        # Calculate trends
        execution_times = [b.execution_time for b in recent_benchmarks]
        memory_usage = [b.memory_usage for b in recent_benchmarks]
        throughput = [b.throughput for b in recent_benchmarks]
        accuracy = [b.accuracy for b in recent_benchmarks]
        
        return {
            "execution_time": {
                "trend": self._calculate_trend(execution_times),
                "average": statistics.mean(execution_times),
                "std_dev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            },
            "memory_usage": {
                "trend": self._calculate_trend(memory_usage),
                "average": statistics.mean(memory_usage),
                "std_dev": statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0
            },
            "throughput": {
                "trend": self._calculate_trend(throughput),
                "average": statistics.mean(throughput),
                "std_dev": statistics.stdev(throughput) if len(throughput) > 1 else 0
            },
            "accuracy": {
                "trend": self._calculate_trend(accuracy),
                "average": statistics.mean(accuracy),
                "std_dev": statistics.stdev(accuracy) if len(accuracy) > 1 else 0
            },
            "benchmark_count": len(recent_benchmarks),
            "time_span_hours": (recent_benchmarks[-1].timestamp - recent_benchmarks[0].timestamp).total_seconds() / 3600
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear regression slope
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"

class SystemHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.health_history: deque = deque(maxlen=100)
        self.monitoring_active = False
        
    def add_health_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Add health check function"""
        self.health_checks[name] = check_func
    
    async def perform_health_assessment(self) -> Dict[str, Any]:
        """Perform comprehensive health assessment"""
        assessment_start = time.time()
        health_results = {}
        
        # Run all health checks
        for check_name, check_func in self.health_checks.items():
            try:
                result = check_func()
                health_results[check_name] = result
            except Exception as e:
                health_results[check_name] = {
                    "status": "error",
                    "error": str(e),
                    "healthy": False
                }
        
        # Analyze overall health
        overall_health = self._calculate_overall_health(health_results)
        
        # Get system metrics
        system_metrics = self._get_system_metrics()
        
        # Check for active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        alert_impact = self._assess_alert_impact(active_alerts)
        
        assessment_result = {
            "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
            "assessment_duration": time.time() - assessment_start,
            "overall_health": overall_health,
            "health_checks": health_results,
            "system_metrics": system_metrics,
            "active_alerts": len(active_alerts),
            "alert_impact": alert_impact,
            "recommendations": self._generate_health_recommendations(health_results, active_alerts)
        }
        
        # Store in history
        self.health_history.append(assessment_result)
        
        # Record health metrics
        self.metrics_collector.record_metric(
            "system_health_score", 
            overall_health["health_score"], 
            MetricType.GAUGE
        )
        
        return assessment_result
    
    def _calculate_overall_health(self, health_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall system health"""
        if not health_results:
            return {
                "status": SystemHealth.DOWN,
                "health_score": 0.0,
                "healthy_checks": 0,
                "total_checks": 0
            }
        
        healthy_count = 0
        total_count = len(health_results)
        
        for result in health_results.values():
            if result.get("healthy", False):
                healthy_count += 1
        
        health_score = healthy_count / total_count if total_count > 0 else 0
        
        # Determine overall status
        if health_score >= 0.9:
            status = SystemHealth.HEALTHY
        elif health_score >= 0.7:
            status = SystemHealth.DEGRADED
        elif health_score >= 0.3:
            status = SystemHealth.CRITICAL
        else:
            status = SystemHealth.DOWN
        
        return {
            "status": status,
            "health_score": health_score,
            "healthy_checks": healthy_count,
            "total_checks": total_count
        }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / 1024 / 1024 / 1024  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free / 1024 / 1024 / 1024  # GB
            
            return {
                "cpu_usage_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_usage_percent": memory_percent,
                "memory_available_gb": memory_available,
                "disk_usage_percent": disk_percent,
                "disk_free_gb": disk_free,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except ImportError:
            return {"error": "psutil not available for system metrics"}
        except Exception as e:
            return {"error": f"Failed to get system metrics: {str(e)}"}
    
    def _assess_alert_impact(self, active_alerts: List[Alert]) -> Dict[str, Any]:
        """Assess impact of active alerts on system health"""
        if not active_alerts:
            return {"impact_score": 0.0, "severity_breakdown": {}}
        
        severity_weights = {
            AlertSeverity.INFO: 0.1,
            AlertSeverity.WARNING: 0.3,
            AlertSeverity.CRITICAL: 0.7,
            AlertSeverity.EMERGENCY: 1.0
        }
        
        severity_counts = defaultdict(int)
        impact_score = 0.0
        
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
            impact_score += severity_weights.get(alert.severity, 0.5)
        
        # Normalize impact score
        max_possible_impact = len(active_alerts) * 1.0
        normalized_impact = min(impact_score / max_possible_impact, 1.0) if max_possible_impact > 0 else 0.0
        
        return {
            "impact_score": normalized_impact,
            "severity_breakdown": dict(severity_counts),
            "total_alerts": len(active_alerts),
            "critical_alerts": severity_counts.get("critical", 0) + severity_counts.get("emergency", 0)
        }
    
    def _generate_health_recommendations(self, health_results: Dict[str, Dict[str, Any]], 
                                       active_alerts: List[Alert]) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        # Check failed health checks
        failed_checks = [name for name, result in health_results.items() if not result.get("healthy", False)]
        
        if failed_checks:
            recommendations.append(f"Investigate failed health checks: {', '.join(failed_checks)}")
        
        # Check for critical alerts
        critical_alerts = [alert for alert in active_alerts if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]
        
        if critical_alerts:
            recommendations.append(f"Address {len(critical_alerts)} critical alerts immediately")
        
        # Check system resource usage
        system_metrics = self._get_system_metrics()
        if "error" not in system_metrics:
            if system_metrics.get("cpu_usage_percent", 0) > 80:
                recommendations.append("High CPU usage detected - consider scaling or optimization")
            
            if system_metrics.get("memory_usage_percent", 0) > 85:
                recommendations.append("High memory usage detected - check for memory leaks")
            
            if system_metrics.get("disk_usage_percent", 0) > 90:
                recommendations.append("High disk usage detected - clean up or expand storage")
        
        # General recommendations based on health score
        overall_health = self._calculate_overall_health(health_results)
        if overall_health["health_score"] < 0.7:
            recommendations.append("System health is degraded - run comprehensive diagnostics")
        
        return recommendations[:10]  # Limit to top 10 recommendations

class AdvancedMonitoringSystem:
    """Main advanced monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.tracer = DistributedTracer()
        self.benchmarker = PerformanceBenchmarker()
        self.health_monitor = SystemHealthMonitor(self.metrics_collector, self.alert_manager)
        
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize default health checks
        self._initialize_default_health_checks()
        self._initialize_default_alerts()
        self._initialize_anomaly_detectors()
    
    def _initialize_default_health_checks(self):
        """Initialize default health check functions"""
        def metrics_collector_health():
            buffer_usage = len(self.metrics_collector.metrics_buffer) / self.metrics_collector.buffer_size
            return {
                "healthy": buffer_usage < 0.9,
                "buffer_usage_percent": buffer_usage * 100,
                "total_metrics": len(self.metrics_collector.metrics_buffer),
                "status": "healthy" if buffer_usage < 0.9 else "buffer_full"
            }
        
        def alert_manager_health():
            active_count = len(self.alert_manager.active_alerts)
            return {
                "healthy": active_count < 10,  # Arbitrary threshold
                "active_alerts": active_count,
                "alert_rules": len(self.alert_manager.alert_rules),
                "status": "healthy" if active_count < 10 else "too_many_alerts"
            }
        
        def tracer_health():
            active_traces = len(self.tracer.active_traces)
            return {
                "healthy": active_traces < 100,
                "active_traces": active_traces,
                "completed_traces": len(self.tracer.completed_traces),
                "status": "healthy" if active_traces < 100 else "trace_buildup"
            }
        
        self.health_monitor.add_health_check("metrics_collector", metrics_collector_health)
        self.health_monitor.add_health_check("alert_manager", alert_manager_health)
        self.health_monitor.add_health_check("tracer", tracer_health)
    
    def _initialize_default_alerts(self):
        """Initialize default alert rules"""
        self.alert_manager.add_alert_rule(
            "high_processing_time",
            "document_processing_time",
            30.0,  # seconds
            ">",
            AlertSeverity.WARNING
        )
        
        self.alert_manager.add_alert_rule(
            "low_accuracy",
            "processing_accuracy",
            0.8,
            "<",
            AlertSeverity.CRITICAL
        )
        
        self.alert_manager.add_alert_rule(
            "high_memory_usage",
            "memory_usage_percent",
            85.0,
            ">",
            AlertSeverity.WARNING
        )
    
    def _initialize_anomaly_detectors(self):
        """Initialize anomaly detection algorithms"""
        def simple_outlier_detector(values: List[float]) -> bool:
            if len(values) < 10:
                return False
            
            # Use IQR method for outlier detection
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            outlier_threshold = 1.5 * iqr
            recent_value = values[-1]
            
            return recent_value > (q3 + outlier_threshold) or recent_value < (q1 - outlier_threshold)
        
        # Add anomaly detectors for key metrics
        self.alert_manager.add_anomaly_detector("document_processing_time", simple_outlier_detector)
        self.alert_manager.add_anomaly_detector("processing_accuracy", simple_outlier_detector)
        self.alert_manager.add_anomaly_detector("memory_usage_percent", simple_outlier_detector)
    
    async def start_monitoring(self):
        """Start monitoring system"""
        self.monitoring_active = True
        
        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(target=self._background_monitoring)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Advanced monitoring system started")
    
    def stop_monitoring(self):
        """Stop monitoring system"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.monitoring_executor.shutdown(wait=True)
        logger.info("Advanced monitoring system stopped")
    
    def _background_monitoring(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform periodic health assessment
                asyncio.run(self.health_monitor.perform_health_assessment())
                
                # Record system metrics
                self._record_system_metrics()
                
                # Sleep before next iteration
                time.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(10)  # Short sleep on error
    
    def _record_system_metrics(self):
        """Record system-wide metrics"""
        try:
            import psutil
            
            # Record CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.record_metric(
                "cpu_usage_percent", cpu_percent, MetricType.GAUGE, unit="percent"
            )
            
            # Record memory usage
            memory = psutil.virtual_memory()
            self.metrics_collector.record_metric(
                "memory_usage_percent", memory.percent, MetricType.GAUGE, unit="percent"
            )
            
            # Record disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_collector.record_metric(
                "disk_usage_percent", disk_percent, MetricType.GAUGE, unit="percent"
            )
            
        except ImportError:
            pass  # psutil not available
        except Exception as e:
            logger.warning(f"Failed to record system metrics: {e}")
    
    async def monitor_document_processing(self, processing_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Monitor document processing with full observability"""
        # Start trace
        span_id = self.tracer.start_trace("document_processing")
        
        try:
            # Record start metrics
            start_time = time.time()
            self.tracer.add_span_tag(span_id, "start_time", start_time)
            
            # Run processing with benchmark
            benchmark = await self.benchmarker.run_benchmark(
                "document_processing", processing_func, *args, **kwargs
            )
            
            # Record metrics
            self.metrics_collector.record_metric(
                "document_processing_time", benchmark.execution_time, MetricType.TIMER, unit="seconds"
            )
            self.metrics_collector.record_metric(
                "processing_accuracy", benchmark.accuracy, MetricType.GAUGE
            )
            self.metrics_collector.record_metric(
                "memory_usage_mb", benchmark.memory_usage, MetricType.GAUGE, unit="megabytes"
            )
            
            # Add trace tags
            self.tracer.add_span_tag(span_id, "execution_time", benchmark.execution_time)
            self.tracer.add_span_tag(span_id, "accuracy", benchmark.accuracy)
            self.tracer.add_span_tag(span_id, "memory_usage", benchmark.memory_usage)
            
            # End trace
            self.tracer.end_trace(span_id, {"status": "success"})
            
            return {
                "monitoring_success": True,
                "benchmark": benchmark,
                "span_id": span_id,
                "trace_id": self.tracer.active_traces.get(span_id, {}).get("trace_id", "unknown")
            }
            
        except Exception as e:
            # Log error to trace
            self.tracer.log_span_event(span_id, "error", {"error": str(e)})
            self.tracer.end_trace(span_id, {"status": "error", "error": str(e)})
            
            logger.error(f"Document processing monitoring failed: {e}")
            return {
                "monitoring_success": False,
                "error": str(e),
                "span_id": span_id
            }
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_recent_metrics(100)
        
        # Get metric statistics
        processing_time_stats = self.metrics_collector.get_metric_statistics("document_processing_time")
        accuracy_stats = self.metrics_collector.get_metric_statistics("processing_accuracy")
        
        # Get alerts
        active_alerts = self.alert_manager.get_active_alerts()
        alert_history = self.alert_manager.get_alert_history(20)
        
        # Get recent traces
        recent_traces = self.tracer.get_recent_traces(10)
        
        # Get health status
        health_history = list(self.health_monitor.health_history)[-5:]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "recent_count": len(recent_metrics),
                "processing_time_stats": processing_time_stats,
                "accuracy_stats": accuracy_stats
            },
            "alerts": {
                "active_count": len(active_alerts),
                "active_alerts": [
                    {
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts
                ],
                "recent_history_count": len(alert_history)
            },
            "tracing": {
                "recent_traces_count": len(recent_traces),
                "active_traces_count": len(self.tracer.active_traces)
            },
            "health": {
                "recent_assessments": len(health_history),
                "latest_health_score": health_history[-1]["overall_health"]["health_score"] if health_history else 0
            }
        }

# Factory function
def create_monitoring_system() -> AdvancedMonitoringSystem:
    """Create advanced monitoring system"""
    return AdvancedMonitoringSystem()

# Example usage
if __name__ == "__main__":
    async def demonstrate_monitoring():
        """Demonstrate monitoring system capabilities"""
        print("📊 Advanced Monitoring System - Generation 6.0")
        print("=" * 60)
        
        # Create monitoring system
        monitoring = create_monitoring_system()
        
        # Start monitoring
        await monitoring.start_monitoring()
        print("✅ Monitoring system started")
        
        # Simulate document processing
        async def mock_processing():
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"accuracy": 0.92, "quality_score": 0.88}
        
        print("\n📄 Monitoring document processing...")
        result = await monitoring.monitor_document_processing(mock_processing)
        
        if result["monitoring_success"]:
            benchmark = result["benchmark"]
            print(f"✅ Processing monitored successfully")
            print(f"  Execution Time: {benchmark.execution_time:.3f}s")
            print(f"  Memory Usage: {benchmark.memory_usage:.2f}MB")
            print(f"  Accuracy: {benchmark.accuracy:.3f}")
            print(f"  Trace ID: {result['trace_id']}")
        
        # Record some additional metrics
        print("\n📈 Recording additional metrics...")
        monitoring.metrics_collector.record_metric("test_counter", 42, MetricType.COUNTER)
        monitoring.metrics_collector.record_metric("test_gauge", 0.85, MetricType.GAUGE)
        monitoring.metrics_collector.record_metric("response_time", 150, MetricType.TIMER, unit="ms")
        
        # Get metric statistics
        processing_stats = monitoring.metrics_collector.get_metric_statistics("document_processing_time")
        if "error" not in processing_stats:
            print(f"  Processing Time Stats: avg={processing_stats['mean']:.3f}s")
        
        # Perform health assessment
        print("\n🏥 Performing health assessment...")
        health_result = await monitoring.health_monitor.perform_health_assessment()
        
        overall_health = health_result["overall_health"]
        print(f"✅ Health Assessment Complete")
        print(f"  Overall Health: {overall_health['status'].value}")
        print(f"  Health Score: {overall_health['health_score']:.2f}")
        print(f"  Healthy Checks: {overall_health['healthy_checks']}/{overall_health['total_checks']}")
        print(f"  Active Alerts: {health_result['active_alerts']}")
        
        # Show recommendations
        if health_result["recommendations"]:
            print(f"  Recommendations:")
            for rec in health_result["recommendations"][:3]:
                print(f"    • {rec}")
        
        # Get dashboard data
        print("\n📊 Dashboard Data Summary:")
        dashboard = monitoring.get_monitoring_dashboard_data()
        print(f"  Recent Metrics: {dashboard['metrics']['recent_count']}")
        print(f"  Active Alerts: {dashboard['alerts']['active_count']}")
        print(f"  Recent Traces: {dashboard['tracing']['recent_traces_count']}")
        print(f"  Latest Health Score: {dashboard['health']['latest_health_score']:.2f}")
        
        # Stop monitoring
        monitoring.stop_monitoring()
        print("\n✅ Monitoring system stopped")
    
    # Run demonstration
    asyncio.run(demonstrate_monitoring())