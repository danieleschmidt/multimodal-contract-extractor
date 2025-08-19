"""
Comprehensive tests for advanced generation systems (Gen 2 & 3).
Testing robust error handling, health checks, security, and performance optimization.
"""
import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import the modules we want to test
import sys
sys.path.insert(0, 'src')

from multimodal_contract_extractor.robust_error_handling import (
    ErrorRecoveryManager, RobustError, ErrorSeverity, ErrorCategory,
    robust_operation, error_context, get_error_manager
)
from multimodal_contract_extractor.advanced_health_checks import (
    HealthMonitor, SystemResourcesChecker, FilesystemChecker,
    DependencyChecker, ApplicationChecker, get_health_monitor
)
from multimodal_contract_extractor.advanced_security_validation import (
    FileSecurityValidator, InputSanitizer, RateLimiter, SecurityManager,
    get_security_manager, ThreatLevel, SecurityViolationType
)
from multimodal_contract_extractor.advanced_performance_optimization_gen3 import (
    AdvancedCache, ParallelProcessor, PerformanceMonitor,
    OptimizedProcessor, get_optimized_processor, cached
)
from multimodal_contract_extractor.load_balancing_orchestrator import (
    LoadBalancer, ProcessingWorker, RequestOrchestrator,
    Request, LoadBalancingStrategy
)


class TestRobustErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    def test_error_classification(self):
        """Test automatic error classification."""
        manager = ErrorRecoveryManager()
        
        # Test network error classification
        network_error = ConnectionError("Connection timeout")
        context = manager.classify_error(network_error)
        assert context.category == ErrorCategory.NETWORK
        
        # Test filesystem error classification
        fs_error = FileNotFoundError("No such file or directory")
        context = manager.classify_error(fs_error)
        assert context.category == ErrorCategory.FILESYSTEM
        
        # Test security error classification
        security_error = Exception("Unauthorized access")
        context = manager.classify_error(security_error)
        assert context.category == ErrorCategory.SECURITY
        assert context.severity == ErrorSeverity.HIGH
    
    def test_robust_error_with_context(self):
        """Test RobustError with context."""
        error = RobustError(
            "Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PROCESSING,
            context={"test": "data"}
        )
        
        assert error.context.message == "Test error"
        assert error.context.severity == ErrorSeverity.HIGH
        assert error.context.category == ErrorCategory.PROCESSING
        assert error.context.details["test"] == "data"
    
    def test_robust_operation_decorator(self):
        """Test robust operation decorator with retries."""
        call_count = 0
        
        @robust_operation(max_retries=2)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3  # Initial call + 2 retries
    
    def test_error_context_manager(self):
        """Test error context manager."""
        with pytest.raises(ValueError):
            with error_context("test_operation", param="value"):
                raise ValueError("Test error")
    
    def test_error_recovery_strategies(self):
        """Test different error recovery strategies."""
        manager = ErrorRecoveryManager()
        
        # Test network retry strategy
        network_error = ConnectionError("Network timeout")
        recovery_attempted = manager.handle_error(network_error)
        # Should attempt recovery for network errors
        assert any(e.recovery_attempted for e in manager.error_history)
    
    def test_error_statistics(self):
        """Test error statistics collection."""
        manager = ErrorRecoveryManager()
        
        # Generate some test errors
        errors = [
            ValueError("Validation error"),
            ConnectionError("Network error"), 
            FileNotFoundError("File error")
        ]
        
        for error in errors:
            manager.handle_error(error)
        
        stats = manager.get_error_stats()
        assert stats["total_errors"] == 3
        assert "categories" in stats
        assert "severities" in stats


class TestAdvancedHealthChecks:
    """Test health monitoring system."""
    
    @pytest.mark.asyncio
    async def test_system_resources_checker(self):
        """Test system resources health checker."""
        checker = SystemResourcesChecker()
        result = await checker.check()
        
        assert result.component == "system_resources"
        assert len(result.metrics) > 0
        
        # Check for expected metrics
        metric_names = [m.name for m in result.metrics]
        assert "cpu_usage" in metric_names
        assert "memory_usage" in metric_names
        assert "disk_usage" in metric_names
    
    @pytest.mark.asyncio
    async def test_filesystem_checker(self):
        """Test filesystem health checker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            checker = FilesystemChecker(paths=[temp_dir])
            result = await checker.check()
            
            assert result.component == "filesystem"
            assert len(result.metrics) > 0
            
            # Should be healthy since temp dir exists and is writable
            assert result.status.value in ["healthy", "warning"]
    
    @pytest.mark.asyncio 
    async def test_dependency_checker(self):
        """Test dependency health checker."""
        checker = DependencyChecker()
        result = await checker.check()
        
        assert result.component == "dependencies"
        assert len(result.metrics) > 0
        
        # Check for package availability metrics
        metric_names = [m.name for m in result.metrics]
        package_metrics = [m for m in metric_names if m.startswith("package_")]
        assert len(package_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_health_monitor_integration(self):
        """Test complete health monitoring system."""
        monitor = HealthMonitor()
        results = await monitor.run_all_checks()
        
        assert len(results) > 0
        assert "system_resources" in results
        assert "filesystem" in results
        assert "dependencies" in results
        
        # Test overall status calculation
        overall_status = monitor.get_overall_status()
        assert overall_status.value in ["healthy", "warning", "degraded", "unhealthy", "critical"]
        
        # Test health summary
        summary = monitor.get_health_summary()
        assert "overall_status" in summary
        assert "components" in summary
        assert "timestamp" in summary
    
    @pytest.mark.asyncio
    async def test_health_monitor_history(self):
        """Test health monitoring history tracking."""
        monitor = HealthMonitor()
        
        # Run checks multiple times
        await monitor.run_all_checks()
        await monitor.run_all_checks()
        
        assert len(monitor.check_history) >= 2
        
        detailed_report = monitor.get_detailed_report()
        assert "history_entries" in detailed_report
        assert detailed_report["history_entries"] >= 2


class TestAdvancedSecurityValidation:
    """Test security validation and threat detection."""
    
    def test_file_security_validator(self):
        """Test file security validation."""
        validator = FileSecurityValidator()
        
        # Test path traversal detection
        threat = validator.validate_file_path("../../../etc/passwd")
        assert threat is not None
        assert threat.violation_type == SecurityViolationType.PATH_TRAVERSAL
        assert threat.blocked is True
        
        # Test invalid extension
        threat = validator.validate_file_path("malicious.exe")
        assert threat is not None
        assert threat.violation_type == SecurityViolationType.INVALID_FORMAT
        assert threat.blocked is True
        
        # Test valid path
        threat = validator.validate_file_path("document.pdf")
        assert threat is None
    
    def test_file_content_validation(self):
        """Test file content security validation."""
        validator = FileSecurityValidator()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            # Write PDF header
            temp_file.write(b"%PDF-1.4\n")
            temp_file.write(b"Normal PDF content here")
            temp_file.flush()
            
            threat = validator.validate_file_content(temp_file.name)
            # Should be None for valid PDF
            assert threat is None
            
            Path(temp_file.name).unlink()  # Clean up
        
        # Test non-existent file
        threat = validator.validate_file_content("nonexistent.pdf")
        assert threat is not None
        assert threat.violation_type == SecurityViolationType.MALICIOUS_FILE
    
    def test_input_sanitizer(self):
        """Test input sanitization and injection detection."""
        sanitizer = InputSanitizer()
        
        # Test string sanitization
        dirty_input = "test\x00string\x1fwith\x7fcontrol chars"
        clean_input = sanitizer.sanitize_string(dirty_input)
        assert "\x00" not in clean_input
        assert "\x1f" not in clean_input
        assert "\x7f" not in clean_input
        
        # Test SQL injection detection
        sql_injection = "'; DROP TABLE users; --"
        threats = sanitizer.detect_injection_attempts(sql_injection)
        assert len(threats) > 0
        assert any(t.violation_type == SecurityViolationType.INJECTION_ATTEMPT for t in threats)
        
        # Test XSS detection
        xss_attempt = "<script>alert('xss')</script>"
        threats = sanitizer.detect_injection_attempts(xss_attempt)
        assert len(threats) > 0
        assert any(t.violation_type == SecurityViolationType.INJECTION_ATTEMPT for t in threats)
    
    def test_rate_limiter(self):
        """Test rate limiting functionality."""
        rate_limiter = RateLimiter(requests_per_minute=2, requests_per_hour=5)
        
        # First request should pass
        threat = rate_limiter.is_rate_limited("client1")
        assert threat is None
        
        # Second request should pass
        threat = rate_limiter.is_rate_limited("client1")
        assert threat is None
        
        # Third request should be rate limited
        threat = rate_limiter.is_rate_limited("client1")
        assert threat is not None
        assert threat.violation_type == SecurityViolationType.RATE_LIMIT_EXCEEDED
        assert threat.blocked is True
    
    def test_security_manager_integration(self):
        """Test integrated security management."""
        manager = SecurityManager()
        
        # Test input validation
        sanitized, threats = manager.sanitize_and_validate_input("normal input")
        assert sanitized == "normal input"
        assert len(threats) == 0
        
        # Test malicious input
        sanitized, threats = manager.sanitize_and_validate_input("'; DROP TABLE users;")
        assert len(threats) > 0
        
        # Test security statistics
        stats = manager.get_security_stats()
        assert "total_threats" in stats


class TestAdvancedPerformanceOptimization:
    """Test performance optimization features."""
    
    def test_advanced_cache(self):
        """Test advanced caching system."""
        cache = AdvancedCache(max_size=3, ttl_seconds=1)
        
        # Test basic set/get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.hits == 1
        
        # Test cache miss
        assert cache.get("nonexistent") is None
        assert cache.misses == 1
        
        # Test TTL expiration
        time.sleep(1.1)  # Wait for TTL to expire
        assert cache.get("key1") is None  # Should be expired
        
        # Test LRU eviction
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict least recently used
        
        assert cache.get("key1") is None  # Should be evicted
        assert cache.get("key4") == "value4"  # Should still exist
    
    def test_cached_decorator(self):
        """Test caching decorator."""
        call_count = 0
        
        @cached(ttl=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Different argument should execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2
    
    def test_parallel_processor(self):
        """Test parallel processing."""
        def square(x):
            return x * x
        
        with ParallelProcessor(max_workers=2) as processor:
            items = [1, 2, 3, 4, 5]
            results = processor.map_parallel(square, items)
            
            expected = [1, 4, 9, 16, 25]
            assert results == expected
    
    @pytest.mark.asyncio
    async def test_async_parallel_processing(self):
        """Test asynchronous parallel processing."""
        async def async_square(x):
            await asyncio.sleep(0.01)  # Simulate async work
            return x * x
        
        with ParallelProcessor(max_workers=2) as processor:
            items = [1, 2, 3, 4, 5]
            results = await processor.map_async(async_square, items, max_concurrency=3)
            
            expected = [1, 4, 9, 16, 25]
            assert results == expected
    
    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        
        # Start and finish an operation
        metrics = monitor.start_operation("test_operation")
        time.sleep(0.1)  # Simulate work
        monitor.finish_operation(metrics)
        
        # Get statistics
        stats = monitor.get_stats("test_operation")
        assert stats["count"] == 1
        assert stats["avg_duration"] > 0
        
        # Test system stats
        system_stats = monitor.get_system_stats()
        assert "cpu_usage" in system_stats
        assert "memory_usage" in system_stats
    
    def test_optimized_processor_integration(self):
        """Test integrated optimized processor."""
        def simple_function(x):
            return x + 1
        
        with OptimizedProcessor(cache_size=100, max_workers=2) as processor:
            # Test cached function execution
            result1 = processor.optimized_function(simple_function, 5, use_cache=True)
            result2 = processor.optimized_function(simple_function, 5, use_cache=True)
            
            assert result1 == 6
            assert result2 == 6
            
            # Test batch processing
            items = [1, 2, 3, 4, 5]
            results = processor.batch_process_optimized(simple_function, items)
            expected = [2, 3, 4, 5, 6]
            assert results == expected
            
            # Get performance report
            report = processor.get_performance_report()
            assert "cache_stats" in report
            assert "performance_stats" in report
            assert "system_stats" in report


class TestLoadBalancingOrchestrator:
    """Test load balancing and request orchestration."""
    
    @pytest.mark.asyncio
    async def test_processing_worker(self):
        """Test processing worker functionality."""
        worker = ProcessingWorker("test_worker", weight=1.0)
        
        request = Request(
            request_id="test_request",
            metadata={"file_size": 1000000}
        )
        
        result = await worker.execute_request(request)
        
        assert result["request_id"] == "test_request"
        assert result["worker_id"] == "test_worker"
        assert "processing_time" in result
        
        # Check metrics were updated
        assert worker.metrics.total_requests == 1
        assert worker.metrics.last_response_time > 0
    
    def test_load_balancer_worker_management(self):
        """Test load balancer worker management."""
        lb = LoadBalancer(strategy=LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add workers
        worker1 = ProcessingWorker("worker1")
        worker2 = ProcessingWorker("worker2")
        
        lb.add_worker(worker1)
        lb.add_worker(worker2)
        
        assert len(lb.workers) == 2
        assert "worker1" in lb.workers
        assert "worker2" in lb.workers
        
        # Remove worker
        lb.remove_worker("worker1")
        assert len(lb.workers) == 1
        assert "worker1" not in lb.workers
    
    def test_load_balancing_strategies(self):
        """Test different load balancing strategies."""
        lb = LoadBalancer(strategy=LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add workers with different loads
        worker1 = ProcessingWorker("worker1")
        worker2 = ProcessingWorker("worker2")
        
        # Simulate different loads
        worker1.metrics.active_requests = 5
        worker2.metrics.active_requests = 2
        
        lb.add_worker(worker1)
        lb.add_worker(worker2)
        
        request = Request()
        
        # Test round robin
        lb.strategy = LoadBalancingStrategy.ROUND_ROBIN
        selected1 = lb.select_worker(request)
        selected2 = lb.select_worker(request)
        assert selected1 != selected2  # Should alternate
        
        # Test least connections
        lb.strategy = LoadBalancingStrategy.LEAST_CONNECTIONS
        selected = lb.select_worker(request)
        assert selected.worker_id == "worker2"  # Should select worker with fewer connections
    
    @pytest.mark.asyncio
    async def test_request_orchestrator(self):
        """Test request orchestrator."""
        lb = LoadBalancer(strategy=LoadBalancingStrategy.ADAPTIVE)
        worker = ProcessingWorker("test_worker")
        lb.add_worker(worker)
        
        orchestrator = RequestOrchestrator(lb, max_queue_size=10)
        
        # Test direct request processing
        request = Request(metadata={"file_size": 500000})
        result = await orchestrator.submit_and_wait(request, timeout=10.0)
        
        assert result["request_id"] == request.request_id
        assert result["worker_id"] == "test_worker"
        
        # Test orchestrator stats
        stats = orchestrator.get_orchestrator_stats()
        assert "queue_size" in stats
        assert "load_balancer" in stats


class TestIntegrationScenarios:
    """Integration tests for complete system scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_processing_pipeline(self):
        """Test complete processing pipeline with all optimizations."""
        # Initialize all components
        security_manager = get_security_manager()
        health_monitor = get_health_monitor()
        optimized_processor = get_optimized_processor()
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\nTest PDF content")
            temp_file.flush()
            
            try:
                # Security validation
                threats = security_manager.validate_file_upload(temp_file.name)
                blocked_threats = [t for t in threats if t.blocked]
                assert len(blocked_threats) == 0  # Should pass security
                
                # Health check
                health_results = await health_monitor.run_all_checks()
                assert len(health_results) > 0
                
                # Performance optimized processing
                def mock_process_file(file_path):
                    return {"processed": True, "file": file_path}
                
                result = optimized_processor.optimized_function(
                    mock_process_file, 
                    temp_file.name,
                    use_cache=True
                )
                
                assert result["processed"] is True
                assert result["file"] == temp_file.name
                
            finally:
                Path(temp_file.name).unlink()  # Clean up
    
    def test_error_handling_across_systems(self):
        """Test error handling integration across different systems."""
        error_manager = get_error_manager()
        security_manager = get_security_manager()
        
        # Simulate various types of errors
        errors = [
            ConnectionError("Network timeout"),
            FileNotFoundError("Missing file"),
            ValueError("Invalid input"),
            PermissionError("Access denied")
        ]
        
        for error in errors:
            recovery_attempted = error_manager.handle_error(error)
            # Should attempt recovery for some error types
            
        # Check error statistics
        stats = error_manager.get_error_stats()
        assert stats["total_errors"] == len(errors)
        
        # Check security stats
        sec_stats = security_manager.get_security_stats()
        # Should have baseline stats even with no security events
        assert "total_threats" in sec_stats
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under simulated load."""
        optimized_processor = get_optimized_processor()
        
        # Simulate processing multiple items
        def cpu_intensive_task(x):
            # Simulate some work
            total = 0
            for i in range(1000):
                total += i * x
            return total
        
        items = list(range(100))  # 100 items to process
        
        start_time = time.time()
        results = optimized_processor.batch_process_optimized(
            cpu_intensive_task, 
            items,
            batch_size=20,
            use_processes=False  # Use threads for this test
        )
        end_time = time.time()
        
        assert len(results) == 100
        assert all(isinstance(r, int) for r in results)
        
        processing_time = end_time - start_time
        assert processing_time < 30  # Should complete within 30 seconds
        
        # Check performance report
        report = optimized_processor.get_performance_report()
        assert "cache_stats" in report
        assert "performance_stats" in report
        
        # Should have cache hits if any repeated operations
        if report["cache_stats"]["hits"] > 0:
            assert report["cache_stats"]["hit_ratio"] > 0


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_advanced_generation_systems.py -v
    pytest.main([__file__, "-v", "--tb=short"])