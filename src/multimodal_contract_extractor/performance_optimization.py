"""Performance Optimization Engine for Contract Processing.

This module implements advanced performance optimization techniques including
intelligent caching, parallel processing, resource pooling, load balancing,
and adaptive performance tuning for maximum throughput and efficiency.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import psutil
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""

    MEMORY_OPTIMIZED = "memory_optimized"
    CPU_OPTIMIZED = "cpu_optimized"
    IO_OPTIMIZED = "io_optimized"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"


class ResourceType(Enum):
    """System resource types for monitoring."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    GPU = "gpu"


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    timestamp: float
    operation: str
    duration: float
    cpu_usage: float
    memory_usage: float
    disk_io_read: int = 0
    disk_io_write: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_workers: int = 1
    throughput_ops_per_sec: float = 0.0

    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (0-1)."""
        # Lower resource usage and higher throughput = higher efficiency
        cpu_efficiency = max(0, 1.0 - (self.cpu_usage / 100.0))
        memory_efficiency = max(0, 1.0 - (self.memory_usage / 100.0))
        cache_efficiency = (
            self.cache_hits / max(1, self.cache_hits + self.cache_misses)
            if self.cache_hits + self.cache_misses > 0 else 0.5
        )

        return (cpu_efficiency * 0.3 + memory_efficiency * 0.3 +
                cache_efficiency * 0.4)


class IntelligentCache:
    """Advanced caching system with TTL, LRU, and adaptive sizing."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float, float]] = {}  # value, timestamp, ttl
        self._access_times: Dict[str, float] = {}
        self._lock = RLock()
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._miss_count += 1
                return None

            value, timestamp, ttl = self._cache[key]

            # Check if expired
            if time.time() - timestamp > ttl:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                self._miss_count += 1
                return None

            # Update access time for LRU
            self._access_times[key] = time.time()
            self._hit_count += 1
            return value

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._lock:
            # Use default TTL if not specified
            actual_ttl = ttl or self.default_ttl

            # Clean expired entries
            self._cleanup_expired()

            # Check if we need to evict (LRU)
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            # Store value
            self._cache[key] = (value, time.time(), actual_ttl)
            self._access_times[key] = time.time()

    def _cleanup_expired(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = []

        for key, (_, timestamp, ttl) in self._cache.items():
            if current_time - timestamp > ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_times:
            return

        # Find LRU key
        lru_key = min(self._access_times.keys(), key=self._access_times.get)

        # Remove from cache
        if lru_key in self._cache:
            del self._cache[lru_key]
        del self._access_times[lru_key]

    def cache_hash(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Convert arguments to hashable string
        arg_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.sha256(arg_str.encode()).hexdigest()[:16]

    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._hit_count = 0
            self._miss_count = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests) if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "memory_usage_estimate": sum(
                    len(str(v)) for v, _, _ in self._cache.values()
                )
            }


class ResourceMonitor:
    """System resource monitoring and adaptation."""

    def __init__(self):
        self.monitoring_enabled = True
        self.sample_interval = 1.0  # seconds
        self.history_size = 100
        self.resource_history: Dict[ResourceType, List[float]] = {
            resource_type: [] for resource_type in ResourceType
        }

    def get_current_resources(self) -> Dict[ResourceType, float]:
        """Get current system resource usage."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = disk_io.read_bytes if disk_io else 0
            disk_write = disk_io.write_bytes if disk_io else 0

            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent = net_io.bytes_sent if net_io else 0
            net_recv = net_io.bytes_recv if net_io else 0

            return {
                ResourceType.CPU: cpu_usage,
                ResourceType.MEMORY: memory_usage,
                ResourceType.DISK_IO: disk_read + disk_write,
                ResourceType.NETWORK_IO: net_sent + net_recv,
                ResourceType.GPU: self._get_gpu_usage()
            }

        except Exception as e:
            logger.warning("Resource monitoring failed: %s", e)
            return dict.fromkeys(ResourceType, 0.0)

    def _get_gpu_usage(self) -> float:
        """Get GPU usage (simplified - would need nvidia-ml-py for real implementation)."""
        try:
            # Placeholder - in production would use proper GPU monitoring
            return 0.0
        except Exception:
            return 0.0

    def update_history(self, resources: Dict[ResourceType, float]) -> None:
        """Update resource history."""
        for resource_type, value in resources.items():
            history = self.resource_history[resource_type]
            history.append(value)

            # Maintain history size
            if len(history) > self.history_size:
                history.pop(0)

    def get_resource_trend(self, resource_type: ResourceType, window: int = 10) -> str:
        """Get resource usage trend (increasing, decreasing, stable)."""
        history = self.resource_history[resource_type]
        if len(history) < window:
            return "stable"

        recent = history[-window:]
        trend = np.polyfit(range(len(recent)), recent, 1)[0]

        if trend > 1.0:
            return "increasing"
        elif trend < -1.0:
            return "decreasing"
        else:
            return "stable"

    def recommend_optimization(self) -> OptimizationStrategy:
        """Recommend optimization strategy based on current resources."""
        current = self.get_current_resources()

        cpu_usage = current[ResourceType.CPU]
        memory_usage = current[ResourceType.MEMORY]

        if memory_usage > 80:
            return OptimizationStrategy.MEMORY_OPTIMIZED
        elif cpu_usage > 80:
            return OptimizationStrategy.CPU_OPTIMIZED
        elif cpu_usage < 30 and memory_usage < 30:
            return OptimizationStrategy.IO_OPTIMIZED
        else:
            return OptimizationStrategy.BALANCED


class AdaptiveThreadPool:
    """Thread pool that adapts size based on workload and system resources."""

    def __init__(self, min_workers: int = 2, max_workers: int = None):
        self.min_workers = min_workers
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.current_workers = min_workers

        self._executor = ThreadPoolExecutor(max_workers=self.current_workers)
        self._resource_monitor = ResourceMonitor()
        self._task_queue_size = 0
        self._completed_tasks = 0
        self._adaptation_lock = Lock()

    def submit(self, fn: Callable, *args, **kwargs):
        """Submit task to adaptive thread pool."""
        self._task_queue_size += 1

        future = self._executor.submit(self._wrap_task, fn, *args, **kwargs)

        # Check if we should adapt pool size
        self._maybe_adapt_pool_size()

        return future

    def _wrap_task(self, fn: Callable, *args, **kwargs):
        """Wrap task execution for monitoring."""
        try:
            result = fn(*args, **kwargs)
            self._completed_tasks += 1
            return result
        finally:
            self._task_queue_size = max(0, self._task_queue_size - 1)

    def _maybe_adapt_pool_size(self) -> None:
        """Adapt pool size based on workload and resources."""
        with self._adaptation_lock:
            # Get current system resources
            resources = self._resource_monitor.get_current_resources()
            cpu_usage = resources[ResourceType.CPU]
            memory_usage = resources[ResourceType.MEMORY]

            # Calculate optimal worker count
            queue_pressure = self._task_queue_size / max(1, self.current_workers)

            if queue_pressure > 2 and cpu_usage < 70 and memory_usage < 70:
                # Scale up
                new_size = min(self.max_workers, self.current_workers + 2)
            elif queue_pressure < 0.5 or cpu_usage > 90 or memory_usage > 90:
                # Scale down
                new_size = max(self.min_workers, self.current_workers - 1)
            else:
                new_size = self.current_workers

            if new_size != self.current_workers:
                self._resize_pool(new_size)

    def _resize_pool(self, new_size: int) -> None:
        """Resize the thread pool."""
        logger.info("Adapting thread pool size: %d -> %d", self.current_workers, new_size)

        # Create new executor with new size
        old_executor = self._executor
        self._executor = ThreadPoolExecutor(max_workers=new_size)
        self.current_workers = new_size

        # Shutdown old executor gracefully
        old_executor.shutdown(wait=False)

    def shutdown(self) -> None:
        """Shutdown the adaptive thread pool."""
        self._executor.shutdown(wait=True)

    def stats(self) -> Dict[str, Any]:
        """Get thread pool statistics."""
        return {
            "current_workers": self.current_workers,
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "queue_size": self._task_queue_size,
            "completed_tasks": self._completed_tasks
        }


class PerformanceOptimizer:
    """Main performance optimization engine."""

    def __init__(self):
        self.cache = IntelligentCache(max_size=2000, default_ttl=7200.0)
        self.resource_monitor = ResourceMonitor()
        self.thread_pool = AdaptiveThreadPool()
        self.process_pool = ProcessPoolExecutor(max_workers=os.cpu_count())

        self.performance_history: List[PerformanceMetrics] = []
        self.optimization_strategies: Dict[str, OptimizationStrategy] = {}

        # Performance tuning parameters
        self.batch_sizes = {
            "small": 10,
            "medium": 50,
            "large": 200
        }
        self.parallel_thresholds = {
            "cpu_intensive": 4,
            "io_intensive": 16,
            "memory_intensive": 2
        }

    def optimize_function(
        self,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[float] = None,
        enable_parallel: bool = True,
        optimization_strategy: Optional[OptimizationStrategy] = None
    ):
        """Decorator for function performance optimization."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key if caching enabled
                if cache_key or cache_key is None:
                    key = cache_key or f"{func.__name__}_{self.cache.cache_hash(*args, **kwargs)}"

                    # Try cache first
                    cached_result = self.cache.get(key)
                    if cached_result is not None:
                        logger.debug("Cache hit for %s", func.__name__)
                        return cached_result

                # Monitor performance
                start_time = time.time()
                start_resources = self.resource_monitor.get_current_resources()

                try:
                    # Determine optimization strategy
                    strategy = optimization_strategy or self.resource_monitor.recommend_optimization()

                    # Execute with optimization
                    if enable_parallel and self._should_parallelize(func, args, kwargs):
                        result = self._execute_parallel(func, args, kwargs, strategy)
                    else:
                        result = func(*args, **kwargs)

                    # Cache result if caching enabled
                    if cache_key or cache_key is None:
                        self.cache.put(key, result, cache_ttl)

                    return result

                finally:
                    # Record performance metrics
                    end_time = time.time()
                    end_resources = self.resource_monitor.get_current_resources()

                    metrics = PerformanceMetrics(
                        timestamp=start_time,
                        operation=func.__name__,
                        duration=end_time - start_time,
                        cpu_usage=end_resources[ResourceType.CPU],
                        memory_usage=end_resources[ResourceType.MEMORY],
                        cache_hits=self.cache._hit_count,
                        cache_misses=self.cache._miss_count
                    )

                    self.performance_history.append(metrics)

                    # Trim history
                    if len(self.performance_history) > 1000:
                        self.performance_history = self.performance_history[-1000:]

            return wrapper
        return decorator

    def _should_parallelize(self, func: Callable, args: Tuple, kwargs: Dict) -> bool:
        """Determine if function should be executed in parallel."""
        # Simple heuristics - in production would be more sophisticated

        # Check if function is CPU intensive
        if hasattr(func, '_cpu_intensive'):
            return True

        # Check argument size
        total_size = sum(len(str(arg)) for arg in args) + sum(len(str(v)) for v in kwargs.values())
        if total_size > 10000:  # Large inputs might benefit from parallelization
            return True

        # Check current system load
        resources = self.resource_monitor.get_current_resources()
        if resources[ResourceType.CPU] < 50:  # CPU available
            return True

        return False

    def _execute_parallel(
        self,
        func: Callable,
        args: Tuple,
        kwargs: Dict,
        strategy: OptimizationStrategy
    ) -> Any:
        """Execute function with parallel optimization."""
        # For now, just use thread pool - in production would be more sophisticated
        future = self.thread_pool.submit(func, *args, **kwargs)
        return future.result()

    async def batch_process(
        self,
        func: Callable,
        items: List[Any],
        batch_size: Optional[int] = None,
        max_concurrent: int = 10
    ) -> List[Any]:
        """Process items in optimized batches."""
        if not items:
            return []

        # Determine optimal batch size
        if batch_size is None:
            resources = self.resource_monitor.get_current_resources()
            if resources[ResourceType.MEMORY] > 70:
                batch_size = self.batch_sizes["small"]
            elif resources[ResourceType.CPU] > 70:
                batch_size = self.batch_sizes["medium"]
            else:
                batch_size = self.batch_sizes["large"]

        # Create batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        # Process batches concurrently
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch(batch):
            async with semaphore:
                return [func(item) for item in batch]

        # Execute all batches
        batch_results = await asyncio.gather(
            *[process_batch(batch) for batch in batches]
        )

        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.performance_history:
            return {"message": "No performance data available"}

        # Calculate aggregate metrics
        recent_metrics = self.performance_history[-100:]  # Last 100 operations

        avg_duration = np.mean([m.duration for m in recent_metrics])
        avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
        avg_memory = np.mean([m.memory_usage for m in recent_metrics])
        avg_efficiency = np.mean([m.efficiency_score for m in recent_metrics])

        # Cache statistics
        cache_stats = self.cache.stats()

        # Thread pool statistics
        thread_stats = self.thread_pool.stats()

        # Resource trends
        resource_trends = {
            resource_type.value: self.resource_monitor.get_resource_trend(resource_type)
            for resource_type in ResourceType
        }

        return {
            "performance_summary": {
                "avg_duration_seconds": round(avg_duration, 3),
                "avg_cpu_usage": round(avg_cpu, 1),
                "avg_memory_usage": round(avg_memory, 1),
                "avg_efficiency_score": round(avg_efficiency, 3),
                "total_operations": len(self.performance_history)
            },
            "cache_statistics": cache_stats,
            "thread_pool_statistics": thread_stats,
            "resource_trends": resource_trends,
            "optimization_recommendations": self._generate_optimization_recommendations(
                avg_cpu, avg_memory, cache_stats["hit_rate"]
            )
        }

    def _generate_optimization_recommendations(
        self,
        avg_cpu: float,
        avg_memory: float,
        cache_hit_rate: float
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if cache_hit_rate < 0.6:
            recommendations.append("Increase cache size or TTL for better hit rate")

        if avg_cpu > 80:
            recommendations.append("Consider CPU optimization or scaling")

        if avg_memory > 80:
            recommendations.append("Implement memory optimization strategies")

        if avg_cpu < 30 and avg_memory < 30:
            recommendations.append("System is underutilized - consider increasing batch sizes")

        return recommendations

    def shutdown(self) -> None:
        """Shutdown performance optimizer and clean up resources."""
        self.thread_pool.shutdown()
        self.process_pool.shutdown(wait=True)


# Global performance optimizer
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def optimize_performance(
    cache_key: Optional[str] = None,
    cache_ttl: Optional[float] = None,
    enable_parallel: bool = True,
    optimization_strategy: Optional[OptimizationStrategy] = None
):
    """Decorator for automatic performance optimization."""
    optimizer = get_performance_optimizer()
    return optimizer.optimize_function(
        cache_key=cache_key,
        cache_ttl=cache_ttl,
        enable_parallel=enable_parallel,
        optimization_strategy=optimization_strategy
    )


class PerformanceConfig(BaseModel):
    """Configuration for performance optimization."""

    enable_caching: bool = True
    cache_size: int = Field(default=2000, ge=100, le=10000)
    cache_ttl: float = Field(default=7200.0, gt=0.0)
    enable_parallel_processing: bool = True
    min_thread_workers: int = Field(default=2, ge=1, le=32)
    max_thread_workers: int = Field(default=16, ge=2, le=64)
    enable_adaptive_batching: bool = True
    default_batch_size: int = Field(default=50, ge=1, le=1000)
    resource_monitoring: bool = True
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
