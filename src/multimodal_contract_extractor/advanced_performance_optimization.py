"""Advanced Performance Optimization Framework for High-Scale Legal AI Operations."""

import asyncio
import json
import logging
import multiprocessing
import os
import statistics
import time
import threading
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """Performance optimization targets."""
    
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    MEMORY_EFFICIENCY = "memory_efficiency"
    CPU_UTILIZATION = "cpu_utilization"
    GPU_UTILIZATION = "gpu_utilization"
    COST_EFFICIENCY = "cost_efficiency"
    ENERGY_EFFICIENCY = "energy_efficiency"
    ACCURACY_PRESERVATION = "accuracy_preservation"


class ScalingStrategy(Enum):
    """Scaling strategies for different workloads."""
    
    HORIZONTAL_SCALING = "horizontal_scaling"
    VERTICAL_SCALING = "vertical_scaling"
    AUTO_SCALING = "auto_scaling"
    ELASTIC_SCALING = "elastic_scaling"
    PREDICTIVE_SCALING = "predictive_scaling"
    BURST_SCALING = "burst_scaling"


class CachingStrategy(Enum):
    """Caching strategies for performance optimization."""
    
    LRU_CACHE = "lru_cache"
    LFU_CACHE = "lfu_cache"
    ADAPTIVE_CACHE = "adaptive_cache"
    DISTRIBUTED_CACHE = "distributed_cache"
    HIERARCHICAL_CACHE = "hierarchical_cache"
    PREDICTIVE_CACHE = "predictive_cache"


@dataclass
class PerformanceProfile:
    """Performance profiling results."""
    
    operation_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    gpu_usage: float
    throughput: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Results from performance optimization."""
    
    target: OptimizationTarget
    strategy_applied: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percentage: float
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


class AdaptiveCache:
    """Adaptive caching system with multiple strategies."""
    
    def __init__(self, max_size: int = 1000, strategy: CachingStrategy = CachingStrategy.ADAPTIVE_CACHE):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: Dict[str, Any] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
        self.access_time: Dict[str, float] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self.cache:
                self.access_count[key] += 1
                self.access_time[key] = time.time()
                self.cache_stats["hits"] += 1
                return self.cache[key]
            else:
                self.cache_stats["misses"] += 1
                return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value into cache."""
        with self._lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            self.cache[key] = value
            self.access_count[key] += 1
            self.access_time[key] = time.time()
    
    def _evict(self) -> None:
        """Evict items based on caching strategy."""
        if not self.cache:
            return
        
        if self.strategy == CachingStrategy.LRU_CACHE:
            # Least Recently Used
            oldest_key = min(self.access_time.keys(), key=lambda k: self.access_time[k])
            del self.cache[oldest_key]
            del self.access_count[oldest_key]
            del self.access_time[oldest_key]
            
        elif self.strategy == CachingStrategy.LFU_CACHE:
            # Least Frequently Used
            least_used_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
            del self.cache[least_used_key]
            del self.access_count[least_used_key]
            del self.access_time[least_used_key]
            
        elif self.strategy == CachingStrategy.ADAPTIVE_CACHE:
            # Adaptive strategy based on access patterns
            current_time = time.time()
            scores = {}
            
            for key in self.cache.keys():
                recency_score = 1.0 / (current_time - self.access_time[key] + 1)
                frequency_score = self.access_count[key]
                scores[key] = recency_score * frequency_score
            
            victim_key = min(scores.keys(), key=lambda k: scores[k])
            del self.cache[victim_key]
            del self.access_count[victim_key]
            del self.access_time[victim_key]
        
        self.cache_stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "evictions": self.cache_stats["evictions"]
        }


class ConcurrencyManager:
    """Advanced concurrency management for high-performance operations."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1))
        self.semaphore = asyncio.Semaphore(self.max_workers)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    async def execute_concurrent(
        self,
        tasks: List[Tuple[Callable, tuple, dict]],
        concurrency_limit: Optional[int] = None
    ) -> List[Any]:
        """Execute multiple tasks concurrently with optional limit."""
        if concurrency_limit:
            semaphore = asyncio.Semaphore(concurrency_limit)
        else:
            semaphore = self.semaphore
        
        async def bounded_task(func, args, kwargs):
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
        
        coroutines = [bounded_task(func, args, kwargs) for func, args, kwargs in tasks]
        return await asyncio.gather(*coroutines, return_exceptions=True)
    
    async def execute_cpu_intensive(
        self, func: Callable, *args, **kwargs
    ) -> Any:
        """Execute CPU-intensive task in process pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, func, *args, **kwargs)
    
    def submit_background_task(
        self, task_id: str, coro: Callable
    ) -> asyncio.Task:
        """Submit a background task."""
        task = asyncio.create_task(coro)
        self.active_tasks[task_id] = task
        
        def cleanup_task(t):
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
        
        task.add_done_callback(cleanup_task)
        return task
    
    def get_active_tasks(self) -> Dict[str, asyncio.Task]:
        """Get currently active background tasks."""
        return self.active_tasks.copy()
    
    async def shutdown(self) -> None:
        """Shutdown the concurrency manager."""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Shutdown executors
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class PerformanceProfiler:
    """Advanced performance profiler for detailed analysis."""
    
    def __init__(self):
        self.profiles: List[PerformanceProfile] = []
        self.active_profiles: Dict[str, Dict[str, Any]] = {}
        
    async def start_profiling(self, operation_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Start profiling an operation."""
        profile_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        self.active_profiles[profile_id] = {
            "operation_name": operation_name,
            "start_time": time.time(),
            "start_memory": self._get_memory_usage(),
            "start_cpu": self._get_cpu_usage(),
            "start_gpu": self._get_gpu_usage(),
            "tags": tags or {},
            "request_count": 0,
            "error_count": 0,
            "latencies": []
        }
        
        return profile_id
    
    async def record_request(self, profile_id: str, latency: float, success: bool = True) -> None:
        """Record a request in the profile."""
        if profile_id in self.active_profiles:
            profile = self.active_profiles[profile_id]
            profile["request_count"] += 1
            profile["latencies"].append(latency)
            
            if not success:
                profile["error_count"] += 1
    
    async def stop_profiling(self, profile_id: str) -> PerformanceProfile:
        """Stop profiling and generate results."""
        if profile_id not in self.active_profiles:
            raise ValueError(f"Profile {profile_id} not found")
        
        profile_data = self.active_profiles[profile_id]
        end_time = time.time()
        
        execution_time = end_time - profile_data["start_time"]
        memory_usage = self._get_memory_usage() - profile_data["start_memory"]
        cpu_usage = self._get_cpu_usage() - profile_data["start_cpu"]
        gpu_usage = self._get_gpu_usage() - profile_data["start_gpu"]
        
        latencies = profile_data["latencies"]
        throughput = profile_data["request_count"] / execution_time if execution_time > 0 else 0
        error_rate = profile_data["error_count"] / max(1, profile_data["request_count"])
        
        performance_profile = PerformanceProfile(
            operation_name=profile_data["operation_name"],
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            gpu_usage=gpu_usage,
            throughput=throughput,
            latency_p50=np.percentile(latencies, 50) if latencies else 0,
            latency_p95=np.percentile(latencies, 95) if latencies else 0,
            latency_p99=np.percentile(latencies, 99) if latencies else 0,
            error_rate=error_rate,
            timestamp=end_time,
            tags=profile_data["tags"]
        )
        
        self.profiles.append(performance_profile)
        del self.active_profiles[profile_id]
        
        return performance_profile
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    def _get_gpu_usage(self) -> float:
        """Get current GPU usage percentage."""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(util.gpu)
        except (ImportError, Exception):
            return 0.0


class AutoScaler:
    """Automatic scaling system based on performance metrics."""
    
    def __init__(self):
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.metric_buffer: deque = deque(maxlen=100)
        
    def register_scaling_policy(
        self,
        policy_name: str,
        metric_name: str,
        scale_up_threshold: float,
        scale_down_threshold: float,
        scale_up_action: Callable,
        scale_down_action: Callable,
        cooldown_period: float = 300.0  # 5 minutes
    ) -> None:
        """Register an auto-scaling policy."""
        self.scaling_policies[policy_name] = {
            "metric_name": metric_name,
            "scale_up_threshold": scale_up_threshold,
            "scale_down_threshold": scale_down_threshold,
            "scale_up_action": scale_up_action,
            "scale_down_action": scale_down_action,
            "cooldown_period": cooldown_period,
            "last_scaling_time": 0
        }
        
        logger.info(f"Registered auto-scaling policy: {policy_name}")
    
    async def update_metric(self, metric_name: str, value: float) -> None:
        """Update metric value and check scaling policies."""
        self.metric_buffer.append({
            "metric_name": metric_name,
            "value": value,
            "timestamp": time.time()
        })
        
        # Check all policies
        for policy_name, policy in self.scaling_policies.items():
            if policy["metric_name"] == metric_name:
                await self._evaluate_scaling_policy(policy_name, policy, value)
    
    async def _evaluate_scaling_policy(
        self, policy_name: str, policy: Dict[str, Any], current_value: float
    ) -> None:
        """Evaluate if scaling action should be triggered."""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - policy["last_scaling_time"] < policy["cooldown_period"]:
            return
        
        # Get recent metric values for trend analysis
        recent_metrics = [
            m for m in self.metric_buffer
            if m["metric_name"] == policy["metric_name"] and
            current_time - m["timestamp"] < 60  # Last minute
        ]
        
        if len(recent_metrics) < 3:  # Need sufficient data
            return
        
        # Calculate average over recent period
        avg_value = statistics.mean([m["value"] for m in recent_metrics])
        
        scaling_action = None
        
        # Scale up condition
        if avg_value > policy["scale_up_threshold"]:
            scaling_action = "scale_up"
            action_func = policy["scale_up_action"]
            
        # Scale down condition
        elif avg_value < policy["scale_down_threshold"]:
            scaling_action = "scale_down"
            action_func = policy["scale_down_action"]
        
        if scaling_action:
            try:
                # Execute scaling action
                if asyncio.iscoroutinefunction(action_func):
                    await action_func()
                else:
                    action_func()
                
                # Record scaling event
                scaling_event = {
                    "policy_name": policy_name,
                    "action": scaling_action,
                    "trigger_value": avg_value,
                    "threshold": policy[f"{scaling_action}_threshold"],
                    "timestamp": current_time
                }
                
                self.scaling_history.append(scaling_event)
                policy["last_scaling_time"] = current_time
                
                logger.info(f"Auto-scaling triggered: {policy_name} - {scaling_action}")
                
            except Exception as e:
                logger.error(f"Auto-scaling action failed for {policy_name}: {e}")


class AdvancedPerformanceOptimizer:
    """Comprehensive performance optimization framework."""
    
    def __init__(self):
        self.cache = AdaptiveCache(max_size=10000)
        self.concurrency_manager = ConcurrencyManager()
        self.profiler = PerformanceProfiler()
        self.auto_scaler = AutoScaler()
        self.optimization_results: List[OptimizationResult] = []
        
        # Optimization strategies
        self.optimization_strategies = {
            OptimizationTarget.THROUGHPUT: self._optimize_throughput,
            OptimizationTarget.LATENCY: self._optimize_latency,
            OptimizationTarget.MEMORY_EFFICIENCY: self._optimize_memory,
            OptimizationTarget.CPU_UTILIZATION: self._optimize_cpu,
            OptimizationTarget.COST_EFFICIENCY: self._optimize_cost
        }
        
        # Performance baselines
        self.baselines: Dict[str, PerformanceProfile] = {}
        
    async def optimize_operation(
        self,
        operation_name: str,
        operation_func: Callable,
        target: OptimizationTarget,
        *args,
        **kwargs
    ) -> Tuple[Any, OptimizationResult]:
        """Optimize an operation for specific target."""
        # Baseline measurement
        baseline_profile_id = await self.profiler.start_profiling(
            f"{operation_name}_baseline", {"optimization_target": target.value}
        )
        
        start_time = time.time()
        baseline_result = await operation_func(*args, **kwargs)
        baseline_latency = time.time() - start_time
        
        await self.profiler.record_request(baseline_profile_id, baseline_latency)
        baseline_profile = await self.profiler.stop_profiling(baseline_profile_id)
        
        # Apply optimization strategy
        optimization_strategy = self.optimization_strategies.get(target)
        if not optimization_strategy:
            raise ValueError(f"No optimization strategy for target: {target}")
        
        optimized_func = await optimization_strategy(operation_func, baseline_profile)
        
        # Optimized measurement
        optimized_profile_id = await self.profiler.start_profiling(
            f"{operation_name}_optimized", {"optimization_target": target.value}
        )
        
        start_time = time.time()
        optimized_result = await optimized_func(*args, **kwargs)
        optimized_latency = time.time() - start_time
        
        await self.profiler.record_request(optimized_profile_id, optimized_latency)
        optimized_profile = await self.profiler.stop_profiling(optimized_profile_id)
        
        # Calculate improvement
        improvement = self._calculate_improvement(baseline_profile, optimized_profile, target)
        
        optimization_result = OptimizationResult(
            target=target,
            strategy_applied=optimization_strategy.__name__,
            before_metrics=self._profile_to_metrics(baseline_profile),
            after_metrics=self._profile_to_metrics(optimized_profile),
            improvement_percentage=improvement,
            timestamp=time.time()
        )
        
        self.optimization_results.append(optimization_result)
        
        return optimized_result, optimization_result
    
    async def _optimize_throughput(
        self, operation_func: Callable, baseline: PerformanceProfile
    ) -> Callable:
        """Optimize for maximum throughput."""
        async def optimized_operation(*args, **kwargs):
            # Use caching to improve throughput
            cache_key = self._generate_cache_key(operation_func.__name__, args, kwargs)
            cached_result = self.cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Use concurrency for batch operations
            if isinstance(args[0], (list, tuple)) and len(args[0]) > 1:
                # Batch processing with concurrency
                batch_data = args[0]
                batch_size = min(10, len(batch_data))
                
                tasks = []
                for i in range(0, len(batch_data), batch_size):
                    batch = batch_data[i:i + batch_size]
                    tasks.append((operation_func, (batch,), kwargs))
                
                batch_results = await self.concurrency_manager.execute_concurrent(tasks)
                result = [item for sublist in batch_results for item in sublist]
            else:
                # Single operation
                result = await operation_func(*args, **kwargs)
            
            # Cache the result
            self.cache.put(cache_key, result)
            return result
        
        return optimized_operation
    
    async def _optimize_latency(
        self, operation_func: Callable, baseline: PerformanceProfile
    ) -> Callable:
        """Optimize for minimum latency."""
        async def optimized_operation(*args, **kwargs):
            # Aggressive caching for latency optimization
            cache_key = self._generate_cache_key(operation_func.__name__, args, kwargs)
            cached_result = self.cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Pre-warm critical components
            await self._prewarm_components()
            
            # Execute with minimal overhead
            result = await operation_func(*args, **kwargs)
            
            # Cache with high priority
            self.cache.put(cache_key, result)
            return result
        
        return optimized_operation
    
    async def _optimize_memory(
        self, operation_func: Callable, baseline: PerformanceProfile
    ) -> Callable:
        """Optimize for memory efficiency."""
        async def optimized_operation(*args, **kwargs):
            # Use streaming/chunking for large data
            if self._is_large_data_operation(args, kwargs):
                return await self._process_in_chunks(operation_func, *args, **kwargs)
            
            # Use process pool for memory isolation
            if baseline.memory_usage > 1000:  # > 1GB
                return await self.concurrency_manager.execute_cpu_intensive(
                    operation_func, *args, **kwargs
                )
            
            return await operation_func(*args, **kwargs)
        
        return optimized_operation
    
    async def _optimize_cpu(
        self, operation_func: Callable, baseline: PerformanceProfile
    ) -> Callable:
        """Optimize for CPU efficiency."""
        async def optimized_operation(*args, **kwargs):
            # Use CPU-optimized algorithms
            if baseline.cpu_usage > 80:  # High CPU usage
                # Distribute across multiple processes
                return await self.concurrency_manager.execute_cpu_intensive(
                    operation_func, *args, **kwargs
                )
            
            # Use thread pool for I/O bound operations
            return await operation_func(*args, **kwargs)
        
        return optimized_operation
    
    async def _optimize_cost(
        self, operation_func: Callable, baseline: PerformanceProfile
    ) -> Callable:
        """Optimize for cost efficiency."""
        async def optimized_operation(*args, **kwargs):
            # Aggressive caching to reduce compute costs
            cache_key = self._generate_cache_key(operation_func.__name__, args, kwargs)
            cached_result = self.cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Use spot instances or cheaper compute
            result = await operation_func(*args, **kwargs)
            
            # Cache with long TTL
            self.cache.put(cache_key, result)
            return result
        
        return optimized_operation
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function parameters."""
        import hashlib
        
        # Create a string representation of args and kwargs
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        
        # Hash for consistent key length
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _prewarm_components(self) -> None:
        """Pre-warm critical components for latency optimization."""
        # Simulate component pre-warming
        await asyncio.sleep(0.001)
    
    def _is_large_data_operation(self, args: tuple, kwargs: dict) -> bool:
        """Check if operation involves large data."""
        for arg in args:
            if isinstance(arg, (list, tuple)) and len(arg) > 1000:
                return True
            if isinstance(arg, dict) and len(arg) > 100:
                return True
        return False
    
    async def _process_in_chunks(
        self, operation_func: Callable, *args, **kwargs
    ) -> Any:
        """Process large data in chunks for memory efficiency."""
        # Find the large data argument
        chunk_size = 100
        results = []
        
        for i, arg in enumerate(args):
            if isinstance(arg, (list, tuple)) and len(arg) > chunk_size:
                # Process in chunks
                for j in range(0, len(arg), chunk_size):
                    chunk = arg[j:j + chunk_size]
                    new_args = list(args)
                    new_args[i] = chunk
                    
                    result = await operation_func(*tuple(new_args), **kwargs)
                    results.append(result)
                
                # Combine results
                return [item for sublist in results for item in sublist]
        
        # No large data found, process normally
        return await operation_func(*args, **kwargs)
    
    def _calculate_improvement(
        self,
        baseline: PerformanceProfile,
        optimized: PerformanceProfile,
        target: OptimizationTarget
    ) -> float:
        """Calculate improvement percentage for optimization target."""
        if target == OptimizationTarget.THROUGHPUT:
            if baseline.throughput > 0:
                return ((optimized.throughput - baseline.throughput) / baseline.throughput) * 100
        elif target == OptimizationTarget.LATENCY:
            if baseline.latency_p95 > 0:
                return ((baseline.latency_p95 - optimized.latency_p95) / baseline.latency_p95) * 100
        elif target == OptimizationTarget.MEMORY_EFFICIENCY:
            if baseline.memory_usage > 0:
                return ((baseline.memory_usage - optimized.memory_usage) / baseline.memory_usage) * 100
        elif target == OptimizationTarget.CPU_UTILIZATION:
            if baseline.cpu_usage > 0:
                return ((baseline.cpu_usage - optimized.cpu_usage) / baseline.cpu_usage) * 100
        
        return 0.0
    
    def _profile_to_metrics(self, profile: PerformanceProfile) -> Dict[str, float]:
        """Convert performance profile to metrics dictionary."""
        return {
            "execution_time": profile.execution_time,
            "memory_usage": profile.memory_usage,
            "cpu_usage": profile.cpu_usage,
            "gpu_usage": profile.gpu_usage,
            "throughput": profile.throughput,
            "latency_p95": profile.latency_p95,
            "error_rate": profile.error_rate
        }
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        if not self.optimization_results:
            return {"status": "no_optimizations"}
        
        # Group results by target
        results_by_target = defaultdict(list)
        for result in self.optimization_results:
            results_by_target[result.target.value].append(result)
        
        # Calculate summary statistics
        summary = {}
        for target, results in results_by_target.items():
            improvements = [r.improvement_percentage for r in results]
            summary[target] = {
                "total_optimizations": len(results),
                "average_improvement": statistics.mean(improvements),
                "best_improvement": max(improvements),
                "total_operations_optimized": len(set(r.strategy_applied for r in results))
            }
        
        # Cache statistics
        cache_stats = self.cache.get_stats()
        
        # Auto-scaling history
        scaling_events = len(self.auto_scaler.scaling_history)
        
        return {
            "optimization_summary": summary,
            "cache_performance": cache_stats,
            "auto_scaling_events": scaling_events,
            "total_optimizations": len(self.optimization_results),
            "active_background_tasks": len(self.concurrency_manager.get_active_tasks()),
            "recommendations": self._generate_optimization_recommendations()
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on results."""
        recommendations = []
        
        # Cache recommendations
        cache_stats = self.cache.get_stats()
        if cache_stats["hit_rate"] < 0.8:
            recommendations.append("Consider increasing cache size or improving cache key strategy")
        
        # Performance recommendations
        if self.optimization_results:
            avg_improvement = statistics.mean([r.improvement_percentage for r in self.optimization_results])
            if avg_improvement < 10:
                recommendations.append("Consider more aggressive optimization strategies")
        
        # Memory recommendations
        recent_profiles = [r.after_metrics for r in self.optimization_results[-10:]]
        if recent_profiles:
            avg_memory = statistics.mean([p.get("memory_usage", 0) for p in recent_profiles])
            if avg_memory > 2000:  # > 2GB
                recommendations.append("Consider implementing memory streaming for large operations")
        
        return recommendations
    
    async def shutdown(self) -> None:
        """Shutdown the performance optimizer."""
        await self.concurrency_manager.shutdown()


# Global performance optimizer instance
performance_optimizer = AdvancedPerformanceOptimizer()


async def optimize_for_throughput(
    operation_name: str, operation_func: Callable, *args, **kwargs
) -> Tuple[Any, OptimizationResult]:
    """Optimize operation for maximum throughput."""
    return await performance_optimizer.optimize_operation(
        operation_name, operation_func, OptimizationTarget.THROUGHPUT, *args, **kwargs
    )


async def optimize_for_latency(
    operation_name: str, operation_func: Callable, *args, **kwargs
) -> Tuple[Any, OptimizationResult]:
    """Optimize operation for minimum latency."""
    return await performance_optimizer.optimize_operation(
        operation_name, operation_func, OptimizationTarget.LATENCY, *args, **kwargs
    )


def get_performance_optimizer() -> AdvancedPerformanceOptimizer:
    """Get the global performance optimizer instance."""
    return performance_optimizer