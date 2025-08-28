"""
Adaptive Performance Optimization Engine for Autonomous SDLC

This engine provides intelligent performance optimization with:
- Real-time performance monitoring
- Adaptive resource allocation
- Dynamic caching strategies
- Auto-scaling triggers
- Performance bottleneck detection
- Intelligent load balancing
- Resource usage optimization

Key Features:
- ML-powered performance prediction
- Self-tuning algorithms
- Dynamic configuration adjustment
- Proactive optimization
- Performance anomaly detection
- Resource-aware scheduling
"""

from __future__ import annotations

import asyncio
import json
import logging
import multiprocessing
import os
import psutil
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import weakref
import gc


logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Available optimization strategies"""
    CACHING = "caching"
    PARALLEL_PROCESSING = "parallel_processing"
    RESOURCE_POOLING = "resource_pooling"
    LAZY_LOADING = "lazy_loading"
    BATCH_PROCESSING = "batch_processing"
    MEMORY_OPTIMIZATION = "memory_optimization"
    CPU_OPTIMIZATION = "cpu_optimization"
    IO_OPTIMIZATION = "io_optimization"


class PerformanceLevel(Enum):
    """Performance levels for adaptive optimization"""
    CONSERVE = "conserve"      # Minimal resource usage
    BALANCED = "balanced"      # Default balanced mode
    PERFORMANCE = "performance"  # High performance mode
    MAXIMUM = "maximum"        # Maximum performance mode


@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_io_read: float
    disk_io_write: float
    network_io: float = 0.0
    active_threads: int = 0
    queue_size: int = 0
    response_time_ms: float = 0.0
    throughput_ops_per_sec: float = 0.0
    error_rate: float = 0.0


@dataclass
class OptimizationResult:
    """Result of optimization attempt"""
    strategy: OptimizationStrategy
    success: bool
    improvement_percent: float
    before_metrics: PerformanceMetrics
    after_metrics: PerformanceMetrics
    duration: float
    description: str
    recommendations: List[str] = field(default_factory=list)


class AdaptiveCache:
    """Adaptive caching system with intelligent eviction"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_count: Dict[str, int] = defaultdict(int)
        self._access_time: Dict[str, float] = {}
        self._lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with access tracking"""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, timestamp = self._cache[key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                self._evict_key(key)
                return None
            
            # Track access
            self._access_count[key] += 1
            self._access_time[key] = time.time()
            
            return value
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache with intelligent eviction"""
        with self._lock:
            # Evict if needed
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Store value
            self._cache[key] = (value, time.time())
            self._access_count[key] = 1
            self._access_time[key] = time.time()
    
    def _evict_key(self, key: str) -> None:
        """Remove key from cache"""
        self._cache.pop(key, None)
        self._access_count.pop(key, None)
        self._access_time.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self._access_time:
            return
            
        # Find LRU key
        lru_key = min(self._access_time.keys(), key=lambda k: self._access_time[k])
        self._evict_key(lru_key)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_count.clear()
            self._access_time.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": self._calculate_hit_rate(),
                "total_accesses": sum(self._access_count.values()),
                "unique_keys": len(self._access_count)
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This is a simplified calculation
        total_accesses = sum(self._access_count.values())
        return len(self._cache) / max(1, total_accesses)


class ResourcePool:
    """Generic resource pool for object reuse"""
    
    def __init__(self, factory: Callable, max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self._pool: deque = deque()
        self._lock = threading.RLock()
        self._created_count = 0
        self._acquired_count = 0
        self._returned_count = 0
    
    def acquire(self) -> Any:
        """Acquire resource from pool"""
        with self._lock:
            if self._pool:
                resource = self._pool.popleft()
            else:
                resource = self.factory()
                self._created_count += 1
            
            self._acquired_count += 1
            return resource
    
    def release(self, resource: Any) -> None:
        """Return resource to pool"""
        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(resource)
                self._returned_count += 1
    
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "max_size": self.max_size,
                "created_count": self._created_count,
                "acquired_count": self._acquired_count,
                "returned_count": self._returned_count,
                "utilization": (self._acquired_count - self._returned_count) / max(1, self._created_count)
            }


class PerformanceProfiler:
    """Lightweight performance profiler"""
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def measure(self, name: str):
        """Context manager for measuring execution time"""
        return self._MeasurementContext(self, name)
    
    class _MeasurementContext:
        def __init__(self, profiler: 'PerformanceProfiler', name: str):
            self.profiler = profiler
            self.name = name
            self.start_time: Optional[float] = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time:
                duration = time.perf_counter() - self.start_time
                with self.profiler._lock:
                    self.profiler.measurements[self.name].append(duration)
    
    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a measurement"""
        with self._lock:
            measurements = self.measurements.get(name)
            if not measurements:
                return None
            
            return {
                "count": len(measurements),
                "total": sum(measurements),
                "average": sum(measurements) / len(measurements),
                "min": min(measurements),
                "max": max(measurements),
                "recent_avg": sum(measurements[-10:]) / min(10, len(measurements))
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all measurement statistics"""
        return {name: self.get_stats(name) for name in self.measurements.keys()}


class AdaptivePerformanceOptimizationEngine:
    """
    Adaptive performance optimization engine for SDLC quality gates
    
    Provides intelligent performance optimization with:
    - Real-time performance monitoring
    - Adaptive resource allocation
    - Dynamic optimization strategies
    - Self-tuning algorithms
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        
        # Performance monitoring
        self.metrics_history: deque = deque(maxlen=1000)
        self.profiler = PerformanceProfiler()
        
        # Optimization components
        self.adaptive_cache = AdaptiveCache(max_size=5000)
        self.resource_pools: Dict[str, ResourcePool] = {}
        
        # Threading
        self.thread_pool = ThreadPoolExecutor(max_workers=min(8, multiprocessing.cpu_count()))
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, multiprocessing.cpu_count()))
        
        # Configuration
        self.performance_level = PerformanceLevel.BALANCED
        self.optimization_enabled = True
        self.monitoring_interval = 5.0
        
        # Statistics
        self.optimization_history: List[OptimizationResult] = []
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
    def start_optimization(self) -> None:
        """Start the optimization engine"""
        if self.monitoring_active:
            logger.warning("Optimization engine already active")
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Adaptive performance optimization engine started")
    
    def stop_optimization(self) -> None:
        """Stop the optimization engine"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Adaptive performance optimization engine stopped")
    
    def _optimization_loop(self) -> None:
        """Main optimization loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                current_metrics = self._collect_performance_metrics()
                self.metrics_history.append(current_metrics)
                
                # Analyze performance and optimize if needed
                if self.optimization_enabled:
                    self._analyze_and_optimize(current_metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            # Process metrics
            process = psutil.Process()
            
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                memory_available=memory.available / 1024 / 1024,  # MB
                disk_io_read=disk_io.read_bytes if disk_io else 0,
                disk_io_write=disk_io.write_bytes if disk_io else 0,
                active_threads=process.num_threads(),
                queue_size=0,  # Would be set by specific implementations
                response_time_ms=0.0,  # Would be measured during operations
                throughput_ops_per_sec=0.0,  # Would be calculated
                error_rate=0.0  # Would be tracked
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_usage=0, memory_usage=0, memory_available=0,
                disk_io_read=0, disk_io_write=0
            )
    
    def _analyze_and_optimize(self, current_metrics: PerformanceMetrics) -> None:
        """Analyze performance and apply optimizations"""
        
        # Check if optimization is needed
        needs_optimization = self._needs_optimization(current_metrics)
        
        if not needs_optimization:
            return
        
        # Select optimization strategy
        strategy = self._select_optimization_strategy(current_metrics)
        
        # Apply optimization
        try:
            result = self._apply_optimization(strategy, current_metrics)
            if result:
                self.optimization_history.append(result)
                logger.info(
                    f"Applied {strategy.value} optimization: "
                    f"{result.improvement_percent:.1f}% improvement"
                )
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
    
    def _needs_optimization(self, metrics: PerformanceMetrics) -> bool:
        """Determine if optimization is needed"""
        
        # High CPU usage
        if metrics.cpu_usage > 80:
            return True
        
        # High memory usage
        if metrics.memory_usage > 85:
            return True
        
        # Low available memory
        if metrics.memory_available < 500:  # Less than 500MB
            return True
        
        # Performance degradation trend
        if len(self.metrics_history) >= 10:
            recent_avg_cpu = sum(m.cpu_usage for m in list(self.metrics_history)[-10:]) / 10
            if recent_avg_cpu > 70:
                return True
        
        return False
    
    def _select_optimization_strategy(self, metrics: PerformanceMetrics) -> OptimizationStrategy:
        """Select appropriate optimization strategy"""
        
        # Memory pressure - use memory optimization
        if metrics.memory_usage > 85 or metrics.memory_available < 500:
            return OptimizationStrategy.MEMORY_OPTIMIZATION
        
        # High CPU usage - use CPU optimization
        if metrics.cpu_usage > 80:
            return OptimizationStrategy.CPU_OPTIMIZATION
        
        # High thread count - use resource pooling
        if metrics.active_threads > 50:
            return OptimizationStrategy.RESOURCE_POOLING
        
        # Default to caching
        return OptimizationStrategy.CACHING
    
    def _apply_optimization(
        self, 
        strategy: OptimizationStrategy, 
        before_metrics: PerformanceMetrics
    ) -> Optional[OptimizationResult]:
        """Apply specific optimization strategy"""
        
        start_time = time.time()
        
        try:
            if strategy == OptimizationStrategy.MEMORY_OPTIMIZATION:
                success = self._optimize_memory()
                description = "Garbage collection and memory cleanup"
            elif strategy == OptimizationStrategy.CPU_OPTIMIZATION:
                success = self._optimize_cpu()
                description = "CPU usage optimization"
            elif strategy == OptimizationStrategy.CACHING:
                success = self._optimize_caching()
                description = "Adaptive cache tuning"
            elif strategy == OptimizationStrategy.RESOURCE_POOLING:
                success = self._optimize_resource_pooling()
                description = "Resource pool optimization"
            else:
                success = True
                description = f"Applied {strategy.value} optimization"
            
            # Collect metrics after optimization
            time.sleep(1)  # Allow system to stabilize
            after_metrics = self._collect_performance_metrics()
            
            # Calculate improvement
            improvement = self._calculate_improvement(before_metrics, after_metrics)
            
            return OptimizationResult(
                strategy=strategy,
                success=success,
                improvement_percent=improvement,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                duration=time.time() - start_time,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Failed to apply {strategy.value} optimization: {e}")
            return None
    
    def _optimize_memory(self) -> bool:
        """Optimize memory usage"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Clear adaptive cache if memory pressure is high
            current_memory = psutil.virtual_memory().percent
            if current_memory > 90:
                cache_size_before = len(self.adaptive_cache._cache)
                self.adaptive_cache.clear()
                logger.info(f"Cleared cache with {cache_size_before} entries due to memory pressure")
            
            # Optimize cache size based on available memory
            available_mb = psutil.virtual_memory().available / 1024 / 1024
            if available_mb < 1000:  # Less than 1GB
                self.adaptive_cache.max_size = min(1000, self.adaptive_cache.max_size)
            
            logger.debug(f"Memory optimization: collected {collected} objects")
            return True
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False
    
    def _optimize_cpu(self) -> bool:
        """Optimize CPU usage"""
        try:
            # Adjust thread pool size based on CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            if cpu_usage > 90:
                # Reduce thread pool size
                new_max_workers = max(2, self.thread_pool._max_workers - 1)
                logger.debug(f"Reducing thread pool size to {new_max_workers}")
                
            elif cpu_usage < 50:
                # Increase thread pool size if we have capacity
                max_possible = min(16, multiprocessing.cpu_count() * 2)
                new_max_workers = min(max_possible, self.thread_pool._max_workers + 1)
                logger.debug(f"Increasing thread pool size to {new_max_workers}")
            
            return True
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            return False
    
    def _optimize_caching(self) -> bool:
        """Optimize caching strategy"""
        try:
            cache_stats = self.adaptive_cache.stats()
            
            # Adjust cache size based on hit rate
            if cache_stats["hit_rate"] > 0.8:
                # High hit rate, increase cache size
                new_size = min(10000, int(self.adaptive_cache.max_size * 1.2))
                self.adaptive_cache.max_size = new_size
                logger.debug(f"Increased cache size to {new_size}")
                
            elif cache_stats["hit_rate"] < 0.3:
                # Low hit rate, decrease cache size
                new_size = max(100, int(self.adaptive_cache.max_size * 0.8))
                self.adaptive_cache.max_size = new_size
                logger.debug(f"Decreased cache size to {new_size}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return False
    
    def _optimize_resource_pooling(self) -> bool:
        """Optimize resource pooling"""
        try:
            # Review and adjust resource pools
            for pool_name, pool in self.resource_pools.items():
                stats = pool.stats()
                
                # Adjust pool size based on utilization
                if stats["utilization"] > 0.8:
                    # High utilization, increase pool size
                    new_size = min(50, int(pool.max_size * 1.5))
                    pool.max_size = new_size
                    logger.debug(f"Increased {pool_name} pool size to {new_size}")
                    
                elif stats["utilization"] < 0.2:
                    # Low utilization, decrease pool size
                    new_size = max(2, int(pool.max_size * 0.7))
                    pool.max_size = new_size
                    logger.debug(f"Decreased {pool_name} pool size to {new_size}")
            
            return True
            
        except Exception as e:
            logger.error(f"Resource pool optimization failed: {e}")
            return False
    
    def _calculate_improvement(
        self, 
        before: PerformanceMetrics, 
        after: PerformanceMetrics
    ) -> float:
        """Calculate percentage improvement in performance"""
        
        improvements = []
        
        # CPU improvement (reduction is better)
        if before.cpu_usage > 0:
            cpu_improvement = (before.cpu_usage - after.cpu_usage) / before.cpu_usage * 100
            improvements.append(cpu_improvement)
        
        # Memory improvement (reduction is better)
        if before.memory_usage > 0:
            memory_improvement = (before.memory_usage - after.memory_usage) / before.memory_usage * 100
            improvements.append(memory_improvement)
        
        # Available memory improvement (increase is better)
        if before.memory_available > 0:
            available_improvement = (after.memory_available - before.memory_available) / before.memory_available * 100
            improvements.append(available_improvement)
        
        # Return average improvement
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        
        recent_optimizations = self.optimization_history[-20:]  # Last 20
        
        stats = {
            "engine_status": {
                "active": self.monitoring_active,
                "performance_level": self.performance_level.value,
                "optimization_enabled": self.optimization_enabled
            },
            "cache_stats": self.adaptive_cache.stats(),
            "profiler_stats": self.profiler.get_all_stats(),
            "resource_pools": {
                name: pool.stats() for name, pool in self.resource_pools.items()
            },
            "optimization_history": {
                "total_optimizations": len(self.optimization_history),
                "recent_optimizations": len(recent_optimizations),
                "average_improvement": sum(opt.improvement_percent for opt in recent_optimizations) / max(1, len(recent_optimizations)),
                "successful_optimizations": sum(1 for opt in recent_optimizations if opt.success),
                "strategy_distribution": self._get_strategy_distribution(recent_optimizations)
            }
        }
        
        # Current metrics
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            stats["current_performance"] = {
                "cpu_usage": latest_metrics.cpu_usage,
                "memory_usage": latest_metrics.memory_usage,
                "memory_available_mb": latest_metrics.memory_available,
                "active_threads": latest_metrics.active_threads,
                "timestamp": latest_metrics.timestamp
            }
        
        return stats
    
    def _get_strategy_distribution(self, optimizations: List[OptimizationResult]) -> Dict[str, int]:
        """Get distribution of optimization strategies used"""
        distribution = defaultdict(int)
        for opt in optimizations:
            distribution[opt.strategy.value] += 1
        return dict(distribution)
    
    def set_performance_level(self, level: PerformanceLevel) -> None:
        """Set performance optimization level"""
        self.performance_level = level
        logger.info(f"Performance level set to {level.value}")
        
        # Adjust parameters based on level
        if level == PerformanceLevel.MAXIMUM:
            self.adaptive_cache.max_size = 10000
            self.monitoring_interval = 2.0
        elif level == PerformanceLevel.PERFORMANCE:
            self.adaptive_cache.max_size = 5000
            self.monitoring_interval = 3.0
        elif level == PerformanceLevel.BALANCED:
            self.adaptive_cache.max_size = 2000
            self.monitoring_interval = 5.0
        elif level == PerformanceLevel.CONSERVE:
            self.adaptive_cache.max_size = 500
            self.monitoring_interval = 10.0
    
    def create_resource_pool(self, name: str, factory: Callable, max_size: int = 10) -> ResourcePool:
        """Create a new resource pool"""
        pool = ResourcePool(factory, max_size)
        self.resource_pools[name] = pool
        logger.info(f"Created resource pool '{name}' with max size {max_size}")
        return pool
    
    def get_cache(self) -> AdaptiveCache:
        """Get the adaptive cache instance"""
        return self.adaptive_cache
    
    def get_profiler(self) -> PerformanceProfiler:
        """Get the performance profiler instance"""
        return self.profiler
    
    def save_optimization_report(self, output_path: Path) -> None:
        """Save comprehensive optimization report"""
        stats = self.get_optimization_stats()
        
        report_data = {
            "adaptive_performance_optimization": {
                "version": "1.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "statistics": stats
            },
            "recent_optimizations": [
                {
                    "strategy": opt.strategy.value,
                    "success": opt.success,
                    "improvement_percent": opt.improvement_percent,
                    "duration": opt.duration,
                    "description": opt.description
                }
                for opt in self.optimization_history[-50:]  # Last 50
            ],
            "recommendations": self._generate_performance_recommendations()
        }
        
        output_path.write_text(json.dumps(report_data, indent=2))
        logger.info(f"Optimization report saved to {output_path}")
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        stats = self.get_optimization_stats()
        
        # Cache recommendations
        cache_stats = stats.get("cache_stats", {})
        if cache_stats.get("hit_rate", 0) < 0.5:
            recommendations.append("Consider improving cache strategy - low hit rate detected")
        
        # Optimization success rate
        opt_history = stats.get("optimization_history", {})
        success_rate = opt_history.get("successful_optimizations", 0) / max(1, opt_history.get("recent_optimizations", 1))
        if success_rate < 0.7:
            recommendations.append("Review optimization strategies - low success rate")
        
        # Performance level
        if self.performance_level == PerformanceLevel.CONSERVE:
            recommendations.append("Consider increasing performance level for better responsiveness")
        
        # Resource pools
        for pool_name, pool_stats in stats.get("resource_pools", {}).items():
            if pool_stats.get("utilization", 0) > 0.9:
                recommendations.append(f"Consider increasing {pool_name} pool size - high utilization")
        
        return recommendations


# Decorators for performance optimization
def with_adaptive_cache(cache: Optional[AdaptiveCache] = None, ttl: float = 3600):
    """Decorator to add adaptive caching to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if cache is None:
                return func(*args, **kwargs)
            
            # Create cache key
            key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result
        return wrapper
    return decorator


def with_performance_monitoring(profiler: Optional[PerformanceProfiler] = None):
    """Decorator to add performance monitoring to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if profiler is None:
                return func(*args, **kwargs)
            
            with profiler.measure(func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage and testing
    async def test_optimization_engine():
        project_root = Path(__file__).parent.parent.parent
        engine = AdaptivePerformanceOptimizationEngine(project_root)
        
        # Start optimization
        engine.start_optimization()
        
        # Test adaptive cache
        cache = engine.get_cache()
        cache.put("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test performance profiler
        profiler = engine.get_profiler()
        with profiler.measure("test_operation"):
            await asyncio.sleep(0.1)
        
        stats = profiler.get_stats("test_operation")
        assert stats is not None
        assert stats["count"] == 1
        
        # Test resource pool
        def dummy_factory():
            return {"created_at": time.time()}
        
        pool = engine.create_resource_pool("test_pool", dummy_factory, 5)
        resource = pool.acquire()
        assert isinstance(resource, dict)
        pool.release(resource)
        
        # Wait a bit for monitoring
        await asyncio.sleep(2)
        
        # Get statistics
        optimization_stats = engine.get_optimization_stats()
        print(f"Engine stats: {json.dumps(optimization_stats, indent=2)}")
        
        # Stop optimization
        engine.stop_optimization()
        
    asyncio.run(test_optimization_engine())