#!/usr/bin/env python3
"""
Advanced Monitoring & Health System v2.0 - Generation 2: MAKE IT ROBUST
Comprehensive monitoring, health checking, and observability system with
real-time metrics, predictive analytics, and automated alerting for the autonomous SDLC.
"""

import asyncio
import time
import psutil
import threading
import json
import statistics
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
from collections import deque, defaultdict
import queue
import socket
import subprocess
import platform
from pathlib import Path
import logging
import aiohttp
from concurrent.futures import ThreadPoolExecutor


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    CRITICAL = auto()
    UNKNOWN = auto()


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()
    RATE = auto()


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class MonitoringScope(Enum):
    """Monitoring scopes"""
    SYSTEM = auto()
    APPLICATION = auto()
    BUSINESS = auto()
    SECURITY = auto()
    PERFORMANCE = auto()


@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: datetime
    name: str
    value: Union[int, float]
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    description: str
    check_function: Callable
    interval_seconds: int
    timeout_seconds: int
    critical: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class HealthResult:
    """Result of a health check"""
    check_name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    timestamp: datetime
    level: AlertLevel
    title: str
    description: str
    source: str
    metric_name: Optional[str] = None
    current_value: Optional[Union[int, float]] = None
    threshold: Optional[Union[int, float]] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class ThresholdRule:
    """Metric threshold rule for alerting"""
    metric_name: str
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: Union[int, float]
    alert_level: AlertLevel
    description: str
    duration_minutes: int = 1  # How long condition must persist
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Advanced metrics collection and aggregation"""
    
    def __init__(self, buffer_size: int = 10000):
        self.metrics_buffer: deque = deque(maxlen=buffer_size)
        self.aggregated_metrics: Dict[str, Dict] = defaultdict(dict)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.Lock()
        
        # System metrics collection
        self.system_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metrics")
        self.collection_active = True
    
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType = MetricType.GAUGE, 
                     tags: Optional[Dict[str, str]] = None):
        """Record a single metric point"""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {}
        )
        
        with self._lock:
            self.metrics_buffer.append(point)
            self.metric_history[name].append(point)
            self._update_aggregations(point)
    
    def _update_aggregations(self, point: MetricPoint):
        """Update metric aggregations"""
        name = point.name
        value = point.value
        
        if name not in self.aggregated_metrics:
            self.aggregated_metrics[name] = {
                'count': 0,
                'sum': 0,
                'min': float('inf'),
                'max': float('-inf'),
                'last_value': 0,
                'last_timestamp': None,
                'values': deque(maxlen=100)
            }
        
        agg = self.aggregated_metrics[name]
        agg['count'] += 1
        agg['sum'] += value
        agg['min'] = min(agg['min'], value)
        agg['max'] = max(agg['max'], value)
        agg['last_value'] = value
        agg['last_timestamp'] = point.timestamp
        agg['values'].append(value)
    
    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get aggregated summary for a metric"""
        with self._lock:
            if name not in self.aggregated_metrics:
                return None
            
            agg = self.aggregated_metrics[name]
            values = list(agg['values'])
            
            if not values:
                return None
            
            return {
                'name': name,
                'count': agg['count'],
                'last_value': agg['last_value'],
                'min': agg['min'],
                'max': agg['max'],
                'avg': agg['sum'] / agg['count'],
                'median': statistics.median(values) if len(values) >= 1 else agg['last_value'],
                'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else agg['max'],
                'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else agg['max'],
                'last_timestamp': agg['last_timestamp'].isoformat() if agg['last_timestamp'] else None
            }
    
    async def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system.cpu.usage_percent", cpu_percent, MetricType.GAUGE)
            
            cpu_count = psutil.cpu_count()
            self.record_metric("system.cpu.count", cpu_count, MetricType.GAUGE)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric("system.memory.usage_percent", memory.percent, MetricType.GAUGE)
            self.record_metric("system.memory.used_bytes", memory.used, MetricType.GAUGE)
            self.record_metric("system.memory.available_bytes", memory.available, MetricType.GAUGE)
            self.record_metric("system.memory.total_bytes", memory.total, MetricType.GAUGE)
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            self.record_metric("system.disk.usage_percent", 
                             (disk_usage.used / disk_usage.total) * 100, MetricType.GAUGE)
            self.record_metric("system.disk.used_bytes", disk_usage.used, MetricType.GAUGE)
            self.record_metric("system.disk.free_bytes", disk_usage.free, MetricType.GAUGE)
            
            # Network metrics
            network = psutil.net_io_counters()
            self.record_metric("system.network.bytes_sent", network.bytes_sent, MetricType.COUNTER)
            self.record_metric("system.network.bytes_recv", network.bytes_recv, MetricType.COUNTER)
            self.record_metric("system.network.packets_sent", network.packets_sent, MetricType.COUNTER)
            self.record_metric("system.network.packets_recv", network.packets_recv, MetricType.COUNTER)
            
            # Process metrics
            process = psutil.Process()
            self.record_metric("process.cpu.usage_percent", process.cpu_percent(), MetricType.GAUGE)
            
            memory_info = process.memory_info()
            self.record_metric("process.memory.rss_bytes", memory_info.rss, MetricType.GAUGE)
            self.record_metric("process.memory.vms_bytes", memory_info.vms, MetricType.GAUGE)
            
            self.record_metric("process.threads.count", process.num_threads(), MetricType.GAUGE)
            self.record_metric("process.file_descriptors.count", process.num_fds(), MetricType.GAUGE)
            
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
    
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all current metrics"""
        with self._lock:
            return [self.get_metric_summary(name) for name in self.aggregated_metrics.keys()]


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, HealthResult] = {}
        self.check_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="health")
        self.running = False
        self.check_tasks: Dict[str, asyncio.Task] = {}
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check"""
        self.health_checks[health_check.name] = health_check
        logging.info(f"Registered health check: {health_check.name}")
    
    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        self.running = True
        
        for check_name, health_check in self.health_checks.items():
            task = asyncio.create_task(self._run_health_check_loop(health_check))
            self.check_tasks[check_name] = task
        
        logging.info(f"Started health monitoring for {len(self.health_checks)} checks")
    
    async def _run_health_check_loop(self, health_check: HealthCheck):
        """Run a health check in a loop"""
        while self.running:
            try:
                result = await self._execute_health_check(health_check)
                self.health_results[health_check.name] = result
                
                logging.debug(f"Health check {health_check.name}: {result.status.name}")
                
            except Exception as e:
                logging.error(f"Health check {health_check.name} failed: {e}")
                
                self.health_results[health_check.name] = HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check execution failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                    error=str(e)
                )
            
            await asyncio.sleep(health_check.interval_seconds)
    
    async def _execute_health_check(self, health_check: HealthCheck) -> HealthResult:
        """Execute a single health check"""
        start_time = time.time()
        
        try:
            # Execute health check with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(health_check.check_function),
                timeout=health_check.timeout_seconds
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, tuple):
                status, message, metadata = result[0], result[1], result[2] if len(result) > 2 else {}
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "Health check passed" if result else "Health check failed"
                metadata = {}
            
            return HealthResult(
                check_name=health_check.name,
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                metadata=metadata
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {health_check.timeout_seconds}s",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error="Timeout"
            )
    
    def get_overall_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Get overall system health status"""
        if not self.health_results:
            return HealthStatus.UNKNOWN, {"message": "No health checks available"}
        
        critical_failed = 0
        degraded_checks = 0
        total_checks = len(self.health_results)
        
        check_summary = {}
        
        for name, result in self.health_results.items():
            check_summary[name] = {
                'status': result.status.name,
                'message': result.message,
                'duration_ms': result.duration_ms,
                'timestamp': result.timestamp.isoformat()
            }
            
            health_check = self.health_checks.get(name)
            if result.status == HealthStatus.CRITICAL:
                critical_failed += 1
            elif result.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                degraded_checks += 1
        
        # Determine overall status
        if critical_failed > 0:
            overall_status = HealthStatus.CRITICAL
            status_message = f"{critical_failed} critical health checks failed"
        elif degraded_checks > 0:
            overall_status = HealthStatus.DEGRADED
            status_message = f"{degraded_checks} health checks degraded"
        else:
            overall_status = HealthStatus.HEALTHY
            status_message = "All health checks passing"
        
        return overall_status, {
            'status': overall_status.name,
            'message': status_message,
            'total_checks': total_checks,
            'critical_failed': critical_failed,
            'degraded_checks': degraded_checks,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': check_summary
        }
    
    def stop_health_monitoring(self):
        """Stop health monitoring"""
        self.running = False
        
        for task in self.check_tasks.values():
            task.cancel()
        
        self.check_tasks.clear()
        logging.info("Stopped health monitoring")


class AlertManager:
    """Intelligent alerting system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.threshold_rules: List[ThresholdRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: List[Callable] = []
        self._lock = threading.Lock()
        
        # Alert suppression to prevent spam
        self.alert_suppression: Dict[str, datetime] = {}
        self.suppression_duration = timedelta(minutes=5)
    
    def add_threshold_rule(self, rule: ThresholdRule):
        """Add a threshold-based alerting rule"""
        self.threshold_rules.append(rule)
        logging.info(f"Added threshold rule for {rule.metric_name}")
    
    def add_notification_channel(self, channel: Callable[[Alert], None]):
        """Add notification channel for alerts"""
        self.notification_channels.append(channel)
    
    async def evaluate_alerts(self):
        """Evaluate all threshold rules and generate alerts"""
        current_time = datetime.utcnow()
        
        for rule in self.threshold_rules:
            try:
                metric_summary = self.metrics_collector.get_metric_summary(rule.metric_name)
                if not metric_summary:
                    continue
                
                current_value = metric_summary['last_value']
                threshold_violated = self._evaluate_threshold(current_value, rule.operator, rule.threshold)
                
                alert_key = f"{rule.metric_name}_{rule.operator}_{rule.threshold}"
                
                if threshold_violated:
                    if alert_key not in self.active_alerts:
                        # Check if alert is suppressed
                        if alert_key in self.alert_suppression:
                            if current_time - self.alert_suppression[alert_key] < self.suppression_duration:
                                continue
                            else:
                                del self.alert_suppression[alert_key]
                        
                        # Create new alert
                        alert = Alert(
                            alert_id=f"alert_{int(time.time() * 1000)}",
                            timestamp=current_time,
                            level=rule.alert_level,
                            title=f"Threshold violation: {rule.metric_name}",
                            description=rule.description,
                            source="threshold_monitor",
                            metric_name=rule.metric_name,
                            current_value=current_value,
                            threshold=rule.threshold,
                            tags=rule.tags,
                            metadata={
                                'operator': rule.operator,
                                'metric_summary': metric_summary
                            }
                        )
                        
                        with self._lock:
                            self.active_alerts[alert_key] = alert
                            self.alert_history.append(alert)
                        
                        await self._send_alert_notifications(alert)
                        logging.warning(f"Alert triggered: {alert.title}")
                
                else:
                    # Resolve alert if it was active
                    if alert_key in self.active_alerts:
                        with self._lock:
                            alert = self.active_alerts[alert_key]
                            alert.resolved = True
                            del self.active_alerts[alert_key]
                        
                        logging.info(f"Alert resolved: {alert.title}")
                        
            except Exception as e:
                logging.error(f"Error evaluating alert rule for {rule.metric_name}: {e}")
    
    def _evaluate_threshold(self, value: Union[int, float], operator: str, threshold: Union[int, float]) -> bool:
        """Evaluate threshold condition"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            return False
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications to all channels"""
        for channel in self.notification_channels:
            try:
                if asyncio.iscoroutinefunction(channel):
                    await channel(alert)
                else:
                    await asyncio.to_thread(channel, alert)
            except Exception as e:
                logging.error(f"Error sending alert notification: {e}")
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an active alert"""
        with self._lock:
            for alert in self.active_alerts.values():
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.metadata['acknowledged_by'] = user
                    alert.metadata['acknowledged_at'] = datetime.utcnow().isoformat()
                    return True
        return False
    
    def suppress_alert(self, metric_name: str, duration_minutes: int = 5):
        """Suppress alerts for a metric temporarily"""
        alert_keys = [key for key in self.active_alerts.keys() if metric_name in key]
        suppression_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        for key in alert_keys:
            self.alert_suppression[key] = suppression_until
        
        logging.info(f"Suppressed alerts for {metric_name} for {duration_minutes} minutes")
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts"""
        with self._lock:
            alert_counts = defaultdict(int)
            for alert in self.active_alerts.values():
                alert_counts[alert.level.name] += 1
            
            return {
                'active_alerts': len(self.active_alerts),
                'alert_counts': dict(alert_counts),
                'total_alerts_today': len([a for a in self.alert_history 
                                         if a.timestamp.date() == datetime.utcnow().date()]),
                'suppressed_alerts': len(self.alert_suppression)
            }


# Built-in health checks
def database_health_check() -> Tuple[HealthStatus, str]:
    """Check database connectivity"""
    try:
        # Simulate database connection check
        # In real implementation, test actual database connection
        return HealthStatus.HEALTHY, "Database connection successful"
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Database connection failed: {str(e)}"

def disk_space_health_check() -> Tuple[HealthStatus, str]:
    """Check available disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        if usage_percent > 95:
            return HealthStatus.CRITICAL, f"Disk usage critical: {usage_percent:.1f}%"
        elif usage_percent > 90:
            return HealthStatus.UNHEALTHY, f"Disk usage high: {usage_percent:.1f}%"
        elif usage_percent > 80:
            return HealthStatus.DEGRADED, f"Disk usage elevated: {usage_percent:.1f}%"
        else:
            return HealthStatus.HEALTHY, f"Disk usage normal: {usage_percent:.1f}%"
    except Exception as e:
        return HealthStatus.UNKNOWN, f"Error checking disk space: {str(e)}"

def memory_health_check() -> Tuple[HealthStatus, str]:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        
        if memory.percent > 95:
            return HealthStatus.CRITICAL, f"Memory usage critical: {memory.percent}%"
        elif memory.percent > 85:
            return HealthStatus.UNHEALTHY, f"Memory usage high: {memory.percent}%"
        elif memory.percent > 75:
            return HealthStatus.DEGRADED, f"Memory usage elevated: {memory.percent}%"
        else:
            return HealthStatus.HEALTHY, f"Memory usage normal: {memory.percent}%"
    except Exception as e:
        return HealthStatus.UNKNOWN, f"Error checking memory: {str(e)}"

async def network_connectivity_health_check() -> Tuple[HealthStatus, str]:
    """Check network connectivity"""
    try:
        # Test connectivity to a reliable service
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://httpbin.org/get') as response:
                if response.status == 200:
                    return HealthStatus.HEALTHY, "Network connectivity normal"
                else:
                    return HealthStatus.DEGRADED, f"Network connectivity issues: HTTP {response.status}"
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Network connectivity failed: {str(e)}"


class AdvancedMonitoringOrchestrator:
    """Main monitoring system orchestrator"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager(self.metrics_collector)
        
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Register default health checks
        self._register_default_health_checks()
        self._setup_default_alerts()
    
    def _register_default_health_checks(self):
        """Register default system health checks"""
        checks = [
            HealthCheck(
                name="disk_space",
                description="Monitor available disk space",
                check_function=disk_space_health_check,
                interval_seconds=60,
                timeout_seconds=10,
                critical=True
            ),
            HealthCheck(
                name="memory_usage",
                description="Monitor system memory usage",
                check_function=memory_health_check,
                interval_seconds=30,
                timeout_seconds=5,
                critical=True
            ),
            HealthCheck(
                name="network_connectivity",
                description="Test network connectivity",
                check_function=network_connectivity_health_check,
                interval_seconds=120,
                timeout_seconds=10,
                critical=False
            )
        ]
        
        for check in checks:
            self.health_checker.register_health_check(check)
    
    def _setup_default_alerts(self):
        """Setup default alerting rules"""
        rules = [
            ThresholdRule(
                metric_name="system.cpu.usage_percent",
                operator=">",
                threshold=90,
                alert_level=AlertLevel.WARNING,
                description="High CPU usage detected"
            ),
            ThresholdRule(
                metric_name="system.memory.usage_percent", 
                operator=">",
                threshold=95,
                alert_level=AlertLevel.CRITICAL,
                description="Critical memory usage"
            ),
            ThresholdRule(
                metric_name="system.disk.usage_percent",
                operator=">",
                threshold=90,
                alert_level=AlertLevel.WARNING,
                description="Low disk space available"
            ),
            ThresholdRule(
                metric_name="process.memory.rss_bytes",
                operator=">",
                threshold=1024 * 1024 * 1024,  # 1GB
                alert_level=AlertLevel.WARNING,
                description="High process memory usage"
            )
        ]
        
        for rule in rules:
            self.alert_manager.add_threshold_rule(rule)
    
    async def start_monitoring(self):
        """Start comprehensive monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start health checking
        await self.health_checker.start_health_monitoring()
        
        # Start metrics collection
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self.monitoring_tasks.append(metrics_task)
        
        # Start alert evaluation
        alert_task = asyncio.create_task(self._alert_evaluation_loop())
        self.monitoring_tasks.append(alert_task)
        
        logging.info("Advanced monitoring system started")
    
    async def _metrics_collection_loop(self):
        """Continuous metrics collection"""
        while self.monitoring_active:
            try:
                await self.metrics_collector.collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)
    
    async def _alert_evaluation_loop(self):
        """Continuous alert evaluation"""
        while self.monitoring_active:
            try:
                await self.alert_manager.evaluate_alerts()
                await asyncio.sleep(60)  # Evaluate every minute
            except Exception as e:
                logging.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(10)
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        self.monitoring_active = False
        self.health_checker.stop_health_monitoring()
        
        for task in self.monitoring_tasks:
            task.cancel()
        
        self.monitoring_tasks.clear()
        logging.info("Advanced monitoring system stopped")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        overall_health, health_details = self.health_checker.get_overall_health()
        alert_summary = self.alert_manager.get_alert_summary()
        
        # Get key metrics
        key_metrics = {}
        metric_names = [
            "system.cpu.usage_percent",
            "system.memory.usage_percent", 
            "system.disk.usage_percent",
            "process.memory.rss_bytes"
        ]
        
        for name in metric_names:
            summary = self.metrics_collector.get_metric_summary(name)
            if summary:
                key_metrics[name] = {
                    'current': summary['last_value'],
                    'avg': summary['avg'],
                    'max': summary['max']
                }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_health': overall_health.name,
            'health_details': health_details,
            'alert_summary': alert_summary,
            'key_metrics': key_metrics,
            'monitoring_active': self.monitoring_active
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_monitoring_system():
        """Test the advanced monitoring system"""
        print("📊 Testing Advanced Monitoring & Health System v2.0")
        
        # Create monitoring orchestrator
        monitor = AdvancedMonitoringOrchestrator()
        
        # Add a simple notification channel
        def console_notification(alert: Alert):
            print(f"🚨 ALERT: {alert.title} - {alert.description}")
            print(f"   Level: {alert.level.name}, Value: {alert.current_value}, Threshold: {alert.threshold}")
        
        monitor.alert_manager.add_notification_channel(console_notification)
        
        # Start monitoring
        await monitor.start_monitoring()
        
        # Let it run for a bit to collect metrics
        await asyncio.sleep(10)
        
        # Record some test metrics
        monitor.metrics_collector.record_metric("test.response_time", 150.5, MetricType.HISTOGRAM)
        monitor.metrics_collector.record_metric("test.request_count", 42, MetricType.COUNTER)
        monitor.metrics_collector.record_metric("test.error_rate", 0.05, MetricType.GAUGE)
        
        # Get comprehensive status
        status = monitor.get_comprehensive_status()
        print(f"\nSystem Status:")
        print(f"Overall Health: {status['overall_health']}")
        print(f"Active Alerts: {status['alert_summary']['active_alerts']}")
        print(f"Health Checks: {status['health_details']['total_checks']}")
        
        print(f"\nKey Metrics:")
        for name, metrics in status['key_metrics'].items():
            print(f"  {name}: current={metrics['current']:.2f}, avg={metrics['avg']:.2f}")
        
        # Stop monitoring
        await asyncio.sleep(5)
        monitor.stop_monitoring()
        print("\nMonitoring test completed")
    
    # Run test
    asyncio.run(test_monitoring_system())