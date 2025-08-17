"""Comprehensive tests for advanced performance optimization framework."""

import asyncio
import time
import pytest

from multimodal_contract_extractor.advanced_performance_optimization import (
    AdaptiveCache,
    AdvancedPerformanceOptimizer,
    AutoScaler,
    CachingStrategy,
    ConcurrencyManager,
    OptimizationResult,
    OptimizationTarget,
    PerformanceProfile,
    PerformanceProfiler,
    get_performance_optimizer,
    optimize_for_latency,
    optimize_for_throughput,
)


class TestAdaptiveCache:
    """Test AdaptiveCache implementation."""

    @pytest.fixture
    def cache(self):
        """Create an adaptive cache for testing."""
        return AdaptiveCache(max_size=5, strategy=CachingStrategy.LRU_CACHE)

    def test_cache_put_and_get(self, cache):
        """Test basic cache put and get operations."""
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self, cache):
        """Test LRU eviction policy."""
        # Fill cache to capacity
        for i in range(5):
            cache.put(f"key{i}", f"value{i}")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add one more item to trigger eviction
        cache.put("key5", "value5")
        
        # key0 should be evicted (least recently used)
        assert cache.get("key0") is None
        assert cache.get("key1") == "value1"  # Should still exist

    def test_lfu_eviction(self):
        """Test LFU eviction policy."""
        cache = AdaptiveCache(max_size=3, strategy=CachingStrategy.LFU_CACHE)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 multiple times
        for _ in range(5):
            cache.get("key1")
        
        # Access key2 fewer times
        for _ in range(2):
            cache.get("key2")
        
        # key3 was accessed only once during put
        # Adding new item should evict key3 (least frequently used)
        cache.put("key4", "value4")
        
        assert cache.get("key3") is None
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_adaptive_eviction(self):
        """Test adaptive eviction strategy."""
        cache = AdaptiveCache(max_size=3, strategy=CachingStrategy.ADAPTIVE_CACHE)
        
        # Add items with different access patterns
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Create different access patterns
        time.sleep(0.01)  # Small delay
        cache.get("key1")  # Recent access
        cache.get("key2")  # Recent access
        # key3 has no recent access
        
        # Add new item to trigger eviction
        cache.put("key4", "value4")
        
        # Adaptive strategy should consider both recency and frequency
        assert cache.get("key4") == "value4"

    def test_cache_stats(self, cache):
        """Test cache statistics tracking."""
        # Test hits and misses
        cache.put("key1", "value1")
        
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 2/3


class TestConcurrencyManager:
    """Test ConcurrencyManager implementation."""

    @pytest.fixture
    def concurrency_manager(self):
        """Create a concurrency manager for testing."""
        return ConcurrencyManager(max_workers=4)

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, concurrency_manager):
        """Test concurrent execution of multiple tasks."""
        async def test_task(value, multiplier=1):
            await asyncio.sleep(0.01)  # Simulate work
            return value * multiplier
        
        tasks = [
            (test_task, (1,), {"multiplier": 2}),
            (test_task, (2,), {"multiplier": 3}),
            (test_task, (3,), {"multiplier": 4}),
            (test_task, (4,), {"multiplier": 5})
        ]
        
        start_time = time.time()
        results = await concurrency_manager.execute_concurrent(tasks)
        execution_time = time.time() - start_time
        
        # Results should be correct
        assert results == [2, 6, 12, 20]
        
        # Should execute concurrently (faster than sequential)
        assert execution_time < 0.04  # Should be much faster than 4 * 0.01

    @pytest.mark.asyncio
    async def test_cpu_intensive_execution(self, concurrency_manager):
        """Test CPU-intensive task execution in process pool."""
        def cpu_intensive_task(n):
            # Simple CPU-intensive calculation
            result = 0
            for i in range(n):
                result += i ** 2
            return result
        
        result = await concurrency_manager.execute_cpu_intensive(cpu_intensive_task, 1000)
        
        # Verify result is correct
        expected = sum(i ** 2 for i in range(1000))
        assert result == expected

    @pytest.mark.asyncio
    async def test_background_task_management(self, concurrency_manager):
        """Test background task submission and management."""
        async def background_task():
            await asyncio.sleep(0.1)
            return "completed"
        
        # Submit background task
        task = concurrency_manager.submit_background_task("test_task", background_task())
        
        # Verify task is tracked
        active_tasks = concurrency_manager.get_active_tasks()
        assert "test_task" in active_tasks
        
        # Wait for completion
        result = await task
        assert result == "completed"
        
        # Task should be cleaned up
        await asyncio.sleep(0.01)  # Small delay for cleanup
        active_tasks = concurrency_manager.get_active_tasks()
        assert "test_task" not in active_tasks

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, concurrency_manager):
        """Test concurrency limiting."""
        call_count = 0
        max_concurrent = 0
        current_concurrent = 0
        
        async def limited_task():
            nonlocal call_count, max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            call_count += 1
            
            await asyncio.sleep(0.05)
            
            current_concurrent -= 1
            return call_count
        
        tasks = [(limited_task, (), {}) for _ in range(10)]
        
        # Limit concurrency to 3
        results = await concurrency_manager.execute_concurrent(tasks, concurrency_limit=3)
        
        # All tasks should complete
        assert len(results) == 10
        
        # Should respect concurrency limit
        assert max_concurrent <= 3


class TestPerformanceProfiler:
    """Test PerformanceProfiler implementation."""

    @pytest.fixture
    def profiler(self):
        """Create a performance profiler for testing."""
        return PerformanceProfiler()

    @pytest.mark.asyncio
    async def test_basic_profiling(self, profiler):
        """Test basic profiling functionality."""
        # Start profiling
        profile_id = await profiler.start_profiling("test_operation", {"env": "test"})
        
        # Simulate operation with requests
        await profiler.record_request(profile_id, 0.1, success=True)
        await profiler.record_request(profile_id, 0.15, success=True)
        await profiler.record_request(profile_id, 0.2, success=False)
        
        # Stop profiling
        profile = await profiler.stop_profiling(profile_id)
        
        # Verify profile results
        assert profile.operation_name == "test_operation"
        assert profile.tags["env"] == "test"
        assert profile.throughput > 0
        assert profile.error_rate == 1/3  # 1 error out of 3 requests
        assert profile.latency_p50 > 0

    @pytest.mark.asyncio
    async def test_multiple_concurrent_profiles(self, profiler):
        """Test multiple concurrent profiling sessions."""
        # Start multiple profiles
        profile1_id = await profiler.start_profiling("operation1")
        profile2_id = await profiler.start_profiling("operation2")
        
        # Record different requests for each
        await profiler.record_request(profile1_id, 0.1)
        await profiler.record_request(profile2_id, 0.2)
        await profiler.record_request(profile1_id, 0.12)
        
        # Stop profiles
        profile1 = await profiler.stop_profiling(profile1_id)
        profile2 = await profiler.stop_profiling(profile2_id)
        
        # Verify profiles are separate
        assert profile1.operation_name == "operation1"
        assert profile2.operation_name == "operation2"
        assert len(profiler.profiles) == 2

    @pytest.mark.asyncio
    async def test_profile_not_found_error(self, profiler):
        """Test error handling for non-existent profile."""
        with pytest.raises(ValueError, match="Profile.*not found"):
            await profiler.stop_profiling("nonexistent_profile")


class TestAutoScaler:
    """Test AutoScaler implementation."""

    @pytest.fixture
    def auto_scaler(self):
        """Create an auto scaler for testing."""
        return AutoScaler()

    @pytest.mark.asyncio
    async def test_scaling_policy_registration(self, auto_scaler):
        """Test scaling policy registration."""
        scale_up_called = False
        scale_down_called = False
        
        def scale_up_action():
            nonlocal scale_up_called
            scale_up_called = True
        
        def scale_down_action():
            nonlocal scale_down_called
            scale_down_called = True
        
        # Register policy
        auto_scaler.register_scaling_policy(
            policy_name="test_policy",
            metric_name="cpu_usage",
            scale_up_threshold=80.0,
            scale_down_threshold=20.0,
            scale_up_action=scale_up_action,
            scale_down_action=scale_down_action,
            cooldown_period=0.1  # Short cooldown for testing
        )
        
        assert "test_policy" in auto_scaler.scaling_policies

    @pytest.mark.asyncio
    async def test_scale_up_trigger(self, auto_scaler):
        """Test scale up trigger."""
        scale_up_triggered = False
        
        def scale_up_action():
            nonlocal scale_up_triggered
            scale_up_triggered = True
        
        def scale_down_action():
            pass
        
        # Register policy with low threshold for testing
        auto_scaler.register_scaling_policy(
            "test_scale_up",
            "cpu_usage",
            scale_up_threshold=50.0,
            scale_down_threshold=10.0,
            scale_up_action=scale_up_action,
            scale_down_action=scale_down_action,
            cooldown_period=0.01
        )
        
        # Send high CPU usage metrics
        for _ in range(5):  # Need multiple data points
            await auto_scaler.update_metric("cpu_usage", 75.0)
            await asyncio.sleep(0.001)
        
        # Wait for evaluation
        await asyncio.sleep(0.02)
        
        assert scale_up_triggered

    @pytest.mark.asyncio
    async def test_scale_down_trigger(self, auto_scaler):
        """Test scale down trigger."""
        scale_down_triggered = False
        
        def scale_up_action():
            pass
        
        def scale_down_action():
            nonlocal scale_down_triggered
            scale_down_triggered = True
        
        # Register policy
        auto_scaler.register_scaling_policy(
            "test_scale_down",
            "cpu_usage",
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            scale_up_action=scale_up_action,
            scale_down_action=scale_down_action,
            cooldown_period=0.01
        )
        
        # Send low CPU usage metrics
        for _ in range(5):
            await auto_scaler.update_metric("cpu_usage", 15.0)
            await asyncio.sleep(0.001)
        
        # Wait for evaluation
        await asyncio.sleep(0.02)
        
        assert scale_down_triggered

    @pytest.mark.asyncio
    async def test_cooldown_period(self, auto_scaler):
        """Test cooldown period prevents rapid scaling."""
        scale_action_count = 0
        
        def scale_action():
            nonlocal scale_action_count
            scale_action_count += 1
        
        # Register policy with longer cooldown
        auto_scaler.register_scaling_policy(
            "cooldown_test",
            "cpu_usage",
            scale_up_threshold=50.0,
            scale_down_threshold=10.0,
            scale_up_action=scale_action,
            scale_down_action=scale_action,
            cooldown_period=0.1  # 100ms cooldown
        )
        
        # Trigger scaling multiple times quickly
        for _ in range(10):
            await auto_scaler.update_metric("cpu_usage", 75.0)
            await asyncio.sleep(0.01)
        
        # Should only scale once due to cooldown
        assert scale_action_count <= 1


class TestAdvancedPerformanceOptimizer:
    """Test AdvancedPerformanceOptimizer implementation."""

    @pytest.fixture
    def optimizer(self):
        """Create a performance optimizer for testing."""
        return AdvancedPerformanceOptimizer()

    @pytest.mark.asyncio
    async def test_throughput_optimization(self, optimizer):
        """Test throughput optimization."""
        call_count = 0
        
        async def test_operation(data_list):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate processing
            return [x * 2 for x in data_list]
        
        # Optimize for throughput
        result, optimization_result = await optimizer.optimize_operation(
            "throughput_test",
            test_operation,
            OptimizationTarget.THROUGHPUT,
            [1, 2, 3, 4, 5]
        )
        
        # Verify results
        assert result == [2, 4, 6, 8, 10]
        assert optimization_result.target == OptimizationTarget.THROUGHPUT
        assert optimization_result.improvement_percentage >= 0

    @pytest.mark.asyncio
    async def test_latency_optimization(self, optimizer):
        """Test latency optimization."""
        async def test_operation(value):
            await asyncio.sleep(0.01)  # Simulate processing
            return value * 2
        
        # Optimize for latency
        result, optimization_result = await optimizer.optimize_operation(
            "latency_test",
            test_operation,
            OptimizationTarget.LATENCY,
            5
        )
        
        # Verify results
        assert result == 10
        assert optimization_result.target == OptimizationTarget.LATENCY

    @pytest.mark.asyncio
    async def test_memory_optimization(self, optimizer):
        """Test memory optimization."""
        async def memory_intensive_operation(data):
            # Simulate memory-intensive operation
            result = []
            for item in data:
                result.append(item ** 2)
            return result
        
        # Large data set to trigger memory optimization
        large_data = list(range(2000))
        
        result, optimization_result = await optimizer.optimize_operation(
            "memory_test",
            memory_intensive_operation,
            OptimizationTarget.MEMORY_EFFICIENCY,
            large_data
        )
        
        # Verify results
        expected = [x ** 2 for x in large_data]
        assert result == expected
        assert optimization_result.target == OptimizationTarget.MEMORY_EFFICIENCY

    @pytest.mark.asyncio
    async def test_caching_optimization(self, optimizer):
        """Test caching in optimization."""
        call_count = 0
        
        async def cacheable_operation(value):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return value * 3
        
        # First call
        result1, _ = await optimizer.optimize_operation(
            "cache_test",
            cacheable_operation,
            OptimizationTarget.THROUGHPUT,
            10
        )
        
        # Second call with same parameters (should use cache)
        result2, _ = await optimizer.optimize_operation(
            "cache_test",
            cacheable_operation,
            OptimizationTarget.THROUGHPUT,
            10
        )
        
        assert result1 == result2 == 30
        # Should be cached for the optimized version
        cache_stats = optimizer.cache.get_stats()
        assert cache_stats["hits"] > 0

    @pytest.mark.asyncio
    async def test_optimization_report(self, optimizer):
        """Test optimization report generation."""
        async def test_operation(value):
            return value * 2
        
        # Perform multiple optimizations
        await optimizer.optimize_operation(
            "test_op1", test_operation, OptimizationTarget.THROUGHPUT, 5
        )
        await optimizer.optimize_operation(
            "test_op2", test_operation, OptimizationTarget.LATENCY, 10
        )
        
        # Generate report
        report = await optimizer.get_optimization_report()
        
        # Verify report structure
        assert "optimization_summary" in report
        assert "cache_performance" in report
        assert "total_optimizations" in report
        assert report["total_optimizations"] == 2


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_optimize_for_throughput(self):
        """Test high-level throughput optimization."""
        async def test_operation(data):
            return [x * 2 for x in data]
        
        result, optimization_result = await optimize_for_throughput(
            "api_throughput_test", test_operation, [1, 2, 3]
        )
        
        assert result == [2, 4, 6]
        assert optimization_result.target == OptimizationTarget.THROUGHPUT

    @pytest.mark.asyncio
    async def test_optimize_for_latency(self):
        """Test high-level latency optimization."""
        async def test_operation(value):
            await asyncio.sleep(0.001)
            return value * 3
        
        result, optimization_result = await optimize_for_latency(
            "api_latency_test", test_operation, 7
        )
        
        assert result == 21
        assert optimization_result.target == OptimizationTarget.LATENCY

    def test_get_performance_optimizer(self):
        """Test getting the global performance optimizer."""
        optimizer = get_performance_optimizer()
        assert isinstance(optimizer, AdvancedPerformanceOptimizer)


class TestEnumerations:
    """Test enumeration values."""

    def test_optimization_target_values(self):
        """Test optimization target enum values."""
        assert OptimizationTarget.THROUGHPUT.value == "throughput"
        assert OptimizationTarget.LATENCY.value == "latency"
        assert OptimizationTarget.MEMORY_EFFICIENCY.value == "memory_efficiency"
        assert OptimizationTarget.CPU_UTILIZATION.value == "cpu_utilization"
        assert OptimizationTarget.GPU_UTILIZATION.value == "gpu_utilization"
        assert OptimizationTarget.COST_EFFICIENCY.value == "cost_efficiency"
        assert OptimizationTarget.ENERGY_EFFICIENCY.value == "energy_efficiency"

    def test_caching_strategy_values(self):
        """Test caching strategy enum values."""
        assert CachingStrategy.LRU_CACHE.value == "lru_cache"
        assert CachingStrategy.LFU_CACHE.value == "lfu_cache"
        assert CachingStrategy.ADAPTIVE_CACHE.value == "adaptive_cache"
        assert CachingStrategy.DISTRIBUTED_CACHE.value == "distributed_cache"
        assert CachingStrategy.HIERARCHICAL_CACHE.value == "hierarchical_cache"
        assert CachingStrategy.PREDICTIVE_CACHE.value == "predictive_cache"


class TestIntegrationScenarios:
    """Test integration scenarios for performance optimization."""

    @pytest.mark.asyncio
    async def test_end_to_end_optimization_pipeline(self):
        """Test complete end-to-end optimization pipeline."""
        optimizer = AdvancedPerformanceOptimizer()
        
        # Complex operation that benefits from multiple optimizations
        async def complex_operation(data_batch, processing_factor=1):
            # Simulate complex processing
            results = []
            for item in data_batch:
                await asyncio.sleep(0.001)  # Simulate work
                result = item * processing_factor + (item ** 2) / 100
                results.append(result)
            return results
        
        # Test data
        test_data = list(range(20))
        
        # Step 1: Optimize for throughput
        throughput_result, throughput_opt = await optimizer.optimize_operation(
            "complex_throughput",
            complex_operation,
            OptimizationTarget.THROUGHPUT,
            test_data,
            processing_factor=2
        )
        
        # Step 2: Optimize for latency
        latency_result, latency_opt = await optimizer.optimize_operation(
            "complex_latency",
            complex_operation,
            OptimizationTarget.LATENCY,
            test_data[:5],  # Smaller batch for latency
            processing_factor=2
        )
        
        # Step 3: Optimize for memory efficiency
        memory_result, memory_opt = await optimizer.optimize_operation(
            "complex_memory",
            complex_operation,
            OptimizationTarget.MEMORY_EFFICIENCY,
            test_data * 100,  # Large data for memory optimization
            processing_factor=1
        )
        
        # Verify all optimizations completed
        assert len(throughput_result) == 20
        assert len(latency_result) == 5
        assert len(memory_result) == 2000
        
        # Generate comprehensive report
        report = await optimizer.get_optimization_report()
        
        assert report["total_optimizations"] == 3
        assert "throughput" in report["optimization_summary"]
        assert "latency" in report["optimization_summary"]
        assert "memory_efficiency" in report["optimization_summary"]

    @pytest.mark.asyncio
    async def test_auto_scaling_integration(self):
        """Test integration with auto-scaling."""
        optimizer = AdvancedPerformanceOptimizer()
        auto_scaler = optimizer.auto_scaler
        
        scaling_actions = []
        
        def scale_up():
            scaling_actions.append("scale_up")
        
        def scale_down():
            scaling_actions.append("scale_down")
        
        # Register scaling policy
        auto_scaler.register_scaling_policy(
            "integration_test",
            "cpu_usage",
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            scale_up_action=scale_up,
            scale_down_action=scale_down,
            cooldown_period=0.01
        )
        
        # Simulate high load triggering scale up
        for _ in range(5):
            await auto_scaler.update_metric("cpu_usage", 80.0)
            await asyncio.sleep(0.001)
        
        await asyncio.sleep(0.02)  # Wait for evaluation
        
        # Verify scale up was triggered
        assert "scale_up" in scaling_actions
        
        # Clear actions and test scale down
        scaling_actions.clear()
        
        # Wait for cooldown
        await asyncio.sleep(0.02)
        
        # Simulate low load triggering scale down
        for _ in range(5):
            await auto_scaler.update_metric("cpu_usage", 20.0)
            await asyncio.sleep(0.001)
        
        await asyncio.sleep(0.02)
        
        # Verify scale down was triggered
        assert "scale_down" in scaling_actions

    @pytest.mark.asyncio
    async def test_concurrent_optimization_and_caching(self):
        """Test concurrent optimization with caching benefits."""
        optimizer = AdvancedPerformanceOptimizer()
        
        # Operation that benefits from caching
        call_count = 0
        
        async def expensive_operation(key, computation_intensity=1):
            nonlocal call_count
            call_count += 1
            
            # Simulate expensive computation
            result = 0
            for i in range(computation_intensity * 100):
                result += hash(f"{key}_{i}") % 1000
            
            await asyncio.sleep(0.01)
            return result
        
        # Run multiple optimizations concurrently
        tasks = []
        
        # Some with same parameters (should benefit from caching)
        for i in range(5):
            task = optimizer.optimize_operation(
                f"concurrent_test_{i}",
                expensive_operation,
                OptimizationTarget.THROUGHPUT,
                "same_key",  # Same key for caching
                computation_intensity=1
            )
            tasks.append(task)
        
        # Some with different parameters
        for i in range(3):
            task = optimizer.optimize_operation(
                f"concurrent_unique_{i}",
                expensive_operation,
                OptimizationTarget.THROUGHPUT,
                f"unique_key_{i}",
                computation_intensity=1
            )
            tasks.append(task)
        
        # Execute all optimizations concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all completed
        assert len(results) == 8
        
        # Check cache effectiveness
        cache_stats = optimizer.cache.get_stats()
        assert cache_stats["hits"] > 0  # Should have cache hits from repeated calls