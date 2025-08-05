"""
Performance analytics and optimization system for Generation 3 scaling.

This module provides real-time performance monitoring, automated performance tuning,
bottleneck detection, resource usage analytics, and performance regression testing.
"""

import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class PerformanceCategory(Enum):
    """Performance analysis categories."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    CACHE_EFFICIENCY = "cache_efficiency"


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    LOCK_CONTENTION = "lock_contention"
    CACHE_MISS = "cache_miss"
    QUEUE_SATURATION = "queue_saturation"


class OptimizationRecommendation(Enum):
    """Optimization recommendations."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    INCREASE_CACHE = "increase_cache"
    REDUCE_BATCH_SIZE = "reduce_batch_size"
    INCREASE_BATCH_SIZE = "increase_batch_size"
    ENABLE_COMPRESSION = "enable_compression"
    OPTIMIZE_QUERIES = "optimize_queries"
    ADD_WORKERS = "add_workers"
    REMOVE_WORKERS = "remove_workers"
    TUNE_GC = "tune_gc"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    category: PerformanceCategory = PerformanceCategory.LATENCY
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        data = asdict(self)
        data['category'] = self.category.value
        return data


@dataclass
class PerformanceProfile:
    """Performance profile for a specific operation."""

    operation_name: str
    duration: float
    cpu_time: float
    memory_peak: float
    cache_hits: int = 0
    cache_misses: int = 0
    network_bytes: int = 0
    disk_reads: int = 0
    disk_writes: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark profile as finished."""
        self.end_time = time.time()
        self.success = success
        self.error_message = error_message

    @property
    def is_finished(self) -> bool:
        """Check if profile is finished."""
        return self.end_time is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)


@dataclass
class BottleneckAnalysis:
    """Bottleneck analysis result."""

    bottleneck_type: BottleneckType
    severity: float  # 0-1, higher is more severe
    affected_operations: List[str]
    evidence: Dict[str, Any]
    recommendations: List[OptimizationRecommendation]
    confidence: float  # 0-1, higher is more confident

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        data = asdict(self)
        data['bottleneck_type'] = self.bottleneck_type.value
        data['recommendations'] = [r.value for r in self.recommendations]
        return data


class PerformanceProfiler:
    """Performance profiler for detailed operation analysis."""

    def __init__(self):
        self._active_profiles: Dict[str, PerformanceProfile] = {}
        self._completed_profiles: deque = deque(maxlen=1000)
        self._lock = threading.RLock()

    def start_profile(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a performance profile."""
        profile_id = f"{operation_name}_{int(time.time() * 1000000)}"

        profile = PerformanceProfile(
            operation_name=operation_name,
            duration=0.0,
            cpu_time=0.0,
            memory_peak=self._get_memory_usage(),
            metadata=metadata or {}
        )

        with self._lock:
            self._active_profiles[profile_id] = profile

        return profile_id

    def end_profile(self, profile_id: str, success: bool = True, error_message: Optional[str] = None) -> Optional[PerformanceProfile]:
        """End a performance profile."""
        with self._lock:
            if profile_id not in self._active_profiles:
                return None

            profile = self._active_profiles[profile_id]
            profile.duration = time.time() - profile.start_time
            profile.memory_peak = max(profile.memory_peak, self._get_memory_usage())
            profile.finish(success, error_message)

            # Move to completed profiles
            del self._active_profiles[profile_id]
            self._completed_profiles.append(profile)

            return profile

    def profile_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Decorator for profiling operations."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                profile_id = self.start_profile(operation_name, metadata)

                try:
                    result = func(*args, **kwargs)
                    self.end_profile(profile_id, success=True)
                    return result
                except Exception as e:
                    self.end_profile(profile_id, success=False, error_message=str(e))
                    raise

            return wrapper
        return decorator

    def get_operation_stats(self, operation_name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a specific operation."""
        cutoff_time = time.time() - (window_minutes * 60)

        with self._lock:
            relevant_profiles = [
                p for p in self._completed_profiles
                if p.operation_name == operation_name and p.start_time > cutoff_time
            ]

        if not relevant_profiles:
            return {'operation_name': operation_name, 'sample_count': 0}

        durations = [p.duration for p in relevant_profiles]
        success_count = sum(1 for p in relevant_profiles if p.success)

        return {
            'operation_name': operation_name,
            'sample_count': len(relevant_profiles),
            'success_rate': success_count / len(relevant_profiles),
            'avg_duration': statistics.mean(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50_duration': statistics.median(durations),
            'p95_duration': self._percentile(durations, 0.95),
            'p99_duration': self._percentile(durations, 0.99),
            'avg_memory_peak': statistics.mean(p.memory_peak for p in relevant_profiles),
            'total_cache_hits': sum(p.cache_hits for p in relevant_profiles),
            'total_cache_misses': sum(p.cache_misses for p in relevant_profiles)
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


class MetricsCollector:
    """Real-time metrics collection system."""

    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=3600))  # 1 hour at 1s intervals
        self._collectors: List[Callable[[], List[PerformanceMetric]]] = []
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def add_collector(self, collector: Callable[[], List[PerformanceMetric]]) -> None:
        """Add a metrics collector function."""
        self._collectors.append(collector)

    def start_collection(self) -> None:
        """Start metrics collection."""
        if self._collecting:
            return

        self._collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        logger.info("Metrics collection started")

    def stop_collection(self) -> None:
        """Stop metrics collection."""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)
        logger.info("Metrics collection stopped")

    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a single metric."""
        with self._lock:
            self._metrics[metric.name].append(metric)

    def get_metrics(self, metric_name: str, window_minutes: int = 5) -> List[PerformanceMetric]:
        """Get metrics for a specific name within time window."""
        cutoff_time = time.time() - (window_minutes * 60)

        with self._lock:
            if metric_name not in self._metrics:
                return []

            return [m for m in self._metrics[metric_name] if m.timestamp > cutoff_time]

    def get_metric_summary(self, metric_name: str, window_minutes: int = 5) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        metrics = self.get_metrics(metric_name, window_minutes)

        if not metrics:
            return {'metric_name': metric_name, 'sample_count': 0}

        values = [m.value for m in metrics]

        return {
            'metric_name': metric_name,
            'sample_count': len(metrics),
            'avg_value': statistics.mean(values),
            'min_value': min(values),
            'max_value': max(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'latest_value': metrics[-1].value,
            'trend': self._calculate_trend(values)
        }

    def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._collecting:
            try:
                start_time = time.time()

                # Collect from all registered collectors
                for collector in self._collectors:
                    try:
                        metrics = collector()
                        for metric in metrics:
                            self.record_metric(metric)
                    except Exception as e:
                        logger.error(f"Metrics collector failed: {e}")

                # Sleep for remaining interval time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.collection_interval - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Metrics collection loop error: {e}")
                time.sleep(self.collection_interval)

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for values."""
        if len(values) < 2:
            return "stable"

        # Simple trend calculation using first and last values
        first_third = values[:len(values)//3] if len(values) >= 3 else values[:1]
        last_third = values[-len(values)//3:] if len(values) >= 3 else values[-1:]

        avg_first = statistics.mean(first_third)
        avg_last = statistics.mean(last_third)

        change_percent = ((avg_last - avg_first) / avg_first) * 100 if avg_first != 0 else 0

        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"


class BottleneckDetector:
    """Automated bottleneck detection system."""

    def __init__(self, profiler: PerformanceProfiler, metrics_collector: MetricsCollector):
        self.profiler = profiler
        self.metrics_collector = metrics_collector
        self._detection_rules: List[Callable[[], Optional[BottleneckAnalysis]]] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default bottleneck detection rules."""
        self._detection_rules.extend([
            self._detect_cpu_bottleneck,
            self._detect_memory_bottleneck,
            self._detect_io_bottleneck,
            self._detect_cache_bottleneck,
            self._detect_queue_bottleneck
        ])

    def detect_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Run bottleneck detection and return findings."""
        bottlenecks = []

        for rule in self._detection_rules:
            try:
                analysis = rule()
                if analysis:
                    bottlenecks.append(analysis)
            except Exception as e:
                logger.error(f"Bottleneck detection rule failed: {e}")

        # Sort by severity (highest first)
        bottlenecks.sort(key=lambda x: x.severity, reverse=True)

        return bottlenecks

    def _detect_cpu_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Detect CPU-bound bottlenecks."""
        cpu_metrics = self.metrics_collector.get_metrics("cpu_usage", window_minutes=5)

        if not cpu_metrics:
            return None

        avg_cpu = statistics.mean(m.value for m in cpu_metrics)

        if avg_cpu > 85:  # High CPU usage
            # Check if operations are CPU-intensive
            slow_operations = []

            # This would analyze operation profiles to find CPU-bound operations
            # For now, using simplified detection

            return BottleneckAnalysis(
                bottleneck_type=BottleneckType.CPU_BOUND,
                severity=min(1.0, avg_cpu / 100.0),
                affected_operations=slow_operations,
                evidence={'avg_cpu_usage': avg_cpu, 'sample_count': len(cpu_metrics)},
                recommendations=[OptimizationRecommendation.SCALE_UP, OptimizationRecommendation.ADD_WORKERS],
                confidence=0.8
            )

        return None

    def _detect_memory_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Detect memory-bound bottlenecks."""
        memory_metrics = self.metrics_collector.get_metrics("memory_usage", window_minutes=5)

        if not memory_metrics:
            return None

        avg_memory = statistics.mean(m.value for m in memory_metrics)

        if avg_memory > 80:  # High memory usage
            return BottleneckAnalysis(
                bottleneck_type=BottleneckType.MEMORY_BOUND,
                severity=min(1.0, avg_memory / 100.0),
                affected_operations=[],
                evidence={'avg_memory_usage': avg_memory, 'sample_count': len(memory_metrics)},
                recommendations=[OptimizationRecommendation.TUNE_GC, OptimizationRecommendation.REDUCE_BATCH_SIZE],
                confidence=0.7
            )

        return None

    def _detect_io_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Detect I/O-bound bottlenecks."""
        # This would analyze disk I/O metrics
        # Simplified implementation
        return None

    def _detect_cache_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Detect cache efficiency issues."""
        cache_hit_metrics = self.metrics_collector.get_metrics("cache_hit_rate", window_minutes=10)

        if not cache_hit_metrics:
            return None

        avg_hit_rate = statistics.mean(m.value for m in cache_hit_metrics)

        if avg_hit_rate < 0.6:  # Low cache hit rate
            return BottleneckAnalysis(
                bottleneck_type=BottleneckType.CACHE_MISS,
                severity=1.0 - avg_hit_rate,
                affected_operations=[],
                evidence={'avg_cache_hit_rate': avg_hit_rate, 'sample_count': len(cache_hit_metrics)},
                recommendations=[OptimizationRecommendation.INCREASE_CACHE],
                confidence=0.9
            )

        return None

    def _detect_queue_bottleneck(self) -> Optional[BottleneckAnalysis]:
        """Detect queue saturation issues."""
        queue_metrics = self.metrics_collector.get_metrics("queue_depth", window_minutes=5)

        if not queue_metrics:
            return None

        avg_queue_depth = statistics.mean(m.value for m in queue_metrics)
        max_queue_depth = max(m.value for m in queue_metrics)

        if avg_queue_depth > 50 or max_queue_depth > 100:  # High queue depth
            return BottleneckAnalysis(
                bottleneck_type=BottleneckType.QUEUE_SATURATION,
                severity=min(1.0, avg_queue_depth / 100.0),
                affected_operations=[],
                evidence={
                    'avg_queue_depth': avg_queue_depth,
                    'max_queue_depth': max_queue_depth,
                    'sample_count': len(queue_metrics)
                },
                recommendations=[OptimizationRecommendation.ADD_WORKERS, OptimizationRecommendation.SCALE_UP],
                confidence=0.8
            )

        return None


class PerformanceOptimizer:
    """Automated performance optimization system."""

    def __init__(self, bottleneck_detector: BottleneckDetector):
        self.bottleneck_detector = bottleneck_detector
        self._optimization_history: List[Dict[str, Any]] = []
        self._optimization_callbacks: Dict[OptimizationRecommendation, Callable] = {}

    def register_optimization_callback(
        self,
        recommendation: OptimizationRecommendation,
        callback: Callable[[BottleneckAnalysis], bool]
    ) -> None:
        """Register callback for optimization recommendation."""
        self._optimization_callbacks[recommendation] = callback

    def run_optimization_cycle(self) -> Dict[str, Any]:
        """Run a complete optimization cycle."""
        start_time = time.time()

        # Detect bottlenecks
        bottlenecks = self.bottleneck_detector.detect_bottlenecks()

        optimizations_applied = []

        # Apply optimizations for significant bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity > 0.5 and bottleneck.confidence > 0.6:
                applied = self._apply_optimizations(bottleneck)
                optimizations_applied.extend(applied)

        # Record optimization cycle
        cycle_result = {
            'timestamp': start_time,
            'duration': time.time() - start_time,
            'bottlenecks_detected': len(bottlenecks),
            'bottlenecks_analyzed': [b.to_dict() for b in bottlenecks],
            'optimizations_applied': optimizations_applied
        }

        self._optimization_history.append(cycle_result)

        logger.info(f"Optimization cycle completed: {len(bottlenecks)} bottlenecks detected, "
                   f"{len(optimizations_applied)} optimizations applied")

        return cycle_result

    def _apply_optimizations(self, bottleneck: BottleneckAnalysis) -> List[Dict[str, Any]]:
        """Apply optimizations for a specific bottleneck."""
        applied_optimizations = []

        for recommendation in bottleneck.recommendations:
            if recommendation in self._optimization_callbacks:
                try:
                    callback = self._optimization_callbacks[recommendation]
                    success = callback(bottleneck)

                    applied_optimizations.append({
                        'recommendation': recommendation.value,
                        'bottleneck_type': bottleneck.bottleneck_type.value,
                        'success': success,
                        'timestamp': time.time()
                    })

                    if success:
                        logger.info(f"Applied optimization: {recommendation.value} for {bottleneck.bottleneck_type.value}")
                    else:
                        logger.warning(f"Failed to apply optimization: {recommendation.value}")

                except Exception as e:
                    logger.error(f"Optimization callback failed for {recommendation.value}: {e}")
                    applied_optimizations.append({
                        'recommendation': recommendation.value,
                        'bottleneck_type': bottleneck.bottleneck_type.value,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    })

        return applied_optimizations

    def get_optimization_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent optimization history."""
        return self._optimization_history[-limit:]


class PerformanceAnalyticsEngine:
    """Main performance analytics engine."""

    def __init__(
        self,
        collection_interval: float = 1.0,
        optimization_interval: float = 300.0  # 5 minutes
    ):
        # Core components
        self.profiler = PerformanceProfiler()
        self.metrics_collector = MetricsCollector(collection_interval)
        self.bottleneck_detector = BottleneckDetector(self.profiler, self.metrics_collector)
        self.optimizer = PerformanceOptimizer(self.bottleneck_detector)

        # Configuration
        self.optimization_interval = optimization_interval

        # State
        self._running = False
        self._optimization_thread: Optional[threading.Thread] = None

        # Setup default metrics collectors
        self._setup_default_collectors()

    def _setup_default_collectors(self) -> None:
        """Setup default system metrics collectors."""

        def collect_system_metrics() -> List[PerformanceMetric]:
            """Collect basic system metrics."""
            metrics = []

            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                metrics.append(PerformanceMetric(
                    name="cpu_usage",
                    value=cpu_percent,
                    unit="percent",
                    category=PerformanceCategory.RESOURCE_USAGE
                ))

                # Memory usage
                memory = psutil.virtual_memory()
                metrics.append(PerformanceMetric(
                    name="memory_usage",
                    value=memory.percent,
                    unit="percent",
                    category=PerformanceCategory.RESOURCE_USAGE
                ))

                # Disk usage
                disk = psutil.disk_usage('/')
                metrics.append(PerformanceMetric(
                    name="disk_usage",
                    value=disk.percent if hasattr(disk, 'percent') else (disk.used / disk.total) * 100,
                    unit="percent",
                    category=PerformanceCategory.RESOURCE_USAGE
                ))

            except Exception as e:
                logger.error(f"System metrics collection failed: {e}")

            return metrics

        self.metrics_collector.add_collector(collect_system_metrics)

    def start(self) -> None:
        """Start the performance analytics engine."""
        if self._running:
            return

        self._running = True

        # Start metrics collection
        self.metrics_collector.start_collection()

        # Start optimization loop
        self._optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self._optimization_thread.start()

        logger.info("Performance analytics engine started")

    def stop(self) -> None:
        """Stop the performance analytics engine."""
        if not self._running:
            return

        self._running = False

        # Stop metrics collection
        self.metrics_collector.stop_collection()

        # Stop optimization thread
        if self._optimization_thread:
            self._optimization_thread.join(timeout=10.0)

        logger.info("Performance analytics engine stopped")

    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self._running:
            try:
                self.optimizer.run_optimization_cycle()
                time.sleep(self.optimization_interval)

            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                time.sleep(self.optimization_interval)

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics report."""
        # Collect current bottlenecks
        bottlenecks = self.bottleneck_detector.detect_bottlenecks()

        # Get key metrics summaries
        key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        metrics_summaries = {}

        for metric_name in key_metrics:
            summary = self.metrics_collector.get_metric_summary(metric_name, window_minutes=30)
            if summary['sample_count'] > 0:
                metrics_summaries[metric_name] = summary

        # Get optimization history
        optimization_history = self.optimizer.get_optimization_history(10)

        return {
            'timestamp': time.time(),
            'system_health': {
                'bottlenecks_detected': len(bottlenecks),
                'critical_bottlenecks': len([b for b in bottlenecks if b.severity > 0.8]),
                'bottlenecks': [b.to_dict() for b in bottlenecks]
            },
            'performance_metrics': metrics_summaries,
            'optimization_summary': {
                'recent_optimizations': len(optimization_history),
                'optimization_history': optimization_history
            },
            'recommendations': self._generate_recommendations(bottlenecks, metrics_summaries)
        }

    def _generate_recommendations(
        self,
        bottlenecks: List[BottleneckAnalysis],
        metrics_summaries: Dict[str, Any]
    ) -> List[str]:
        """Generate high-level performance recommendations."""
        recommendations = []

        # Analyze bottlenecks
        if bottlenecks:
            critical_bottlenecks = [b for b in bottlenecks if b.severity > 0.8]
            if critical_bottlenecks:
                recommendations.append(
                    f"Critical performance issues detected: {len(critical_bottlenecks)} bottlenecks require immediate attention"
                )

        # Analyze metrics trends
        for metric_name, summary in metrics_summaries.items():
            if summary['trend'] == 'increasing' and summary['latest_value'] > 80:
                recommendations.append(f"High {metric_name.replace('_', ' ')}: {summary['latest_value']:.1f}% - consider scaling resources")

        # General recommendations
        if not recommendations:
            recommendations.append("System performance is within normal parameters")

        return recommendations


# Global performance analytics engine
_analytics_engine: Optional[PerformanceAnalyticsEngine] = None


def get_performance_analytics(
    collection_interval: float = 1.0,
    optimization_interval: float = 300.0
) -> PerformanceAnalyticsEngine:
    """Get global performance analytics engine."""
    global _analytics_engine

    if _analytics_engine is None:
        _analytics_engine = PerformanceAnalyticsEngine(collection_interval, optimization_interval)

    return _analytics_engine


# Convenience decorators
def profile_performance(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for profiling function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            engine = get_performance_analytics()
            profiler = engine.profiler

            profile_id = profiler.start_profile(operation_name, metadata)

            try:
                result = func(*args, **kwargs)
                profiler.end_profile(profile_id, success=True)
                return result
            except Exception as e:
                profiler.end_profile(profile_id, success=False, error_message=str(e))
                raise

        return wrapper
    return decorator


def track_metric(metric_name: str, category: PerformanceCategory = PerformanceCategory.LATENCY):
    """Decorator for tracking custom metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)

                # Record successful execution time
                duration = time.perf_counter() - start_time
                engine = get_performance_analytics()

                metric = PerformanceMetric(
                    name=metric_name,
                    value=duration,
                    unit="seconds",
                    category=category
                )

                engine.metrics_collector.record_metric(metric)

                return result

            except Exception:
                # Record error metric
                engine = get_performance_analytics()

                error_metric = PerformanceMetric(
                    name=f"{metric_name}_errors",
                    value=1,
                    unit="count",
                    category=PerformanceCategory.ERROR_RATE
                )

                engine.metrics_collector.record_metric(error_metric)
                raise

        return wrapper
    return decorator
