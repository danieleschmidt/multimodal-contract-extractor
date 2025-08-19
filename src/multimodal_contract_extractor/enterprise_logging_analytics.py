"""
Enterprise Logging and Analytics System

Comprehensive logging, performance metrics, error analytics, user behavior tracking,
and research experiment tracking for the multimodal contract extractor system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import threading
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
import statistics
from concurrent.futures import ThreadPoolExecutor
import gzip
import traceback

import numpy as np
from pydantic import BaseModel

from .enterprise_error_handling import ComponentType, ErrorSeverity
from .enhanced_enterprise_security import SecurityContext, AuditEventType

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Enhanced log levels for enterprise logging."""
    
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    BUSINESS = "business"


class EventCategory(Enum):
    """Categories for event classification."""
    
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS_LOGIC = "business_logic"
    USER_INTERACTION = "user_interaction"
    RESEARCH = "research"
    ALGORITHM = "algorithm"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"


class AnalyticsMetricType(Enum):
    """Types of analytics metrics."""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"
    PERCENTILE = "percentile"


@dataclass
class StructuredLogEntry:
    """Structured log entry with comprehensive metadata."""
    
    timestamp: float = field(default_factory=time.time)
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: LogLevel = LogLevel.INFO
    category: EventCategory = EventCategory.APPLICATION
    component: ComponentType = ComponentType.DOCUMENT_PROCESSOR
    message: str = ""
    
    # Context information
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Execution context
    operation: Optional[str] = None
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    # Additional structured data
    tags: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Research-specific fields
    algorithm_name: Optional[str] = None
    experiment_id: Optional[str] = None
    model_version: Optional[str] = None
    accuracy: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    
    name: str
    metric_type: AnalyticsMetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    component: ComponentType = ComponentType.DOCUMENT_PROCESSOR
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class UserBehaviorEvent:
    """User behavior tracking event."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    user_id: str = ""
    session_id: str = ""
    event_type: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)
    
    # Page/screen information
    page: Optional[str] = None
    referrer: Optional[str] = None
    
    # Device/browser information
    user_agent: Optional[str] = None
    client_ip: Optional[str] = None
    
    # Performance timing
    page_load_time: Optional[float] = None
    interaction_time: Optional[float] = None


@dataclass
class ResearchExperimentMetrics:
    """Research experiment tracking metrics."""
    
    experiment_id: str
    algorithm_name: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"
    
    # Experiment parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    results: Dict[str, float] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # System information
    hardware_info: Dict[str, Any] = field(default_factory=dict)
    software_versions: Dict[str, str] = field(default_factory=dict)
    
    # Resource usage
    max_memory_mb: Optional[float] = None
    total_cpu_hours: Optional[float] = None
    gpu_utilization: Optional[float] = None
    
    # Quality metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Additional metadata
    tags: Dict[str, str] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    notes: str = ""


class StructuredLogger:
    """Enterprise-grade structured logger."""
    
    def __init__(self, logger_name: str = "enterprise", log_file_path: Optional[Path] = None):
        self.logger_name = logger_name
        self.log_file_path = log_file_path or Path("enterprise_logs.jsonl")
        self.rotation_size_mb = 100
        self.max_files = 10
        self.compression_enabled = True
        
        self._log_buffer: deque = deque(maxlen=10000)
        self._buffer_lock = threading.Lock()
        self._flush_interval = 5.0  # Flush buffer every 5 seconds
        self._flush_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._log_counts = defaultdict(int)
        self._log_rates = defaultdict(lambda: deque(maxlen=100))
        
        # Initialize logging infrastructure
        self._setup_file_rotation()
    
    def _setup_file_rotation(self):
        """Setup log file rotation."""
        # Ensure log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(
        self,
        level: LogLevel,
        message: str,
        component: ComponentType = ComponentType.DOCUMENT_PROCESSOR,
        category: EventCategory = EventCategory.APPLICATION,
        **kwargs
    ) -> str:
        """Log a structured message."""
        
        # Create structured log entry
        entry = StructuredLogEntry(
            level=level,
            message=message,
            component=component,
            category=category,
            **kwargs
        )
        
        # Add execution context
        frame = traceback.extract_stack()[-2]
        entry.file_name = frame.filename
        entry.line_number = frame.lineno
        entry.function_name = frame.name
        entry.module_name = Path(frame.filename).stem
        
        # Add to buffer
        with self._buffer_lock:
            self._log_buffer.append(entry)
            self._log_counts[level.value] += 1
            self._log_rates[level.value].append(time.time())
        
        # Also log to Python logger for immediate visibility
        python_level = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.SECURITY: logging.CRITICAL,
            LogLevel.AUDIT: logging.INFO,
            LogLevel.PERFORMANCE: logging.INFO,
            LogLevel.BUSINESS: logging.INFO,
        }.get(level, logging.INFO)
        
        logger.log(
            python_level,
            f"[{component.value}] {message}",
            extra={
                "log_id": entry.log_id,
                "correlation_id": entry.correlation_id,
                "category": category.value
            }
        )
        
        return entry.log_id
    
    def trace(self, message: str, **kwargs) -> str:
        """Log trace level message."""
        return self.log(LogLevel.TRACE, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> str:
        """Log debug level message."""
        return self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> str:
        """Log info level message."""
        return self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> str:
        """Log warning level message."""
        return self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(
        self, 
        message: str, 
        error: Optional[Exception] = None, 
        **kwargs
    ) -> str:
        """Log error level message."""
        if error:
            kwargs.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc()
            })
        return self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(
        self, 
        message: str, 
        error: Optional[Exception] = None, 
        **kwargs
    ) -> str:
        """Log critical level message."""
        if error:
            kwargs.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc()
            })
        return self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def security(self, message: str, **kwargs) -> str:
        """Log security event."""
        return self.log(
            LogLevel.SECURITY, 
            message, 
            category=EventCategory.SECURITY,
            **kwargs
        )
    
    def audit(self, message: str, **kwargs) -> str:
        """Log audit event."""
        return self.log(
            LogLevel.AUDIT,
            message,
            category=EventCategory.COMPLIANCE,
            **kwargs
        )
    
    def performance(
        self,
        message: str,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> str:
        """Log performance event."""
        return self.log(
            LogLevel.PERFORMANCE,
            message,
            category=EventCategory.PERFORMANCE,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def business(self, message: str, **kwargs) -> str:
        """Log business logic event."""
        return self.log(
            LogLevel.BUSINESS,
            message,
            category=EventCategory.BUSINESS_LOGIC,
            **kwargs
        )
    
    def research(
        self,
        message: str,
        experiment_id: Optional[str] = None,
        algorithm_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log research event."""
        return self.log(
            LogLevel.INFO,
            message,
            category=EventCategory.RESEARCH,
            experiment_id=experiment_id,
            algorithm_name=algorithm_name,
            **kwargs
        )
    
    async def start_flush_task(self):
        """Start the buffer flush task."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())
    
    async def stop_flush_task(self):
        """Stop the buffer flush task."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_buffer()
    
    async def _periodic_flush(self):
        """Periodically flush the log buffer."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                await self._flush_buffer()  # Final flush
                break
            except Exception as e:
                logger.error(f"Error in log buffer flush: {e}")
    
    async def _flush_buffer(self):
        """Flush the log buffer to file."""
        if not self._log_buffer:
            return
        
        # Get current buffer contents
        with self._buffer_lock:
            entries_to_flush = list(self._log_buffer)
            self._log_buffer.clear()
        
        if not entries_to_flush:
            return
        
        # Write to file
        try:
            # Check if rotation is needed
            if self.log_file_path.exists() and self.log_file_path.stat().st_size > self.rotation_size_mb * 1024 * 1024:
                self._rotate_log_files()
            
            # Write entries
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for entry in entries_to_flush:
                    log_dict = self._entry_to_dict(entry)
                    f.write(json.dumps(log_dict) + '\n')
            
        except Exception as e:
            logger.error(f"Failed to flush log buffer: {e}")
            # Put entries back in buffer
            with self._buffer_lock:
                self._log_buffer.extendleft(reversed(entries_to_flush))
    
    def _entry_to_dict(self, entry: StructuredLogEntry) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization."""
        return {
            "timestamp": entry.timestamp,
            "iso_timestamp": datetime.fromtimestamp(entry.timestamp).isoformat(),
            "log_id": entry.log_id,
            "level": entry.level.value,
            "category": entry.category.value,
            "component": entry.component.value,
            "message": entry.message,
            
            # Context
            "correlation_id": entry.correlation_id,
            "session_id": entry.session_id,
            "user_id": entry.user_id,
            "request_id": entry.request_id,
            
            # Execution context
            "operation": entry.operation,
            "function": entry.function_name,
            "module": entry.module_name,
            "file": entry.file_name,
            "line": entry.line_number,
            
            # Performance
            "duration_ms": entry.duration_ms,
            "memory_mb": entry.memory_mb,
            "cpu_percent": entry.cpu_percent,
            
            # Data
            "tags": entry.tags,
            "metrics": entry.metrics,
            "context": entry.context_data,
            
            # Errors
            "error_type": entry.error_type,
            "error_message": entry.error_message,
            "stack_trace": entry.stack_trace,
            
            # Research
            "algorithm": entry.algorithm_name,
            "experiment_id": entry.experiment_id,
            "model_version": entry.model_version,
            "accuracy": entry.accuracy,
            "confidence": entry.confidence
        }
    
    def _rotate_log_files(self):
        """Rotate log files."""
        try:
            # Compress and move existing log files
            for i in range(self.max_files - 1, 0, -1):
                old_file = self.log_file_path.with_suffix(f'.{i}.gz')
                new_file = self.log_file_path.with_suffix(f'.{i+1}.gz')
                if old_file.exists():
                    old_file.rename(new_file)
            
            # Compress current log file
            if self.log_file_path.exists():
                compressed_file = self.log_file_path.with_suffix('.1.gz')
                with open(self.log_file_path, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                # Remove original file
                self.log_file_path.unlink()
            
        except Exception as e:
            logger.error(f"Failed to rotate log files: {e}")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._buffer_lock:
            buffer_size = len(self._log_buffer)
            
            # Calculate log rates (logs per minute)
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            rates = {}
            for level, timestamps in self._log_rates.items():
                recent_logs = [t for t in timestamps if t > one_minute_ago]
                rates[level] = len(recent_logs)
        
        return {
            "total_logs_by_level": dict(self._log_counts),
            "buffer_size": buffer_size,
            "log_rates_per_minute": rates,
            "log_file_size_mb": self.log_file_path.stat().st_size / (1024*1024) if self.log_file_path.exists() else 0
        }


class PerformanceAnalytics:
    """Performance analytics and metrics collection."""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.metric_aggregates: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()
        self.retention_hours = 24
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: AnalyticsMetricType = AnalyticsMetricType.GAUGE,
        component: ComponentType = ComponentType.DOCUMENT_PROCESSOR,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = ""
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            component=component,
            tags=tags or {},
            unit=unit,
            description=description
        )
        
        with self._lock:
            self.metrics[name].append(metric)
            
            # Keep only recent metrics
            cutoff_time = time.time() - (self.retention_hours * 3600)
            self.metrics[name] = [
                m for m in self.metrics[name] 
                if m.timestamp > cutoff_time
            ]
            
            # Update aggregates
            self._update_aggregates(name)
    
    def _update_aggregates(self, metric_name: str):
        """Update metric aggregates."""
        metrics = self.metrics[metric_name]
        if not metrics:
            return
        
        values = [m.value for m in metrics]
        recent_values = [m.value for m in metrics if m.timestamp > time.time() - 3600]  # Last hour
        
        aggregates = {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "recent_count": len(recent_values),
            "recent_mean": statistics.mean(recent_values) if recent_values else 0,
        }
        
        # Percentiles
        if values:
            sorted_values = sorted(values)
            n = len(sorted_values)
            aggregates.update({
                "p50": sorted_values[int(0.5 * n)],
                "p90": sorted_values[int(0.9 * n)],
                "p95": sorted_values[int(0.95 * n)],
                "p99": sorted_values[int(0.99 * n)],
            })
        
        self.metric_aggregates[metric_name] = aggregates
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        with self._lock:
            return self.metric_aggregates.get(metric_name, {})
    
    def get_all_metrics_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary for all metrics."""
        with self._lock:
            return self.metric_aggregates.copy()
    
    def get_metric_history(
        self, 
        metric_name: str, 
        time_window_hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get metric history within time window."""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        with self._lock:
            metrics = self.metrics.get(metric_name, [])
            recent_metrics = [
                {
                    "timestamp": m.timestamp,
                    "value": m.value,
                    "component": m.component.value,
                    "tags": m.tags
                }
                for m in metrics
                if m.timestamp > cutoff_time
            ]
        
        return recent_metrics
    
    def record_algorithm_performance(
        self,
        algorithm_name: str,
        execution_time: float,
        accuracy: float,
        confidence: float,
        memory_usage: float,
        throughput: float,
        component: ComponentType
    ):
        """Record comprehensive algorithm performance metrics."""
        base_tags = {"algorithm": algorithm_name}
        
        self.record_metric(
            f"algorithm.{algorithm_name}.execution_time",
            execution_time,
            AnalyticsMetricType.TIMER,
            component,
            base_tags,
            "seconds",
            f"Execution time for {algorithm_name}"
        )
        
        self.record_metric(
            f"algorithm.{algorithm_name}.accuracy",
            accuracy,
            AnalyticsMetricType.GAUGE,
            component,
            base_tags,
            "percent",
            f"Accuracy for {algorithm_name}"
        )
        
        self.record_metric(
            f"algorithm.{algorithm_name}.confidence",
            confidence,
            AnalyticsMetricType.GAUGE,
            component,
            base_tags,
            "percent",
            f"Confidence for {algorithm_name}"
        )
        
        self.record_metric(
            f"algorithm.{algorithm_name}.memory_usage",
            memory_usage,
            AnalyticsMetricType.GAUGE,
            component,
            base_tags,
            "MB",
            f"Memory usage for {algorithm_name}"
        )
        
        self.record_metric(
            f"algorithm.{algorithm_name}.throughput",
            throughput,
            AnalyticsMetricType.GAUGE,
            component,
            base_tags,
            "items/sec",
            f"Throughput for {algorithm_name}"
        )


class ErrorAnalytics:
    """Error analytics and pattern detection."""
    
    def __init__(self):
        self.error_events: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.max_events = 10000
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        component: ComponentType,
        operation: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ):
        """Record an error event for analytics."""
        error_event = {
            "timestamp": time.time(),
            "error_id": str(uuid.uuid4()),
            "error_type": error_type,
            "error_message": error_message,
            "component": component.value,
            "operation": operation,
            "stack_trace": stack_trace,
            "context": context or {},
            "severity": severity.value
        }
        
        with self._lock:
            self.error_events.append(error_event)
            
            # Keep only recent events
            if len(self.error_events) > self.max_events:
                self.error_events = self.error_events[-self.max_events:]
            
            # Update error patterns
            self._update_error_patterns(error_event)
    
    def _update_error_patterns(self, error_event: Dict[str, Any]):
        """Update error patterns for analytics."""
        error_key = f"{error_event['component']}.{error_event['error_type']}"
        
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = {
                "first_seen": error_event["timestamp"],
                "last_seen": error_event["timestamp"],
                "count": 0,
                "operations": set(),
                "severity_distribution": defaultdict(int),
                "hourly_counts": defaultdict(int)
            }
        
        pattern = self.error_patterns[error_key]
        pattern["last_seen"] = error_event["timestamp"]
        pattern["count"] += 1
        pattern["operations"].add(error_event["operation"])
        pattern["severity_distribution"][error_event["severity"]] += 1
        
        # Update hourly counts
        hour_key = int(error_event["timestamp"] // 3600)
        pattern["hourly_counts"][hour_key] += 1
    
    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time window."""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        with self._lock:
            recent_errors = [
                e for e in self.error_events
                if e["timestamp"] > cutoff_time
            ]
        
        if not recent_errors:
            return {
                "total_errors": 0,
                "error_rate_per_hour": 0,
                "top_errors": [],
                "component_distribution": {},
                "severity_distribution": {}
            }
        
        # Count by type
        error_type_counts = defaultdict(int)
        component_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for error in recent_errors:
            error_type_counts[error["error_type"]] += 1
            component_counts[error["component"]] += 1
            severity_counts[error["severity"]] += 1
        
        # Top errors
        top_errors = sorted(
            error_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(recent_errors),
            "error_rate_per_hour": len(recent_errors) / time_window_hours,
            "top_errors": [{"type": error_type, "count": count} for error_type, count in top_errors],
            "component_distribution": dict(component_counts),
            "severity_distribution": dict(severity_counts),
            "time_window_hours": time_window_hours
        }
    
    def detect_error_anomalies(self) -> List[Dict[str, Any]]:
        """Detect error rate anomalies."""
        anomalies = []
        current_hour = int(time.time() // 3600)
        
        with self._lock:
            for error_key, pattern in self.error_patterns.items():
                hourly_counts = pattern["hourly_counts"]
                
                # Get recent hourly counts
                recent_hours = [
                    hourly_counts.get(current_hour - i, 0)
                    for i in range(24)  # Last 24 hours
                ]
                
                if len([c for c in recent_hours if c > 0]) < 3:
                    continue  # Not enough data
                
                # Calculate baseline (average of hours 4-24)
                baseline_counts = recent_hours[4:]
                if baseline_counts:
                    baseline_mean = statistics.mean(baseline_counts)
                    baseline_std = statistics.stdev(baseline_counts) if len(baseline_counts) > 1 else 0
                    
                    # Check current hour
                    current_count = recent_hours[0]
                    threshold = baseline_mean + (3 * baseline_std)  # 3 sigma threshold
                    
                    if current_count > threshold and current_count > baseline_mean * 2:
                        anomalies.append({
                            "error_pattern": error_key,
                            "current_count": current_count,
                            "baseline_mean": baseline_mean,
                            "threshold": threshold,
                            "anomaly_score": (current_count - baseline_mean) / (baseline_std + 0.001),
                            "severity": "high" if current_count > baseline_mean * 5 else "medium"
                        })
        
        return anomalies


class UserBehaviorTracker:
    """User behavior tracking and analytics."""
    
    def __init__(self):
        self.behavior_events: List[UserBehaviorEvent] = []
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.max_events = 50000
    
    def track_event(
        self,
        user_id: str,
        session_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        page: Optional[str] = None,
        user_agent: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> str:
        """Track a user behavior event."""
        event = UserBehaviorEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_data=event_data or {},
            page=page,
            user_agent=user_agent,
            client_ip=client_ip
        )
        
        with self._lock:
            self.behavior_events.append(event)
            
            # Keep only recent events
            if len(self.behavior_events) > self.max_events:
                self.behavior_events = self.behavior_events[-self.max_events:]
            
            # Update user session info
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    "user_id": user_id,
                    "start_time": event.timestamp,
                    "last_activity": event.timestamp,
                    "event_count": 0,
                    "pages_visited": set(),
                    "user_agent": user_agent,
                    "client_ip": client_ip
                }
            
            session = self.user_sessions[session_id]
            session["last_activity"] = event.timestamp
            session["event_count"] += 1
            if page:
                session["pages_visited"].add(page)
        
        return event.event_id
    
    def get_user_analytics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get user behavior analytics."""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        with self._lock:
            recent_events = [
                e for e in self.behavior_events
                if e.timestamp > cutoff_time
            ]
            
            active_sessions = [
                s for s in self.user_sessions.values()
                if s["last_activity"] > cutoff_time
            ]
        
        if not recent_events:
            return {
                "total_events": 0,
                "unique_users": 0,
                "active_sessions": 0,
                "top_events": [],
                "top_pages": []
            }
        
        # Count events by type
        event_type_counts = defaultdict(int)
        page_counts = defaultdict(int)
        unique_users = set()
        
        for event in recent_events:
            event_type_counts[event.event_type] += 1
            unique_users.add(event.user_id)
            if event.page:
                page_counts[event.page] += 1
        
        # Top events and pages
        top_events = sorted(
            event_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        top_pages = sorted(
            page_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Session analytics
        session_durations = []
        for session in active_sessions:
            duration = session["last_activity"] - session["start_time"]
            session_durations.append(duration)
        
        avg_session_duration = statistics.mean(session_durations) if session_durations else 0
        
        return {
            "total_events": len(recent_events),
            "unique_users": len(unique_users),
            "active_sessions": len(active_sessions),
            "avg_session_duration_minutes": avg_session_duration / 60,
            "top_events": [{"type": event_type, "count": count} for event_type, count in top_events],
            "top_pages": [{"page": page, "count": count} for page, count in top_pages],
            "time_window_hours": time_window_hours
        }
    
    def get_user_journey(self, user_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user journey for analysis."""
        with self._lock:
            user_events = [
                e for e in self.behavior_events
                if e.user_id == user_id and (session_id is None or e.session_id == session_id)
            ]
        
        # Sort by timestamp
        user_events.sort(key=lambda x: x.timestamp)
        
        return [
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "page": event.page,
                "event_data": event.event_data,
                "session_id": event.session_id
            }
            for event in user_events
        ]


class ResearchExperimentTracker:
    """Research experiment tracking and analytics."""
    
    def __init__(self):
        self.experiments: Dict[str, ResearchExperimentMetrics] = {}
        self.experiment_history: List[ResearchExperimentMetrics] = []
        self._lock = threading.Lock()
    
    def start_experiment(
        self,
        algorithm_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start tracking a research experiment."""
        experiment_id = str(uuid.uuid4())
        
        experiment = ResearchExperimentMetrics(
            experiment_id=experiment_id,
            algorithm_name=algorithm_name,
            start_time=time.time(),
            parameters=parameters or {},
            hyperparameters=hyperparameters or {},
            tags=tags or {}
        )
        
        # Add system information
        experiment.hardware_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "platform": "linux"  # Could be detected dynamically
        }
        
        with self._lock:
            self.experiments[experiment_id] = experiment
        
        logger.info(f"Started research experiment: {experiment_id} ({algorithm_name})")
        return experiment_id
    
    def update_experiment_metrics(
        self,
        experiment_id: str,
        metrics: Dict[str, float],
        results: Optional[Dict[str, float]] = None
    ):
        """Update experiment metrics during execution."""
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            return
        
        experiment.metrics.update(metrics)
        if results:
            experiment.results.update(results)
        
        # Update specific quality metrics if provided
        if "accuracy" in metrics:
            experiment.accuracy = metrics["accuracy"]
        if "precision" in metrics:
            experiment.precision = metrics["precision"]
        if "recall" in metrics:
            experiment.recall = metrics["recall"]
        if "f1_score" in metrics:
            experiment.f1_score = metrics["f1_score"]
    
    def record_resource_usage(
        self,
        experiment_id: str,
        memory_mb: float,
        cpu_hours: float,
        gpu_utilization: Optional[float] = None
    ):
        """Record resource usage for experiment."""
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            
        if not experiment:
            return
        
        # Update maximum resource usage
        experiment.max_memory_mb = max(experiment.max_memory_mb or 0, memory_mb)
        experiment.total_cpu_hours = (experiment.total_cpu_hours or 0) + cpu_hours
        if gpu_utilization is not None:
            experiment.gpu_utilization = max(experiment.gpu_utilization or 0, gpu_utilization)
    
    def finish_experiment(
        self,
        experiment_id: str,
        status: str = "completed",
        final_results: Optional[Dict[str, float]] = None,
        artifacts: Optional[List[str]] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Finish a research experiment."""
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            
        if not experiment:
            return {"error": f"Experiment {experiment_id} not found"}
        
        experiment.end_time = time.time()
        experiment.status = status
        if final_results:
            experiment.results.update(final_results)
        if artifacts:
            experiment.artifacts.extend(artifacts)
        experiment.notes = notes
        
        # Move to history and remove from active experiments
        with self._lock:
            self.experiment_history.append(experiment)
            del self.experiments[experiment_id]
        
        duration_hours = (experiment.end_time - experiment.start_time) / 3600
        logger.info(f"Finished research experiment: {experiment_id} ({status}) - Duration: {duration_hours:.2f}h")
        
        return {
            "experiment_id": experiment_id,
            "status": status,
            "duration_hours": duration_hours,
            "final_results": experiment.results,
            "resource_usage": {
                "max_memory_mb": experiment.max_memory_mb,
                "total_cpu_hours": experiment.total_cpu_hours,
                "gpu_utilization": experiment.gpu_utilization
            }
        }
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment summary."""
        with self._lock:
            # Check active experiments
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                # Check history
                for exp in self.experiment_history:
                    if exp.experiment_id == experiment_id:
                        experiment = exp
                        break
        
        if not experiment:
            return None
        
        duration = (experiment.end_time or time.time()) - experiment.start_time
        
        return {
            "experiment_id": experiment.experiment_id,
            "algorithm_name": experiment.algorithm_name,
            "status": experiment.status,
            "start_time": experiment.start_time,
            "end_time": experiment.end_time,
            "duration_hours": duration / 3600,
            "parameters": experiment.parameters,
            "hyperparameters": experiment.hyperparameters,
            "results": experiment.results,
            "metrics": experiment.metrics,
            "quality_metrics": {
                "accuracy": experiment.accuracy,
                "precision": experiment.precision,
                "recall": experiment.recall,
                "f1_score": experiment.f1_score
            },
            "resource_usage": {
                "max_memory_mb": experiment.max_memory_mb,
                "total_cpu_hours": experiment.total_cpu_hours,
                "gpu_utilization": experiment.gpu_utilization
            },
            "hardware_info": experiment.hardware_info,
            "tags": experiment.tags,
            "artifacts": experiment.artifacts,
            "notes": experiment.notes
        }
    
    def get_experiment_comparison(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple experiments."""
        experiments = []
        
        with self._lock:
            for exp_id in experiment_ids:
                # Check active experiments
                exp = self.experiments.get(exp_id)
                if not exp:
                    # Check history
                    for hist_exp in self.experiment_history:
                        if hist_exp.experiment_id == exp_id:
                            exp = hist_exp
                            break
                
                if exp:
                    experiments.append(exp)
        
        if not experiments:
            return {"error": "No experiments found"}
        
        comparison = {
            "experiments": [],
            "metric_comparison": {},
            "best_performers": {}
        }
        
        # Collect all metrics across experiments
        all_metric_names = set()
        for exp in experiments:
            all_metric_names.update(exp.results.keys())
            all_metric_names.update(exp.metrics.keys())
        
        # Compare experiments
        for exp in experiments:
            duration = (exp.end_time or time.time()) - exp.start_time
            comparison["experiments"].append({
                "experiment_id": exp.experiment_id,
                "algorithm_name": exp.algorithm_name,
                "status": exp.status,
                "duration_hours": duration / 3600,
                "accuracy": exp.accuracy,
                "max_memory_mb": exp.max_memory_mb,
                "total_cpu_hours": exp.total_cpu_hours
            })
        
        # Find best performers for each metric
        for metric_name in all_metric_names:
            metric_values = []
            for exp in experiments:
                value = exp.results.get(metric_name) or exp.metrics.get(metric_name)
                if value is not None:
                    metric_values.append((exp.experiment_id, value))
            
            if metric_values:
                best_exp_id, best_value = max(metric_values, key=lambda x: x[1])
                comparison["best_performers"][metric_name] = {
                    "experiment_id": best_exp_id,
                    "value": best_value
                }
        
        return comparison


class EnterpriseLoggingAnalyticsSystem:
    """Comprehensive enterprise logging and analytics system."""
    
    def __init__(self):
        self.structured_logger = StructuredLogger("enterprise_system")
        self.performance_analytics = PerformanceAnalytics()
        self.error_analytics = ErrorAnalytics()
        self.user_behavior = UserBehaviorTracker()
        self.research_tracker = ResearchExperimentTracker()
        
        self.analytics_enabled = True
        self._analytics_task: Optional[asyncio.Task] = None
    
    async def start_analytics(self):
        """Start the analytics system."""
        if self._analytics_task is None or self._analytics_task.done():
            await self.structured_logger.start_flush_task()
            self._analytics_task = asyncio.create_task(self._analytics_loop())
            logger.info("Enterprise logging and analytics system started")
    
    async def stop_analytics(self):
        """Stop the analytics system."""
        self.analytics_enabled = False
        
        if self._analytics_task and not self._analytics_task.done():
            self._analytics_task.cancel()
            try:
                await self._analytics_task
            except asyncio.CancelledError:
                pass
        
        await self.structured_logger.stop_flush_task()
        logger.info("Enterprise logging and analytics system stopped")
    
    async def _analytics_loop(self):
        """Main analytics processing loop."""
        while self.analytics_enabled:
            try:
                # Periodic analytics tasks
                await self._detect_anomalies()
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _detect_anomalies(self):
        """Detect various types of anomalies."""
        try:
            # Detect error anomalies
            error_anomalies = self.error_analytics.detect_error_anomalies()
            for anomaly in error_anomalies:
                self.structured_logger.warning(
                    f"Error anomaly detected: {anomaly['error_pattern']}",
                    category=EventCategory.SYSTEM,
                    context_data=anomaly
                )
            
            # Could add more anomaly detection here
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
    
    def get_comprehensive_analytics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data."""
        return {
            "timestamp": time.time(),
            "system_overview": {
                "logging": self.structured_logger.get_log_statistics(),
                "performance": self.performance_analytics.get_all_metrics_summary(),
                "errors": self.error_analytics.get_error_statistics(),
                "user_behavior": self.user_behavior.get_user_analytics(),
            },
            "active_experiments": len(self.research_tracker.experiments),
            "total_experiment_history": len(self.research_tracker.experiment_history),
            "anomalies": {
                "errors": self.error_analytics.detect_error_anomalies()
            }
        }


# Global enterprise logging and analytics system
enterprise_logging_system = EnterpriseLoggingAnalyticsSystem()


def get_enterprise_logger() -> StructuredLogger:
    """Get the enterprise structured logger."""
    return enterprise_logging_system.structured_logger


def get_performance_analytics() -> PerformanceAnalytics:
    """Get the performance analytics system."""
    return enterprise_logging_system.performance_analytics


def get_error_analytics() -> ErrorAnalytics:
    """Get the error analytics system."""
    return enterprise_logging_system.error_analytics


def get_user_behavior_tracker() -> UserBehaviorTracker:
    """Get the user behavior tracker."""
    return enterprise_logging_system.user_behavior


def get_research_tracker() -> ResearchExperimentTracker:
    """Get the research experiment tracker."""
    return enterprise_logging_system.research_tracker


def get_logging_analytics_system() -> EnterpriseLoggingAnalyticsSystem:
    """Get the global logging and analytics system."""
    return enterprise_logging_system


# Decorators for automatic logging
def log_performance(algorithm_name: str, component: ComponentType = ComponentType.DOCUMENT_PROCESSOR):
    """Decorator to automatically log algorithm performance."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            memory_start = psutil.virtual_memory().used / (1024**2)
            
            try:
                result = await func(*args, **kwargs)
                
                # Calculate performance metrics
                execution_time = time.time() - start_time
                memory_end = psutil.virtual_memory().used / (1024**2)
                memory_usage = memory_end - memory_start
                
                # Extract metrics from result if available
                accuracy = result.get('accuracy', 0.0) if isinstance(result, dict) else 0.0
                confidence = result.get('confidence', 0.0) if isinstance(result, dict) else 0.0
                throughput = 1.0 / execution_time if execution_time > 0 else 0.0
                
                # Record performance
                enterprise_logging_system.performance_analytics.record_algorithm_performance(
                    algorithm_name=algorithm_name,
                    execution_time=execution_time,
                    accuracy=accuracy,
                    confidence=confidence,
                    memory_usage=memory_usage,
                    throughput=throughput,
                    component=component
                )
                
                # Log performance
                enterprise_logging_system.structured_logger.performance(
                    f"Algorithm {algorithm_name} executed successfully",
                    component=component,
                    algorithm_name=algorithm_name,
                    duration_ms=execution_time * 1000,
                    memory_mb=memory_usage,
                    accuracy=accuracy,
                    confidence=confidence
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log error
                enterprise_logging_system.structured_logger.error(
                    f"Algorithm {algorithm_name} failed",
                    error=e,
                    component=component,
                    algorithm_name=algorithm_name,
                    duration_ms=execution_time * 1000
                )
                
                # Record error
                enterprise_logging_system.error_analytics.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    component=component,
                    operation=f"execute_{algorithm_name}",
                    stack_trace=traceback.format_exc()
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            memory_start = psutil.virtual_memory().used / (1024**2)
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate performance metrics
                execution_time = time.time() - start_time
                memory_end = psutil.virtual_memory().used / (1024**2)
                memory_usage = memory_end - memory_start
                
                # Extract metrics from result if available
                accuracy = result.get('accuracy', 0.0) if isinstance(result, dict) else 0.0
                confidence = result.get('confidence', 0.0) if isinstance(result, dict) else 0.0
                throughput = 1.0 / execution_time if execution_time > 0 else 0.0
                
                # Record performance
                enterprise_logging_system.performance_analytics.record_algorithm_performance(
                    algorithm_name=algorithm_name,
                    execution_time=execution_time,
                    accuracy=accuracy,
                    confidence=confidence,
                    memory_usage=memory_usage,
                    throughput=throughput,
                    component=component
                )
                
                # Log performance
                enterprise_logging_system.structured_logger.performance(
                    f"Algorithm {algorithm_name} executed successfully",
                    component=component,
                    algorithm_name=algorithm_name,
                    duration_ms=execution_time * 1000,
                    memory_mb=memory_usage,
                    accuracy=accuracy,
                    confidence=confidence
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log error
                enterprise_logging_system.structured_logger.error(
                    f"Algorithm {algorithm_name} failed",
                    error=e,
                    component=component,
                    algorithm_name=algorithm_name,
                    duration_ms=execution_time * 1000
                )
                
                # Record error
                enterprise_logging_system.error_analytics.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    component=component,
                    operation=f"execute_{algorithm_name}",
                    stack_trace=traceback.format_exc()
                )
                
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator