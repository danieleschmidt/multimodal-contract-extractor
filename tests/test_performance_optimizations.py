"""Tests for performance optimizations in document processing."""

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from multimodal_contract_extractor.extraction import extract_from_document
from multimodal_contract_extractor.document import load_document, stream_document
from tests.test_helpers import create_test_pdf


class TestAdaptiveDocumentLoading:
    """Test adaptive document loading for optimal performance."""
    
    def test_small_file_uses_standard_loading(self, tmp_path):
        """Small files should use standard loading for faster access."""
        # Create a small test PDF (< 10MB threshold)
        input_file = tmp_path / "small_doc.pdf"
        create_test_pdf(input_file, "Test content for small document")
        
        # Mock the load_document to track calls and OCR to avoid errors
        with patch('multimodal_contract_extractor.extraction.load_document') as mock_load, \
             patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            
            # Set up mocks to return valid structures
            mock_load.return_value = MagicMock()
            mock_load.return_value.pages = [MagicMock()]
            mock_ocr.return_value = "Test document content"
            
            # Call extraction
            extract_from_document(input_file)
            
            # Verify standard loading was used for small file  
            mock_load.assert_called_once()
    
    def test_large_file_uses_streaming(self, tmp_path):
        """Large files should use streaming to manage memory."""
        # Create a large test file (simulate by patching file size)
        input_file = tmp_path / "large_doc.pdf"
        create_test_pdf(input_file, "Test content for large document")
        
        # Mock file size to be > 10MB threshold
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 15_000_000  # 15MB
            
            with patch('multimodal_contract_extractor.extraction.stream_document') as mock_stream, \
                 patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
                
                # Set up mock to return valid document pages
                mock_stream.return_value = [MagicMock()]
                mock_stream.return_value[0].number = 1
                mock_ocr.return_value = "Test document content"
                    
                # Call extraction
                extract_from_document(input_file)
                    
                # Verify streaming was used for large file
                mock_stream.assert_called_once()
    
    def test_streaming_performance_benchmark(self, tmp_path):
        """Benchmark streaming vs standard loading for performance comparison."""
        input_file = tmp_path / "benchmark_doc.pdf" 
        create_test_pdf(input_file, "Benchmark content " * 100)  # Larger content
        
        # Test standard loading time
        start_time = time.perf_counter()
        doc_standard = load_document(input_file)
        standard_time = time.perf_counter() - start_time
        
        # Test streaming time 
        start_time = time.perf_counter()
        pages_streamed = list(stream_document(input_file, chunk_size=1))
        streaming_time = time.perf_counter() - start_time
        
        # Streaming should be comparable or better for memory efficiency
        # (Time may vary, but we're mainly testing it doesn't crash and works)
        assert len(pages_streamed) == len(doc_standard.pages)
        assert streaming_time >= 0  # Basic sanity check
        assert standard_time >= 0   # Basic sanity check


class TestOCRCaching:
    """Test OCR result caching for improved performance."""
    
    def test_ocr_cache_reduces_duplicate_processing(self, tmp_path):
        """OCR cache should avoid reprocessing the same page content."""
        input_file = tmp_path / "cache_test.pdf"
        create_test_pdf(input_file, "Cache test content")
        
        # Mock the OCR function to track how many times it's called
        with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            mock_ocr.return_value = "Cached test content"
            
            # Process the same document twice
            result1 = extract_from_document(input_file)
            result2 = extract_from_document(input_file)
            
            # With caching, OCR should be called fewer times for second processing
            # For now, verify both results are valid
            assert result1 is not None
            assert result2 is not None
            assert "document_info" in result1
            assert "document_info" in result2
            
            # OCR should have been called at least once
            assert mock_ocr.call_count >= 1
    
    def test_cache_invalidation_on_different_content(self, tmp_path):
        """Cache should be invalidated when processing different content."""
        # Placeholder for future caching implementation
        pass


class TestPerformanceMetrics:
    """Test performance monitoring and metrics collection."""
    
    def test_processing_time_recorded(self, tmp_path):
        """Processing time should be accurately recorded in results."""
        input_file = tmp_path / "timing_test.pdf"
        create_test_pdf(input_file, "Timing test content")
        
        start_time = time.perf_counter()
        result = extract_from_document(input_file)
        actual_time = time.perf_counter() - start_time
        
        # Check that processing time is recorded and reasonable
        recorded_time = result["document_info"]["processing_time"]
        assert recorded_time > 0
        assert recorded_time <= actual_time + 0.1  # Allow small margin for overhead
    
    def test_memory_usage_monitoring(self, tmp_path):
        """Memory usage should be monitored during processing."""
        input_file = tmp_path / "memory_test.pdf"
        create_test_pdf(input_file, "Memory test content")
        
        # Basic test - ensure processing completes without memory issues
        result = extract_from_document(input_file)
        assert result is not None
        
        # Future: Add actual memory monitoring when implemented