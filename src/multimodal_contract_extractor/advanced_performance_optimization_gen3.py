"""
Advanced Performance Optimization for Generation 3: Scale
High-performance computing with parallel processing, caching, and resource optimization.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import logging
import multiprocessing as mp
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    cpu_usage_before: Optional[float] = None
    cpu_usage_after: Optional[float] = None
    memory_usage_before: Optional[int] = None
    memory_usage_after: Optional[int] = None
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_workers: int = 1
    throughput: Optional[float] = None  # items per second

    def finish(self):
        """Mark operation as finished and calculate metrics."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.cpu_usage_after = psutil.cpu_percent()
        self.memory_usage_after = psutil.virtual_memory().used

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "duration": self.duration,
            "cpu_usage_change": (self.cpu_usage_after - self.cpu_usage_before) if self.cpu_usage_after and self.cpu_usage_before else None,
            "memory_usage_change": (self.memory_usage_after - self.memory_usage_before) if self.memory_usage_after and self.memory_usage_before else None,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "parallel_workers": self.parallel_workers,
            "throughput": self.throughput
        }


class AdvancedCache:
    """High-performance multi-level caching system."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        key_data = f"{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self.ttl_seconds

    def _evict_expired(self):
        """Remove expired entries."""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
            self._access_times.pop(key, None)

    def _evict_lru(self):
        """Evict least recently used entries."""
        if len(self._cache) <= self.max_size:
            return

        # Sort by access time and remove oldest
        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
        num_to_remove = len(self._cache) - self.max_size + 1

        for key, _ in sorted_items[:num_to_remove]:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if not self._is_expired(timestamp):
                    self._access_times[key] = time.time()
                    self.hits += 1
                    return value
                else:
                    # Remove expired entry
                    del self._cache[key]
                    self._access_times.pop(key, None)

            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        """Set item in cache."""
        with self._lock:
            now = time.time()
            self._cache[key] = (value, now)
            self._access_times[key] = now

            # Periodic cleanup
            if len(self._cache) % 100 == 0:
                self._evict_expired()

            # LRU eviction if needed
            if len(self._cache) > self.max_size:
                self._evict_lru()

    def clear(self):
        """Clear cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = self.hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": hit_ratio,
                "ttl_seconds": self.ttl_seconds
            }


def cached(cache: Optional[AdvancedCache] = None, ttl: int = 3600):
    """Decorator for caching function results."""
    if cache is None:
        cache = AdvancedCache(ttl_seconds=ttl)

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper._cache = cache
        return wrapper
    return decorator


class ParallelProcessor:
    """High-performance parallel processing system."""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=min(self.max_workers, mp.cpu_count()))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def shutdown(self):
        """Shutdown thread and process pools."""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

    def map_parallel(self, func: Callable, items: List[Any], use_processes: bool = False) -> List[Any]:
        """Map function over items in parallel."""
        if not items:
            return []

        pool = self.process_pool if use_processes else self.thread_pool

        try:
            results = list(pool.map(func, items))
            return results
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}")
            # Fallback to sequential processing
            return [func(item) for item in items]

    async def map_async(self, func: Callable, items: List[Any], max_concurrency: int = 10) -> List[Any]:
        """Map function over items asynchronously with concurrency control."""
        if not items:
            return []

        semaphore = asyncio.Semaphore(max_concurrency)

        async def bounded_task(item):
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(item)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, func, item)

        tasks = [bounded_task(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        clean_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Async task failed: {result}")
                clean_results.append(None)
            else:
                clean_results.append(result)

        return clean_results

    def batch_process(self, func: Callable, items: List[Any], batch_size: int = 100, use_processes: bool = False) -> List[Any]:
        """Process items in batches for better memory management."""
        if not items:
            return []

        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = self.map_parallel(func, batch, use_processes=use_processes)
            results.extend(batch_results)

            # Optional: garbage collection between batches
            if i > 0 and i % (batch_size * 10) == 0:
                import gc
                gc.collect()

        return results


class ResourcePool:
    """Resource pool for expensive objects (database connections, etc.)."""

    def __init__(self, factory: Callable, max_size: int = 10, timeout: float = 30.0):
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self._pool: queue.Queue = queue.Queue(maxsize=max_size)
        self._all_resources: List[Any] = []
        self._lock = threading.Lock()

        # Pre-populate pool
        for _ in range(min(3, max_size)):  # Start with 3 resources
            resource = self.factory()
            self._pool.put(resource)
            self._all_resources.append(resource)

    def acquire(self) -> Any:
        """Acquire resource from pool."""
        try:
            # Try to get existing resource
            resource = self._pool.get(timeout=1.0)
            return resource
        except queue.Empty:
            # Create new resource if pool not at max capacity
            with self._lock:
                if len(self._all_resources) < self.max_size:
                    resource = self.factory()
                    self._all_resources.append(resource)
                    return resource
                else:
                    # Wait for resource to be available
                    resource = self._pool.get(timeout=self.timeout)
                    return resource

    def release(self, resource: Any):
        """Release resource back to pool."""
        try:
            self._pool.put_nowait(resource)
        except queue.Full:
            # Pool is full, resource will be garbage collected
            pass

    def close_all(self):
        """Close all resources in pool."""
        with self._lock:
            # Close all resources if they have a close method
            for resource in self._all_resources:
                if hasattr(resource, 'close'):
                    try:
                        resource.close()
                    except Exception as e:
                        logger.error(f"Error closing resource: {e}")

            self._all_resources.clear()

            # Clear the queue
            while not self._pool.empty():
                try:
                    self._pool.get_nowait()
                except queue.Empty:
                    break


class PerformanceMonitor:
    """Real-time performance monitoring and optimization."""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.max_history = 1000
        self._lock = threading.Lock()

    def start_operation(self, operation: str) -> PerformanceMetrics:
        """Start tracking an operation."""
        metrics = PerformanceMetrics(operation=operation)
        metrics.cpu_usage_before = psutil.cpu_percent()
        metrics.memory_usage_before = psutil.virtual_memory().used
        return metrics

    def finish_operation(self, metrics: PerformanceMetrics):
        """Finish tracking an operation."""
        metrics.finish()

        with self._lock:
            self.metrics.append(metrics)
            if len(self.metrics) > self.max_history:
                self.metrics = self.metrics[-self.max_history:]

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            if operation:
                filtered_metrics = [m for m in self.metrics if m.operation == operation]
            else:
                filtered_metrics = self.metrics

        if not filtered_metrics:
            return {"operation": operation, "count": 0}

        durations = [m.duration for m in filtered_metrics if m.duration]
        cache_hits = sum(m.cache_hits for m in filtered_metrics)
        cache_misses = sum(m.cache_misses for m in filtered_metrics)

        return {
            "operation": operation,
            "count": len(filtered_metrics),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "total_cache_hits": cache_hits,
            "total_cache_misses": cache_misses,
            "cache_hit_ratio": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
            "avg_throughput": sum(m.throughput for m in filtered_metrics if m.throughput) / len([m for m in filtered_metrics if m.throughput]) if any(m.throughput for m in filtered_metrics) else 0
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system performance stats."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_usage": (disk.used / disk.total) * 100,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
        }


class AutoScaler:
    """Automatic scaling based on performance metrics."""

    def __init__(self, min_workers: int = 1, max_workers: int = 16):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.performance_monitor = PerformanceMonitor()
        self.scale_up_threshold = 0.8  # Scale up if CPU > 80%
        self.scale_down_threshold = 0.3  # Scale down if CPU < 30%
        self.check_interval = 30  # Check every 30 seconds
        self._running = False
        self._monitor_thread = None

    def start_monitoring(self):
        """Start automatic scaling monitoring."""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("AutoScaler monitoring started")

    def stop_monitoring(self):
        """Stop automatic scaling monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("AutoScaler monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_and_scale()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"AutoScaler error: {e}")
                time.sleep(self.check_interval)

    def _check_and_scale(self):
        """Check metrics and adjust scaling."""
        stats = self.performance_monitor.get_system_stats()
        cpu_usage = stats["cpu_usage"] / 100.0
        memory_usage = stats["memory_usage"] / 100.0

        # Scale up conditions
        if cpu_usage > self.scale_up_threshold or memory_usage > 0.9:
            if self.current_workers < self.max_workers:
                old_workers = self.current_workers
                self.current_workers = min(self.current_workers * 2, self.max_workers)
                logger.info(f"Scaling UP: {old_workers} -> {self.current_workers} workers (CPU: {cpu_usage:.1%}, Memory: {memory_usage:.1%})")

        # Scale down conditions
        elif cpu_usage < self.scale_down_threshold and memory_usage < 0.5:
            if self.current_workers > self.min_workers:
                old_workers = self.current_workers
                self.current_workers = max(self.current_workers // 2, self.min_workers)
                logger.info(f"Scaling DOWN: {old_workers} -> {self.current_workers} workers (CPU: {cpu_usage:.1%}, Memory: {memory_usage:.1%})")

    def get_current_capacity(self) -> int:
        """Get current worker capacity."""
        return self.current_workers


class OptimizedProcessor:
    """Main optimized processing class combining all performance features."""

    def __init__(self, cache_size: int = 1000, max_workers: Optional[int] = None):
        self.cache = AdvancedCache(max_size=cache_size)
        self.parallel_processor = ParallelProcessor(max_workers=max_workers)
        self.performance_monitor = PerformanceMonitor()
        self.auto_scaler = AutoScaler()
        self.resource_pools: Dict[str, ResourcePool] = {}

        # Start auto-scaling
        self.auto_scaler.start_monitoring()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def shutdown(self):
        """Shutdown all components."""
        self.auto_scaler.stop_monitoring()
        self.parallel_processor.shutdown()
        for pool in self.resource_pools.values():
            pool.close_all()

    def create_resource_pool(self, name: str, factory: Callable, max_size: int = 10) -> ResourcePool:
        """Create a resource pool."""
        pool = ResourcePool(factory, max_size=max_size)
        self.resource_pools[name] = pool
        return pool

    def get_resource_pool(self, name: str) -> Optional[ResourcePool]:
        """Get existing resource pool."""
        return self.resource_pools.get(name)

    @cached()
    def optimized_function(self, func: Callable, *args, use_cache: bool = True, **kwargs):
        """Execute function with optimization."""
        if use_cache:
            cache_key = self.cache._generate_key(func.__name__, *args, **kwargs)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Track performance
        metrics = self.performance_monitor.start_operation(func.__name__)

        try:
            result = func(*args, **kwargs)

            if use_cache:
                self.cache.set(cache_key, result)
                metrics.cache_misses = 1

            return result

        finally:
            self.performance_monitor.finish_operation(metrics)

    def batch_process_optimized(self, func: Callable, items: List[Any], batch_size: Optional[int] = None, use_processes: bool = False) -> List[Any]:
        """Optimized batch processing with automatic scaling."""
        if not items:
            return []

        # Determine optimal batch size based on current capacity
        if batch_size is None:
            current_workers = self.auto_scaler.get_current_capacity()
            batch_size = max(10, len(items) // current_workers)

        # Track performance
        metrics = self.performance_monitor.start_operation("batch_process")
        metrics.parallel_workers = self.auto_scaler.get_current_capacity()

        try:
            results = self.parallel_processor.batch_process(func, items, batch_size=batch_size, use_processes=use_processes)
            metrics.throughput = len(items) / metrics.duration if metrics.duration and metrics.duration > 0 else 0
            return results

        finally:
            self.performance_monitor.finish_operation(metrics)

    async def async_batch_process(self, func: Callable, items: List[Any], max_concurrency: Optional[int] = None) -> List[Any]:
        """Async batch processing with optimizations."""
        if not items:
            return []

        # Use current capacity for concurrency if not specified
        if max_concurrency is None:
            max_concurrency = self.auto_scaler.get_current_capacity()

        # Track performance
        metrics = self.performance_monitor.start_operation("async_batch_process")
        metrics.parallel_workers = max_concurrency

        try:
            results = await self.parallel_processor.map_async(func, items, max_concurrency=max_concurrency)
            metrics.throughput = len(items) / metrics.duration if metrics.duration and metrics.duration > 0 else 0
            return results

        finally:
            self.performance_monitor.finish_operation(metrics)

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "cache_stats": self.cache.stats(),
            "performance_stats": self.performance_monitor.get_stats(),
            "system_stats": self.performance_monitor.get_system_stats(),
            "current_workers": self.auto_scaler.get_current_capacity(),
            "resource_pools": {name: {"size": len(pool._all_resources)} for name, pool in self.resource_pools.items()}
        }


# Global optimized processor instance
_optimized_processor = None


def get_optimized_processor() -> OptimizedProcessor:
    """Get global optimized processor instance."""
    global _optimized_processor
    if _optimized_processor is None:
        _optimized_processor = OptimizedProcessor()
    return _optimized_processor


def performance_optimized(use_cache: bool = True, use_parallel: bool = False):
    """Decorator for performance optimization."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            processor = get_optimized_processor()

            if use_parallel and len(args) > 0 and isinstance(args[0], (list, tuple)):
                # Assume first argument is a list to process in parallel
                items = args[0]
                rest_args = args[1:]

                def partial_func(item):
                    return func(item, *rest_args, **kwargs)

                return processor.batch_process_optimized(partial_func, list(items))
            else:
                return processor.optimized_function(func, *args, use_cache=use_cache, **kwargs)

        return wrapper
    return decorator
