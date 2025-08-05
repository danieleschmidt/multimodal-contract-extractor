"""
SLA/SLO monitoring and alerting system.
Service Level Agreement and Objective tracking with automated alerting.
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class SLAStatus(Enum):
    """SLA status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    BREACHED = "breached"


class MetricType(Enum):
    """Types of SLA metrics."""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CUSTOM = "custom"


@dataclass
class SLOTarget:
    """Service Level Objective target definition."""
    name: str
    metric_type: MetricType
    target_value: float
    comparison: str  # "<=", ">=", "==", "!=", "<", ">"
    window_minutes: int
    description: str
    critical_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        return data


@dataclass
class SLAMetric:
    """SLA metric measurement."""
    timestamp: str
    metric_type: MetricType
    value: float
    tags: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        return data


@dataclass
class SLOViolation:
    """SLO violation record."""
    id: str
    slo_name: str
    violation_time: str
    current_value: float
    target_value: float
    severity: SLAStatus
    duration_minutes: int
    resolved: bool = False
    resolved_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        return data


class SLAMonitoringConfig:
    """Configuration for SLA monitoring."""

    def __init__(self):
        # Storage configuration
        self.storage_directory = os.getenv('SLA_STORAGE_DIR', 'monitoring/sla')
        self.metrics_retention_days = int(os.getenv('SLA_METRICS_RETENTION_DAYS', '30'))

        # Monitoring configuration
        self.evaluation_interval_seconds = int(os.getenv('SLA_EVALUATION_INTERVAL', '60'))
        self.metric_collection_interval_seconds = int(os.getenv('SLA_COLLECTION_INTERVAL', '10'))

        # Alerting configuration
        self.alert_enabled = os.getenv('SLA_ALERTS_ENABLED', 'true').lower() == 'true'
        self.alert_webhook_url = os.getenv('SLA_ALERT_WEBHOOK_URL')
        self.alert_cooldown_minutes = int(os.getenv('SLA_ALERT_COOLDOWN', '15'))

        # Default SLO targets
        self.default_slos = self._load_default_slos()

    def _load_default_slos(self) -> List[SLOTarget]:
        """Load default SLO targets."""
        return [
            SLOTarget(
                name="api_availability",
                metric_type=MetricType.AVAILABILITY,
                target_value=99.9,  # 99.9% availability
                comparison=">=",
                window_minutes=60,
                description="API availability should be >= 99.9%",
                warning_threshold=99.5,
                critical_threshold=99.0
            ),
            SLOTarget(
                name="api_response_time",
                metric_type=MetricType.RESPONSE_TIME,
                target_value=1.0,  # 1 second
                comparison="<=",
                window_minutes=30,
                description="95th percentile response time should be <= 1s",
                warning_threshold=1.5,
                critical_threshold=3.0
            ),
            SLOTarget(
                name="error_rate",
                metric_type=MetricType.ERROR_RATE,
                target_value=1.0,  # 1% error rate
                comparison="<=",
                window_minutes=30,
                description="Error rate should be <= 1%",
                warning_threshold=2.0,
                critical_threshold=5.0
            ),
            SLOTarget(
                name="processing_throughput",
                metric_type=MetricType.THROUGHPUT,
                target_value=100.0,  # 100 requests/minute
                comparison=">=",
                window_minutes=60,
                description="Processing throughput should be >= 100 req/min",
                warning_threshold=75.0,
                critical_threshold=50.0
            )
        ]


class SLAMonitor:
    """SLA/SLO monitoring system."""

    def __init__(self, config: Optional[SLAMonitoringConfig] = None):
        self.config = config or SLAMonitoringConfig()
        self.logger = logging.getLogger(__name__)

        # Storage setup
        self.storage_path = Path(self.config.storage_directory)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # SLO targets
        self.slo_targets: Dict[str, SLOTarget] = {}
        for slo in self.config.default_slos:
            self.slo_targets[slo.name] = slo

        # Metrics storage (in-memory with time-based cleanup)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metrics_lock = threading.Lock()

        # Violation tracking
        self.violations: Dict[str, SLOViolation] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}

        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False

        # Current status cache
        self.current_status: Dict[str, Dict[str, Any]] = {}

        # Load existing data
        self._load_violations()

    def add_slo_target(self, slo: SLOTarget) -> None:
        """Add or update an SLO target."""
        self.slo_targets[slo.name] = slo
        self.logger.info(f"Added SLO target: {slo.name}")

    def remove_slo_target(self, slo_name: str) -> bool:
        """Remove an SLO target."""
        if slo_name in self.slo_targets:
            del self.slo_targets[slo_name]
            self.logger.info(f"Removed SLO target: {slo_name}")
            return True
        return False

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric measurement."""
        metric = SLAMetric(
            timestamp=datetime.now(timezone.utc).isoformat(),
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )

        with self.metrics_lock:
            self.metrics[metric_type.value].append(metric)

        # Immediate evaluation for critical metrics
        if metric_type in [MetricType.AVAILABILITY, MetricType.ERROR_RATE]:
            self._evaluate_slos_for_metric_type(metric_type)

    def record_request(
        self,
        response_time: float,
        success: bool,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a request for SLA calculation."""
        current_time = datetime.now(timezone.utc)

        # Record response time
        self.record_metric(MetricType.RESPONSE_TIME, response_time, tags)

        # Record success/failure for availability and error rate
        self.record_metric(MetricType.AVAILABILITY, 1.0 if success else 0.0, tags)

        # Update throughput counter
        self.record_metric(MetricType.THROUGHPUT, 1.0, tags)

    def start_monitoring(self) -> None:
        """Start the SLA monitoring thread."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("SLA monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the SLA monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("SLA monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Evaluate all SLOs
                self._evaluate_all_slos()

                # Cleanup old metrics
                self._cleanup_old_metrics()

                # Sleep until next evaluation
                time.sleep(self.config.evaluation_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Brief sleep on error

    def _evaluate_all_slos(self) -> None:
        """Evaluate all SLO targets."""
        for slo_name, slo_target in self.slo_targets.items():
            try:
                self._evaluate_slo(slo_target)
            except Exception as e:
                self.logger.error(f"Error evaluating SLO {slo_name}: {e}")

    def _evaluate_slos_for_metric_type(self, metric_type: MetricType) -> None:
        """Evaluate SLOs for a specific metric type."""
        for slo_target in self.slo_targets.values():
            if slo_target.metric_type == metric_type:
                self._evaluate_slo(slo_target)

    def _evaluate_slo(self, slo_target: SLOTarget) -> None:
        """Evaluate a single SLO target."""
        # Get metrics for the time window
        window_start = datetime.now(timezone.utc) - timedelta(minutes=slo_target.window_minutes)
        metrics = self._get_metrics_in_window(slo_target.metric_type, window_start)

        if not metrics:
            return

        # Calculate current value based on metric type
        current_value = self._calculate_metric_value(slo_target.metric_type, metrics)

        # Evaluate against target
        status = self._evaluate_against_target(slo_target, current_value)

        # Update current status
        self.current_status[slo_target.name] = {
            'current_value': current_value,
            'target_value': slo_target.target_value,
            'status': status.value,
            'last_evaluated': datetime.now(timezone.utc).isoformat(),
            'window_minutes': slo_target.window_minutes,
            'metric_count': len(metrics)
        }

        # Handle violations
        if status in [SLAStatus.WARNING, SLAStatus.CRITICAL, SLAStatus.BREACHED]:
            self._handle_violation(slo_target, current_value, status)
        else:
            self._resolve_violation(slo_target.name)

    def _get_metrics_in_window(
        self,
        metric_type: MetricType,
        window_start: datetime
    ) -> List[SLAMetric]:
        """Get metrics within a time window."""
        with self.metrics_lock:
            metrics = []
            metric_queue = self.metrics.get(metric_type.value, deque())

            for metric in metric_queue:
                metric_time = datetime.fromisoformat(metric.timestamp.replace('Z', '+00:00'))
                if metric_time >= window_start:
                    metrics.append(metric)

            return metrics

    def _calculate_metric_value(self, metric_type: MetricType, metrics: List[SLAMetric]) -> float:
        """Calculate the current metric value."""
        if not metrics:
            return 0.0

        values = [m.value for m in metrics]

        if metric_type == MetricType.AVAILABILITY:
            # Availability: percentage of successful requests
            return (sum(values) / len(values)) * 100.0

        elif metric_type == MetricType.ERROR_RATE:
            # Error rate: percentage of failed requests
            return (1.0 - sum(values) / len(values)) * 100.0

        elif metric_type == MetricType.RESPONSE_TIME:
            # Response time: 95th percentile
            sorted_values = sorted(values)
            idx = int(0.95 * len(sorted_values))
            return sorted_values[min(idx, len(sorted_values) - 1)]

        elif metric_type == MetricType.THROUGHPUT:
            # Throughput: requests per minute
            if len(metrics) < 2:
                return 0.0

            # Calculate time span
            start_time = datetime.fromisoformat(metrics[0].timestamp.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(metrics[-1].timestamp.replace('Z', '+00:00'))
            time_span_minutes = (end_time - start_time).total_seconds() / 60.0

            if time_span_minutes == 0:
                return 0.0

            return len(metrics) / time_span_minutes

        else:  # CUSTOM
            # Custom: average value
            return sum(values) / len(values)

    def _evaluate_against_target(self, slo_target: SLOTarget, current_value: float) -> SLAStatus:
        """Evaluate current value against SLO target."""
        target = slo_target.target_value
        comparison = slo_target.comparison

        # Check if target is met
        target_met = self._compare_values(current_value, target, comparison)

        if target_met:
            return SLAStatus.HEALTHY

        # Check severity levels
        if slo_target.critical_threshold is not None:
            critical_breached = self._compare_values(
                current_value,
                slo_target.critical_threshold,
                self._invert_comparison(comparison)
            )
            if critical_breached:
                return SLAStatus.BREACHED

        if slo_target.warning_threshold is not None:
            warning_breached = self._compare_values(
                current_value,
                slo_target.warning_threshold,
                self._invert_comparison(comparison)
            )
            if warning_breached:
                return SLAStatus.CRITICAL

        return SLAStatus.WARNING

    def _compare_values(self, value1: float, value2: float, comparison: str) -> bool:
        """Compare two values based on comparison operator."""
        if comparison == "<=":
            return value1 <= value2
        elif comparison == ">=":
            return value1 >= value2
        elif comparison == "==":
            return abs(value1 - value2) < 1e-6
        elif comparison == "!=":
            return abs(value1 - value2) >= 1e-6
        elif comparison == "<":
            return value1 < value2
        elif comparison == ">":
            return value1 > value2
        else:
            return False

    def _invert_comparison(self, comparison: str) -> str:
        """Invert comparison operator for threshold checking."""
        inversion_map = {
            "<=": ">=",
            ">=": "<=",
            "<": ">",
            ">": "<",
            "==": "!=",
            "!=": "=="
        }
        return inversion_map.get(comparison, comparison)

    def _handle_violation(
        self,
        slo_target: SLOTarget,
        current_value: float,
        status: SLAStatus
    ) -> None:
        """Handle SLO violation."""
        violation_id = f"{slo_target.name}_{int(time.time())}"

        # Check if this is a new violation or continuation
        existing_violation = None
        for violation in self.violations.values():
            if violation.slo_name == slo_target.name and not violation.resolved:
                existing_violation = violation
                break

        if existing_violation:
            # Update existing violation
            existing_violation.current_value = current_value
            existing_violation.severity = status
            duration = (
                datetime.now(timezone.utc) -
                datetime.fromisoformat(existing_violation.violation_time.replace('Z', '+00:00'))
            ).total_seconds() / 60.0
            existing_violation.duration_minutes = int(duration)
        else:
            # Create new violation
            violation = SLOViolation(
                id=violation_id,
                slo_name=slo_target.name,
                violation_time=datetime.now(timezone.utc).isoformat(),
                current_value=current_value,
                target_value=slo_target.target_value,
                severity=status,
                duration_minutes=0
            )
            self.violations[violation_id] = violation

            # Send alert if enabled and not in cooldown
            if self.config.alert_enabled:
                self._send_alert_if_needed(slo_target, violation)

        # Save violations
        self._save_violations()

    def _resolve_violation(self, slo_name: str) -> None:
        """Resolve active violations for an SLO."""
        for violation in self.violations.values():
            if violation.slo_name == slo_name and not violation.resolved:
                violation.resolved = True
                violation.resolved_time = datetime.now(timezone.utc).isoformat()

                self.logger.info(f"SLO violation resolved: {slo_name}")

                # Send resolution alert
                if self.config.alert_enabled:
                    self._send_resolution_alert(violation)

        self._save_violations()

    def _send_alert_if_needed(self, slo_target: SLOTarget, violation: SLOViolation) -> None:
        """Send alert if not in cooldown period."""
        now = datetime.now(timezone.utc)
        cooldown_key = slo_target.name

        # Check cooldown
        if cooldown_key in self.alert_cooldowns:
            last_alert = self.alert_cooldowns[cooldown_key]
            if (now - last_alert).total_seconds() < (self.config.alert_cooldown_minutes * 60):
                return

        # Send alert
        self._send_alert(slo_target, violation)
        self.alert_cooldowns[cooldown_key] = now

    def _send_alert(self, slo_target: SLOTarget, violation: SLOViolation) -> None:
        """Send SLO violation alert."""
        if not self.config.alert_webhook_url:
            return

        try:
            import requests

            alert_data = {
                'type': 'slo_violation',
                'slo_name': slo_target.name,
                'description': slo_target.description,
                'current_value': violation.current_value,
                'target_value': violation.target_value,
                'severity': violation.severity.value,
                'violation_time': violation.violation_time,
                'duration_minutes': violation.duration_minutes,
                'comparison': slo_target.comparison,
                'metric_type': slo_target.metric_type.value
            }

            response = requests.post(
                self.config.alert_webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"SLO violation alert sent for {slo_target.name}")

        except Exception as e:
            self.logger.error(f"Failed to send SLO alert: {e}")

    def _send_resolution_alert(self, violation: SLOViolation) -> None:
        """Send SLO violation resolution alert."""
        if not self.config.alert_webhook_url:
            return

        try:
            import requests

            alert_data = {
                'type': 'slo_resolution',
                'slo_name': violation.slo_name,
                'violation_id': violation.id,
                'resolved_time': violation.resolved_time,
                'total_duration_minutes': violation.duration_minutes
            }

            response = requests.post(
                self.config.alert_webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"SLO resolution alert sent for {violation.slo_name}")

        except Exception as e:
            self.logger.error(f"Failed to send SLO resolution alert: {e}")

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics beyond retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.config.metrics_retention_days)

        with self.metrics_lock:
            for metric_type, metric_queue in self.metrics.items():
                # Remove old metrics
                while metric_queue and len(metric_queue) > 0:
                    oldest_metric = metric_queue[0]
                    metric_time = datetime.fromisoformat(oldest_metric.timestamp.replace('Z', '+00:00'))

                    if metric_time < cutoff_time:
                        metric_queue.popleft()
                    else:
                        break

    def _save_violations(self) -> None:
        """Save violations to disk."""
        try:
            violations_file = self.storage_path / "violations.json"
            violations_data = {
                'violations': [v.to_dict() for v in self.violations.values()],
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            with open(violations_file, 'w') as f:
                json.dump(violations_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save violations: {e}")

    def _load_violations(self) -> None:
        """Load violations from disk."""
        try:
            violations_file = self.storage_path / "violations.json"
            if violations_file.exists():
                with open(violations_file) as f:
                    data = json.load(f)

                for violation_data in data.get('violations', []):
                    violation = SLOViolation(
                        id=violation_data['id'],
                        slo_name=violation_data['slo_name'],
                        violation_time=violation_data['violation_time'],
                        current_value=violation_data['current_value'],
                        target_value=violation_data['target_value'],
                        severity=SLAStatus(violation_data['severity']),
                        duration_minutes=violation_data['duration_minutes'],
                        resolved=violation_data['resolved'],
                        resolved_time=violation_data.get('resolved_time')
                    )
                    self.violations[violation.id] = violation

        except Exception as e:
            self.logger.error(f"Failed to load violations: {e}")

    def get_sla_status(self) -> Dict[str, Any]:
        """Get current SLA status."""
        return {
            'overall_status': self._calculate_overall_status(),
            'slo_targets': {name: slo.to_dict() for name, slo in self.slo_targets.items()},
            'current_status': self.current_status,
            'active_violations': [
                v.to_dict() for v in self.violations.values() if not v.resolved
            ],
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall SLA status."""
        if not self.current_status:
            return SLAStatus.HEALTHY.value

        statuses = [status['status'] for status in self.current_status.values()]

        if SLAStatus.BREACHED.value in statuses:
            return SLAStatus.BREACHED.value
        elif SLAStatus.CRITICAL.value in statuses:
            return SLAStatus.CRITICAL.value
        elif SLAStatus.WARNING.value in statuses:
            return SLAStatus.WARNING.value
        else:
            return SLAStatus.HEALTHY.value

    def get_violation_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get violation history for the specified number of days."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        recent_violations = []
        for violation in self.violations.values():
            violation_time = datetime.fromisoformat(violation.violation_time.replace('Z', '+00:00'))
            if violation_time >= cutoff_time:
                recent_violations.append(violation.to_dict())

        return sorted(recent_violations, key=lambda x: x['violation_time'], reverse=True)


# Global SLA monitor instance
_sla_monitor: Optional[SLAMonitor] = None


def get_sla_monitor() -> SLAMonitor:
    """Get the global SLA monitor instance."""
    global _sla_monitor

    if _sla_monitor is None:
        _sla_monitor = SLAMonitor()
        _sla_monitor.start_monitoring()

    return _sla_monitor


def record_request(response_time: float, success: bool, tags: Optional[Dict[str, str]] = None) -> None:
    """Record a request for SLA monitoring."""
    get_sla_monitor().record_request(response_time, success, tags)


def record_metric(metric_type: MetricType, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Record a custom metric."""
    get_sla_monitor().record_metric(metric_type, value, tags)


# Decorator for automatic request tracking
def track_sla(tags: Optional[Dict[str, str]] = None):
    """Decorator for automatic SLA tracking."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                response_time = time.time() - start_time
                function_tags = tags or {}
                function_tags.update({
                    'function': f"{func.__module__}.{func.__name__}"
                })

                record_request(response_time, success, function_tags)

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize SLA monitoring
    sla_monitor = get_sla_monitor()

    # Add custom SLO
    custom_slo = SLOTarget(
        name="custom_processing_time",
        metric_type=MetricType.RESPONSE_TIME,
        target_value=0.5,  # 500ms
        comparison="<=",
        window_minutes=15,
        description="Custom processing should complete within 500ms",
        warning_threshold=0.8,
        critical_threshold=1.2
    )
    sla_monitor.add_slo_target(custom_slo)

    # Simulate some requests
    import random

    for i in range(100):
        # Simulate varying response times and success rates
        response_time = random.uniform(0.1, 2.0)
        success = random.random() > 0.05  # 95% success rate

        record_request(response_time, success, {'endpoint': '/api/extract'})
        time.sleep(0.1)

    # Wait a bit for evaluation
    time.sleep(5)

    # Get SLA status
    status = sla_monitor.get_sla_status()
    print(f"Overall SLA Status: {status['overall_status']}")

    for slo_name, slo_status in status['current_status'].items():
        print(f"  {slo_name}: {slo_status['status']} "
              f"(current: {slo_status['current_value']:.2f}, "
              f"target: {slo_status['target_value']:.2f})")

    # Get violations
    violations = sla_monitor.get_violation_history()
    print(f"\nViolations in last 7 days: {len(violations)}")

    # Stop monitoring
    sla_monitor.stop_monitoring()
