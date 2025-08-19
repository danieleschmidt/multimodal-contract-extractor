"""Advanced Monitoring and Analytics for Production Legal AI Systems."""

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for monitoring."""

    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    BUSINESS_IMPACT = "business_impact"
    MODEL_DRIFT = "model_drift"
    DATA_QUALITY = "data_quality"


class AlertSeverity(Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalyticsScope(Enum):
    """Scope of analytics analysis."""

    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class MetricPoint:
    """Single metric data point."""

    timestamp: float
    metric_name: str
    metric_type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert for monitoring."""

    id: str
    severity: AlertSeverity
    metric_name: str
    message: str
    threshold: float
    current_value: float
    timestamp: float
    resolved: bool = False
    resolution_time: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalyticsReport:
    """Analytics report for a specific time period."""

    scope: AnalyticsScope
    start_time: float
    end_time: float
    metrics_summary: Dict[str, Dict[str, float]]
    trends: Dict[str, str]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]
    sla_compliance: Dict[str, float]


class AdvancedMonitoringSystem:
    """Advanced monitoring and analytics system for legal AI applications."""

    def __init__(self, retention_hours: int = 168):  # 1 week default
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.retention_hours = retention_hours
        self.last_cleanup = time.time()

        # SLA thresholds
        self.sla_thresholds = {
            "accuracy": 0.85,
            "latency_p95": 2000,  # milliseconds
            "error_rate": 0.05,
            "availability": 0.999
        }

        # Initialize monitoring
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self) -> None:
        """Setup default alerting rules."""
        self.alert_rules = {
            "accuracy_drop": {
                "metric_name": "model_accuracy",
                "threshold": 0.80,
                "comparison": "less_than",
                "severity": AlertSeverity.HIGH,
                "message": "Model accuracy dropped below acceptable threshold"
            },
            "high_latency": {
                "metric_name": "response_latency_p95",
                "threshold": 5000,  # 5 seconds
                "comparison": "greater_than",
                "severity": AlertSeverity.MEDIUM,
                "message": "Response latency exceeded threshold"
            },
            "error_rate_spike": {
                "metric_name": "error_rate",
                "threshold": 0.10,
                "comparison": "greater_than",
                "severity": AlertSeverity.CRITICAL,
                "message": "Error rate spiked above threshold"
            },
            "memory_usage_high": {
                "metric_name": "memory_usage_percent",
                "threshold": 85.0,
                "comparison": "greater_than",
                "severity": AlertSeverity.HIGH,
                "message": "Memory usage exceeded threshold"
            },
            "model_drift_detected": {
                "metric_name": "model_drift_score",
                "threshold": 0.15,
                "comparison": "greater_than",
                "severity": AlertSeverity.MEDIUM,
                "message": "Significant model drift detected"
            }
        }

    async def record_metric(
        self,
        metric_name: str,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric point."""
        metric_point = MetricPoint(
            timestamp=time.time(),
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            tags=tags or {},
            metadata=metadata or {}
        )

        self.metrics_buffer.append(metric_point)

        # Check alert rules
        await self._check_alert_rules(metric_point)

        # Periodic cleanup
        if time.time() - self.last_cleanup > 3600:  # Every hour
            await self._cleanup_old_metrics()

    async def _check_alert_rules(self, metric_point: MetricPoint) -> None:
        """Check if metric point triggers any alerts."""
        for rule_name, rule in self.alert_rules.items():
            if metric_point.metric_name == rule["metric_name"]:
                threshold = rule["threshold"]
                comparison = rule["comparison"]

                alert_triggered = False
                if comparison == "greater_than" and metric_point.value > threshold:
                    alert_triggered = True
                elif comparison == "less_than" and metric_point.value < threshold:
                    alert_triggered = True
                elif comparison == "equals" and abs(metric_point.value - threshold) < 0.001:
                    alert_triggered = True

                if alert_triggered:
                    await self._create_alert(rule, metric_point)

    async def _create_alert(self, rule: Dict[str, Any], metric_point: MetricPoint) -> None:
        """Create and store an alert."""
        alert = Alert(
            id=f"alert_{len(self.alerts)}_{int(time.time())}",
            severity=rule["severity"],
            metric_name=metric_point.metric_name,
            message=rule["message"],
            threshold=rule["threshold"],
            current_value=metric_point.value,
            timestamp=metric_point.timestamp,
            tags=metric_point.tags.copy()
        )

        self.alerts.append(alert)
        logger.warning(f"Alert triggered: {alert.message} (value: {alert.current_value})")

    async def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period."""
        cutoff_time = time.time() - (self.retention_hours * 3600)

        # Convert deque to list, filter, and recreate deque
        metrics_list = list(self.metrics_buffer)
        filtered_metrics = [m for m in metrics_list if m.timestamp > cutoff_time]

        self.metrics_buffer.clear()
        self.metrics_buffer.extend(filtered_metrics)

        self.last_cleanup = time.time()
        logger.info(f"Cleaned up old metrics, retained {len(filtered_metrics)} points")

    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """Retrieve metrics based on filters."""
        filtered_metrics = list(self.metrics_buffer)

        if metric_name:
            filtered_metrics = [m for m in filtered_metrics if m.metric_name == metric_name]

        if metric_type:
            filtered_metrics = [m for m in filtered_metrics if m.metric_type == metric_type]

        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]

        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]

        if tags:
            def matches_tags(metric: MetricPoint) -> bool:
                return all(metric.tags.get(k) == v for k, v in tags.items())
            filtered_metrics = [m for m in filtered_metrics if matches_tags(m)]

        return sorted(filtered_metrics, key=lambda m: m.timestamp)

    def calculate_metric_statistics(
        self, metrics: List[MetricPoint]
    ) -> Dict[str, float]:
        """Calculate statistical measures for metrics."""
        if not metrics:
            return {}

        values = [m.value for m in metrics]

        statistics_dict = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99)
        }

        return statistics_dict

    def detect_anomalies(
        self, metrics: List[MetricPoint], sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in metric series using statistical methods."""
        if len(metrics) < 10:
            return []

        values = [m.value for m in metrics]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        anomalies = []
        for metric in metrics:
            if std_val > 0:
                z_score = abs(metric.value - mean_val) / std_val
                if z_score > sensitivity:
                    anomalies.append({
                        "timestamp": metric.timestamp,
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "z_score": z_score,
                        "expected_range": (mean_val - sensitivity * std_val,
                                         mean_val + sensitivity * std_val)
                    })

        return anomalies

    def analyze_trends(
        self, metrics: List[MetricPoint], window_size: int = 20
    ) -> Dict[str, str]:
        """Analyze trends in metric data."""
        if len(metrics) < window_size:
            return {"trend": "insufficient_data"}

        values = [m.value for m in metrics[-window_size:]]

        # Simple linear trend analysis
        x = list(range(len(values)))
        correlation = np.corrcoef(x, values)[0, 1]

        if correlation > 0.7:
            trend = "strongly_increasing"
        elif correlation > 0.3:
            trend = "increasing"
        elif correlation > -0.3:
            trend = "stable"
        elif correlation > -0.7:
            trend = "decreasing"
        else:
            trend = "strongly_decreasing"

        # Calculate trend strength
        slope = np.polyfit(x, values, 1)[0]

        return {
            "trend": trend,
            "correlation": correlation,
            "slope": slope,
            "confidence": abs(correlation)
        }

    def check_sla_compliance(
        self, start_time: float, end_time: float
    ) -> Dict[str, float]:
        """Check SLA compliance for the given time period."""
        compliance_results = {}

        for sla_metric, threshold in self.sla_thresholds.items():
            metrics = self.get_metrics(
                metric_name=sla_metric,
                start_time=start_time,
                end_time=end_time
            )

            if not metrics:
                compliance_results[sla_metric] = 0.0
                continue

            if sla_metric == "accuracy":
                # For accuracy, calculate percentage of time above threshold
                compliant_points = sum(1 for m in metrics if m.value >= threshold)
                compliance_rate = compliant_points / len(metrics)
            elif sla_metric == "latency_p95":
                # For latency, calculate percentage of time below threshold
                stats = self.calculate_metric_statistics(metrics)
                compliance_rate = 1.0 if stats.get("p95", float('inf')) <= threshold else 0.0
            elif sla_metric == "error_rate":
                # For error rate, calculate percentage of time below threshold
                compliant_points = sum(1 for m in metrics if m.value <= threshold)
                compliance_rate = compliant_points / len(metrics)
            elif sla_metric == "availability":
                # For availability, calculate uptime percentage
                # Simplified: assume all recorded metrics indicate uptime
                compliance_rate = min(1.0, len(metrics) / max(1, (end_time - start_time) / 60))
            else:
                compliance_rate = 0.0

            compliance_results[sla_metric] = compliance_rate

        return compliance_results

    async def generate_analytics_report(
        self, scope: AnalyticsScope, start_time: float, end_time: float
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        # Get all metrics for the period
        all_metrics = self.get_metrics(start_time=start_time, end_time=end_time)

        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in all_metrics:
            metrics_by_name[metric.metric_name].append(metric)

        # Calculate summary statistics
        metrics_summary = {}
        for metric_name, metric_list in metrics_by_name.items():
            metrics_summary[metric_name] = self.calculate_metric_statistics(metric_list)

        # Analyze trends
        trends = {}
        for metric_name, metric_list in metrics_by_name.items():
            trends[metric_name] = self.analyze_trends(metric_list)["trend"]

        # Detect anomalies
        all_anomalies = []
        for metric_name, metric_list in metrics_by_name.items():
            anomalies = self.detect_anomalies(metric_list)
            all_anomalies.extend(anomalies)

        # Check SLA compliance
        sla_compliance = self.check_sla_compliance(start_time, end_time)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics_summary, trends, all_anomalies, sla_compliance
        )

        return AnalyticsReport(
            scope=scope,
            start_time=start_time,
            end_time=end_time,
            metrics_summary=metrics_summary,
            trends=trends,
            anomalies=all_anomalies,
            recommendations=recommendations,
            sla_compliance=sla_compliance
        )

    def _generate_recommendations(
        self,
        metrics_summary: Dict[str, Dict[str, float]],
        trends: Dict[str, str],
        anomalies: List[Dict[str, Any]],
        sla_compliance: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []

        # Check for performance issues
        if "response_latency_p95" in metrics_summary:
            latency_stats = metrics_summary["response_latency_p95"]
            if latency_stats.get("p95", 0) > 3000:  # > 3 seconds
                recommendations.append(
                    "Consider optimizing response latency - 95th percentile exceeds 3 seconds"
                )

        # Check for accuracy degradation
        if "model_accuracy" in trends:
            if trends["model_accuracy"] in ["decreasing", "strongly_decreasing"]:
                recommendations.append(
                    "Model accuracy is trending downward - consider retraining or model refresh"
                )

        # Check for resource issues
        if "memory_usage_percent" in metrics_summary:
            memory_stats = metrics_summary["memory_usage_percent"]
            if memory_stats.get("mean", 0) > 80:
                recommendations.append(
                    "High memory usage detected - consider scaling resources or optimization"
                )

        # Check SLA compliance
        for sla_metric, compliance_rate in sla_compliance.items():
            if compliance_rate < 0.95:  # Below 95% compliance
                recommendations.append(
                    f"SLA compliance for {sla_metric} is below target (95%): {compliance_rate:.2%}"
                )

        # Check for anomalies
        if len(anomalies) > 10:
            recommendations.append(
                f"High number of anomalies detected ({len(anomalies)}) - investigate potential issues"
            )

        # Error rate recommendations
        if "error_rate" in trends and trends["error_rate"] == "increasing":
            recommendations.append(
                "Error rate is increasing - investigate recent changes and error patterns"
            )

        return recommendations

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get currently active (unresolved) alerts."""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]

        if severity:
            active_alerts = [alert for alert in active_alerts if alert.severity == severity]

        return sorted(active_alerts, key=lambda a: a.timestamp, reverse=True)

    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = time.time()
                logger.info(f"Alert {alert_id} resolved")
                return True
        return False

    def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        current_time = time.time()
        last_hour = current_time - 3600

        # Get recent metrics
        recent_metrics = self.get_metrics(start_time=last_hour)

        if not recent_metrics:
            return {"health_score": 0.0, "status": "no_data"}

        health_components = {}

        # Accuracy health
        accuracy_metrics = [m for m in recent_metrics if m.metric_name == "model_accuracy"]
        if accuracy_metrics:
            avg_accuracy = statistics.mean([m.value for m in accuracy_metrics])
            health_components["accuracy"] = min(1.0, avg_accuracy / 0.85)  # Normalize to 85% baseline

        # Latency health
        latency_metrics = [m for m in recent_metrics if "latency" in m.metric_name]
        if latency_metrics:
            avg_latency = statistics.mean([m.value for m in latency_metrics])
            health_components["latency"] = max(0.0, 1.0 - (avg_latency / 5000))  # 5s max acceptable

        # Error rate health
        error_metrics = [m for m in recent_metrics if m.metric_name == "error_rate"]
        if error_metrics:
            avg_error_rate = statistics.mean([m.value for m in error_metrics])
            health_components["error_rate"] = max(0.0, 1.0 - (avg_error_rate / 0.1))  # 10% max

        # Active alerts impact
        critical_alerts = len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.CRITICAL])
        high_alerts = len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.HIGH])

        alert_penalty = (critical_alerts * 0.3) + (high_alerts * 0.1)
        health_components["alerts"] = max(0.0, 1.0 - alert_penalty)

        # Calculate overall health score
        if health_components:
            overall_score = statistics.mean(health_components.values())
        else:
            overall_score = 0.5  # Neutral score if no components

        # Determine status
        if overall_score >= 0.9:
            status = "excellent"
        elif overall_score >= 0.7:
            status = "good"
        elif overall_score >= 0.5:
            status = "fair"
        elif overall_score >= 0.3:
            status = "poor"
        else:
            status = "critical"

        return {
            "health_score": overall_score,
            "status": status,
            "components": health_components,
            "active_alerts": {
                "critical": critical_alerts,
                "high": high_alerts,
                "total": len(self.get_active_alerts())
            }
        }


# Global monitoring system instance
monitoring_system = AdvancedMonitoringSystem()


async def record_performance_metric(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a performance metric."""
    await monitoring_system.record_metric(
        metric_name, MetricType.PERFORMANCE, value, tags
    )


async def record_accuracy_metric(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record an accuracy metric."""
    await monitoring_system.record_metric(
        metric_name, MetricType.ACCURACY, value, tags
    )


async def record_business_metric(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a business impact metric."""
    await monitoring_system.record_metric(
        metric_name, MetricType.BUSINESS_IMPACT, value, tags
    )


def get_monitoring_system() -> AdvancedMonitoringSystem:
    """Get the global monitoring system instance."""
    return monitoring_system


async def generate_daily_report() -> AnalyticsReport:
    """Generate daily analytics report."""
    end_time = time.time()
    start_time = end_time - 86400  # 24 hours ago

    return await monitoring_system.generate_analytics_report(
        AnalyticsScope.DAILY, start_time, end_time
    )
