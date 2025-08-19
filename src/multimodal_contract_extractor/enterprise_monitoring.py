"""
Enterprise Monitoring and Observability System

Advanced monitoring, performance analytics, and observability for the multimodal
contract extractor system with novel research algorithms.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import psutil

from .enterprise_error_handling import ComponentType

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for monitoring."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data structure."""

    name: str
    type: MetricType
    value: Union[float, int]
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class PerformanceMetrics:
    """Performance metrics for research algorithms."""

    algorithm_name: str
    execution_time: float
    throughput: float  # items/second
    accuracy: float
    confidence: float
    resource_usage: Dict[str, float]
    error_rate: float
    success_rate: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    condition: str  # e.g., "cpu_usage > 80"
    threshold: float
    level: AlertLevel
    component: ComponentType
    cooldown_seconds: int = 300  # 5 minutes
    last_triggered: float = 0.0
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    level: AlertLevel = AlertLevel.INFO
    message: str = ""
    component: ComponentType = ComponentType.DOCUMENT_PROCESSOR
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolution_time: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


class ResearchAlgorithmMonitor:
    """Specialized monitor for novel research algorithms."""

    def __init__(self):
        self.algorithm_metrics: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.Lock()

    def record_algorithm_performance(
        self,
        algorithm_name: str,
        execution_time: float,
        throughput: float,
        accuracy: float,
        confidence: float,
        resource_usage: Dict[str, float],
        error_count: int = 0,
        success_count: int = 1
    ):
        """Record performance metrics for a research algorithm."""

        total_operations = error_count + success_count
        error_rate = error_count / total_operations if total_operations > 0 else 0.0
        success_rate = success_count / total_operations if total_operations > 0 else 1.0

        metrics = PerformanceMetrics(
            algorithm_name=algorithm_name,
            execution_time=execution_time,
            throughput=throughput,
            accuracy=accuracy,
            confidence=confidence,
            resource_usage=resource_usage,
            error_rate=error_rate,
            success_rate=success_rate
        )

        with self._lock:
            self.algorithm_metrics[algorithm_name].append(metrics)
            self.performance_history[algorithm_name].append({
                'timestamp': metrics.timestamp,
                'execution_time': execution_time,
                'accuracy': accuracy,
                'throughput': throughput,
                'confidence': confidence
            })

    def set_baseline_metrics(self, algorithm_name: str, baseline: PerformanceMetrics):
        """Set baseline metrics for comparison."""
        self.baseline_metrics[algorithm_name] = baseline

    def get_algorithm_statistics(self, algorithm_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an algorithm."""
        with self._lock:
            metrics = self.algorithm_metrics.get(algorithm_name, [])

        if not metrics:
            return {"error": f"No metrics found for algorithm {algorithm_name}"}

        # Calculate statistics
        recent_metrics = metrics[-100:]  # Last 100 executions

        execution_times = [m.execution_time for m in recent_metrics]
        accuracies = [m.accuracy for m in recent_metrics]
        throughputs = [m.throughput for m in recent_metrics]
        confidences = [m.confidence for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]

        stats = {
            'algorithm_name': algorithm_name,
            'total_executions': len(metrics),
            'recent_executions': len(recent_metrics),
            'execution_time': {
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'std': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                'min': min(execution_times),
                'max': max(execution_times),
                'p95': np.percentile(execution_times, 95),
                'p99': np.percentile(execution_times, 99)
            },
            'accuracy': {
                'mean': statistics.mean(accuracies),
                'median': statistics.median(accuracies),
                'std': statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
                'min': min(accuracies),
                'max': max(accuracies)
            },
            'throughput': {
                'mean': statistics.mean(throughputs),
                'median': statistics.median(throughputs),
                'std': statistics.stdev(throughputs) if len(throughputs) > 1 else 0,
                'min': min(throughputs),
                'max': max(throughputs)
            },
            'confidence': {
                'mean': statistics.mean(confidences),
                'median': statistics.median(confidences),
                'std': statistics.stdev(confidences) if len(confidences) > 1 else 0
            },
            'error_rate': {
                'mean': statistics.mean(error_rates),
                'current': error_rates[-1] if error_rates else 0
            }
        }

        # Compare with baseline if available
        baseline = self.baseline_metrics.get(algorithm_name)
        if baseline:
            stats['baseline_comparison'] = {
                'execution_time_improvement': (baseline.execution_time - stats['execution_time']['mean']) / baseline.execution_time,
                'accuracy_improvement': (stats['accuracy']['mean'] - baseline.accuracy) / baseline.accuracy,
                'throughput_improvement': (stats['throughput']['mean'] - baseline.throughput) / baseline.throughput,
                'confidence_improvement': (stats['confidence']['mean'] - baseline.confidence) / baseline.confidence
            }

        return stats

    def detect_performance_anomalies(self, algorithm_name: str, window_size: int = 50) -> List[Dict[str, Any]]:
        """Detect performance anomalies using statistical methods."""
        with self._lock:
            history = list(self.performance_history[algorithm_name])

        if len(history) < window_size * 2:
            return []

        anomalies = []
        recent_data = history[-window_size:]
        historical_data = history[-window_size*2:-window_size]

        metrics_to_check = ['execution_time', 'accuracy', 'throughput', 'confidence']

        for metric in metrics_to_check:
            recent_values = [d[metric] for d in recent_data]
            historical_values = [d[metric] for d in historical_data]

            if len(historical_values) < 10:
                continue

            # Calculate Z-score for anomaly detection
            historical_mean = statistics.mean(historical_values)
            historical_std = statistics.stdev(historical_values)

            if historical_std == 0:
                continue

            recent_mean = statistics.mean(recent_values)
            z_score = abs(recent_mean - historical_mean) / historical_std

            # Flag as anomaly if Z-score > 2 (95% confidence)
            if z_score > 2:
                anomaly_type = "degradation" if recent_mean < historical_mean else "improvement"
                if metric == "accuracy" or metric == "throughput" or metric == "confidence":
                    anomaly_type = "improvement" if recent_mean > historical_mean else "degradation"

                anomalies.append({
                    'algorithm': algorithm_name,
                    'metric': metric,
                    'type': anomaly_type,
                    'z_score': z_score,
                    'historical_mean': historical_mean,
                    'recent_mean': recent_mean,
                    'severity': 'high' if z_score > 3 else 'medium',
                    'timestamp': time.time()
                })

        return anomalies


class SystemResourceMonitor:
    """Monitor system resources and infrastructure."""

    def __init__(self):
        self.resource_history = defaultdict(lambda: deque(maxlen=1000))
        self.gpu_available = self._check_gpu_availability()

    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available."""
        try:
            import pynvml
            pynvml.nvmlInit()
            return True
        except ImportError:
            logger.info("GPU monitoring not available - pynvml not installed")
            return False
        except Exception as e:
            logger.warning(f"GPU monitoring initialization failed: {e}")
            return False

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        timestamp = time.time()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        # Network metrics
        network = psutil.net_io_counters()

        # Process metrics
        process_count = len(psutil.pids())

        metrics = {
            'timestamp': timestamp,
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'frequency_mhz': cpu_freq.current if cpu_freq else 0,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent': memory.percent,
                'swap_total_gb': swap.total / (1024**3),
                'swap_used_gb': swap.used / (1024**3),
                'swap_percent': swap.percent
            },
            'disk': {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': (disk.used / disk.total) * 100,
                'read_bytes_per_sec': disk_io.read_bytes if disk_io else 0,
                'write_bytes_per_sec': disk_io.write_bytes if disk_io else 0
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'process_count': process_count
        }

        # Add GPU metrics if available
        if self.gpu_available:
            gpu_metrics = self._collect_gpu_metrics()
            metrics['gpu'] = gpu_metrics

        # Store in history
        for key, value in metrics.items():
            if key != 'timestamp':
                self.resource_history[key].append({'timestamp': timestamp, 'value': value})

        return metrics

    def _collect_gpu_metrics(self) -> Dict[str, Any]:
        """Collect GPU metrics if available."""
        try:
            import pynvml

            device_count = pynvml.nvmlDeviceGetCount()
            gpu_metrics = {'device_count': device_count, 'devices': []}

            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                # Memory info
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                # Temperature
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = 0

                # Utilization
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = utilization.gpu
                    memory_util = utilization.memory
                except:
                    gpu_util = 0
                    memory_util = 0

                # Power
                try:
                    power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                except:
                    power_draw = 0

                device_metrics = {
                    'index': i,
                    'memory': {
                        'total_mb': mem_info.total / (1024**2),
                        'used_mb': mem_info.used / (1024**2),
                        'free_mb': mem_info.free / (1024**2),
                        'percent': (mem_info.used / mem_info.total) * 100
                    },
                    'temperature_c': temperature,
                    'utilization': {
                        'gpu_percent': gpu_util,
                        'memory_percent': memory_util
                    },
                    'power_draw_w': power_draw
                }

                gpu_metrics['devices'].append(device_metrics)

            return gpu_metrics

        except Exception as e:
            logger.warning(f"Failed to collect GPU metrics: {e}")
            return {'error': str(e)}

    def get_resource_trends(self, metric_name: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get resource usage trends over time."""
        cutoff_time = time.time() - (time_window_minutes * 60)

        history = [
            item for item in self.resource_history[metric_name]
            if item['timestamp'] > cutoff_time
        ]

        if not history:
            return {'error': f'No data available for {metric_name}'}

        values = [item['value'] for item in history]
        timestamps = [item['timestamp'] for item in history]

        # Calculate trend statistics
        if len(values) > 1:
            # Simple linear trend calculation
            x = np.array(range(len(values)))
            y = np.array(values)
            trend_slope = np.polyfit(x, y, 1)[0]
            trend_direction = "increasing" if trend_slope > 0 else "decreasing" if trend_slope < 0 else "stable"
        else:
            trend_slope = 0
            trend_direction = "stable"

        return {
            'metric_name': metric_name,
            'time_window_minutes': time_window_minutes,
            'data_points': len(values),
            'current_value': values[-1] if values else None,
            'min_value': min(values) if values else None,
            'max_value': max(values) if values else None,
            'mean_value': statistics.mean(values) if values else None,
            'trend_slope': trend_slope,
            'trend_direction': trend_direction,
            'start_time': timestamps[0] if timestamps else None,
            'end_time': timestamps[-1] if timestamps else None
        }


class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._lock = threading.Lock()

        # Initialize default alert rules
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default alert rules for the system."""
        default_rules = [
            AlertRule("high_cpu_usage", "cpu_usage > 80", 80.0, AlertLevel.WARNING, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("critical_cpu_usage", "cpu_usage > 95", 95.0, AlertLevel.CRITICAL, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("high_memory_usage", "memory_usage > 85", 85.0, AlertLevel.WARNING, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("critical_memory_usage", "memory_usage > 95", 95.0, AlertLevel.CRITICAL, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("high_error_rate", "error_rate > 0.05", 0.05, AlertLevel.WARNING, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("critical_error_rate", "error_rate > 0.1", 0.1, AlertLevel.CRITICAL, ComponentType.DOCUMENT_PROCESSOR),
            AlertRule("low_accuracy", "accuracy < 0.7", 0.7, AlertLevel.WARNING, ComponentType.QUANTUM_PROCESSOR),
            AlertRule("very_low_accuracy", "accuracy < 0.5", 0.5, AlertLevel.CRITICAL, ComponentType.QUANTUM_PROCESSOR),
            AlertRule("gpu_memory_high", "gpu_memory_usage > 90", 90.0, AlertLevel.WARNING, ComponentType.NEUROMORPHIC_ENGINE),
            AlertRule("gpu_temperature_high", "gpu_temperature > 80", 80.0, AlertLevel.WARNING, ComponentType.NEUROMORPHIC_ENGINE),
        ]

        for rule in default_rules:
            self.alert_rules[rule.name] = rule

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def evaluate_alerts(self, metrics: Dict[str, Any]):
        """Evaluate all alert rules against current metrics."""
        current_time = time.time()

        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Check cooldown
            if current_time - rule.last_triggered < rule.cooldown_seconds:
                continue

            # Evaluate condition
            if self._evaluate_condition(rule, metrics):
                self._trigger_alert(rule, metrics)

    def _evaluate_condition(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Evaluate if an alert condition is met."""
        try:
            # Extract relevant metric value based on rule condition
            if "cpu_usage" in rule.condition:
                value = metrics.get('cpu', {}).get('percent', 0)
            elif "memory_usage" in rule.condition:
                value = metrics.get('memory', {}).get('percent', 0)
            elif "error_rate" in rule.condition:
                value = metrics.get('error_rate', 0)
            elif "accuracy" in rule.condition:
                value = metrics.get('accuracy', 1.0)
            elif "gpu_memory_usage" in rule.condition:
                gpu_devices = metrics.get('gpu', {}).get('devices', [])
                if gpu_devices:
                    value = max(device.get('memory', {}).get('percent', 0) for device in gpu_devices)
                else:
                    value = 0
            elif "gpu_temperature" in rule.condition:
                gpu_devices = metrics.get('gpu', {}).get('devices', [])
                if gpu_devices:
                    value = max(device.get('temperature_c', 0) for device in gpu_devices)
                else:
                    value = 0
            else:
                return False

            # Simple threshold comparison
            if ">" in rule.condition:
                return value > rule.threshold
            elif "<" in rule.condition:
                return value < rule.threshold
            elif "=" in rule.condition:
                return abs(value - rule.threshold) < 0.001
            else:
                return False

        except Exception as e:
            logger.error(f"Error evaluating alert condition {rule.condition}: {e}")
            return False

    def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert = Alert(
            rule_name=rule.name,
            level=rule.level,
            message=f"Alert {rule.name}: {rule.condition}",
            component=rule.component,
            context=metrics
        )

        with self._lock:
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

        rule.last_triggered = time.time()

        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.CRITICAL: logging.ERROR,
            AlertLevel.EMERGENCY: logging.CRITICAL
        }.get(rule.level, logging.WARNING)

        logger.log(log_level, f"ALERT [{rule.level.value.upper()}] {alert.message}")

        # Send notifications (would integrate with external systems)
        self._send_notification(alert)

    def _send_notification(self, alert: Alert):
        """Send alert notification (placeholder for integration)."""
        # This would integrate with external notification systems
        # like PagerDuty, Slack, email, etc.
        logger.info(f"Notification would be sent for alert: {alert.id}")

    def resolve_alert(self, alert_id: str):
        """Manually resolve an alert."""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_time = time.time()
                del self.active_alerts[alert_id]
                logger.info(f"Resolved alert: {alert_id}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self._lock:
            return list(self.active_alerts.values())

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            active_count = len(self.active_alerts)
            total_alerts = len(self.alert_history)

            # Count by level
            level_counts = defaultdict(int)
            for alert in self.alert_history:
                level_counts[alert.level.value] += 1

            # Recent alerts (last 24 hours)
            cutoff = time.time() - 86400
            recent_alerts = [a for a in self.alert_history if a.timestamp > cutoff]

            return {
                'active_alerts': active_count,
                'total_alerts': total_alerts,
                'recent_alerts_24h': len(recent_alerts),
                'alerts_by_level': dict(level_counts),
                'alert_rules_count': len(self.alert_rules),
                'enabled_rules': sum(1 for rule in self.alert_rules.values() if rule.enabled)
            }


class EnterpriseMonitoringSystem:
    """Comprehensive enterprise monitoring system."""

    def __init__(self):
        self.algorithm_monitor = ResearchAlgorithmMonitor()
        self.resource_monitor = SystemResourceMonitor()
        self.alert_manager = AlertManager()
        self.metrics_store: Dict[str, List[Metric]] = defaultdict(list)
        self.running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()

    async def start_monitoring(self, collection_interval: float = 10.0):
        """Start the monitoring system."""
        if self.running:
            logger.warning("Monitoring system is already running")
            return

        self.running = True
        logger.info("Starting enterprise monitoring system")

        # Start monitoring task
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(collection_interval)
        )

    async def stop_monitoring(self):
        """Stop the monitoring system."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping enterprise monitoring system")

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self.resource_monitor.collect_system_metrics()

                # Store metrics
                self._store_metrics(system_metrics)

                # Evaluate alerts
                self.alert_manager.evaluate_alerts(system_metrics)

                # Check for algorithm performance anomalies
                await self._check_algorithm_anomalies()

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(interval)

    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in the metrics store."""
        timestamp = metrics.get('timestamp', time.time())

        # Convert nested metrics to flat metrics
        flat_metrics = self._flatten_metrics(metrics, timestamp)

        with self._lock:
            for metric in flat_metrics:
                self.metrics_store[metric.name].append(metric)

                # Keep only recent metrics (last 24 hours)
                cutoff_time = time.time() - 86400
                self.metrics_store[metric.name] = [
                    m for m in self.metrics_store[metric.name]
                    if m.timestamp > cutoff_time
                ]

    def _flatten_metrics(self, data: Dict[str, Any], timestamp: float, prefix: str = "") -> List[Metric]:
        """Flatten nested metrics dictionary."""
        metrics = []

        for key, value in data.items():
            if key == 'timestamp':
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                metrics.extend(self._flatten_metrics(value, timestamp, full_key))
            elif isinstance(value, (int, float)):
                # Create metric for numeric values
                metric = Metric(
                    name=full_key,
                    type=MetricType.GAUGE,
                    value=float(value),
                    timestamp=timestamp
                )
                metrics.append(metric)

        return metrics

    async def _check_algorithm_anomalies(self):
        """Check for algorithm performance anomalies."""
        for algorithm_name in self.algorithm_monitor.algorithm_metrics.keys():
            anomalies = self.algorithm_monitor.detect_performance_anomalies(algorithm_name)

            for anomaly in anomalies:
                if anomaly['severity'] == 'high':
                    # Create alert for high-severity anomalies
                    alert = Alert(
                        rule_name=f"algorithm_anomaly_{algorithm_name}",
                        level=AlertLevel.WARNING,
                        message=f"Performance anomaly detected in {algorithm_name}: {anomaly['type']} in {anomaly['metric']}",
                        component=ComponentType.QUANTUM_PROCESSOR,  # Default, could be more specific
                        context=anomaly
                    )

                    with self._lock:
                        self.alert_manager.active_alerts[alert.id] = alert
                        self.alert_manager.alert_history.append(alert)

    def record_algorithm_metrics(
        self,
        algorithm_name: str,
        execution_time: float,
        throughput: float,
        accuracy: float,
        confidence: float,
        resource_usage: Dict[str, float],
        error_count: int = 0,
        success_count: int = 1
    ):
        """Record metrics for a research algorithm."""
        self.algorithm_monitor.record_algorithm_performance(
            algorithm_name=algorithm_name,
            execution_time=execution_time,
            throughput=throughput,
            accuracy=accuracy,
            confidence=confidence,
            resource_usage=resource_usage,
            error_count=error_count,
            success_count=success_count
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        # System metrics
        system_metrics = self.resource_monitor.collect_system_metrics()

        # Alert statistics
        alert_stats = self.alert_manager.get_alert_statistics()

        # Algorithm statistics
        algorithm_stats = {}
        for algorithm_name in self.algorithm_monitor.algorithm_metrics.keys():
            algorithm_stats[algorithm_name] = self.algorithm_monitor.get_algorithm_statistics(algorithm_name)

        # Active alerts
        active_alerts = self.alert_manager.get_active_alerts()

        # Resource trends
        resource_trends = {}
        for metric in ['cpu', 'memory', 'disk']:
            trends = self.resource_monitor.get_resource_trends(metric, 60)  # Last hour
            if 'error' not in trends:
                resource_trends[metric] = trends

        return {
            'timestamp': time.time(),
            'system_metrics': system_metrics,
            'alert_statistics': alert_stats,
            'active_alerts': [
                {
                    'id': alert.id,
                    'level': alert.level.value,
                    'message': alert.message,
                    'component': alert.component.value,
                    'timestamp': alert.timestamp
                }
                for alert in active_alerts
            ],
            'algorithm_statistics': algorithm_stats,
            'resource_trends': resource_trends,
            'health_status': self._calculate_overall_health_status()
        }

    def _calculate_overall_health_status(self) -> str:
        """Calculate overall system health status."""
        active_alerts = self.alert_manager.get_active_alerts()

        # Check for critical alerts
        critical_alerts = [a for a in active_alerts if a.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]]
        if critical_alerts:
            return HealthStatus.CRITICAL.value

        # Check for warning alerts
        warning_alerts = [a for a in active_alerts if a.level == AlertLevel.WARNING]
        if len(warning_alerts) > 5:  # Many warnings indicate degraded health
            return HealthStatus.DEGRADED.value
        elif warning_alerts:
            return HealthStatus.DEGRADED.value

        # Check system resources
        try:
            system_metrics = self.resource_monitor.collect_system_metrics()
            cpu_usage = system_metrics.get('cpu', {}).get('percent', 0)
            memory_usage = system_metrics.get('memory', {}).get('percent', 0)

            if cpu_usage > 90 or memory_usage > 90:
                return HealthStatus.UNHEALTHY.value
            elif cpu_usage > 80 or memory_usage > 80:
                return HealthStatus.DEGRADED.value
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return HealthStatus.DEGRADED.value

        return HealthStatus.HEALTHY.value

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        return {
            'monitoring_system': {
                'running': self.running,
                'uptime_seconds': time.time() - (self._monitoring_task.get_coro().cr_frame.f_locals.get('start_time', time.time()) if self._monitoring_task else time.time())
            },
            'system_health': self._calculate_overall_health_status(),
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'metrics_collected': sum(len(metrics) for metrics in self.metrics_store.values()),
            'algorithms_monitored': len(self.algorithm_monitor.algorithm_metrics),
            'timestamp': time.time()
        }


# Global monitoring system instance
monitoring_system = EnterpriseMonitoringSystem()


# Decorator for automatic performance monitoring
def monitor_algorithm_performance(algorithm_name: str):
    """Decorator to automatically monitor algorithm performance."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error_count = 0
            success_count = 0

            try:
                result = await func(*args, **kwargs)
                success_count = 1

                # Extract metrics from result if it's a dict
                accuracy = result.get('accuracy', 0.0) if isinstance(result, dict) else 0.0
                confidence = result.get('confidence', 0.0) if isinstance(result, dict) else 0.0

            except Exception:
                error_count = 1
                accuracy = 0.0
                confidence = 0.0
                raise
            finally:
                execution_time = time.time() - start_time
                throughput = 1.0 / execution_time if execution_time > 0 else 0.0

                # Get current resource usage
                resource_usage = {
                    'memory_mb': psutil.virtual_memory().used / (1024**2),
                    'cpu_percent': psutil.cpu_percent()
                }

                # Record metrics
                monitoring_system.record_algorithm_metrics(
                    algorithm_name=algorithm_name,
                    execution_time=execution_time,
                    throughput=throughput,
                    accuracy=accuracy,
                    confidence=confidence,
                    resource_usage=resource_usage,
                    error_count=error_count,
                    success_count=success_count
                )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error_count = 0
            success_count = 0

            try:
                result = func(*args, **kwargs)
                success_count = 1

                # Extract metrics from result if it's a dict
                accuracy = result.get('accuracy', 0.0) if isinstance(result, dict) else 0.0
                confidence = result.get('confidence', 0.0) if isinstance(result, dict) else 0.0

            except Exception:
                error_count = 1
                accuracy = 0.0
                confidence = 0.0
                raise
            finally:
                execution_time = time.time() - start_time
                throughput = 1.0 / execution_time if execution_time > 0 else 0.0

                # Get current resource usage
                resource_usage = {
                    'memory_mb': psutil.virtual_memory().used / (1024**2),
                    'cpu_percent': psutil.cpu_percent()
                }

                # Record metrics
                monitoring_system.record_algorithm_metrics(
                    algorithm_name=algorithm_name,
                    execution_time=execution_time,
                    throughput=throughput,
                    accuracy=accuracy,
                    confidence=confidence,
                    resource_usage=resource_usage,
                    error_count=error_count,
                    success_count=success_count
                )

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_monitoring_system() -> EnterpriseMonitoringSystem:
    """Get the global monitoring system instance."""
    return monitoring_system
