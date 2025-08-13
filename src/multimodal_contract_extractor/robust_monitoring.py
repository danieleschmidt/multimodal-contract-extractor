"""Robust monitoring and health checking system for Generation 2."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import psutil
from prometheus_client import Counter, Histogram, push_to_gateway

from .config import get_config

logger = logging.getLogger(__name__)

# Prometheus metrics - use try/except to avoid duplicate registration
try:
    EXTRACTION_SUCCESS_TOTAL = Counter('extraction_success_total', 'Total successful extractions')
    EXTRACTION_ERROR_TOTAL = Counter('extraction_error_total', 'Total extraction errors', ['error_type'])
    HEALTH_CHECK_DURATION = Histogram('health_check_duration_seconds', 'Health check duration')
except ValueError:
    # Metrics already registered, get them from registry
    from prometheus_client import REGISTRY
    for collector in REGISTRY._collector_to_names:
        if 'extraction_success_total' in REGISTRY._collector_to_names[collector]:
            EXTRACTION_SUCCESS_TOTAL = collector
        elif 'extraction_error_total' in REGISTRY._collector_to_names[collector]:
            EXTRACTION_ERROR_TOTAL = collector
        elif 'health_check_duration_seconds' in REGISTRY._collector_to_names[collector]:
            HEALTH_CHECK_DURATION = collector

@dataclass
class SystemHealth:
    """System health status."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_processes: int
    timestamp: datetime
    healthy: bool
    issues: list[str]

@dataclass
class ComponentHealth:
    """Individual component health."""
    name: str
    healthy: bool
    latency_ms: float
    error_rate: float
    last_check: datetime
    issues: list[str]

class RobustHealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        self.config = get_config()
        self.components: dict[str, ComponentHealth] = {}
        self.system_thresholds = {
            'cpu_max': 80.0,
            'memory_max': 85.0,
            'disk_max': 90.0,
            'error_rate_max': 0.05,
            'latency_max_ms': 5000
        }

    async def check_system_health(self) -> SystemHealth:
        """Check overall system health."""
        with HEALTH_CHECK_DURATION.time():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                active_processes = len(psutil.pids())

                issues = []
                if cpu_percent > self.system_thresholds['cpu_max']:
                    issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                if memory_percent > self.system_thresholds['memory_max']:
                    issues.append(f"High memory usage: {memory_percent:.1f}%")
                if disk_percent > self.system_thresholds['disk_max']:
                    issues.append(f"Low disk space: {disk_percent:.1f}% used")

                healthy = len(issues) == 0

                return SystemHealth(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_percent=disk_percent,
                    active_processes=active_processes,
                    timestamp=datetime.now(timezone.utc),
                    healthy=healthy,
                    issues=issues
                )
            except Exception as e:
                logger.error("Failed to check system health: %s", e)
                return SystemHealth(
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    disk_percent=0.0,
                    active_processes=0,
                    timestamp=datetime.now(timezone.utc),
                    healthy=False,
                    issues=[f"Health check failed: {e}"]
                )

    async def check_component_health(self, component_name: str) -> ComponentHealth:
        """Check individual component health."""
        start_time = time.perf_counter()

        try:
            # Component-specific health checks
            if component_name == "ocr_engine":
                await self._check_ocr_engine()
            elif component_name == "document_processor":
                await self._check_document_processor()
            elif component_name == "database":
                await self._check_database()
            else:
                raise ValueError(f"Unknown component: {component_name}")

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Simulate error rate calculation
            error_rate = 0.0  # Would be calculated from metrics

            issues = []
            if latency_ms > self.system_thresholds['latency_max_ms']:
                issues.append(f"High latency: {latency_ms:.1f}ms")
            if error_rate > self.system_thresholds['error_rate_max']:
                issues.append(f"High error rate: {error_rate:.1%}")

            healthy = len(issues) == 0

            return ComponentHealth(
                name=component_name,
                healthy=healthy,
                latency_ms=latency_ms,
                error_rate=error_rate,
                last_check=datetime.now(timezone.utc),
                issues=issues
            )

        except Exception as e:
            logger.error("Component health check failed for %s: %s", component_name, e)
            return ComponentHealth(
                name=component_name,
                healthy=False,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                error_rate=1.0,
                last_check=datetime.now(timezone.utc),
                issues=[f"Health check failed: {e}"]
            )

    async def _check_ocr_engine(self) -> None:
        """Check OCR engine health."""
        # Simulate OCR engine check
        await asyncio.sleep(0.1)

    async def _check_document_processor(self) -> None:
        """Check document processor health."""
        # Simulate document processor check
        await asyncio.sleep(0.05)

    async def _check_database(self) -> None:
        """Check database connectivity."""
        # Simulate database check
        await asyncio.sleep(0.02)

    async def comprehensive_health_check(self) -> dict[str, Any]:
        """Perform comprehensive system and component health checks."""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': await self.check_system_health(),
            'components': {}
        }

        # Check all registered components
        component_names = ['ocr_engine', 'document_processor', 'database']

        for component in component_names:
            results['components'][component] = await self.check_component_health(component)

        # Overall health status
        system_healthy = results['system'].healthy
        components_healthy = all(
            comp.healthy for comp in results['components'].values()
        )

        results['overall_healthy'] = system_healthy and components_healthy

        return results

class CircuitBreaker:
    """Circuit breaker pattern for robust error handling."""

    def __init__(self, failure_threshold: int = 5, timeout_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open

    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self) -> None:
        """Record successful operation."""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

class RobustOperationWrapper:
    """Wrapper for robust operation execution with monitoring."""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.health_monitor = RobustHealthMonitor()

    def get_circuit_breaker(self, operation_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation."""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreaker()
        return self.circuit_breakers[operation_name]

    async def execute_robust(self, operation_name: str, operation, *args, **kwargs):
        """Execute operation with robust error handling and monitoring."""
        circuit_breaker = self.get_circuit_breaker(operation_name)

        if not circuit_breaker.can_execute():
            raise RuntimeError(f"Circuit breaker open for operation: {operation_name}")

        start_time = time.perf_counter()

        try:
            result = await operation(*args, **kwargs)
            circuit_breaker.record_success()

            # Record success metrics
            EXTRACTION_SUCCESS_TOTAL.inc()

            execution_time = time.perf_counter() - start_time
            logger.info("Operation %s completed successfully in %.2fs",
                       operation_name, execution_time)

            return result

        except Exception as e:
            circuit_breaker.record_failure()

            # Record error metrics
            error_type = type(e).__name__
            EXTRACTION_ERROR_TOTAL.labels(error_type=error_type).inc()

            execution_time = time.perf_counter() - start_time
            logger.error("Operation %s failed after %.2fs: %s",
                        operation_name, execution_time, e)

            raise

# Global instance
robust_monitor = RobustHealthMonitor()
operation_wrapper = RobustOperationWrapper()

async def get_health_status() -> dict[str, Any]:
    """Get comprehensive health status."""
    return await robust_monitor.comprehensive_health_check()

def push_metrics_to_gateway() -> None:
    """Push metrics to Prometheus gateway if configured."""
    config = get_config()

    if hasattr(config, 'prometheus') and config.prometheus.get('gateway_url'):
        try:
            push_to_gateway(
                gateway=config.prometheus['gateway_url'],
                job='contract_extractor',
                registry=None
            )
            logger.info("Metrics pushed to Prometheus gateway")
        except Exception as e:
            logger.warning("Failed to push metrics to gateway: %s", e)
