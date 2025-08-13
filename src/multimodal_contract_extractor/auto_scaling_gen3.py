"""Auto-scaling and load balancing for Generation 3."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

import psutil

logger = logging.getLogger(__name__)

class ScalingTrigger(Enum):
    """Scaling trigger types."""
    CPU_THRESHOLD = "cpu_threshold"
    MEMORY_THRESHOLD = "memory_threshold"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"

@dataclass
class ScalingMetrics:
    """System metrics for scaling decisions."""
    cpu_percent: float
    memory_percent: float
    queue_length: int
    active_workers: int
    average_response_time: float
    error_rate: float
    throughput: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ScalingRule:
    """Auto-scaling rule definition."""
    trigger: ScalingTrigger
    threshold_up: float
    threshold_down: float
    scale_up_count: int
    scale_down_count: int
    cooldown_seconds: int
    enabled: bool = True

class WorkerPool(Protocol):
    """Protocol for worker pool implementations."""

    def scale_up(self, count: int) -> None:
        """Scale up worker pool by count."""
        ...

    def scale_down(self, count: int) -> None:
        """Scale down worker pool by count."""
        ...

    def get_worker_count(self) -> int:
        """Get current worker count."""
        ...

    def get_queue_length(self) -> int:
        """Get current queue length."""
        ...

class AutoScaler:
    """Intelligent auto-scaling system."""

    def __init__(self, worker_pool: WorkerPool):
        self.worker_pool = worker_pool
        self.scaling_rules: list[ScalingRule] = self._create_default_rules()
        self.metrics_history: list[ScalingMetrics] = []
        self.last_scaling_action: datetime | None = None
        self.scaling_enabled = True

        # Performance tracking
        self.total_scale_ups = 0
        self.total_scale_downs = 0
        self.scaling_decisions: list[dict] = []

    def _create_default_rules(self) -> list[ScalingRule]:
        """Create default scaling rules."""
        return [
            ScalingRule(
                trigger=ScalingTrigger.CPU_THRESHOLD,
                threshold_up=75.0,
                threshold_down=30.0,
                scale_up_count=2,
                scale_down_count=1,
                cooldown_seconds=60
            ),
            ScalingRule(
                trigger=ScalingTrigger.MEMORY_THRESHOLD,
                threshold_up=80.0,
                threshold_down=40.0,
                scale_up_count=3,
                scale_down_count=1,
                cooldown_seconds=90
            ),
            ScalingRule(
                trigger=ScalingTrigger.QUEUE_LENGTH,
                threshold_up=10.0,  # Queue items per worker
                threshold_down=2.0,
                scale_up_count=2,
                scale_down_count=1,
                cooldown_seconds=30
            ),
            ScalingRule(
                trigger=ScalingTrigger.RESPONSE_TIME,
                threshold_up=5.0,  # seconds
                threshold_down=1.0,
                scale_up_count=2,
                scale_down_count=1,
                cooldown_seconds=45
            )
        ]

    def collect_metrics(self) -> ScalingMetrics:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            queue_length = self.worker_pool.get_queue_length()
            active_workers = self.worker_pool.get_worker_count()

            # Calculate average response time from recent history
            recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
            avg_response_time = (
                sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
                if recent_metrics else 0.0
            )

            # Calculate error rate (simplified)
            error_rate = 0.0  # Would be calculated from actual error tracking

            # Calculate throughput
            throughput = active_workers * 1.0  # Simplified throughput calculation

            metrics = ScalingMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                queue_length=queue_length,
                active_workers=active_workers,
                average_response_time=avg_response_time,
                error_rate=error_rate,
                throughput=throughput
            )

            # Store in history (keep last 100 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error("Failed to collect metrics: %s", e)
            return ScalingMetrics(0, 0, 0, 1, 0, 0, 0)

    def should_scale(self, metrics: ScalingMetrics) -> tuple[str, int]:
        """Determine if scaling is needed and by how much."""
        if not self.scaling_enabled:
            return "none", 0

        # Check cooldown period
        if self.last_scaling_action:
            min_cooldown = min(rule.cooldown_seconds for rule in self.scaling_rules if rule.enabled)
            time_since_last = (datetime.now(timezone.utc) - self.last_scaling_action).total_seconds()
            if time_since_last < min_cooldown:
                return "cooldown", 0

        # Evaluate scaling rules
        for rule in self.scaling_rules:
            if not rule.enabled:
                continue

            metric_value = self._get_metric_value(metrics, rule.trigger)

            # Check scale-up condition
            if metric_value > rule.threshold_up:
                logger.info("Scale-up triggered by %s: %.2f > %.2f",
                           rule.trigger.value, metric_value, rule.threshold_up)
                return "up", rule.scale_up_count

            # Check scale-down condition (with minimum worker protection)
            if (metric_value < rule.threshold_down and
                metrics.active_workers > rule.scale_down_count):
                logger.info("Scale-down triggered by %s: %.2f < %.2f",
                           rule.trigger.value, metric_value, rule.threshold_down)
                return "down", rule.scale_down_count

        return "none", 0

    def _get_metric_value(self, metrics: ScalingMetrics, trigger: ScalingTrigger) -> float:
        """Get metric value for specific trigger type."""
        if trigger == ScalingTrigger.CPU_THRESHOLD:
            return metrics.cpu_percent
        elif trigger == ScalingTrigger.MEMORY_THRESHOLD:
            return metrics.memory_percent
        elif trigger == ScalingTrigger.QUEUE_LENGTH:
            return metrics.queue_length / max(1, metrics.active_workers)
        elif trigger == ScalingTrigger.RESPONSE_TIME:
            return metrics.average_response_time
        elif trigger == ScalingTrigger.ERROR_RATE:
            return metrics.error_rate * 100
        else:
            return 0.0

    def execute_scaling(self, direction: str, count: int) -> bool:
        """Execute scaling action."""
        try:
            if direction == "up":
                self.worker_pool.scale_up(count)
                self.total_scale_ups += 1
                logger.info("Scaled up by %d workers", count)
            elif direction == "down":
                self.worker_pool.scale_down(count)
                self.total_scale_downs += 1
                logger.info("Scaled down by %d workers", count)
            else:
                return False

            self.last_scaling_action = datetime.now(timezone.utc)

            # Record scaling decision
            self.scaling_decisions.append({
                'timestamp': self.last_scaling_action.isoformat(),
                'direction': direction,
                'count': count,
                'new_worker_count': self.worker_pool.get_worker_count()
            })

            # Keep only recent decisions
            if len(self.scaling_decisions) > 50:
                self.scaling_decisions.pop(0)

            return True

        except Exception as e:
            logger.error("Failed to execute scaling: %s", e)
            return False

    async def run_scaling_loop(self, check_interval: float = 30.0) -> None:
        """Run continuous auto-scaling monitoring loop."""
        logger.info("Starting auto-scaling loop (interval: %.1fs)", check_interval)

        while self.scaling_enabled:
            try:
                # Collect current metrics
                metrics = self.collect_metrics()

                # Determine scaling action
                direction, count = self.should_scale(metrics)

                # Execute scaling if needed
                if direction in ("up", "down"):
                    success = self.execute_scaling(direction, count)
                    if success:
                        logger.info("Auto-scaling action completed: %s by %d", direction, count)
                    else:
                        logger.warning("Auto-scaling action failed: %s by %d", direction, count)

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error("Error in scaling loop: %s", e)
                await asyncio.sleep(check_interval)

    def get_scaling_stats(self) -> dict[str, Any]:
        """Get auto-scaling statistics."""
        recent_metrics = self.metrics_history[-10:] if self.metrics_history else []

        return {
            'enabled': self.scaling_enabled,
            'total_scale_ups': self.total_scale_ups,
            'total_scale_downs': self.total_scale_downs,
            'current_workers': self.worker_pool.get_worker_count(),
            'current_queue_length': self.worker_pool.get_queue_length(),
            'recent_decisions': self.scaling_decisions[-10:],
            'average_cpu': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
            'average_memory': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
            'last_scaling_action': self.last_scaling_action.isoformat() if self.last_scaling_action else None
        }

class LoadBalancer:
    """Intelligent load balancing for document processing."""

    def __init__(self):
        self.worker_loads: dict[str, float] = {}
        self.worker_capabilities: dict[str, dict] = {}
        self.pending_tasks: list[dict] = []

    def register_worker(self, worker_id: str, capabilities: dict[str, Any]) -> None:
        """Register a new worker with its capabilities."""
        self.worker_loads[worker_id] = 0.0
        self.worker_capabilities[worker_id] = capabilities
        logger.info("Registered worker %s with capabilities: %s", worker_id, capabilities)

    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker."""
        self.worker_loads.pop(worker_id, None)
        self.worker_capabilities.pop(worker_id, None)
        logger.info("Unregistered worker %s", worker_id)

    def get_best_worker(self, task_requirements: dict[str, Any]) -> str | None:
        """Select best worker for a task based on load and capabilities."""
        if not self.worker_loads:
            return None

        # Filter workers by capabilities
        suitable_workers = []
        for worker_id, capabilities in self.worker_capabilities.items():
            if self._worker_can_handle_task(capabilities, task_requirements):
                current_load = self.worker_loads[worker_id]
                suitable_workers.append((worker_id, current_load))

        if not suitable_workers:
            return None

        # Select worker with lowest load
        best_worker = min(suitable_workers, key=lambda x: x[1])
        return best_worker[0]

    def _worker_can_handle_task(self, capabilities: dict, requirements: dict) -> bool:
        """Check if worker can handle task requirements."""
        # Check memory requirements
        if 'memory_mb' in requirements:
            if capabilities.get('available_memory_mb', 0) < requirements['memory_mb']:
                return False

        # Check processing type
        if 'processing_type' in requirements:
            supported_types = capabilities.get('supported_types', [])
            if requirements['processing_type'] not in supported_types:
                return False

        return True

    def update_worker_load(self, worker_id: str, load: float) -> None:
        """Update worker load information."""
        if worker_id in self.worker_loads:
            self.worker_loads[worker_id] = max(0.0, min(1.0, load))

    def get_load_distribution(self) -> dict[str, float]:
        """Get current load distribution across workers."""
        return self.worker_loads.copy()

    def get_balancing_stats(self) -> dict[str, Any]:
        """Get load balancing statistics."""
        if not self.worker_loads:
            return {'workers': 0, 'average_load': 0.0, 'load_variance': 0.0}

        loads = list(self.worker_loads.values())
        avg_load = sum(loads) / len(loads)
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)

        return {
            'workers': len(self.worker_loads),
            'average_load': avg_load,
            'load_variance': variance,
            'min_load': min(loads),
            'max_load': max(loads),
            'load_distribution': self.worker_loads.copy()
        }

# Global instances
auto_scaler_instance: AutoScaler | None = None
load_balancer_instance = LoadBalancer()

def get_load_balancer() -> LoadBalancer:
    """Get load balancer instance."""
    return load_balancer_instance

def create_auto_scaler(worker_pool: WorkerPool) -> AutoScaler:
    """Create auto-scaler instance."""
    global auto_scaler_instance
    auto_scaler_instance = AutoScaler(worker_pool)
    return auto_scaler_instance

def get_auto_scaler() -> AutoScaler | None:
    """Get auto-scaler instance."""
    return auto_scaler_instance
