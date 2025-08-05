"""
Enhanced monitoring and observability framework.

This module provides comprehensive monitoring with structured logging, performance metrics,
alerting rules, distributed tracing integration, and operational dashboards for
production-ready observability.
"""

from __future__ import annotations

import functools
import logging
import logging.handlers
import os
import platform
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        delete_from_gateway,
        generate_latest,
        push_to_gateway,
    )
    from prometheus_client import Enum as PrometheusEnum
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    component: str
    operation: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
        }

        # Add optional fields
        optional_fields = [
            "operation", "user_id", "request_id", "trace_id", "span_id",
            "duration_ms", "error_type", "stack_trace"
        ]

        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                data[field_name] = value

        # Add metadata
        if self.metadata:
            data["metadata"] = self.metadata

        return data


@dataclass
class MetricDefinition:
    """Definition of a custom metric."""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[Dict[float, float]] = None  # For summaries


@dataclass
class AlertRule:
    """Definition of an alert rule."""
    name: str
    expression: str
    severity: AlertSeverity
    duration: str = "1m"
    summary: str = ""
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


class StructuredLogger:
    """Enhanced structured logging with multiple outputs."""

    def __init__(self, component_name: str, log_file: Optional[str] = None):
        self.component_name = component_name
        self.log_file = log_file
        self.entries: List[LogEntry] = []
        self._lock = threading.Lock()
        self.max_entries = 10000

        # Setup structured logger
        if STRUCTLOG_AVAILABLE:
            self.struct_logger = structlog.get_logger(component_name)
        else:
            self.struct_logger = None

        # Setup standard logger
        self.std_logger = logging.getLogger(f"structured.{component_name}")
        self._setup_standard_logger()

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.log_entries_counter = Counter(
                'log_entries_total',
                'Total log entries by level and component',
                ['component', 'level']
            )

    def _setup_standard_logger(self):
        """Setup standard Python logger with JSON formatting."""
        if self.std_logger.handlers:
            return  # Already setup

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.std_logger.addHandler(console_handler)

        # File handler if specified
        if self.log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=100*1024*1024,  # 100MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.std_logger.addHandler(file_handler)

        self.std_logger.setLevel(logging.INFO)

    def log(self, level: LogLevel, message: str, operation: str = None,
            user_id: str = None, request_id: str = None, error: Exception = None,
            duration_ms: float = None, **metadata):
        """Log a structured entry."""
        timestamp = datetime.now(timezone.utc)

        # Get trace information if available
        trace_id = None
        span_id = None
        if OPENTELEMETRY_AVAILABLE:
            try:
                current_span = trace.get_current_span()
                if current_span:
                    span_context = current_span.get_span_context()
                    trace_id = format(span_context.trace_id, '032x')
                    span_id = format(span_context.span_id, '016x')
            except Exception:
                pass  # Ignore tracing errors

        # Handle error information
        error_type = None
        stack_trace = None
        if error:
            error_type = type(error).__name__
            stack_trace = ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))

        # Create log entry
        entry = LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            component=self.component_name,
            operation=operation,
            user_id=user_id,
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            error_type=error_type,
            stack_trace=stack_trace,
            metadata=metadata
        )

        # Store entry
        with self._lock:
            self.entries.append(entry)
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]

        # Log with structured logger if available
        if self.struct_logger:
            try:
                log_data = entry.to_dict()
                getattr(self.struct_logger, level.value)(message, **log_data)
            except Exception:
                pass  # Fallback to standard logging

        # Log with standard logger
        std_level = getattr(logging, level.value.upper())
        log_message = f"[{self.component_name}] {message}"
        if operation:
            log_message += f" (operation: {operation})"
        if duration_ms:
            log_message += f" (duration: {duration_ms:.2f}ms)"

        self.std_logger.log(std_level, log_message)

        # Update metrics
        if PROMETHEUS_AVAILABLE:
            self.log_entries_counter.labels(
                component=self.component_name,
                level=level.value
            ).inc()

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message."""
        self.log(LogLevel.ERROR, message, error=error, **kwargs)

    def critical(self, message: str, error: Exception = None, **kwargs):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, error=error, **kwargs)

    @contextmanager
    def operation_context(self, operation: str, user_id: str = None,
                         request_id: str = None, **metadata):
        """Context manager for logging operations with timing."""
        start_time = time.time()

        self.info(f"Starting operation: {operation}",
                 operation=operation, user_id=user_id, request_id=request_id, **metadata)

        try:
            yield
            duration_ms = (time.time() - start_time) * 1000
            self.info(f"Completed operation: {operation}",
                     operation=operation, user_id=user_id, request_id=request_id,
                     duration_ms=duration_ms, **metadata)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.error(f"Failed operation: {operation}",
                      operation=operation, user_id=user_id, request_id=request_id,
                      duration_ms=duration_ms, error=e, **metadata)
            raise

    def get_recent_entries(self, limit: int = 100, level: LogLevel = None) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        with self._lock:
            entries = self.entries.copy()

        if level:
            entries = [e for e in entries if e.level == level]

        return [entry.to_dict() for entry in entries[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._lock:
            total_entries = len(self.entries)

            # Count by level
            level_counts = {}
            for level in LogLevel:
                level_counts[level.value] = sum(
                    1 for entry in self.entries if entry.level == level
                )

        return {
            "component": self.component_name,
            "total_entries": total_entries,
            "entries_by_level": level_counts,
            "log_file": self.log_file
        }


class MetricsCollector:
    """Enhanced metrics collection and management."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or (CollectorRegistry() if PROMETHEUS_AVAILABLE else None)
        self.custom_metrics: Dict[str, Any] = {}
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self._lock = threading.Lock()

        # Initialize system metrics
        self._init_system_metrics()

        # Performance tracking
        self.operation_timers: Dict[str, float] = {}

    def _init_system_metrics(self):
        """Initialize system-level metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # System metrics
        self.system_cpu_percent = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_bytes = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type'],  # available, used, total
            registry=self.registry
        )

        self.system_disk_bytes = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['mountpoint', 'type'],  # used, free, total
            registry=self.registry
        )

        # Application metrics
        self.app_uptime_seconds = Gauge(
            'application_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )

        self.app_requests_total = Counter(
            'application_requests_total',
            'Total application requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.app_request_duration = Histogram(
            'application_request_duration_seconds',
            'Application request duration',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        # Business metrics
        self.documents_processed_total = Counter(
            'documents_processed_total',
            'Total documents processed',
            ['status', 'document_type'],
            registry=self.registry
        )

        self.document_processing_duration = Histogram(
            'document_processing_duration_seconds',
            'Time spent processing documents',
            ['document_type'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )

        self.active_operations = Gauge(
            'active_operations_count',
            'Number of currently active operations',
            ['operation_type'],
            registry=self.registry
        )

        # Error metrics
        self.error_count_total = Counter(
            'errors_total',
            'Total number of errors',
            ['component', 'error_type', 'severity'],
            registry=self.registry
        )

        # Start background system metrics collection
        self._start_system_metrics_collection()

    def _start_system_metrics_collection(self):
        """Start background thread for system metrics collection."""
        if not PROMETHEUS_AVAILABLE:
            return

        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_cpu_percent.set(cpu_percent)

                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_memory_bytes.labels(type='total').set(memory.total)
                    self.system_memory_bytes.labels(type='used').set(memory.used)
                    self.system_memory_bytes.labels(type='available').set(memory.available)

                    # Disk usage
                    for partition in psutil.disk_partitions():
                        try:
                            disk_usage = psutil.disk_usage(partition.mountpoint)
                            mountpoint = partition.mountpoint
                            self.system_disk_bytes.labels(mountpoint=mountpoint, type='total').set(disk_usage.total)
                            self.system_disk_bytes.labels(mountpoint=mountpoint, type='used').set(disk_usage.used)
                            self.system_disk_bytes.labels(mountpoint=mountpoint, type='free').set(disk_usage.free)
                        except PermissionError:
                            continue

                    time.sleep(30)  # Collect every 30 seconds

                except Exception as e:
                    logger.error(f"System metrics collection failed: {e}")
                    time.sleep(60)  # Back off on errors

        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()

    def register_metric(self, definition: MetricDefinition) -> Any:
        """Register a custom metric."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, metric registration skipped")
            return None

        with self._lock:
            if definition.name in self.custom_metrics:
                return self.custom_metrics[definition.name]

            # Create the appropriate metric type
            if definition.metric_type == MetricType.COUNTER:
                metric = Counter(
                    definition.name,
                    definition.description,
                    definition.labels,
                    registry=self.registry
                )
            elif definition.metric_type == MetricType.GAUGE:
                metric = Gauge(
                    definition.name,
                    definition.description,
                    definition.labels,
                    registry=self.registry
                )
            elif definition.metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    definition.name,
                    definition.description,
                    definition.labels,
                    buckets=definition.buckets,
                    registry=self.registry
                )
            elif definition.metric_type == MetricType.SUMMARY:
                metric = Summary(
                    definition.name,
                    definition.description,
                    definition.labels,
                    registry=self.registry
                )
            else:
                raise ValueError(f"Unsupported metric type: {definition.metric_type}")

            self.custom_metrics[definition.name] = metric
            self.metric_definitions[definition.name] = definition

            logger.info(f"Registered custom metric: {definition.name} ({definition.metric_type.value})")
            return metric

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.app_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        self.app_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_document_processing(self, document_type: str, duration: float, status: str = "success"):
        """Record document processing metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.documents_processed_total.labels(
            status=status,
            document_type=document_type
        ).inc()

        self.document_processing_duration.labels(
            document_type=document_type
        ).observe(duration)

    def record_error(self, component: str, error_type: str, severity: str = "error"):
        """Record error metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.error_count_total.labels(
            component=component,
            error_type=error_type,
            severity=severity
        ).inc()

    @contextmanager
    def track_operation(self, operation_type: str):
        """Context manager to track active operations."""
        if PROMETHEUS_AVAILABLE:
            self.active_operations.labels(operation_type=operation_type).inc()

        try:
            yield
        finally:
            if PROMETHEUS_AVAILABLE:
                self.active_operations.labels(operation_type=operation_type).dec()

    def get_metrics(self, format: str = "prometheus") -> str:
        """Get metrics in specified format."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus not available\n"

        if format == "prometheus":
            return generate_latest(self.registry).decode('utf-8')
        else:
            raise ValueError(f"Unsupported format: {format}")

    def push_to_gateway(self, gateway_url: str, job_name: str):
        """Push metrics to Prometheus pushgateway."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, cannot push metrics")
            return

        try:
            push_to_gateway(gateway_url, job=job_name, registry=self.registry)
            logger.info(f"Pushed metrics to gateway: {gateway_url}")
        except Exception as e:
            logger.error(f"Failed to push metrics to gateway: {e}")

    def get_metric_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered metric definitions."""
        with self._lock:
            return {
                name: {
                    "type": defn.metric_type.value,
                    "description": defn.description,
                    "labels": defn.labels
                }
                for name, defn in self.metric_definitions.items()
            }


class AlertManager:
    """Alert rule management and evaluation."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable] = []
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.alerts_fired = Counter(
                'alerts_fired_total',
                'Total alerts fired',
                ['alert_name', 'severity']
            )

    def register_alert_rule(self, rule: AlertRule):
        """Register an alert rule."""
        with self._lock:
            self.alert_rules[rule.name] = rule
        logger.info(f"Registered alert rule: {rule.name}")

    def register_callback(self, callback: Callable[[str, AlertRule, Dict[str, Any]], None]):
        """Register a callback for alert notifications."""
        self.alert_callbacks.append(callback)

    def fire_alert(self, alert_name: str, context: Dict[str, Any] = None):
        """Fire an alert."""
        context = context or {}

        with self._lock:
            if alert_name not in self.alert_rules:
                logger.error(f"Unknown alert rule: {alert_name}")
                return

            rule = self.alert_rules[alert_name]

            # Check if alert is already active
            if alert_name in self.active_alerts:
                logger.debug(f"Alert {alert_name} already active")
                return

            # Activate alert
            alert_data = {
                "fired_at": datetime.now(timezone.utc),
                "rule": rule,
                "context": context
            }
            self.active_alerts[alert_name] = alert_data

            logger.warning(f"Alert fired: {alert_name} (severity: {rule.severity.value})")

            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self.alerts_fired.labels(
                    alert_name=alert_name,
                    severity=rule.severity.value
                ).inc()

            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_name, rule, context)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

    def resolve_alert(self, alert_name: str):
        """Resolve an active alert."""
        with self._lock:
            if alert_name in self.active_alerts:
                del self.active_alerts[alert_name]
                logger.info(f"Alert resolved: {alert_name}")

    def get_active_alerts(self) -> Dict[str, Any]:
        """Get currently active alerts."""
        with self._lock:
            return {
                name: {
                    "fired_at": data["fired_at"].isoformat(),
                    "severity": data["rule"].severity.value,
                    "summary": data["rule"].summary,
                    "context": data["context"]
                }
                for name, data in self.active_alerts.items()
            }

    def get_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered alert rules."""
        with self._lock:
            return {
                name: {
                    "expression": rule.expression,
                    "severity": rule.severity.value,
                    "duration": rule.duration,
                    "summary": rule.summary,
                    "description": rule.description
                }
                for name, rule in self.alert_rules.items()
            }


class PerformanceProfiler:
    """Performance profiling and analysis."""

    def __init__(self):
        self.profiles: Dict[str, List[Dict[str, Any]]] = {}
        self.active_profiles: Dict[str, float] = {}
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.profile_duration = Histogram(
                'performance_profile_duration_seconds',
                'Performance profile durations',
                ['profile_name']
            )

    @contextmanager
    def profile(self, name: str, metadata: Dict[str, Any] = None):
        """Context manager for performance profiling."""
        start_time = time.time()
        start_cpu = time.process_time()

        # Record start
        with self._lock:
            self.active_profiles[name] = start_time

        try:
            yield
        finally:
            end_time = time.time()
            end_cpu = time.process_time()

            # Calculate metrics
            wall_time = end_time - start_time
            cpu_time = end_cpu - start_cpu

            # Store profile data
            profile_data = {
                "timestamp": start_time,
                "wall_time": wall_time,
                "cpu_time": cpu_time,
                "cpu_percent": (cpu_time / wall_time * 100) if wall_time > 0 else 0,
                "metadata": metadata or {}
            }

            with self._lock:
                if name not in self.profiles:
                    self.profiles[name] = []
                self.profiles[name].append(profile_data)

                # Keep only recent profiles (last 1000)
                if len(self.profiles[name]) > 1000:
                    self.profiles[name] = self.profiles[name][-1000:]

                # Remove from active
                self.active_profiles.pop(name, None)

            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self.profile_duration.labels(profile_name=name).observe(wall_time)

            logger.debug(f"Profile {name}: wall={wall_time:.3f}s cpu={cpu_time:.3f}s")

    def get_profile_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a specific profile."""
        with self._lock:
            if name not in self.profiles:
                return {"error": "Profile not found"}

            profiles = self.profiles[name]
            if not profiles:
                return {"error": "No profile data"}

            wall_times = [p["wall_time"] for p in profiles]
            cpu_times = [p["cpu_time"] for p in profiles]

            return {
                "count": len(profiles),
                "wall_time": {
                    "min": min(wall_times),
                    "max": max(wall_times),
                    "avg": sum(wall_times) / len(wall_times),
                    "total": sum(wall_times)
                },
                "cpu_time": {
                    "min": min(cpu_times),
                    "max": max(cpu_times),
                    "avg": sum(cpu_times) / len(cpu_times),
                    "total": sum(cpu_times)
                },
                "recent_samples": profiles[-10:]  # Last 10 samples
            }

    def profile_decorator(self, name: str = None, metadata: Dict[str, Any] = None):
        """Decorator for function profiling."""
        def decorator(func):
            profile_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile(profile_name, metadata):
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class MonitoringManager:
    """Central monitoring and observability manager."""

    def __init__(self):
        self.loggers: Dict[str, StructuredLogger] = {}
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.profiler = PerformanceProfiler()
        self.start_time = time.time()

        # Setup default alert rules
        self._setup_default_alerts()

        # Setup alert callbacks
        self.alert_manager.register_callback(self._default_alert_callback)

    def _setup_default_alerts(self):
        """Setup default alert rules."""
        # High error rate alert
        error_rate_alert = AlertRule(
            name="high_error_rate",
            expression="rate(errors_total[5m]) > 0.1",
            severity=AlertSeverity.WARNING,
            duration="2m",
            summary="High error rate detected",
            description="Error rate is above 10% for the last 5 minutes"
        )
        self.alert_manager.register_alert_rule(error_rate_alert)

        # High CPU usage alert
        cpu_alert = AlertRule(
            name="high_cpu_usage",
            expression="system_cpu_usage_percent > 80",
            severity=AlertSeverity.WARNING,
            duration="1m",
            summary="High CPU usage",
            description="CPU usage is above 80%"
        )
        self.alert_manager.register_alert_rule(cpu_alert)

        # High memory usage alert
        memory_alert = AlertRule(
            name="high_memory_usage",
            expression="(system_memory_usage_bytes{type='used'} / system_memory_usage_bytes{type='total'}) * 100 > 85",
            severity=AlertSeverity.CRITICAL,
            duration="1m",
            summary="High memory usage",
            description="Memory usage is above 85%"
        )
        self.alert_manager.register_alert_rule(memory_alert)

    def _default_alert_callback(self, alert_name: str, rule: AlertRule, context: Dict[str, Any]):
        """Default alert callback."""
        logger.warning(f"ALERT: {alert_name} - {rule.summary}")

    def get_logger(self, component_name: str, log_file: str = None) -> StructuredLogger:
        """Get or create a structured logger for a component."""
        if component_name not in self.loggers:
            self.loggers[component_name] = StructuredLogger(component_name, log_file)
        return self.loggers[component_name]

    def get_metrics_collector(self) -> MetricsCollector:
        """Get the metrics collector."""
        return self.metrics_collector

    def get_alert_manager(self) -> AlertManager:
        """Get the alert manager."""
        return self.alert_manager

    def get_profiler(self) -> PerformanceProfiler:
        """Get the performance profiler."""
        return self.profiler

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system monitoring status."""
        uptime = time.time() - self.start_time

        # Update uptime metric
        if PROMETHEUS_AVAILABLE:
            self.metrics_collector.app_uptime_seconds.set(uptime)

        # Collect system information
        system_info = {
            "uptime_seconds": uptime,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
        }

        # Add process information
        try:
            process = psutil.Process()
            system_info.update({
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            })
        except Exception:
            pass

        # Component status
        component_status = {
            "loggers": {
                name: logger.get_stats() for name, logger in self.loggers.items()
            },
            "metrics": {
                "custom_metrics_count": len(self.metrics_collector.custom_metrics),
                "definitions": self.metrics_collector.get_metric_definitions()
            },
            "alerts": {
                "active_alerts": self.alert_manager.get_active_alerts(),
                "alert_rules_count": len(self.alert_manager.alert_rules)
            },
            "profiler": {
                "active_profiles": len(self.profiler.active_profiles),
                "total_profiles": len(self.profiler.profiles)
            }
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": system_info,
            "components": component_status,
            "monitoring_enabled": True
        }

    def export_metrics(self, format: str = "prometheus") -> str:
        """Export all metrics."""
        return self.metrics_collector.get_metrics(format)

    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        checks = {
            "monitoring_system": True,
            "metrics_collection": PROMETHEUS_AVAILABLE,
            "structured_logging": STRUCTLOG_AVAILABLE,
            "distributed_tracing": OPENTELEMETRY_AVAILABLE,
        }

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            checks.update({
                "cpu_available": cpu_percent < 95,
                "memory_available": memory.percent < 95,
                "disk_available": True  # Simplified check
            })
        except Exception:
            checks["system_resources"] = False

        overall_health = all(checks.values())

        return {
            "healthy": overall_health,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global monitoring manager instance
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager() -> MonitoringManager:
    """Get the global monitoring manager instance."""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager


# Convenience functions and decorators
def get_logger(component_name: str) -> StructuredLogger:
    """Get a structured logger for a component."""
    return get_monitoring_manager().get_logger(component_name)


def track_performance(name: str = None, metadata: Dict[str, Any] = None):
    """Decorator for performance tracking."""
    def decorator(func):
        profile_name = name or f"{func.__module__}.{func.__name__}"
        return get_monitoring_manager().get_profiler().profile_decorator(profile_name, metadata)(func)
    return decorator


def record_metric(metric_name: str, value: float, labels: Dict[str, str] = None):
    """Record a custom metric value."""
    # This would need to be implemented based on the metric type
    # For now, it's a placeholder
    pass


# Example usage and testing
if __name__ == "__main__":
    # Initialize monitoring
    manager = get_monitoring_manager()

    # Get a logger
    logger = get_logger("test_component")

    # Test logging
    logger.info("Testing structured logging", operation="test", user_id="test_user")

    # Test performance profiling
    @track_performance("test_function")
    def test_function():
        time.sleep(0.1)
        return "success"

    result = test_function()
    print(f"Function result: {result}")

    # Test metrics
    metrics = manager.get_metrics_collector()
    metrics.record_request("GET", "/test", 200, 0.1)

    # Test alerts
    alert_mgr = manager.get_alert_manager()
    alert_mgr.fire_alert("high_error_rate", {"error_count": 10})

    # Get system status
    status = manager.get_system_status()
    print(f"System status: {status['system']['uptime_seconds']:.1f}s uptime")

    # Export metrics
    if PROMETHEUS_AVAILABLE:
        metrics_output = manager.export_metrics()
        print(f"Exported {len(metrics_output.split('\n'))} metric lines")
