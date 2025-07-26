"""Performance tests for coordinate extraction optimization."""

import pytest
from src.multimodal_contract_extractor.clause_detection import _extract_text_coordinates


class TestCoordinateExtractionPerformance:
    """Test performance characteristics of coordinate extraction."""
    
    def test_coordinate_extraction_with_large_ocr_data(self):
        """Test coordinate extraction performance with large OCR dataset."""
        # Create large OCR data to test performance
        large_text = ["word" + str(i) for i in range(1000)]
        mock_ocr_data = {
            'text': large_text,
            'left': list(range(0, 1000 * 50, 50)),  # Words spaced 50 pixels apart
            'top': [100] * 1000,  # All on same line
            'width': [40] * 1000,  # All same width
            'height': [20] * 1000,  # All same height
            'conf': [95] * 1000  # All high confidence
        }
        
        # Test finding text near the end (worst case scenario)
        text_to_find = "word990 word991"
        
        import time
        start_time = time.time()
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        end_time = time.time()
        
        # Should complete in reasonable time (under 100ms for 1000 words)
        processing_time = end_time - start_time
        assert processing_time < 0.1, f"Processing took too long: {processing_time:.3f}s"
        
        # Should find correct coordinates
        assert coordinates is not None
        assert coordinates[0] == 990 * 50  # Left position of word990
        
    def test_coordinate_extraction_early_termination(self):
        """Test that coordinate extraction terminates early on match."""
        # Create OCR data where target is at the beginning
        mock_ocr_data = {
            'text': ['target', 'word'] + ['filler'] * 100,
            'left': list(range(0, 102 * 50, 50)),
            'top': [100] * 102,
            'width': [40] * 102,
            'height': [20] * 102,
            'conf': [95] * 102
        }
        
        text_to_find = "target word"
        
        import time
        start_time = time.time()
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        end_time = time.time()
        
        # Should complete very quickly since match is at beginning
        processing_time = end_time - start_time
        assert processing_time < 0.01, f"Early termination failed: {processing_time:.3f}s"
        
        # Should find correct coordinates
        assert coordinates is not None
        assert coordinates[0] == 0  # Left position of first word
        
    def test_coordinate_extraction_no_match_performance(self):
        """Test performance when no match is found."""
        mock_ocr_data = {
            'text': ['different'] * 500,
            'left': list(range(0, 500 * 50, 50)),
            'top': [100] * 500,
            'width': [40] * 500,
            'height': [20] * 500,
            'conf': [95] * 500
        }
        
        text_to_find = "not found anywhere"
        
        import time
        start_time = time.time()
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        end_time = time.time()
        
        # Should complete in reasonable time even when no match
        processing_time = end_time - start_time
        assert processing_time < 0.05, f"No-match case took too long: {processing_time:.3f}s"
        
        # Should return None for no match
        assert coordinates is None