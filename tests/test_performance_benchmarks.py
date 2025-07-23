"""Performance benchmark tests for the optimization implementations."""

import time
from unittest.mock import MagicMock, patch

import pytest

from multimodal_contract_extractor.clause_detection import (
    _detect_clauses_legacy,
    _detect_clauses_optimized,
    clear_ocr_cache,
    clear_pattern_cache,
)
from multimodal_contract_extractor.extraction import extract_from_document
from tests.test_helpers import create_test_pdf


class TestPerformanceBenchmarks:
    """Benchmark tests to validate performance optimizations."""

    def test_adaptive_loading_benchmark(self, tmp_path):
        """Benchmark adaptive document loading performance."""
        # Create test files of different sizes
        small_file = tmp_path / "small.pdf"
        large_file = tmp_path / "large.pdf"

        create_test_pdf(small_file, "Small document content")
        create_test_pdf(large_file, "Large document content " * 100)

        # Test small file processing
        start_time = time.perf_counter()
        small_result = extract_from_document(small_file)
        small_time = time.perf_counter() - start_time

        # Test large file processing (would use streaming in real scenario)
        start_time = time.perf_counter()
        large_result = extract_from_document(large_file)
        large_time = time.perf_counter() - start_time

        # Both should complete successfully
        assert small_result is not None
        assert large_result is not None
        assert small_time > 0
        assert large_time > 0

        # Record timing info for comparison

    def test_ocr_caching_benchmark(self, tmp_path):
        """Benchmark OCR caching performance improvement."""
        input_file = tmp_path / "cache_benchmark.pdf"
        create_test_pdf(input_file, "Benchmark content for OCR caching test")

        # Clear cache to start fresh
        clear_ocr_cache()

        # First run (cold cache)
        start_time = time.perf_counter()
        result1 = extract_from_document(input_file)
        cold_time = time.perf_counter() - start_time

        # Second run (warm cache)
        start_time = time.perf_counter()
        result2 = extract_from_document(input_file)
        warm_time = time.perf_counter() - start_time

        # Both should produce the same results
        assert result1 is not None
        assert result2 is not None
        assert len(result1["clauses"]) == len(result2["clauses"])

        # Warm cache should be faster or similar (depending on OCR overhead)

        # At minimum, warm cache should not be significantly slower
        assert warm_time <= cold_time + 0.1  # Allow small margin

    def test_clause_detection_optimization_benchmark(self):
        """Benchmark clause detection optimization (legacy vs optimized)."""
        # Create a mock document with multiple pages containing various clause types
        test_text = """
        This agreement contains confidential information that must be protected.
        Either party may terminate this agreement with proper notice.
        Payment terms are specified in Schedule A of this agreement.
        Liability shall be limited as described in the limitation clause.
        This agreement is governed by the laws of the specified jurisdiction.
        Disputes will be resolved through arbitration as outlined herein.
        """

        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock() for _ in range(5)]  # 5 pages for more processing
        for i, page in enumerate(mock_doc.pages):
            page.number = i + 1
            page.image = MagicMock()

        # Clear caches
        clear_ocr_cache()
        clear_pattern_cache()

        with patch(
            "multimodal_contract_extractor.clause_detection._ocr_image"
        ) as mock_ocr:
            mock_ocr.return_value = test_text

            # Benchmark legacy implementation
            start_time = time.perf_counter()
            legacy_clauses = _detect_clauses_legacy(mock_doc)
            legacy_time = time.perf_counter() - start_time

            # Reset mock for fair comparison
            mock_ocr.reset_mock()

            # Benchmark optimized implementation
            start_time = time.perf_counter()
            optimized_clauses = _detect_clauses_optimized(mock_doc)
            optimized_time = time.perf_counter() - start_time

            # Both should find clauses
            assert len(legacy_clauses) > 0
            assert len(optimized_clauses) > 0

            if legacy_time > 0:
                ((legacy_time - optimized_time) / legacy_time * 100)

                # Optimized should be at least as fast as legacy
                assert optimized_time <= legacy_time + 0.001  # Allow small margin

    def test_end_to_end_performance_benchmark(self, tmp_path):
        """End-to-end performance benchmark with all optimizations."""
        # Create a document with content that triggers multiple clause types
        input_file = tmp_path / "e2e_benchmark.pdf"
        create_test_pdf(
            input_file,
            "This confidential agreement includes payment terms, termination clauses, "
            "liability limitations, and dispute resolution procedures. The governing law "
            "provisions are detailed in the appendix.",
        )

        # Clear all caches for baseline
        clear_ocr_cache()
        clear_pattern_cache()

        # Benchmark full extraction pipeline
        start_time = time.perf_counter()
        result = extract_from_document(input_file)
        total_time = time.perf_counter() - start_time

        # Verify successful extraction
        assert result is not None
        assert "document_info" in result
        assert "clauses" in result
        assert result["document_info"]["processing_time"] > 0

        # Benchmark second run with warm caches
        start_time = time.perf_counter()
        result2 = extract_from_document(input_file)
        cached_time = time.perf_counter() - start_time

        # Results should be consistent
        assert len(result["clauses"]) == len(result2["clauses"])

        # Cached run should be faster or similar
        assert cached_time <= total_time + 0.05  # Allow margin for timing variance

    @pytest.mark.slow
    def test_memory_usage_benchmark(self, tmp_path):
        """Benchmark memory usage efficiency (marked as slow test)."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Create a larger document for memory testing
        input_file = tmp_path / "memory_test.pdf"
        create_test_pdf(input_file, "Memory test content " * 200)  # Larger content

        # Measure memory before processing
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Process document
        result = extract_from_document(input_file)

        # Measure memory after processing
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Verify processing succeeded
        assert result is not None

        # Memory usage should be reasonable (less than 100MB for this test)
        assert memory_used < 100, f"Memory usage too high: {memory_used:.1f} MB"
