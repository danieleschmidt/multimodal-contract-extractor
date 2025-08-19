"""
Advanced health check system for comprehensive system monitoring.
Generation 2 Enhancement: Comprehensive health monitoring and alerting.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Individual health metric with thresholds and current value."""
    name: str
    current_value: Union[float, int, bool, str]
    threshold_warning: Optional[Union[float, int]] = None
    threshold_critical: Optional[Union[float, int]] = None
    unit: str = ""
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def status(self) -> HealthStatus:
        """Determine status based on current value and thresholds."""
        if isinstance(self.current_value, bool):
            return HealthStatus.HEALTHY if self.current_value else HealthStatus.UNHEALTHY

        if not isinstance(self.current_value, (int, float)):
            return HealthStatus.HEALTHY

        if self.threshold_critical is not None and self.current_value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.threshold_warning is not None and self.current_value >= self.threshold_warning:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


@dataclass
class HealthCheck:
    """Complete health check result with multiple metrics."""
    component: str
    status: HealthStatus
    metrics: List[HealthMetric] = field(default_factory=list)
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component,
            "status": self.status.value,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.current_value,
                    "unit": m.unit,
                    "status": m.status.value,
                    "description": m.description,
                    "threshold_warning": m.threshold_warning,
                    "threshold_critical": m.threshold_critical,
                    "timestamp": m.timestamp
                }
                for m in self.metrics
            ],
            "message": self.message,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms
        }


class HealthChecker:
    """Base class for health check implementations."""

    def __init__(self, component_name: str):
        self.component_name = component_name

    async def check(self) -> HealthCheck:
        """Perform health check and return result."""
        start_time = time.time()
        try:
            result = await self._perform_check()
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Health check failed for {self.component_name}")
            return HealthCheck(
                component=self.component_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms
            )

    async def _perform_check(self) -> HealthCheck:
        """Override this method in subclasses."""
        raise NotImplementedError


class SystemResourcesChecker(HealthChecker):
    """Health checker for system resources (CPU, memory, disk)."""

    def __init__(self):
        super().__init__("system_resources")

    async def _perform_check(self) -> HealthCheck:
        metrics = []

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(HealthMetric(
            name="cpu_usage",
            current_value=cpu_percent,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            description="Current CPU usage percentage"
        ))

        # Memory usage
        memory = psutil.virtual_memory()
        metrics.append(HealthMetric(
            name="memory_usage",
            current_value=memory.percent,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            description="Current memory usage percentage"
        ))

        # Available memory
        metrics.append(HealthMetric(
            name="memory_available",
            current_value=memory.available / (1024**3),  # GB
            threshold_warning=1.0,
            threshold_critical=0.5,
            unit="GB",
            description="Available memory in GB"
        ))

        # Disk usage for current directory
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        metrics.append(HealthMetric(
            name="disk_usage",
            current_value=disk_percent,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            description="Root disk usage percentage"
        ))

        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
            cpu_count = psutil.cpu_count()
            load_percent = (load_avg / cpu_count) * 100
            metrics.append(HealthMetric(
                name="load_average",
                current_value=load_percent,
                threshold_warning=70.0,
                threshold_critical=90.0,
                unit="%",
                description="System load average as percentage of CPU cores"
            ))
        except (AttributeError, OSError):
            # getloadavg not available on Windows
            pass

        # Determine overall status
        statuses = [metric.status for metric in metrics]
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthCheck(
            component=self.component_name,
            status=overall_status,
            metrics=metrics,
            message="System resources check completed"
        )


class FilesystemChecker(HealthChecker):
    """Health checker for filesystem access and permissions."""

    def __init__(self, paths: Optional[List[str]] = None):
        super().__init__("filesystem")
        self.paths = paths or ["/tmp", ".", "/var/log"]

    async def _perform_check(self) -> HealthCheck:
        metrics = []
        issues = []

        for path_str in self.paths:
            path = Path(path_str)

            # Check if path exists
            exists = path.exists()
            metrics.append(HealthMetric(
                name=f"path_exists_{path_str}",
                current_value=exists,
                description=f"Path {path_str} exists"
            ))

            if not exists:
                issues.append(f"Path {path_str} does not exist")
                continue

            # Check permissions
            try:
                readable = path.stat().st_mode & 0o444
                writable = path.stat().st_mode & 0o222 if path.is_dir() else True

                metrics.append(HealthMetric(
                    name=f"path_readable_{path_str}",
                    current_value=bool(readable),
                    description=f"Path {path_str} is readable"
                ))

                if path.is_dir():
                    metrics.append(HealthMetric(
                        name=f"path_writable_{path_str}",
                        current_value=bool(writable),
                        description=f"Path {path_str} is writable"
                    ))

                    # Test write access
                    test_file = path / f".health_check_{int(time.time())}"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                        write_test_passed = True
                    except Exception:
                        write_test_passed = False
                        issues.append(f"Cannot write to {path_str}")

                    metrics.append(HealthMetric(
                        name=f"write_test_{path_str}",
                        current_value=write_test_passed,
                        description=f"Write test for {path_str}"
                    ))

            except Exception as e:
                issues.append(f"Cannot check permissions for {path_str}: {str(e)}")

        # Determine status
        failed_metrics = [m for m in metrics if m.status != HealthStatus.HEALTHY]
        if failed_metrics:
            status = HealthStatus.DEGRADED if len(failed_metrics) < len(metrics) / 2 else HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.HEALTHY

        return HealthCheck(
            component=self.component_name,
            status=status,
            metrics=metrics,
            message="; ".join(issues) if issues else "Filesystem access check passed"
        )


class DependencyChecker(HealthChecker):
    """Health checker for external dependencies and services."""

    def __init__(self):
        super().__init__("dependencies")

    async def _perform_check(self) -> HealthCheck:
        metrics = []

        # Check required Python packages
        required_packages = [
            "PIL", "pdf2image", "pytesseract", "streamlit",
            "prometheus_client", "pydantic", "PyYAML"
        ]

        for package in required_packages:
            try:
                __import__(package)
                available = True
            except ImportError:
                available = False

            metrics.append(HealthMetric(
                name=f"package_{package}",
                current_value=available,
                description=f"Python package {package} is available"
            ))

        # Check external executables
        external_deps = ["tesseract"]  # OCR executable

        for dep in external_deps:
            try:
                import shutil
                available = shutil.which(dep) is not None
            except Exception:
                available = False

            metrics.append(HealthMetric(
                name=f"executable_{dep}",
                current_value=available,
                description=f"External executable {dep} is available"
            ))

        # Determine status
        failed_deps = [m for m in metrics if not m.current_value]
        if not failed_deps:
            status = HealthStatus.HEALTHY
        elif len(failed_deps) <= 2:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.UNHEALTHY

        return HealthCheck(
            component=self.component_name,
            status=status,
            metrics=metrics,
            message=f"Dependencies check: {len(failed_deps)} missing" if failed_deps else "All dependencies available"
        )


class ApplicationChecker(HealthChecker):
    """Health checker for application-specific components."""

    def __init__(self):
        super().__init__("application")

    async def _perform_check(self) -> HealthCheck:
        metrics = []

        # Check configuration loading
        try:
            from multimodal_contract_extractor.config import get_config
            config = get_config()
            config_loaded = True
        except Exception as e:
            config_loaded = False
            logger.warning(f"Configuration loading failed: {e}")

        metrics.append(HealthMetric(
            name="config_loading",
            current_value=config_loaded,
            description="Configuration can be loaded successfully"
        ))

        # Check model/extraction pipeline initialization
        try:
            from pathlib import Path

            from multimodal_contract_extractor import validate_file_input
            # Test with a simple validation
            validate_file_input(Path(__file__))  # Use this file as test
            pipeline_ready = True
        except Exception as e:
            pipeline_ready = False
            logger.warning(f"Pipeline validation failed: {e}")

        metrics.append(HealthMetric(
            name="pipeline_ready",
            current_value=pipeline_ready,
            description="Extraction pipeline is ready"
        ))

        # Check error recovery system
        try:
            from multimodal_contract_extractor.robust_error_handling import (
                get_error_manager,
            )
            error_manager = get_error_manager()
            error_system_ready = len(error_manager.strategies) > 0
        except Exception:
            error_system_ready = False

        metrics.append(HealthMetric(
            name="error_system",
            current_value=error_system_ready,
            description="Error recovery system is operational"
        ))

        # Determine status
        failed_components = [m for m in metrics if not m.current_value]
        if not failed_components:
            status = HealthStatus.HEALTHY
        elif len(failed_components) == 1:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return HealthCheck(
            component=self.component_name,
            status=status,
            metrics=metrics,
            message=f"Application check: {len(failed_components)} issues" if failed_components else "Application healthy"
        )


class HealthMonitor:
    """Central health monitoring system."""

    def __init__(self):
        self.checkers: List[HealthChecker] = [
            SystemResourcesChecker(),
            FilesystemChecker(),
            DependencyChecker(),
            ApplicationChecker()
        ]
        self.last_results: Dict[str, HealthCheck] = {}
        self.check_history: List[Dict[str, Any]] = []
        self.max_history = 100

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks concurrently."""
        tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_results = {}
        for checker, result in zip(self.checkers, results):
            if isinstance(result, Exception):
                logger.error(f"Health checker {checker.component_name} failed: {result}")
                health_results[checker.component_name] = HealthCheck(
                    component=checker.component_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}"
                )
            else:
                health_results[checker.component_name] = result

        self.last_results = health_results

        # Add to history
        self.check_history.append({
            "timestamp": time.time(),
            "results": {k: v.to_dict() for k, v in health_results.items()}
        })

        # Trim history
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]

        return health_results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.last_results:
            return HealthStatus.UNHEALTHY

        statuses = [result.status for result in self.last_results.values()]

        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        overall_status = self.get_overall_status()

        summary = {
            "overall_status": overall_status.value,
            "timestamp": time.time(),
            "components": {}
        }

        for component_name, result in self.last_results.items():
            summary["components"][component_name] = {
                "status": result.status.value,
                "message": result.message,
                "metrics_count": len(result.metrics),
                "duration_ms": result.duration_ms
            }

        return summary

    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed health report with all metrics."""
        return {
            "overall_status": self.get_overall_status().value,
            "timestamp": time.time(),
            "components": {k: v.to_dict() for k, v in self.last_results.items()},
            "history_entries": len(self.check_history)
        }

    async def continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous health monitoring."""
        logger.info(f"Starting continuous health monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                await self.run_all_checks()
                status = self.get_overall_status()
                logger.info(f"Health check completed - Status: {status.value}")

                # Alert on status changes
                if status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                    logger.error(f"ALERT: System health is {status.value}")
                elif status == HealthStatus.DEGRADED:
                    logger.warning(f"WARNING: System health is {status.value}")

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

            await asyncio.sleep(interval_seconds)


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


async def health_check_endpoint() -> Dict[str, Any]:
    """Health check endpoint for web services."""
    monitor = get_health_monitor()
    await monitor.run_all_checks()
    return monitor.get_health_summary()


async def detailed_health_endpoint() -> Dict[str, Any]:
    """Detailed health check endpoint."""
    monitor = get_health_monitor()
    await monitor.run_all_checks()
    return monitor.get_detailed_report()
