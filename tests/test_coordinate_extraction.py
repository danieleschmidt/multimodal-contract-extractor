"""Tests for coordinate extraction from OCR data."""

import pytest
from unittest.mock import patch, Mock
from src.multimodal_contract_extractor.clause_detection import _extract_text_coordinates


class TestCoordinateExtraction:
    """Test coordinate extraction functionality."""
    
    def test_extract_text_coordinates_with_ocr_data(self):
        """Test extracting coordinates from OCR bounding box data."""
        # Mock OCR data with bounding boxes
        mock_ocr_data = {
            'text': ['', 'This', 'is', 'a', 'contract', 'clause', '', ''],
            'left': [0, 100, 150, 180, 200, 280, 0, 0],
            'top': [0, 50, 50, 50, 50, 50, 0, 0],
            'width': [0, 40, 25, 15, 70, 45, 0, 0],
            'height': [0, 20, 20, 20, 20, 20, 0, 0],
            'conf': [0, 95, 95, 95, 95, 95, 0, 0]
        }
        
        text_to_find = "contract clause"
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        
        # Should return bounding box coordinates [left, top, right, bottom]
        assert coordinates is not None
        assert len(coordinates) == 4
        assert coordinates[0] <= coordinates[2]  # left <= right
        assert coordinates[1] <= coordinates[3]  # top <= bottom
    
    def test_extract_text_coordinates_text_not_found(self):
        """Test coordinate extraction when text is not found in OCR data."""
        mock_ocr_data = {
            'text': ['This', 'is', 'different', 'text'],
            'left': [100, 150, 200, 250],
            'top': [50, 50, 50, 50],
            'width': [40, 25, 60, 30],
            'height': [20, 20, 20, 20],
            'conf': [95, 95, 95, 95]
        }
        
        text_to_find = "contract clause"
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        
        # Should return None when text not found
        assert coordinates is None
    
    def test_extract_text_coordinates_partial_match(self):
        """Test coordinate extraction with partial text match."""
        mock_ocr_data = {
            'text': ['The', 'payment', 'terms', 'clause', 'states'],
            'left': [50, 100, 180, 230, 280],
            'top': [100, 100, 100, 100, 100],
            'width': [30, 60, 40, 45, 40],
            'height': [15, 15, 15, 15, 15],
            'conf': [95, 95, 95, 95, 95]
        }
        
        text_to_find = "payment terms"
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        
        # Should find coordinates spanning both words
        assert coordinates is not None
        assert coordinates[0] == 100  # left of "payment"
        assert coordinates[2] == 220  # right of "terms" (180 + 40)
    
    def test_extract_text_coordinates_empty_ocr_data(self):
        """Test coordinate extraction with empty OCR data."""
        mock_ocr_data = {
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': [],
            'conf': []
        }
        
        text_to_find = "any text"
        coordinates = _extract_text_coordinates(text_to_find, mock_ocr_data)
        
        assert coordinates is None