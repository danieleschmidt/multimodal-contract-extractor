"""
Resource management and auto-scaling system for Generation 3 scaling.

This module provides intelligent resource allocation, auto-scaling based on load metrics,
resource optimization algorithms, and dynamic worker pool management.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from weakref import WeakSet

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    WORKERS = "workers"


class ScalingDirection(Enum):
    """Auto-scaling directions."""
    SCALE_UP = auto()
    SCALE_DOWN = auto()
    MAINTAIN = auto()


class ResourceStatus(Enum):
    """Resource status indicators."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    THROTTLED = "throttled"


@dataclass
class ResourceMetrics:
    """System resource metrics."""

    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    cpu_count: int = 0
    memory_percent: float = 0.0
    memory_available_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_free_gb: float = 0.0
    network_sent_mbps: float = 0.0
    network_recv_mbps: float = 0.0
    load_average: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    active_processes: int = 0
    gpu_utilization: float = 0.0
    gpu_memory_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)

    @property
    def overall_health_score(self) -> float:
        """Calculate overall system health score (0-1, higher is better)."""
        score = 0.0

        # CPU health (0-1, lower usage is better)
        cpu_score = max(0, 1.0 - (self.cpu_percent / 100.0))
        score += cpu_score * 0.3

        # Memory health (0-1, lower usage is better)
        memory_score = max(0, 1.0 - (self.memory_percent / 100.0))
        score += memory_score * 0.3

        # Disk health (0-1, lower usage is better)
        disk_score = max(0, 1.0 - (self.disk_usage_percent / 100.0))
        score += disk_score * 0.2

        # Load average health (0-1, lower load is better)
        if self.cpu_count > 0:
            load_score = max(0, 1.0 - (self.load_average[0] / self.cpu_count))
            score += load_score * 0.2

        return min(1.0, score)


@dataclass
class ResourceThresholds:
    """Resource threshold configuration."""

    cpu_warning: float = 70.0  # Percentage
    cpu_critical: float = 90.0
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    disk_warning: float = 80.0
    disk_critical: float = 95.0
    load_warning_multiplier: float = 0.8  # Times CPU count
    load_critical_multiplier: float = 1.2

    def get_status(self, metrics: ResourceMetrics) -> Dict[ResourceType, ResourceStatus]:
        """Get resource status based on thresholds."""
        status = {}

        # CPU status
        if metrics.cpu_percent >= self.cpu_critical:
            status[ResourceType.CPU] = ResourceStatus.CRITICAL
        elif metrics.cpu_percent >= self.cpu_warning:
            status[ResourceType.CPU] = ResourceStatus.WARNING
        else:
            status[ResourceType.CPU] = ResourceStatus.HEALTHY

        # Memory status
        if metrics.memory_percent >= self.memory_critical:
            status[ResourceType.MEMORY] = ResourceStatus.CRITICAL
        elif metrics.memory_percent >= self.memory_warning:
            status[ResourceType.MEMORY] = ResourceStatus.WARNING
        else:
            status[ResourceType.MEMORY] = ResourceStatus.HEALTHY

        # Disk status
        if metrics.disk_usage_percent >= self.disk_critical:
            status[ResourceType.DISK] = ResourceStatus.CRITICAL
        elif metrics.disk_usage_percent >= self.disk_warning:
            status[ResourceType.DISK] = ResourceStatus.WARNING
        else:
            status[ResourceType.DISK] = ResourceStatus.HEALTHY

        # Load average status
        if metrics.cpu_count > 0:
            load_threshold_warning = metrics.cpu_count * self.load_warning_multiplier
            load_threshold_critical = metrics.cpu_count * self.load_critical_multiplier

            if metrics.load_average[0] >= load_threshold_critical:
                status[ResourceType.CPU] = ResourceStatus.CRITICAL  # Override CPU status if worse
            elif metrics.load_average[0] >= load_threshold_warning:
                if status[ResourceType.CPU] == ResourceStatus.HEALTHY:
                    status[ResourceType.CPU] = ResourceStatus.WARNING

        return status


class ResourceMonitor:
    """System resource monitoring."""

    def __init__(self, sample_interval: float = 5.0, history_size: int = 100):
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.thresholds = ResourceThresholds()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[ResourceMetrics], None]] = []

        # Network baseline for calculating rates
        self._last_network_stats: Optional[Dict[str, int]] = None
        self._last_network_time: Optional[float] = None

    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Resource monitoring stopped")

    def add_callback(self, callback: Callable[[ResourceMetrics], None]) -> None:
        """Add callback for resource metric updates."""
        self._callbacks.append(callback)

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent if hasattr(disk, 'percent') else 0.0
            if not hasattr(disk, 'percent'):
                disk_usage_percent = (disk.used / disk.total) * 100 if disk.total > 0 else 0.0
            disk_free_gb = disk.free / 1024 / 1024 / 1024

            # Network metrics
            network_sent_mbps, network_recv_mbps = self._get_network_rates()

            # Load average (Unix-like systems)
            try:
                load_average = psutil.getloadavg()
            except (AttributeError, OSError):
                load_average = (0.0, 0.0, 0.0)

            # Process count
            active_processes = len(psutil.pids())

            # GPU metrics (if available)
            gpu_utilization, gpu_memory_percent = self._get_gpu_metrics()

            return ResourceMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                memory_total_mb=memory_total_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_sent_mbps=network_sent_mbps,
                network_recv_mbps=network_recv_mbps,
                load_average=load_average,
                active_processes=active_processes,
                gpu_utilization=gpu_utilization,
                gpu_memory_percent=gpu_memory_percent
            )

        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            return ResourceMetrics()

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Resource monitor callback failed: {e}")

                time.sleep(self.sample_interval)

            except Exception as e:
                logger.error(f"Resource monitoring loop error: {e}")
                time.sleep(self.sample_interval)

    def _get_network_rates(self) -> Tuple[float, float]:
        """Calculate network transmission rates in Mbps."""
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.time()

            if self._last_network_stats and self._last_network_time:
                time_delta = current_time - self._last_network_time

                if time_delta > 0:
                    sent_delta = current_stats.bytes_sent - self._last_network_stats['bytes_sent']
                    recv_delta = current_stats.bytes_recv - self._last_network_stats['bytes_recv']

                    # Convert to Mbps
                    sent_mbps = (sent_delta * 8) / (time_delta * 1024 * 1024)
                    recv_mbps = (recv_delta * 8) / (time_delta * 1024 * 1024)

                    self._last_network_stats = {
                        'bytes_sent': current_stats.bytes_sent,
                        'bytes_recv': current_stats.bytes_recv
                    }
                    self._last_network_time = current_time

                    return sent_mbps, recv_mbps

            # First run or error - just store baseline
            self._last_network_stats = {
                'bytes_sent': current_stats.bytes_sent,
                'bytes_recv': current_stats.bytes_recv
            }
            self._last_network_time = current_time

            return 0.0, 0.0

        except Exception as e:
            logger.error(f"Error calculating network rates: {e}")
            return 0.0, 0.0

    def _get_gpu_metrics(self) -> Tuple[float, float]:
        """Get GPU utilization metrics."""
        try:
            # Try nvidia-ml-py
            import pynvml
            pynvml.nvmlInit()

            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Use first GPU

                # GPU utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = utilization.gpu

                # GPU memory
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory_percent = (memory_info.used / memory_info.total) * 100

                return gpu_util, gpu_memory_percent

        except ImportError:
            # pynvml not available
            pass
        except Exception as e:
            logger.debug(f"GPU metrics unavailable: {e}")

        return 0.0, 0.0

    def get_average_metrics(self, window_minutes: int = 5) -> Optional[ResourceMetrics]:
        """Get average metrics over a time window."""
        if not self.metrics_history:
            return None

        cutoff_time = time.time() - (window_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return None

        # Calculate averages
        count = len(recent_metrics)
        avg_metrics = ResourceMetrics(
            timestamp=time.time(),
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / count,
            cpu_count=recent_metrics[0].cpu_count,  # This doesn't change
            memory_percent=sum(m.memory_percent for m in recent_metrics) / count,
            memory_available_mb=sum(m.memory_available_mb for m in recent_metrics) / count,
            memory_total_mb=recent_metrics[0].memory_total_mb,  # This doesn't change
            disk_usage_percent=sum(m.disk_usage_percent for m in recent_metrics) / count,
            disk_free_gb=sum(m.disk_free_gb for m in recent_metrics) / count,
            network_sent_mbps=sum(m.network_sent_mbps for m in recent_metrics) / count,
            network_recv_mbps=sum(m.network_recv_mbps for m in recent_metrics) / count,
            load_average=(
                sum(m.load_average[0] for m in recent_metrics) / count,
                sum(m.load_average[1] for m in recent_metrics) / count,
                sum(m.load_average[2] for m in recent_metrics) / count
            ),
            active_processes=int(sum(m.active_processes for m in recent_metrics) / count),
            gpu_utilization=sum(m.gpu_utilization for m in recent_metrics) / count,
            gpu_memory_percent=sum(m.gpu_memory_percent for m in recent_metrics) / count
        )

        return avg_metrics


@dataclass
class AutoScalingPolicy:
    """Auto-scaling policy configuration."""

    scale_up_cpu_threshold: float = 70.0
    scale_up_memory_threshold: float = 75.0
    scale_up_queue_threshold: int = 50
    scale_down_cpu_threshold: float = 30.0
    scale_down_memory_threshold: float = 40.0
    scale_down_queue_threshold: int = 5

    min_workers: int = 2
    max_workers: int = 20
    scale_up_increment: int = 2
    scale_down_increment: int = 1

    cooldown_seconds: float = 300.0  # 5 minutes
    evaluation_window_minutes: int = 5

    def should_scale_up(self, metrics: ResourceMetrics, queue_size: int, current_workers: int) -> bool:
        """Determine if we should scale up."""
        if current_workers >= self.max_workers:
            return False

        conditions = [
            metrics.cpu_percent > self.scale_up_cpu_threshold,
            metrics.memory_percent > self.scale_up_memory_threshold,
            queue_size > self.scale_up_queue_threshold
        ]

        # Scale up if any condition is met
        return any(conditions)

    def should_scale_down(self, metrics: ResourceMetrics, queue_size: int, current_workers: int) -> bool:
        """Determine if we should scale down."""
        if current_workers <= self.min_workers:
            return False

        conditions = [
            metrics.cpu_percent < self.scale_down_cpu_threshold,
            metrics.memory_percent < self.scale_down_memory_threshold,
            queue_size < self.scale_down_queue_threshold
        ]

        # Scale down only if all conditions are met
        return all(conditions)


class WorkerPoolManager:
    """Dynamic worker pool management."""

    def __init__(self, initial_size: int = 4):
        self.current_size = initial_size
        self.workers: WeakSet = WeakSet()
        self.pending_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self._lock = threading.RLock()

        # Performance tracking
        self.avg_task_duration = 0.0
        self.throughput_per_minute = 0.0
        self._task_times = deque(maxlen=100)
        self._last_throughput_calculation = time.time()

    def adjust_size(self, new_size: int) -> int:
        """Adjust worker pool size."""
        with self._lock:
            old_size = self.current_size
            self.current_size = max(1, new_size)

            logger.info(f"Worker pool size adjusted: {old_size} -> {self.current_size}")
            return self.current_size

    def record_task_completion(self, duration: float, success: bool) -> None:
        """Record task completion metrics."""
        with self._lock:
            self._task_times.append(duration)

            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1

            # Update average duration
            if self._task_times:
                self.avg_task_duration = sum(self._task_times) / len(self._task_times)

            # Update throughput (tasks per minute)
            now = time.time()
            if now - self._last_throughput_calculation >= 60:  # Update every minute
                recent_tasks = [t for t in self._task_times if t > 0]  # Valid completions
                self.throughput_per_minute = len(recent_tasks)
                self._last_throughput_calculation = now

    def get_utilization(self) -> float:
        """Get current worker utilization percentage."""
        if self.current_size == 0:
            return 100.0  # Overloaded

        # This is a simplified calculation - in practice, you'd track active workers
        active_workers = min(self.pending_tasks, self.current_size)
        return (active_workers / self.current_size) * 100.0

    def get_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics."""
        with self._lock:
            total_tasks = self.completed_tasks + self.failed_tasks
            success_rate = (self.completed_tasks / total_tasks) if total_tasks > 0 else 0.0

            return {
                'current_size': self.current_size,
                'pending_tasks': self.pending_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'success_rate': success_rate,
                'avg_task_duration': self.avg_task_duration,
                'throughput_per_minute': self.throughput_per_minute,
                'utilization': self.get_utilization()
            }


class AutoScaler:
    """Auto-scaling engine for dynamic resource management."""

    def __init__(
        self,
        resource_monitor: ResourceMonitor,
        worker_pool_manager: WorkerPoolManager,
        policy: Optional[AutoScalingPolicy] = None
    ):
        self.resource_monitor = resource_monitor
        self.worker_pool_manager = worker_pool_manager
        self.policy = policy or AutoScalingPolicy()

        self._scaling_history: List[Dict[str, Any]] = []
        self._last_scaling_action: Optional[float] = None
        self._running = False
        self._scaling_thread: Optional[threading.Thread] = None

        # Register for resource updates
        self.resource_monitor.add_callback(self._on_resource_update)

    def start(self) -> None:
        """Start the auto-scaler."""
        if self._running:
            return

        self._running = True
        self._scaling_thread = threading.Thread(target=self._scaling_loop, daemon=True)
        self._scaling_thread.start()
        logger.info("Auto-scaler started")

    def stop(self) -> None:
        """Stop the auto-scaler."""
        self._running = False
        if self._scaling_thread:
            self._scaling_thread.join(timeout=5.0)
        logger.info("Auto-scaler stopped")

    def _on_resource_update(self, metrics: ResourceMetrics) -> None:
        """Called when resource metrics are updated."""
        # This could trigger immediate scaling decisions for critical conditions
        status = self.policy.scale_up_cpu_threshold

        if metrics.cpu_percent > 95 or metrics.memory_percent > 95:
            logger.warning(f"Critical resource usage detected: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_percent:.1f}%")
            # Could trigger emergency scaling here

    def _scaling_loop(self) -> None:
        """Main auto-scaling loop."""
        while self._running:
            try:
                self._evaluate_scaling()
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Auto-scaling evaluation error: {e}")
                time.sleep(30)

    def _evaluate_scaling(self) -> None:
        """Evaluate whether scaling action is needed."""
        # Check cooldown period
        now = time.time()
        if (self._last_scaling_action and
            now - self._last_scaling_action < self.policy.cooldown_seconds):
            return

        # Get average metrics over evaluation window
        avg_metrics = self.resource_monitor.get_average_metrics(
            self.policy.evaluation_window_minutes
        )

        if not avg_metrics:
            return

        # Get current queue size and worker stats
        worker_stats = self.worker_pool_manager.get_stats()
        queue_size = worker_stats['pending_tasks']
        current_workers = worker_stats['current_size']

        # Determine scaling action
        scaling_decision = self._make_scaling_decision(avg_metrics, queue_size, current_workers)

        if scaling_decision != ScalingDirection.MAINTAIN:
            self._execute_scaling(scaling_decision, avg_metrics, worker_stats)

    def _make_scaling_decision(
        self,
        metrics: ResourceMetrics,
        queue_size: int,
        current_workers: int
    ) -> ScalingDirection:
        """Make scaling decision based on metrics."""

        if self.policy.should_scale_up(metrics, queue_size, current_workers):
            return ScalingDirection.SCALE_UP
        elif self.policy.should_scale_down(metrics, queue_size, current_workers):
            return ScalingDirection.SCALE_DOWN
        else:
            return ScalingDirection.MAINTAIN

    def _execute_scaling(
        self,
        direction: ScalingDirection,
        metrics: ResourceMetrics,
        worker_stats: Dict[str, Any]
    ) -> None:
        """Execute scaling action."""
        current_workers = worker_stats['current_size']

        if direction == ScalingDirection.SCALE_UP:
            new_size = min(
                current_workers + self.policy.scale_up_increment,
                self.policy.max_workers
            )
            action = "scale_up"
        else:  # SCALE_DOWN
            new_size = max(
                current_workers - self.policy.scale_down_increment,
                self.policy.min_workers
            )
            action = "scale_down"

        if new_size != current_workers:
            # Execute scaling
            actual_size = self.worker_pool_manager.adjust_size(new_size)

            # Record scaling action
            scaling_record = {
                'timestamp': time.time(),
                'action': action,
                'old_size': current_workers,
                'new_size': actual_size,
                'trigger_metrics': metrics.to_dict(),
                'worker_stats': worker_stats
            }

            self._scaling_history.append(scaling_record)
            self._last_scaling_action = time.time()

            logger.info(f"Auto-scaling executed: {action} from {current_workers} to {actual_size} workers")

    def get_scaling_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scaling history."""
        return self._scaling_history[-limit:]

    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics."""
        if not self._scaling_history:
            return {
                'total_scaling_actions': 0,
                'scale_up_actions': 0,
                'scale_down_actions': 0,
                'avg_time_between_actions': 0.0,
                'last_action': None
            }

        scale_up_count = sum(1 for h in self._scaling_history if h['action'] == 'scale_up')
        scale_down_count = len(self._scaling_history) - scale_up_count

        # Calculate average time between actions
        timestamps = [h['timestamp'] for h in self._scaling_history]
        if len(timestamps) > 1:
            time_diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_time_between = sum(time_diffs) / len(time_diffs)
        else:
            avg_time_between = 0.0

        return {
            'total_scaling_actions': len(self._scaling_history),
            'scale_up_actions': scale_up_count,
            'scale_down_actions': scale_down_count,
            'avg_time_between_actions': avg_time_between,
            'last_action': self._scaling_history[-1] if self._scaling_history else None
        }


class ResourceManager:
    """Main resource management system."""

    def __init__(
        self,
        monitor_interval: float = 5.0,
        auto_scaling_enabled: bool = True,
        initial_workers: int = 4
    ):
        self.resource_monitor = ResourceMonitor(sample_interval=monitor_interval)
        self.worker_pool_manager = WorkerPoolManager(initial_size=initial_workers)
        self.auto_scaler = AutoScaler(
            self.resource_monitor,
            self.worker_pool_manager
        ) if auto_scaling_enabled else None

        self._initialized = False

    def initialize(self) -> None:
        """Initialize the resource management system."""
        if self._initialized:
            return

        self.resource_monitor.start_monitoring()

        if self.auto_scaler:
            self.auto_scaler.start()

        self._initialized = True
        logger.info("Resource management system initialized")

    def shutdown(self) -> None:
        """Shutdown the resource management system."""
        if not self._initialized:
            return

        if self.auto_scaler:
            self.auto_scaler.stop()

        self.resource_monitor.stop_monitoring()

        self._initialized = False
        logger.info("Resource management system shutdown")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        current_metrics = self.resource_monitor.get_current_metrics()
        avg_metrics = self.resource_monitor.get_average_metrics(5)

        thresholds = ResourceThresholds()
        resource_status = thresholds.get_status(current_metrics)

        status = {
            'initialized': self._initialized,
            'timestamp': time.time(),
            'current_metrics': current_metrics.to_dict(),
            'average_metrics': avg_metrics.to_dict() if avg_metrics else None,
            'resource_status': {k.value: v.value for k, v in resource_status.items()},
            'overall_health_score': current_metrics.overall_health_score,
            'worker_pool_stats': self.worker_pool_manager.get_stats()
        }

        if self.auto_scaler:
            status['auto_scaling'] = {
                'enabled': True,
                'scaling_stats': self.auto_scaler.get_scaling_stats(),
                'recent_history': self.auto_scaler.get_scaling_history(10)
            }
        else:
            status['auto_scaling'] = {'enabled': False}

        return status

    def optimize_resources(self) -> Dict[str, Any]:
        """Perform resource optimization."""
        current_metrics = self.resource_monitor.get_current_metrics()
        optimizations = []

        # Memory optimization
        if current_metrics.memory_percent > 80:
            # Trigger garbage collection
            import gc
            collected = gc.collect()
            optimizations.append(f"Garbage collection freed {collected} objects")

        # Worker pool optimization
        worker_stats = self.worker_pool_manager.get_stats()
        utilization = worker_stats['utilization']

        if utilization < 20 and worker_stats['current_size'] > 2:
            # Consider reducing workers (but let auto-scaler handle it)
            optimizations.append("Low worker utilization detected - consider scaling down")
        elif utilization > 90:
            optimizations.append("High worker utilization detected - consider scaling up")

        # Disk optimization
        if current_metrics.disk_usage_percent > 90:
            optimizations.append("Critical disk usage - consider cleanup")

        return {
            'timestamp': time.time(),
            'optimizations_applied': optimizations,
            'metrics_before': current_metrics.to_dict(),
            'metrics_after': self.resource_monitor.get_current_metrics().to_dict()
        }


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager(
    monitor_interval: float = 5.0,
    auto_scaling_enabled: bool = True,
    initial_workers: int = 4
) -> ResourceManager:
    """Get global resource manager instance."""
    global _resource_manager

    if _resource_manager is None:
        _resource_manager = ResourceManager(
            monitor_interval=monitor_interval,
            auto_scaling_enabled=auto_scaling_enabled,
            initial_workers=initial_workers
        )

    return _resource_manager
