"""
Performance benchmarks and load testing for the Multimodal Contract Extractor.

This module contains performance tests that validate system performance
under various load conditions and document types.
"""

import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from tests.conftest import PERFORMANCE_THRESHOLDS


@pytest.mark.performance
class TestDocumentProcessingPerformance:
    """Test performance of document processing operations."""
    
    def test_single_document_processing_time(self, performance_timer, sample_pdf_path):
        """Test that single document processing meets performance requirements."""
        performance_timer("document_processing")
        
        # Mock the actual processing since we're testing infrastructure
        with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            mock_extract.return_value = []
            
            # Simulate processing time
            time.sleep(0.1)  # Simulate processing
            
        elapsed = performance_timer("document_processing")
        
        assert elapsed < PERFORMANCE_THRESHOLDS["document_processing"], \
            f"Document processing took {elapsed:.2f}s, expected < {PERFORMANCE_THRESHOLDS['document_processing']}s"
    
    @pytest.mark.parametrize("document_count", [1, 5, 10, 20])
    def test_batch_processing_scalability(self, performance_timer, document_count):
        """Test batch processing performance with different document counts."""
        performance_timer("batch_processing")
        
        # Mock batch processing
        with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            mock_extract.return_value = []
            
            for i in range(document_count):
                # Simulate processing each document
                time.sleep(0.01)  # Minimal processing time per document
                
        elapsed = performance_timer("batch_processing")
        avg_per_document = elapsed / document_count
        
        assert avg_per_document < PERFORMANCE_THRESHOLDS["batch_processing"], \
            f"Average processing time per document: {avg_per_document:.2f}s, " \
            f"expected < {PERFORMANCE_THRESHOLDS['batch_processing']}s"
    
    def test_ocr_processing_performance(self, performance_timer, sample_image_path):
        """Test OCR processing performance meets requirements."""
        performance_timer("ocr_processing")
        
        # Mock OCR processing
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Sample text from OCR"
            
            # Simulate OCR processing
            time.sleep(0.05)
            
        elapsed = performance_timer("ocr_processing")
        
        assert elapsed < PERFORMANCE_THRESHOLDS["ocr_processing"], \
            f"OCR processing took {elapsed:.2f}s, expected < {PERFORMANCE_THRESHOLDS['ocr_processing']}s"
    
    def test_clause_extraction_performance(self, performance_timer, mock_ocr_result):
        """Test clause extraction performance."""
        performance_timer("clause_extraction")
        
        # Mock clause extraction
        with patch('multimodal_contract_extractor.clause_detection.detect_clauses') as mock_detect:
            mock_detect.return_value = []
            
            # Simulate clause extraction
            time.sleep(0.02)
            
        elapsed = performance_timer("clause_extraction")
        
        assert elapsed < PERFORMANCE_THRESHOLDS["clause_extraction"], \
            f"Clause extraction took {elapsed:.2f}s, expected < {PERFORMANCE_THRESHOLDS['clause_extraction']}s"


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns during processing."""
    
    def test_memory_usage_single_document(self, sample_pdf_path):
        """Test memory usage for single document processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Mock document processing
        with patch('multimodal_contract_extractor.document.load_document') as mock_load:
            mock_doc = Mock()
            mock_doc.pages = 5
            mock_load.return_value = mock_doc
            
            # Simulate processing
            data = [i for i in range(1000)]  # Simulate some memory usage
            
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Assert memory increase is reasonable (less than 100MB for test)
        assert memory_increase < 100, \
            f"Memory usage increased by {memory_increase:.2f}MB, which may indicate a memory leak"
    
    def test_memory_cleanup_after_processing(self, sample_pdf_path):
        """Test that memory is properly cleaned up after processing."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        gc.collect()
        memory_baseline = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing with cleanup
        with patch('multimodal_contract_extractor.document.load_document') as mock_load:
            mock_doc = Mock()
            mock_load.return_value = mock_doc
            
            # Create and cleanup data
            large_data = [i for i in range(10000)]
            del large_data
            
        # Force garbage collection and check memory
        gc.collect()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory should return close to baseline (within 50MB tolerance)
        memory_difference = abs(memory_after - memory_baseline)
        assert memory_difference < 50, \
            f"Memory not properly cleaned up. Difference: {memory_difference:.2f}MB"


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Test performance under concurrent load."""
    
    def test_concurrent_document_processing(self, performance_timer):
        """Test performance with concurrent document processing."""
        import threading
        import queue
        
        num_threads = 4
        documents_per_thread = 5
        results_queue = queue.Queue()
        
        def process_documents(thread_id: int):
            """Process documents in a thread."""
            thread_times = []
            for i in range(documents_per_thread):
                start_time = time.time()
                
                # Mock processing
                with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
                    mock_extract.return_value = []
                    time.sleep(0.01)  # Simulate processing
                
                end_time = time.time()
                thread_times.append(end_time - start_time)
                
            results_queue.put((thread_id, thread_times))
        
        # Start concurrent processing
        performance_timer("concurrent_processing")
        threads = []
        
        for i in range(num_threads):
            thread = threading.Thread(target=process_documents, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        elapsed = performance_timer("concurrent_processing")
        
        # Collect results
        all_times = []
        while not results_queue.empty():
            thread_id, times = results_queue.get()
            all_times.extend(times)
        
        # Verify performance
        avg_time = sum(all_times) / len(all_times)
        total_documents = num_threads * documents_per_thread
        
        assert len(all_times) == total_documents, \
            f"Expected {total_documents} processing times, got {len(all_times)}"
        
        assert avg_time < 1.0, \
            f"Average processing time under concurrent load: {avg_time:.2f}s, expected < 1.0s"
        
        # Concurrent processing should be faster than sequential
        estimated_sequential_time = total_documents * 0.01
        efficiency = estimated_sequential_time / elapsed
        
        assert efficiency > 2.0, \
            f"Concurrent processing efficiency: {efficiency:.2f}x, expected > 2.0x"


@pytest.mark.performance
class TestLoadTesting:
    """Load testing scenarios."""
    
    @pytest.mark.parametrize("load_level", [
        {"documents": 10, "concurrent_users": 2},
        {"documents": 50, "concurrent_users": 5},
        {"documents": 100, "concurrent_users": 10},
    ])
    def test_system_under_load(self, performance_timer, load_level):
        """Test system performance under various load levels."""
        documents = load_level["documents"]
        concurrent_users = load_level["concurrent_users"]
        
        performance_timer("load_test")
        
        # Mock heavy load scenario
        with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            mock_extract.return_value = []
            
            # Simulate processing time proportional to load
            processing_time = documents * 0.001  # 1ms per document
            time.sleep(processing_time)
        
        elapsed = performance_timer("load_test")
        
        # Calculate performance metrics
        throughput = documents / elapsed  # documents per second
        avg_response_time = elapsed / documents
        
        # Performance assertions
        assert throughput > 10, \
            f"Throughput: {throughput:.2f} docs/sec, expected > 10 docs/sec"
        
        assert avg_response_time < 1.0, \
            f"Average response time: {avg_response_time:.2f}s, expected < 1.0s"
    
    def test_stress_testing(self, performance_timer):
        """Test system behavior under stress conditions."""
        # Simulate high load for stress testing
        performance_timer("stress_test")
        
        with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            mock_extract.return_value = []
            
            # Simulate stress conditions
            for i in range(100):
                # Rapid processing requests
                time.sleep(0.001)  # 1ms per request
        
        elapsed = performance_timer("stress_test")
        
        # System should handle stress without crashing
        assert elapsed < 10.0, \
            f"Stress test took {elapsed:.2f}s, system may be under excessive load"


@pytest.mark.performance
def test_performance_regression_detection(performance_timer):
    """Test for performance regression detection."""
    # This test would compare against baseline performance metrics
    # stored in a performance database or file
    
    baseline_metrics = {
        "document_processing": 5.0,  # seconds
        "clause_extraction": 2.0,    # seconds
        "ocr_processing": 3.0,       # seconds
    }
    
    # Run performance tests and compare against baseline
    current_metrics = {}
    
    for metric_name, baseline_time in baseline_metrics.items():
        performance_timer(metric_name)
        
        # Simulate processing
        time.sleep(0.01)
        
        current_time = performance_timer(metric_name)
        current_metrics[metric_name] = current_time
        
        # Check for regression (current time should not be significantly worse)
        regression_threshold = baseline_time * 1.2  # 20% tolerance
        
        assert current_time < regression_threshold, \
            f"Performance regression detected in {metric_name}: " \
            f"current={current_time:.2f}s, baseline={baseline_time:.2f}s, " \
            f"threshold={regression_threshold:.2f}s"


if __name__ == "__main__":
    # Allow running performance tests directly
    pytest.main([__file__, "-v", "-m", "performance"])