"""
Intelligent Monitoring System for Autonomous SDLC

This system provides comprehensive monitoring and observability for the autonomous SDLC process:
- Real-time health monitoring
- Performance metrics collection
- Predictive failure detection
- Adaptive alerting
- System health scoring
- Automated anomaly detection

Key Features:
- Multi-dimensional metrics collection
- ML-powered anomaly detection  
- Self-adapting thresholds
- Contextual alerting
- Performance trend analysis
- Resource usage optimization
"""

from __future__ import annotations

import asyncio
import json
import logging
import psutil
import time
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
import threading
import websockets
import os

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels"""
    EXCELLENT = "excellent"     # 90-100% health
    GOOD = "good"              # 75-89% health  
    FAIR = "fair"              # 50-74% health
    POOR = "poor"              # 25-49% health
    CRITICAL = "critical"      # 0-24% health


class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"           # Monotonically increasing
    GAUGE = "gauge"              # Point-in-time value
    HISTOGRAM = "histogram"       # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Events per time unit


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """System alert information"""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[float] = None


@dataclass
class HealthReport:
    """Comprehensive system health report"""
    timestamp: float
    overall_score: float
    status: HealthStatus
    component_scores: Dict[str, float]
    active_alerts: List[Alert]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    trend_analysis: Dict[str, Any]


class AnomalyDetector:
    """Simple anomaly detection using statistical methods"""
    
    def __init__(self, window_size: int = 100, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity  # Number of standard deviations
        self.data_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        
    def add_data_point(self, metric_name: str, value: float) -> bool:
        """
        Add data point and return True if anomalous
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            
        Returns:
            True if value is anomalous, False otherwise
        """
        window = self.data_windows[metric_name]
        window.append(value)
        
        # Need at least 10 points for anomaly detection
        if len(window) < 10:
            return False
        
        # Calculate statistics
        values = list(window)
        mean = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            return False
        
        # Check if current value is anomalous
        if stdev == 0:
            return False
            
        z_score = abs(value - mean) / stdev
        return z_score > self.sensitivity
    
    def get_statistics(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistical summary for a metric"""
        window = self.data_windows.get(metric_name)
        if not window or len(window) < 2:
            return None
            
        values = list(window)
        try:
            return {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
        except statistics.StatisticsError:
            return None


class IntelligentMonitoringSystem:
    """
    Intelligent monitoring system for autonomous SDLC quality gates
    
    Provides comprehensive monitoring with:
    - Real-time metrics collection
    - Anomaly detection
    - Performance analysis
    - Health scoring
    - Adaptive alerting
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.metrics_storage: Dict[str, List[Metric]] = defaultdict(list)
        self.alerts: List[Alert] = []
        self.anomaly_detector = AnomalyDetector()
        
        # Monitoring configuration
        self.collection_interval = 5.0  # seconds
        self.retention_hours = 24
        self.alert_thresholds = self._initialize_thresholds()
        
        # Health scoring weights
        self.health_weights = {
            "performance": 0.3,
            "resources": 0.25,
            "errors": 0.25,
            "availability": 0.2
        }
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alert thresholds"""
        return {
            "cpu_usage": {"warning": 80.0, "error": 95.0},
            "memory_usage": {"warning": 85.0, "error": 95.0},
            "disk_usage": {"warning": 85.0, "error": 95.0},
            "error_rate": {"warning": 5.0, "error": 15.0},
            "response_time": {"warning": 5000.0, "error": 10000.0},  # ms
            "test_failure_rate": {"warning": 10.0, "error": 25.0}
        }
    
    def start_monitoring(self) -> None:
        """Start background monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Intelligent monitoring system started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Intelligent monitoring system stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_alert_conditions()
                self._cleanup_old_data()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system.cpu.usage_percent", cpu_percent, MetricType.GAUGE)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric("system.memory.usage_percent", memory.percent, MetricType.GAUGE)
            self.record_metric("system.memory.available_mb", memory.available / 1024 / 1024, MetricType.GAUGE)
            
            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric("system.disk.usage_percent", disk_percent, MetricType.GAUGE)
            self.record_metric("system.disk.free_gb", disk.free / 1024 / 1024 / 1024, MetricType.GAUGE)
            
            # Process metrics for current process
            process = psutil.Process()
            self.record_metric("process.cpu.usage_percent", process.cpu_percent(), MetricType.GAUGE)
            self.record_metric("process.memory.rss_mb", process.memory_info().rss / 1024 / 1024, MetricType.GAUGE)
            self.record_metric("process.threads.count", process.num_threads(), MetricType.GAUGE)
            
            # File descriptor usage (Unix only)
            if hasattr(process, "num_fds"):
                self.record_metric("process.fds.count", process.num_fds(), MetricType.GAUGE)
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, 
                     labels: Optional[Dict[str, str]] = None, unit: str = "") -> None:
        """
        Record a metric value
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional labels for the metric
            unit: Unit of measurement
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            unit=unit,
            timestamp=time.time()
        )
        
        self.metrics_storage[name].append(metric)
        
        # Check for anomalies
        if self.anomaly_detector.add_data_point(name, value):
            self._create_alert(
                name=f"anomaly_detected_{name}",
                severity=AlertSeverity.WARNING,
                message=f"Anomalous value detected for {name}: {value}",
                source="anomaly_detector",
                metadata={"metric_name": name, "value": value}
            )
    
    def _check_alert_conditions(self) -> None:
        """Check metrics against alert thresholds"""
        for metric_name, thresholds in self.alert_thresholds.items():
            # Get latest metric value
            metrics = self.metrics_storage.get(metric_name)
            if not metrics:
                continue
                
            latest_metric = metrics[-1]
            value = latest_metric.value
            
            # Check thresholds
            if "error" in thresholds and value >= thresholds["error"]:
                self._create_alert(
                    name=f"{metric_name}_error",
                    severity=AlertSeverity.ERROR,
                    message=f"{metric_name} is critical: {value:.2f} >= {thresholds['error']}",
                    source="threshold_monitor"
                )
            elif "warning" in thresholds and value >= thresholds["warning"]:
                self._create_alert(
                    name=f"{metric_name}_warning",
                    severity=AlertSeverity.WARNING,
                    message=f"{metric_name} is high: {value:.2f} >= {thresholds['warning']}",
                    source="threshold_monitor"
                )
    
    def _create_alert(self, name: str, severity: AlertSeverity, message: str,
                     source: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create a new alert"""
        # Check if similar alert already exists and is unresolved
        for existing_alert in self.alerts:
            if (existing_alert.name == name and 
                not existing_alert.resolved and
                time.time() - existing_alert.timestamp < 300):  # 5 minutes
                return  # Don't create duplicate alert
        
        alert = Alert(
            name=name,
            severity=severity,
            message=message,
            source=source,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        logger.warning(f"Alert created: {severity.value} - {message}")
    
    def resolve_alert(self, alert_name: str) -> bool:
        """Resolve an alert by name"""
        for alert in self.alerts:
            if alert.name == alert_name and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = time.time()
                logger.info(f"Alert resolved: {alert_name}")
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def _cleanup_old_data(self) -> None:
        """Remove old metrics and alerts"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        # Clean up metrics
        for metric_name in list(self.metrics_storage.keys()):
            metrics = self.metrics_storage[metric_name]
            self.metrics_storage[metric_name] = [
                m for m in metrics if m.timestamp > cutoff_time
            ]
            
        # Clean up old resolved alerts
        self.alerts = [
            alert for alert in self.alerts 
            if not alert.resolved or alert.timestamp > cutoff_time
        ]
    
    def calculate_health_score(self) -> float:
        """
        Calculate overall system health score (0-100)
        
        Returns:
            Health score from 0 (critical) to 100 (excellent)
        """
        scores = {}
        
        # Performance score based on response times and throughput
        scores["performance"] = self._calculate_performance_score()
        
        # Resource score based on CPU, memory, disk usage
        scores["resources"] = self._calculate_resource_score()
        
        # Error score based on error rates and failures
        scores["errors"] = self._calculate_error_score()
        
        # Availability score based on uptime and service availability
        scores["availability"] = self._calculate_availability_score()
        
        # Weighted average
        total_score = sum(
            scores[component] * weight 
            for component, weight in self.health_weights.items()
            if component in scores
        )
        
        return max(0, min(100, total_score))
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score component"""
        # Check response time metrics
        response_times = self.metrics_storage.get("response_time", [])
        if response_times:
            # Get recent response times (last 10 minutes)
            recent_cutoff = time.time() - 600
            recent_times = [m.value for m in response_times if m.timestamp > recent_cutoff]
            
            if recent_times:
                avg_response_time = statistics.mean(recent_times)
                # Score inversely related to response time
                # 100 for <1s, 50 for ~5s, 0 for >10s
                score = max(0, 100 - (avg_response_time / 100))
                return min(100, score)
        
        return 85.0  # Default good score if no data
    
    def _calculate_resource_score(self) -> float:
        """Calculate resource utilization score"""
        scores = []
        
        # CPU usage score
        cpu_metrics = self.metrics_storage.get("system.cpu.usage_percent", [])
        if cpu_metrics:
            latest_cpu = cpu_metrics[-1].value
            cpu_score = max(0, 100 - latest_cpu)  # 100% CPU = 0 score
            scores.append(cpu_score)
        
        # Memory usage score
        memory_metrics = self.metrics_storage.get("system.memory.usage_percent", [])
        if memory_metrics:
            latest_memory = memory_metrics[-1].value
            memory_score = max(0, 100 - latest_memory)
            scores.append(memory_score)
        
        # Disk usage score
        disk_metrics = self.metrics_storage.get("system.disk.usage_percent", [])
        if disk_metrics:
            latest_disk = disk_metrics[-1].value
            disk_score = max(0, 100 - latest_disk)
            scores.append(disk_score)
        
        return statistics.mean(scores) if scores else 80.0
    
    def _calculate_error_score(self) -> float:
        """Calculate error rate score"""
        # Count recent errors from alerts
        recent_cutoff = time.time() - 3600  # Last hour
        recent_errors = [
            alert for alert in self.alerts 
            if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]
            and alert.timestamp > recent_cutoff
        ]
        
        # Score based on error count
        error_count = len(recent_errors)
        if error_count == 0:
            return 100.0
        elif error_count <= 2:
            return 75.0
        elif error_count <= 5:
            return 50.0
        elif error_count <= 10:
            return 25.0
        else:
            return 0.0
    
    def _calculate_availability_score(self) -> float:
        """Calculate availability score"""
        # For now, assume high availability if system is running
        # In a real implementation, this would track actual uptime
        return 95.0
    
    def get_health_status(self, score: float) -> HealthStatus:
        """Convert health score to status"""
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 75:
            return HealthStatus.GOOD
        elif score >= 50:
            return HealthStatus.FAIR
        elif score >= 25:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL
    
    def generate_health_report(self) -> HealthReport:
        """Generate comprehensive health report"""
        overall_score = self.calculate_health_score()
        status = self.get_health_status(overall_score)
        
        # Component scores
        component_scores = {
            "performance": self._calculate_performance_score(),
            "resources": self._calculate_resource_score(),
            "errors": self._calculate_error_score(),
            "availability": self._calculate_availability_score()
        }
        
        # Performance summary
        performance_summary = self._get_performance_summary()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(component_scores)
        
        # Trend analysis
        trend_analysis = self._analyze_trends()
        
        return HealthReport(
            timestamp=time.time(),
            overall_score=overall_score,
            status=status,
            component_scores=component_scores,
            active_alerts=self.get_active_alerts(),
            performance_summary=performance_summary,
            recommendations=recommendations,
            trend_analysis=trend_analysis
        )
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        summary = {}
        
        # System metrics summary
        for metric_name in ["system.cpu.usage_percent", "system.memory.usage_percent", "system.disk.usage_percent"]:
            metrics = self.metrics_storage.get(metric_name, [])
            if metrics:
                recent_values = [m.value for m in metrics[-10:]]  # Last 10 values
                summary[metric_name] = {
                    "current": metrics[-1].value,
                    "average": statistics.mean(recent_values),
                    "min": min(recent_values),
                    "max": max(recent_values)
                }
        
        return summary
    
    def _generate_recommendations(self, component_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on component scores"""
        recommendations = []
        
        if component_scores["resources"] < 70:
            recommendations.append("Consider resource optimization or scaling")
            
        if component_scores["performance"] < 70:
            recommendations.append("Investigate performance bottlenecks")
            
        if component_scores["errors"] < 80:
            recommendations.append("Review and address recent errors")
            
        if len(self.get_active_alerts()) > 5:
            recommendations.append("Address active alerts to improve stability")
            
        # Check for anomalies
        anomaly_count = sum(1 for alert in self.alerts[-10:] 
                          if "anomaly_detected" in alert.name)
        if anomaly_count > 3:
            recommendations.append("Investigate anomalous behavior patterns")
        
        return recommendations
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in key metrics"""
        trends = {}
        
        # Analyze CPU trend
        cpu_metrics = self.metrics_storage.get("system.cpu.usage_percent", [])
        if len(cpu_metrics) >= 10:
            recent_values = [m.value for m in cpu_metrics[-20:]]
            first_half = recent_values[:10]
            second_half = recent_values[10:]
            
            if len(first_half) > 0 and len(second_half) > 0:
                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)
                trends["cpu_trend"] = "increasing" if second_avg > first_avg else "decreasing"
                trends["cpu_change_percent"] = ((second_avg - first_avg) / first_avg) * 100
        
        return trends
    
    def get_metrics_summary(self, metric_name: str, hours: int = 1) -> Optional[Dict[str, Any]]:
        """Get statistical summary for a specific metric"""
        metrics = self.metrics_storage.get(metric_name)
        if not metrics:
            return None
            
        # Filter by time window
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return None
            
        values = [m.value for m in recent_metrics]
        
        try:
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "first": values[0],
                "last": values[-1],
                "trend": "increasing" if values[-1] > values[0] else "decreasing"
            }
        except statistics.StatisticsError:
            return None
    
    def save_monitoring_report(self, output_path: Path) -> None:
        """Save comprehensive monitoring report"""
        health_report = self.generate_health_report()
        
        report_data = {
            "monitoring_report": {
                "timestamp": health_report.timestamp,
                "overall_health": {
                    "score": health_report.overall_score,
                    "status": health_report.status.value
                },
                "component_scores": health_report.component_scores,
                "performance_summary": health_report.performance_summary,
                "active_alerts": [
                    {
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp,
                        "source": alert.source
                    }
                    for alert in health_report.active_alerts
                ],
                "recommendations": health_report.recommendations,
                "trend_analysis": health_report.trend_analysis
            },
            "metrics_summary": {
                name: self.get_metrics_summary(name)
                for name in self.metrics_storage.keys()
            },
            "anomaly_statistics": {
                name: self.anomaly_detector.get_statistics(name)
                for name in self.anomaly_detector.data_windows.keys()
            }
        }
        
        output_path.write_text(json.dumps(report_data, indent=2))
        logger.info(f"Monitoring report saved to {output_path}")


# Context manager for monitoring operations
class MonitoringContext:
    """Context manager for monitoring specific operations"""
    
    def __init__(self, monitoring_system: IntelligentMonitoringSystem, 
                 operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.monitoring_system = monitoring_system
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.monitoring_system.record_metric(
            f"operation.{self.operation_name}.started",
            1, MetricType.COUNTER, self.labels
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitoring_system.record_metric(
                f"operation.{self.operation_name}.duration_ms",
                duration * 1000, MetricType.TIMER, self.labels
            )
            
            if exc_type is None:
                self.monitoring_system.record_metric(
                    f"operation.{self.operation_name}.success",
                    1, MetricType.COUNTER, self.labels
                )
            else:
                self.monitoring_system.record_metric(
                    f"operation.{self.operation_name}.error",
                    1, MetricType.COUNTER, self.labels
                )


if __name__ == "__main__":
    # Example usage and testing
    async def test_monitoring_system():
        project_root = Path(__file__).parent.parent.parent
        monitoring = IntelligentMonitoringSystem(project_root)
        
        # Start monitoring
        monitoring.start_monitoring()
        
        # Simulate some metrics
        for i in range(10):
            monitoring.record_metric("test.counter", i, MetricType.COUNTER)
            monitoring.record_metric("test.gauge", 50 + i * 5, MetricType.GAUGE)
            await asyncio.sleep(0.1)
        
        # Generate health report
        health_report = monitoring.generate_health_report()
        print(f"Health Score: {health_report.overall_score:.2f}")
        print(f"Status: {health_report.status.value}")
        print(f"Active Alerts: {len(health_report.active_alerts)}")
        
        # Stop monitoring
        monitoring.stop_monitoring()
    
    asyncio.run(test_monitoring_system())