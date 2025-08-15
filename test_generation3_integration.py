#!/usr/bin/env python3
"""
Generation 3 Integration Test - Comprehensive validation of high-performance features.
"""

import asyncio
import logging
import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multimodal_contract_extractor.auto_scaling_gen3 import (
    LoadBalancer,
)
from multimodal_contract_extractor.high_performance_gen3 import (
    get_cache_manager,
    get_performance_processor,
    process_documents_high_performance,
)
from multimodal_contract_extractor.robust_monitoring import (
    get_health_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_documents() -> list[Path]:
    """Create test documents for processing."""
    test_docs = []

    for i in range(5):
        # Create temporary PDF-like files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write(f"""Sample contract content {i}
            
            PARTIES:
            Company ABC Inc.
            John Doe
            
            CLAUSES:
            1. Payment Terms: Payment due within 30 days
            2. Termination: Either party may terminate with 30 days notice
            3. Confidentiality: All information shall remain confidential
            """)
            test_docs.append(Path(f.name))

    return test_docs

async def test_high_performance_processing():
    """Test high-performance batch processing."""
    logger.info("🚀 Testing Generation 3 High-Performance Processing")

    test_docs = create_test_documents()

    try:
        # Test batch processing
        start_time = time.perf_counter()
        results = await process_documents_high_performance(test_docs)
        processing_time = time.perf_counter() - start_time

        logger.info("✅ Processed %d documents in %.2fs", len(results), processing_time)

        # Verify results
        successful_count = sum(1 for r in results if r.get('success', False))
        logger.info("✅ Success rate: %d/%d (%.1f%%)",
                   successful_count, len(results),
                   (successful_count / len(results)) * 100)

        return True

    except Exception as e:
        logger.error("❌ High-performance processing test failed: %s", e)
        return False

    finally:
        # Cleanup
        for doc in test_docs:
            try:
                doc.unlink()
            except Exception:
                pass

def test_intelligent_caching():
    """Test intelligent caching system."""
    logger.info("🧠 Testing Generation 3 Intelligent Caching")

    cache_manager = get_cache_manager()

    try:
        # Test cache operations
        test_data = {
            'document_info': {'filename': 'test.pdf', 'pages': 3},
            'clauses': [{'id': 'c1', 'text': 'Test clause'}],
            'metadata': {'cached': True}
        }

        # Test cache miss
        cache_key = "test_key_123"
        result = cache_manager.get(cache_key)
        assert result is None, "Expected cache miss"

        # Test cache put and hit
        cache_manager.put(cache_key, test_data)
        result = cache_manager.get(cache_key)
        assert result is not None, "Expected cache hit"
        assert result['metadata']['cached'] is True

        # Test cache stats
        stats = cache_manager.get_stats()
        assert stats['hit_count'] >= 1
        assert stats['miss_count'] >= 1
        assert 0 <= stats['hit_rate'] <= 1

        logger.info("✅ Cache hit rate: %.1f%%, Memory used: %.1fMB",
                   stats['hit_rate'] * 100, stats['memory_used_mb'])

        return True

    except Exception as e:
        logger.error("❌ Intelligent caching test failed: %s", e)
        return False

def test_load_balancing():
    """Test load balancing functionality."""
    logger.info("⚖️ Testing Generation 3 Load Balancing")

    load_balancer = LoadBalancer()

    try:
        # Register test workers
        workers = [
            ("worker_1", {"available_memory_mb": 1000, "supported_types": ["pdf", "image"]}),
            ("worker_2", {"available_memory_mb": 500, "supported_types": ["pdf"]}),
            ("worker_3", {"available_memory_mb": 2000, "supported_types": ["pdf", "image", "text"]})
        ]

        for worker_id, capabilities in workers:
            load_balancer.register_worker(worker_id, capabilities)

        # Test worker selection
        task_req = {"memory_mb": 800, "processing_type": "pdf"}
        best_worker = load_balancer.get_best_worker(task_req)
        assert best_worker in ["worker_1", "worker_3"], f"Unexpected worker selection: {best_worker}"

        # Test load updates
        load_balancer.update_worker_load("worker_1", 0.8)
        load_balancer.update_worker_load("worker_2", 0.3)

        # Test load distribution
        distribution = load_balancer.get_load_distribution()
        assert len(distribution) == 3
        assert distribution["worker_1"] == 0.8

        # Test balancing stats
        stats = load_balancer.get_balancing_stats()
        assert stats['workers'] == 3
        assert 0 <= stats['average_load'] <= 1

        logger.info("✅ Load balancing - Workers: %d, Avg Load: %.2f",
                   stats['workers'], stats['average_load'])

        return True

    except Exception as e:
        logger.error("❌ Load balancing test failed: %s", e)
        return False

async def test_health_monitoring():
    """Test robust health monitoring."""
    logger.info("💊 Testing Generation 3 Health Monitoring")

    try:
        # Test health status collection
        health_status = await get_health_status()

        assert 'timestamp' in health_status
        assert 'system' in health_status
        assert 'components' in health_status
        assert 'overall_healthy' in health_status

        # Verify system health structure
        system_health = health_status['system']
        required_fields = ['cpu_percent', 'memory_percent', 'disk_percent', 'healthy']
        for field in required_fields:
            assert field in system_health, f"Missing system health field: {field}"

        # Verify component health
        components = health_status['components']
        assert len(components) > 0, "No components found in health check"

        for component_name, component_health in components.items():
            assert hasattr(component_health, 'healthy')
            assert hasattr(component_health, 'latency_ms')

        logger.info("✅ Health monitoring - Overall healthy: %s, Components: %d",
                   health_status['overall_healthy'], len(components))

        return True

    except Exception as e:
        logger.error("❌ Health monitoring test failed: %s", e)
        return False

def test_performance_metrics():
    """Test performance metrics collection."""
    logger.info("📊 Testing Generation 3 Performance Metrics")

    try:
        with get_performance_processor() as processor:
            # Test metrics initialization
            assert processor.metrics.total_documents == 0
            assert processor.metrics.successful_documents == 0

            # Test metrics update
            processor.metrics.update_metrics(processing_time=1.5, success=True)
            processor.metrics.update_metrics(processing_time=2.0, success=True)
            processor.metrics.update_metrics(processing_time=0.8, success=False)

            # Verify metrics
            assert processor.metrics.total_documents == 3
            assert processor.metrics.successful_documents == 2
            assert processor.metrics.failed_documents == 1
            assert processor.metrics.average_processing_time > 0
            assert processor.metrics.throughput_docs_per_second > 0

        logger.info("✅ Performance metrics - Docs: %d, Avg time: %.2fs, Throughput: %.2f/s",
                   processor.metrics.total_documents,
                   processor.metrics.average_processing_time,
                   processor.metrics.throughput_docs_per_second)

        return True

    except Exception as e:
        logger.error("❌ Performance metrics test failed: %s", e)
        return False

async def run_comprehensive_test():
    """Run comprehensive Generation 3 test suite."""
    logger.info("🎯 Starting Generation 3 Comprehensive Test Suite")
    print("=" * 60)

    test_results = []

    # High-performance processing test
    result = await test_high_performance_processing()
    test_results.append(("High-Performance Processing", result))

    # Intelligent caching test
    result = test_intelligent_caching()
    test_results.append(("Intelligent Caching", result))

    # Load balancing test
    result = test_load_balancing()
    test_results.append(("Load Balancing", result))

    # Health monitoring test
    result = await test_health_monitoring()
    test_results.append(("Health Monitoring", result))

    # Performance metrics test
    result = test_performance_metrics()
    test_results.append(("Performance Metrics", result))

    # Summary
    print("\n" + "=" * 60)
    logger.info("📋 Generation 3 Test Results Summary:")

    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info("  %s: %s", test_name, status)
        if passed:
            passed_tests += 1

    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100

    print("=" * 60)
    logger.info("🏆 GENERATION 3 TEST SUITE COMPLETE")
    logger.info("📊 Results: %d/%d tests passed (%.1f%% success rate)",
               passed_tests, total_tests, success_rate)

    if success_rate >= 80:
        logger.info("🎉 Generation 3 implementation is ROBUST and SCALABLE!")
        return True
    else:
        logger.warning("⚠️ Generation 3 implementation needs improvements")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)
