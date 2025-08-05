"""
Enhanced health monitoring system for Multimodal Contract Extractor.

This module provides comprehensive health monitoring with metrics collection,
alerting, and observability features beyond the basic health checks.
"""

import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check configuration."""
    name: str
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: int = 60
    timeout_seconds: int = 30
    critical: bool = False
    enabled: bool = True
    last_run: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    failure_count: int = 0
    max_failures: int = 3
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    """Alert configuration."""
    webhook_url: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook: Optional[str] = None
    alert_threshold: int = 1
    cooldown_minutes: int = 15


class HealthMetrics:
    """Prometheus metrics for health monitoring."""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            return

        self.health_status = Gauge(
            'mce_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['check_name', 'instance']
        )

        self.health_check_duration = Histogram(
            'mce_health_check_duration_seconds',
            'Time spent executing health checks',
            ['check_name']
        )

        self.health_check_failures = Counter(
            'mce_health_check_failures_total',
            'Total number of health check failures',
            ['check_name', 'failure_type']
        )

        self.system_memory_usage = Gauge(
            'mce_system_memory_usage_percent',
            'System memory usage percentage'
        )

        self.system_cpu_usage = Gauge(
            'mce_system_cpu_usage_percent',
            'System CPU usage percentage'
        )

        self.system_disk_usage = Gauge(
            'mce_system_disk_usage_percent',
            'System disk usage percentage',
            ['mountpoint']
        )

        self.application_uptime = Gauge(
            'mce_application_uptime_seconds',
            'Application uptime in seconds'
        )

        self.dependency_status = Gauge(
            'mce_dependency_status',
            'Dependency availability status (1=available, 0=unavailable)',
            ['dependency_name', 'dependency_type']
        )

        self.business_metric_accuracy = Gauge(
            'mce_clause_detection_accuracy',
            'Clause detection accuracy'
        )

        self.document_processing_queue = Gauge(
            'mce_document_processing_queue_size',
            'Number of documents in processing queue'
        )


class EnhancedHealthMonitor:
    """Enhanced health monitoring system with comprehensive observability."""

    def __init__(self, alert_config: Optional[AlertConfig] = None):
        self.alert_config = alert_config or AlertConfig()
        self.checks: Dict[str, HealthCheck] = {}
        self.metrics = HealthMetrics() if PROMETHEUS_AVAILABLE else None
        self.history: List[Dict[str, Any]] = []
        self.running = False
        self.monitor_thread = None
        self.start_time = datetime.now()
        self.last_alerts: Dict[str, datetime] = {}

        # Register default health checks
        self._register_default_checks()

        # Initialize application uptime
        if self.metrics:
            self.metrics.application_uptime.set(0)

    def _register_default_checks(self):
        """Register comprehensive default health checks."""
        # System resource monitoring
        self.register_check(HealthCheck(
            name="system_resources",
            check_function=self._check_system_resources,
            interval_seconds=30,
            critical=True,
            tags=["system", "resources"]
        ))

        # Application dependencies
        self.register_check(HealthCheck(
            name="dependencies",
            check_function=self._check_dependencies,
            interval_seconds=120,
            critical=True,
            tags=["dependencies", "external"]
        ))

        # Filesystem health
        self.register_check(HealthCheck(
            name="filesystem",
            check_function=self._check_filesystem,
            interval_seconds=60,
            critical=True,
            tags=["filesystem", "storage"]
        ))

        # Network connectivity
        self.register_check(HealthCheck(
            name="network",
            check_function=self._check_network,
            interval_seconds=90,
            critical=False,
            tags=["network", "connectivity"]
        ))

        # Application configuration
        self.register_check(HealthCheck(
            name="configuration",
            check_function=self._check_configuration,
            interval_seconds=300,
            critical=False,
            tags=["config", "application"]
        ))

        # Security posture
        self.register_check(HealthCheck(
            name="security",
            check_function=self._check_security,
            interval_seconds=600,
            critical=False,
            tags=["security", "compliance"]
        ))

        # Performance benchmarks
        self.register_check(HealthCheck(
            name="performance",
            check_function=self._check_performance,
            interval_seconds=180,
            critical=False,
            tags=["performance", "benchmarks"]
        ))

        # Data integrity
        self.register_check(HealthCheck(
            name="data_integrity",
            check_function=self._check_data_integrity,
            interval_seconds=1800,  # 30 minutes
            critical=False,
            tags=["data", "integrity"]
        ))

    def register_check(self, check: HealthCheck):
        """Register a new health check."""
        self.checks[check.name] = check
        logger.info(f"Registered health check: {check.name} (critical: {check.critical})")

    def start_monitoring(self):
        """Start the health monitoring background thread."""
        if self.running:
            logger.warning("Health monitoring is already running")
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Enhanced health monitoring started")

    def stop_monitoring(self):
        """Stop the health monitoring background thread."""
        if not self.running:
            return

        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Enhanced health monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop with error handling."""
        logger.info("Health monitoring loop started")

        while self.running:
            try:
                # Update uptime metric
                if self.metrics:
                    uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                    self.metrics.application_uptime.set(uptime_seconds)

                # Run scheduled checks
                self._run_scheduled_checks()

                # Cleanup old history
                self._cleanup_history()

                # Sleep with graceful shutdown check
                for _ in range(30):  # 30 second check interval
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                logger.debug(traceback.format_exc())
                time.sleep(30)  # Back off on errors

        logger.info("Health monitoring loop stopped")

    def _run_scheduled_checks(self):
        """Run health checks that are due."""
        current_time = datetime.now()

        for check in self.checks.values():
            if not check.enabled:
                continue

            # Check if it's time to run this check
            if (check.last_run is None or
                (current_time - check.last_run).total_seconds() >= check.interval_seconds):

                try:
                    self._run_single_check(check)
                except Exception as e:
                    logger.error(f"Error running health check {check.name}: {e}")
                    self._record_check_failure(check, str(e), "execution_error")

    def _run_single_check(self, check: HealthCheck):
        """Run a single health check with comprehensive error handling."""
        start_time = time.time()
        check.last_run = datetime.now()

        logger.debug(f"Running health check: {check.name}")

        try:
            # Run the check with timeout
            result = self._run_with_timeout(check.check_function, check.timeout_seconds)

            # Validate result format
            if not isinstance(result, dict) or "status" not in result:
                raise ValueError(f"Invalid health check result format from {check.name}")

            # Update check state
            check.last_result = result
            check.last_result["timestamp"] = datetime.now().isoformat()

            # Handle success/failure counting
            if result.get("status") == HealthStatus.HEALTHY.value:
                check.failure_count = 0
            else:
                check.failure_count += 1

            # Record metrics
            if self.metrics:
                duration = time.time() - start_time
                self.metrics.health_check_duration.labels(check_name=check.name).observe(duration)

                status_value = 1 if result.get("status") == HealthStatus.HEALTHY.value else 0
                self.metrics.health_status.labels(
                    check_name=check.name,
                    instance=self._get_instance_id()
                ).set(status_value)

                if status_value == 0:
                    self.metrics.health_check_failures.labels(
                        check_name=check.name,
                        failure_type=result.get("error_type", "unknown")
                    ).inc()

            # Add to history
            history_entry = {
                "check_name": check.name,
                "timestamp": check.last_result["timestamp"],
                "status": result.get("status"),
                "duration_seconds": time.time() - start_time,
                "critical": check.critical
            }
            self.history.append(history_entry)

            # Log result
            status = result.get("status")
            if status == HealthStatus.HEALTHY.value:
                logger.debug(f"Health check {check.name}: HEALTHY")
            elif status == HealthStatus.WARNING.value:
                logger.warning(f"Health check {check.name}: WARNING - {result.get('message', '')}")
            else:
                logger.error(f"Health check {check.name}: {status.upper()} - {result.get('message', '')}")

            # Handle critical check failures and alerting
            if (check.critical and
                status in [HealthStatus.UNHEALTHY.value, HealthStatus.CRITICAL.value] and
                check.failure_count >= check.max_failures):
                self._handle_critical_failure(check, result)

        except Exception as e:
            logger.error(f"Health check {check.name} execution failed: {e}")
            self._record_check_failure(check, str(e), "execution_error")

    def _run_with_timeout(self, func: Callable, timeout: int) -> Dict[str, Any]:
        """Run a function with a timeout using threading."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(func)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": f"Health check timed out after {timeout} seconds",
                    "error_type": "timeout"
                }
            except Exception as e:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": str(e),
                    "error_type": "execution_error"
                }

    def _record_check_failure(self, check: HealthCheck, error: str, error_type: str):
        """Record a comprehensive health check failure."""
        check.failure_count += 1
        check.last_result = {
            "status": HealthStatus.UNHEALTHY.value,
            "error": error,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "failure_count": check.failure_count
        }

        logger.error(f"Health check {check.name} failed (attempt {check.failure_count}): {error}")

        # Record metrics
        if self.metrics:
            self.metrics.health_check_failures.labels(
                check_name=check.name,
                failure_type=error_type
            ).inc()

            self.metrics.health_status.labels(
                check_name=check.name,
                instance=self._get_instance_id()
            ).set(0)

    def _handle_critical_failure(self, check: HealthCheck, result: Dict[str, Any]):
        """Handle critical health check failures with alerting."""
        # Check alert cooldown
        last_alert_time = self.last_alerts.get(check.name)
        current_time = datetime.now()

        if (last_alert_time and
            (current_time - last_alert_time).total_seconds() < (self.alert_config.cooldown_minutes * 60)):
            logger.debug(f"Alert cooldown active for {check.name}, skipping alert")
            return

        # Prepare alert data
        alert_data = {
            "alert_type": "critical_health_check_failure",
            "check_name": check.name,
            "status": result.get("status"),
            "message": result.get("message", "Critical health check failed"),
            "error": result.get("error", ""),
            "failure_count": check.failure_count,
            "max_failures": check.max_failures,
            "timestamp": current_time.isoformat(),
            "instance": self._get_instance_id(),
            "tags": check.tags,
            "severity": "critical" if check.critical else "warning"
        }

        logger.critical(f"CRITICAL HEALTH FAILURE: {check.name} - {alert_data['message']}")

        # Send alerts
        self._send_alerts(alert_data)

        # Update last alert time
        self.last_alerts[check.name] = current_time

    def _send_alerts(self, alert_data: Dict[str, Any]):
        """Send alerts through configured channels."""
        # Webhook alerts
        if self.alert_config.webhook_url:
            self._send_webhook_alert(self.alert_config.webhook_url, alert_data)

        # Slack alerts
        if self.alert_config.slack_webhook:
            self._send_slack_alert(self.alert_config.slack_webhook, alert_data)

        # Additional alerting mechanisms can be added here

    def _send_webhook_alert(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send alert via webhook."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for webhook alerts")
            return

        try:
            response = requests.post(
                webhook_url,
                json=alert_data,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Alert sent successfully to webhook: {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert to {webhook_url}: {e}")

    def _send_slack_alert(self, slack_webhook: str, alert_data: Dict[str, Any]):
        """Send alert to Slack."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for Slack alerts")
            return

        try:
            slack_message = {
                "text": f"🚨 Health Check Alert: {alert_data['check_name']}",
                "attachments": [
                    {
                        "color": "danger" if alert_data["severity"] == "critical" else "warning",
                        "fields": [
                            {"title": "Check", "value": alert_data["check_name"], "short": True},
                            {"title": "Status", "value": alert_data["status"], "short": True},
                            {"title": "Message", "value": alert_data["message"], "short": False},
                            {"title": "Instance", "value": alert_data["instance"], "short": True},
                            {"title": "Failure Count", "value": str(alert_data["failure_count"]), "short": True}
                        ],
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }

            response = requests.post(slack_webhook, json=slack_message, timeout=10)
            response.raise_for_status()
            logger.info("Alert sent successfully to Slack")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _cleanup_history(self):
        """Clean up old history entries."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        initial_count = len(self.history)

        self.history = [
            entry for entry in self.history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]

        cleaned_count = initial_count - len(self.history)
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} old history entries")

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with detailed metrics."""
        current_time = datetime.now()
        uptime = current_time - self.start_time

        # Compile check results
        check_results = {}
        overall_status = HealthStatus.HEALTHY
        critical_issues = []
        warnings = []
        check_summary = {
            "total": 0,
            "healthy": 0,
            "warning": 0,
            "unhealthy": 0,
            "critical": 0,
            "unknown": 0
        }

        for name, check in self.checks.items():
            if not check.enabled:
                continue

            check_summary["total"] += 1
            result = check.last_result or {"status": HealthStatus.UNKNOWN.value}

            check_results[name] = {
                **result,
                "last_run": check.last_run.isoformat() if check.last_run else None,
                "failure_count": check.failure_count,
                "critical": check.critical,
                "enabled": check.enabled,
                "tags": check.tags,
                "interval_seconds": check.interval_seconds
            }

            # Count status types
            status = result.get("status", HealthStatus.UNKNOWN.value)
            if status == HealthStatus.HEALTHY.value:
                check_summary["healthy"] += 1
            elif status == HealthStatus.WARNING.value:
                check_summary["warning"] += 1
                warnings.append(f"{name}: {result.get('message', 'Warning')}")
            elif status == HealthStatus.UNHEALTHY.value:
                check_summary["unhealthy"] += 1
                if check.critical:
                    critical_issues.append(f"{name}: {result.get('message', 'Failed')}")
                else:
                    warnings.append(f"{name}: {result.get('message', 'Failed')}")
            elif status == HealthStatus.CRITICAL.value:
                check_summary["critical"] += 1
                critical_issues.append(f"{name}: {result.get('message', 'Critical failure')}")
            else:
                check_summary["unknown"] += 1

        # Determine overall status
        if check_summary["critical"] > 0:
            overall_status = HealthStatus.CRITICAL
        elif critical_issues:
            overall_status = HealthStatus.CRITICAL
        elif check_summary["unhealthy"] > 0 or warnings:
            overall_status = HealthStatus.WARNING
        elif check_summary["unknown"] > 0:
            overall_status = HealthStatus.WARNING

        return {
            "status": overall_status.value,
            "timestamp": current_time.isoformat(),
            "uptime": {
                "seconds": int(uptime.total_seconds()),
                "human": str(uptime),
                "start_time": self.start_time.isoformat()
            },
            "summary": check_summary,
            "checks": check_results,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "monitoring": {
                "enabled": self.running,
                "history_entries": len(self.history),
                "metrics_enabled": PROMETHEUS_AVAILABLE and self.metrics is not None
            },
            "instance": self._get_instance_id(),
            "version": self._get_application_version()
        }

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        if not PROMETHEUS_AVAILABLE or not self.metrics:
            return "# Prometheus metrics not available\n"

        try:
            return generate_latest(REGISTRY).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return f"# Error generating metrics: {e}\n"

    def _get_instance_id(self) -> str:
        """Get unique instance identifier."""
        return os.environ.get('HOSTNAME', socket.gethostname())

    def _get_application_version(self) -> str:
        """Get application version."""
        try:
            import multimodal_contract_extractor
            return getattr(multimodal_contract_extractor, '__version__', '0.1.0')
        except ImportError:
            return '0.1.0'

    # Enhanced health check implementations
    def _check_system_resources(self) -> Dict[str, Any]:
        """Comprehensive system resource monitoring."""
        if not PSUTIL_AVAILABLE:
            return {
                "status": HealthStatus.WARNING.value,
                "message": "psutil not available for system monitoring"
            }

        try:
            # Memory monitoring
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Disk monitoring
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        "percent": (usage.used / usage.total) * 100,
                        "total_gb": usage.total / (1024**3),
                        "used_gb": usage.used / (1024**3),
                        "free_gb": usage.free / (1024**3)
                    }
                except PermissionError:
                    continue

            # Network I/O
            network_io = psutil.net_io_counters()

            # Process information
            process = psutil.Process()
            process_info = {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_mb": process.memory_info().rss / (1024**2),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
            }

            # Load average (Unix systems)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                pass

            # Determine status and issues
            status = HealthStatus.HEALTHY
            issues = []
            warnings = []

            # Memory thresholds
            if memory_percent > 95:
                status = HealthStatus.CRITICAL
                issues.append(f"Critical memory usage: {memory_percent:.1f}%")
            elif memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 80:
                warnings.append(f"Elevated memory usage: {memory_percent:.1f}%")

            # CPU thresholds
            if cpu_percent > 95:
                if status in [HealthStatus.HEALTHY, HealthStatus.WARNING]:
                    status = HealthStatus.CRITICAL
                issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 90:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.UNHEALTHY
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                warnings.append(f"Elevated CPU usage: {cpu_percent:.1f}%")

            # Disk thresholds
            for mountpoint, usage in disk_usage.items():
                percent = usage["percent"]
                if percent > 98:
                    status = HealthStatus.CRITICAL
                    issues.append(f"Critical disk usage on {mountpoint}: {percent:.1f}%")
                elif percent > 95:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.UNHEALTHY
                    issues.append(f"High disk usage on {mountpoint}: {percent:.1f}%")
                elif percent > 85:
                    warnings.append(f"Elevated disk usage on {mountpoint}: {percent:.1f}%")

            # Update Prometheus metrics
            if self.metrics:
                self.metrics.system_memory_usage.set(memory_percent)
                self.metrics.system_cpu_usage.set(cpu_percent)
                for mountpoint, usage in disk_usage.items():
                    self.metrics.system_disk_usage.labels(mountpoint=mountpoint).set(usage["percent"])

            result = {
                "status": status.value,
                "details": {
                    "memory": {
                        "percent": memory_percent,
                        "total_gb": memory.total / (1024**3),
                        "available_gb": memory.available / (1024**3),
                        "used_gb": memory.used / (1024**3)
                    },
                    "cpu": {
                        "percent": cpu_percent,
                        "count": cpu_count
                    },
                    "disk": disk_usage,
                    "network": {
                        "bytes_sent": network_io.bytes_sent,
                        "bytes_recv": network_io.bytes_recv,
                        "packets_sent": network_io.packets_sent,
                        "packets_recv": network_io.packets_recv
                    },
                    "process": process_info
                }
            }

            if load_avg:
                result["details"]["load_average"] = {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                }

            if issues:
                result["message"] = "; ".join(issues)
            elif warnings:
                result["message"] = "; ".join(warnings)
                if status == HealthStatus.HEALTHY:
                    result["status"] = HealthStatus.WARNING.value

            return result

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "error_type": "system_error"
            }

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies with detailed status."""
        dependencies = {
            "tesseract": self._check_tesseract_detailed(),
            "poppler": self._check_poppler_detailed(),
            "python_packages": self._check_python_packages_detailed(),
            "system_libraries": self._check_system_libraries()
        }

        # Determine overall status
        critical_deps_down = []
        warning_deps = []

        for dep_name, dep_status in dependencies.items():
            if not dep_status.get("available", False):
                if dep_status.get("critical", True):
                    critical_deps_down.append(dep_name)
                else:
                    warning_deps.append(dep_name)

        if critical_deps_down:
            status = HealthStatus.CRITICAL
            message = f"Critical dependencies unavailable: {', '.join(critical_deps_down)}"
        elif warning_deps:
            status = HealthStatus.WARNING
            message = f"Non-critical dependencies unavailable: {', '.join(warning_deps)}"
        else:
            status = HealthStatus.HEALTHY
            message = "All dependencies available"

        # Update dependency metrics
        if self.metrics:
            for dep_name, dep_status in dependencies.items():
                if isinstance(dep_status, dict) and "available" in dep_status:
                    self.metrics.dependency_status.labels(
                        dependency_name=dep_name,
                        dependency_type="external"
                    ).set(1 if dep_status["available"] else 0)

        return {
            "status": status.value,
            "message": message,
            "details": dependencies
        }

    def _check_tesseract_detailed(self) -> Dict[str, Any]:
        """Detailed Tesseract OCR availability check."""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_line = result.stderr.split('\n')[0] if result.stderr else "Unknown"

                # Check language support
                lang_result = subprocess.run(
                    ['tesseract', '--list-langs'],
                    capture_output=True, text=True, timeout=10
                )

                languages = []
                if lang_result.returncode == 0:
                    languages = lang_result.stdout.strip().split('\n')[1:]  # Skip first line

                return {
                    "available": True,
                    "version": version_line,
                    "languages": languages,
                    "critical": True
                }
            else:
                return {
                    "available": False,
                    "error": f"Tesseract returned code {result.returncode}",
                    "critical": True
                }

        except subprocess.TimeoutExpired:
            return {
                "available": False,
                "error": "Tesseract command timed out",
                "critical": True
            }
        except FileNotFoundError:
            return {
                "available": False,
                "error": "Tesseract not found in PATH",
                "critical": True
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "critical": True
            }

    def _check_poppler_detailed(self) -> Dict[str, Any]:
        """Detailed Poppler utilities check."""
        tools = ['pdfinfo', 'pdftoppm', 'pdftotext']
        tool_status = {}

        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, '-v'] if tool == 'pdfinfo' else [tool, '-h'],
                    capture_output=True, text=True, timeout=5
                )
                tool_status[tool] = {
                    "available": result.returncode in [0, 1],  # Some tools return 1 for help
                    "version": result.stderr.strip() if result.stderr else "Available"
                }
            except (FileNotFoundError, subprocess.TimeoutExpired):
                tool_status[tool] = {"available": False, "error": "Not found or timeout"}

        available_tools = [tool for tool, status in tool_status.items() if status["available"]]

        return {
            "available": len(available_tools) >= 2,  # Need at least 2 core tools
            "tools": tool_status,
            "available_tools": available_tools,
            "critical": True
        }

    def _check_python_packages_detailed(self) -> Dict[str, Any]:
        """Detailed Python package availability check."""
        packages = {
            'PIL': {'critical': True, 'import_name': 'PIL'},
            'pdf2image': {'critical': True},
            'pytesseract': {'critical': True},
            'streamlit': {'critical': True},
            'numpy': {'critical': True},
            'opencv-python': {'critical': False, 'import_name': 'cv2'},
            'requests': {'critical': False},
            'psutil': {'critical': False},
            'prometheus_client': {'critical': False}
        }

        package_status = {}
        critical_missing = []

        for package, config in packages.items():
            import_name = config.get('import_name', package.replace('-', '_'))
            try:
                imported_module = __import__(import_name)
                version = getattr(imported_module, '__version__', 'Unknown')
                package_status[package] = {
                    "available": True,
                    "version": version,
                    "critical": config['critical']
                }
            except ImportError as e:
                package_status[package] = {
                    "available": False,
                    "error": str(e),
                    "critical": config['critical']
                }
                if config['critical']:
                    critical_missing.append(package)

        return {
            "available": len(critical_missing) == 0,
            "packages": package_status,
            "critical_missing": critical_missing,
            "critical": len(critical_missing) > 0
        }

    def _check_system_libraries(self) -> Dict[str, Any]:
        """Check system library availability."""
        # This is a simplified implementation
        # In production, you might use ctypes.util.find_library
        return {
            "available": True,
            "message": "System library checks not fully implemented",
            "critical": False
        }

    def _check_filesystem(self) -> Dict[str, Any]:
        """Enhanced filesystem health check."""
        directories = [
            {'path': '/tmp', 'name': 'temp', 'critical': True},
            {'path': '/app/data', 'name': 'app_data', 'critical': False},
            {'path': '/app/logs', 'name': 'app_logs', 'critical': False},
            {'path': '/app/cache', 'name': 'app_cache', 'critical': False}
        ]

        results = {}
        overall_status = HealthStatus.HEALTHY
        issues = []

        for dir_config in directories:
            path = dir_config['path']
            name = dir_config['name']

            check_result = {
                "path": path,
                "exists": os.path.exists(path),
                "readable": False,
                "writable": False,
                "critical": dir_config['critical']
            }

            if check_result["exists"]:
                check_result["readable"] = os.access(path, os.R_OK)
                check_result["writable"] = os.access(path, os.W_OK)

                # Test actual write operation
                if check_result["writable"]:
                    test_file = os.path.join(path, f'health_check_{int(time.time())}.tmp')
                    try:
                        with open(test_file, 'w') as f:
                            f.write('health check test')
                        os.remove(test_file)
                        check_result["write_test"] = True
                    except Exception as e:
                        check_result["write_test"] = False
                        check_result["write_error"] = str(e)
                else:
                    check_result["write_test"] = False

            # Determine status impact
            if dir_config['critical']:
                if not check_result["exists"] or not check_result.get("write_test", False):
                    overall_status = HealthStatus.CRITICAL
                    issues.append(f"Critical filesystem issue with {path}")
            elif not check_result["exists"] or not check_result.get("write_test", False):
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
                issues.append(f"Filesystem warning for {path}")

            results[name] = check_result

        return {
            "status": overall_status.value,
            "details": results,
            "message": "; ".join(issues) if issues else "All filesystem checks passed"
        }

    def _check_network(self) -> Dict[str, Any]:
        """Network connectivity and DNS resolution check."""
        checks = {
            "dns_resolution": self._check_dns_resolution(),
            "external_connectivity": self._check_external_connectivity(),
            "localhost_connectivity": self._check_localhost_connectivity()
        }

        failed_checks = [name for name, result in checks.items() if not result.get("success", False)]

        if not failed_checks:
            status = HealthStatus.HEALTHY
            message = "All network checks passed"
        elif len(failed_checks) < len(checks):
            status = HealthStatus.WARNING
            message = f"Some network checks failed: {', '.join(failed_checks)}"
        else:
            status = HealthStatus.UNHEALTHY
            message = "All network checks failed"

        return {
            "status": status.value,
            "message": message,
            "details": checks
        }

    def _check_dns_resolution(self) -> Dict[str, Any]:
        """Check DNS resolution."""
        try:
            import socket
            socket.gethostbyname('google.com')
            return {"success": True, "message": "DNS resolution working"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_external_connectivity(self) -> Dict[str, Any]:
        """Check external network connectivity."""
        if not REQUESTS_AVAILABLE:
            return {"success": False, "error": "Requests library not available"}

        try:
            response = requests.get('https://httpbin.org/get', timeout=10)
            response.raise_for_status()
            return {"success": True, "message": "External connectivity working"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_localhost_connectivity(self) -> Dict[str, Any]:
        """Check localhost connectivity."""
        try:
            import socket
            with socket.create_connection(('127.0.0.1', 22), timeout=5):
                pass
            return {"success": True, "message": "Localhost connectivity working"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_configuration(self) -> Dict[str, Any]:
        """Application configuration validation."""
        config_checks = {
            "environment_variables": self._check_environment_variables(),
            "config_files": self._check_config_files(),
            "permissions": self._check_permissions()
        }

        issues = []
        for check_name, result in config_checks.items():
            if not result.get("valid", True):
                issues.append(f"{check_name}: {result.get('message', 'Invalid')}")

        status = HealthStatus.HEALTHY if not issues else HealthStatus.WARNING

        return {
            "status": status.value,
            "details": config_checks,
            "message": "; ".join(issues) if issues else "Configuration valid"
        }

    def _check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables."""
        required_vars = ['MCE_ENV']
        optional_vars = ['MCE_DATA_DIR', 'MCE_LOGS_DIR', 'MCE_DEBUG']

        env_status = {}
        missing_required = []

        for var in required_vars:
            value = os.environ.get(var)
            env_status[var] = {"set": value is not None, "value": value}
            if not value:
                missing_required.append(var)

        for var in optional_vars:
            value = os.environ.get(var)
            env_status[var] = {"set": value is not None, "value": value}

        return {
            "valid": len(missing_required) == 0,
            "environment_variables": env_status,
            "missing_required": missing_required,
            "message": f"Missing required variables: {', '.join(missing_required)}" if missing_required else "All required variables set"
        }

    def _check_config_files(self) -> Dict[str, Any]:
        """Check configuration file availability."""
        config_files = ['config.yml', 'config.yaml']
        file_status = {}

        for config_file in config_files:
            exists = os.path.exists(config_file)
            readable = os.access(config_file, os.R_OK) if exists else False
            file_status[config_file] = {
                "exists": exists,
                "readable": readable
            }

        any_config_available = any(status["exists"] and status["readable"] for status in file_status.values())

        return {
            "valid": any_config_available,
            "files": file_status,
            "message": "Configuration file available" if any_config_available else "No readable config file found"
        }

    def _check_permissions(self) -> Dict[str, Any]:
        """Check file system permissions."""
        # Simplified permission check
        return {
            "valid": True,
            "message": "Permission checks not fully implemented"
        }

    def _check_security(self) -> Dict[str, Any]:
        """Security posture assessment."""
        security_checks = {
            "file_permissions": self._check_file_permissions(),
            "process_user": self._check_process_user(),
            "environment_security": self._check_environment_security()
        }

        issues = []
        for check_name, result in security_checks.items():
            if not result.get("secure", True):
                issues.append(f"{check_name}: {result.get('message', 'Security issue')}")

        status = HealthStatus.HEALTHY if not issues else HealthStatus.WARNING

        return {
            "status": status.value,
            "details": security_checks,
            "message": "; ".join(issues) if issues else "Security checks passed"
        }

    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check critical file permissions."""
        # Simplified implementation
        return {
            "secure": True,
            "message": "File permission checks not fully implemented"
        }

    def _check_process_user(self) -> Dict[str, Any]:
        """Check if running as appropriate user."""
        import getpass
        current_user = getpass.getuser()
        is_root = current_user == 'root'

        return {
            "secure": not is_root,  # Generally don't want to run as root
            "current_user": current_user,
            "is_root": is_root,
            "message": "Running as root" if is_root else f"Running as {current_user}"
        }

    def _check_environment_security(self) -> Dict[str, Any]:
        """Check environment security settings."""
        # Check for sensitive environment variables
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        exposed_sensitive = []

        for var_name, var_value in os.environ.items():
            if any(pattern.lower() in var_name.lower() for pattern in sensitive_patterns):
                if var_value:  # Non-empty sensitive variable
                    exposed_sensitive.append(var_name)

        return {
            "secure": len(exposed_sensitive) == 0,
            "exposed_sensitive_vars": exposed_sensitive,
            "message": f"Exposed sensitive variables: {', '.join(exposed_sensitive)}" if exposed_sensitive else "No exposed sensitive variables"
        }

    def _check_performance(self) -> Dict[str, Any]:
        """Performance benchmark checks."""
        benchmarks = {
            "cpu_benchmark": self._cpu_benchmark(),
            "memory_benchmark": self._memory_benchmark(),
            "disk_benchmark": self._disk_benchmark()
        }

        # Simple performance scoring
        performance_score = sum(b.get("score", 0) for b in benchmarks.values()) / len(benchmarks)

        if performance_score > 0.8:
            status = HealthStatus.HEALTHY
        elif performance_score > 0.6:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.UNHEALTHY

        return {
            "status": status.value,
            "performance_score": performance_score,
            "details": benchmarks,
            "message": f"Performance score: {performance_score:.2f}"
        }

    def _cpu_benchmark(self) -> Dict[str, Any]:
        """Simple CPU benchmark."""
        import time
        start_time = time.time()

        # Simple CPU-intensive task
        result = sum(i * i for i in range(100000))

        duration = time.time() - start_time
        score = max(0, min(1, (1.0 - duration) / 1.0))  # Normalize to 0-1

        return {
            "duration_seconds": duration,
            "score": score,
            "result": result
        }

    def _memory_benchmark(self) -> Dict[str, Any]:
        """Simple memory benchmark."""
        if not PSUTIL_AVAILABLE:
            return {"score": 0.5, "message": "psutil not available"}

        memory = psutil.virtual_memory()
        score = max(0, min(1, (100 - memory.percent) / 100))

        return {
            "memory_percent": memory.percent,
            "score": score
        }

    def _disk_benchmark(self) -> Dict[str, Any]:
        """Simple disk I/O benchmark."""
        import tempfile
        import time

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                data = b'x' * 1024 * 1024  # 1MB

                start_time = time.time()
                tmp_file.write(data)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                duration = time.time() - start_time

                os.unlink(tmp_file.name)

                # Score based on write speed (higher is better)
                score = max(0, min(1, (2.0 - duration) / 2.0))

                return {
                    "write_duration_seconds": duration,
                    "score": score,
                    "data_size_mb": 1
                }
        except Exception as e:
            return {
                "score": 0,
                "error": str(e)
            }

    def _check_data_integrity(self) -> Dict[str, Any]:
        """Data integrity and consistency checks."""
        # This would implement actual data validation
        # For now, return a placeholder
        return {
            "status": HealthStatus.HEALTHY.value,
            "message": "Data integrity checks not implemented",
            "details": {
                "file_integrity": "Not implemented",
                "data_validation": "Not implemented",
                "backup_status": "Not implemented"
            }
        }


# Global enhanced health monitor instance
_enhanced_monitor: Optional[EnhancedHealthMonitor] = None


def get_enhanced_monitor(alert_config: Optional[AlertConfig] = None) -> EnhancedHealthMonitor:
    """Get the global enhanced health monitor instance."""
    global _enhanced_monitor
    if _enhanced_monitor is None:
        _enhanced_monitor = EnhancedHealthMonitor(alert_config)
    return _enhanced_monitor


def start_enhanced_monitoring(alert_config: Optional[AlertConfig] = None):
    """Start enhanced health monitoring."""
    monitor = get_enhanced_monitor(alert_config)
    monitor.start_monitoring()
    return monitor


def stop_enhanced_monitoring():
    """Stop enhanced health monitoring."""
    global _enhanced_monitor
    if _enhanced_monitor:
        _enhanced_monitor.stop_monitoring()


def get_enhanced_health() -> Dict[str, Any]:
    """Get enhanced health status."""
    monitor = get_enhanced_monitor()
    return monitor.get_comprehensive_status()


def get_enhanced_metrics() -> str:
    """Get enhanced Prometheus metrics."""
    monitor = get_enhanced_monitor()
    return monitor.get_metrics()


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Enhanced Health Monitor")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--start-monitoring", action="store_true")
    parser.add_argument("--metrics", action="store_true")
    parser.add_argument("--webhook", help="Alert webhook URL")
    parser.add_argument("--slack", help="Slack webhook URL")

    args = parser.parse_args()

    # Setup alert configuration
    alert_config = AlertConfig()
    if args.webhook:
        alert_config.webhook_url = args.webhook
    if args.slack:
        alert_config.slack_webhook = args.slack

    if args.metrics:
        print(get_enhanced_metrics())
        sys.exit(0)

    if args.start_monitoring:
        print("Starting enhanced health monitoring...")
        monitor = start_enhanced_monitoring(alert_config)
        try:
            while True:
                time.sleep(60)
                print(f"Monitoring active... Uptime: {(datetime.now() - monitor.start_time)}")
        except KeyboardInterrupt:
            print("\nStopping enhanced health monitoring...")
            stop_enhanced_monitoring()
        sys.exit(0)

    # Get health status
    health = get_enhanced_health()

    if args.format == "json":
        print(json.dumps(health, indent=2))
    else:
        print(f"Enhanced Health Status: {health['status'].upper()}")
        print(f"Timestamp: {health['timestamp']}")
        print(f"Uptime: {health['uptime']['human']}")
        print(f"Instance: {health['instance']}")

        summary = health['summary']
        print("\nHealth Summary:")
        print(f"  Total Checks: {summary['total']}")
        print(f"  Healthy: {summary['healthy']}")
        print(f"  Warning: {summary['warning']}")
        print(f"  Unhealthy: {summary['unhealthy']}")
        print(f"  Critical: {summary['critical']}")

        if health.get('critical_issues'):
            print("\nCRITICAL ISSUES:")
            for issue in health['critical_issues']:
                print(f"  🚨 {issue}")

        if health.get('warnings'):
            print("\nWARNINGS:")
            for warning in health['warnings']:
                print(f"  ⚠️  {warning}")

        if health['status'] == 'healthy':
            print("\n✅ All enhanced health checks passed!")

    # Exit with appropriate status code
    if health['status'] in ['critical', 'unhealthy']:
        sys.exit(1)
    elif health['status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)
