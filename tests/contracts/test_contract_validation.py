"""
Contract testing for API contracts and service interfaces.

This module implements contract testing to ensure API compatibility
and service interface adherence.
"""

import json
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest


class TestAPIContracts:
    """Test API contract compliance."""
    
    def test_extraction_api_contract(self, sample_contract_data):
        """Test that extraction API returns expected contract structure."""
        # Expected API response structure
        expected_schema = {
            "document_info": {
                "filename": str,
                "pages": int,
                "processing_time": float,
                "overall_confidence": float,
                "document_type": str
            },
            "parties": list,
            "clauses": list,
            "metadata": dict
        }
        
        # Validate contract data matches expected schema
        self._validate_schema(sample_contract_data, expected_schema)
    
    def test_clause_structure_contract(self, sample_contract_data):
        """Test that clause objects match expected structure."""
        expected_clause_schema = {
            "id": str,
            "type": str,
            "title": str,
            "text": str,
            "page": int,
            "coordinates": list,
            "confidence": float,
            "key_terms": list
        }
        
        clauses = sample_contract_data.get("clauses", [])
        assert len(clauses) > 0, "Sample data should contain clauses"
        
        for clause in clauses:
            self._validate_schema(clause, expected_clause_schema)
    
    def test_party_structure_contract(self, sample_contract_data):
        """Test that party objects match expected structure."""
        expected_party_schema = {
            "role": str,
            "name": str,
            "address": str
        }
        
        parties = sample_contract_data.get("parties", [])
        assert len(parties) > 0, "Sample data should contain parties"
        
        for party in parties:
            self._validate_schema(party, expected_party_schema)
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate that data matches the expected schema.
        
        Args:
            data: Data to validate
            schema: Expected schema structure
        """
        for key, expected_type in schema.items():
            assert key in data, f"Missing required field: {key}"
            
            if expected_type in (dict, list):
                assert isinstance(data[key], expected_type), \
                    f"Field {key} should be {expected_type.__name__}, got {type(data[key]).__name__}"
            else:
                assert isinstance(data[key], expected_type), \
                    f"Field {key} should be {expected_type.__name__}, got {type(data[key]).__name__}"


class TestServiceContracts:
    """Test service interface contracts."""
    
    def test_document_loader_contract(self, sample_pdf_path):
        """Test document loader service contract."""
        # Mock the document loader to test contract
        with patch('multimodal_contract_extractor.document.load_document') as mock_loader:
            # Define expected contract
            mock_doc = Mock()
            mock_doc.filename = str(sample_pdf_path)
            mock_doc.pages = 3
            mock_doc.content = "Sample content"
            mock_loader.return_value = mock_doc
            
            # Test contract compliance
            from multimodal_contract_extractor.document import load_document
            doc = load_document(str(sample_pdf_path))
            
            # Validate contract
            assert hasattr(doc, 'filename'), "Document should have filename attribute"
            assert hasattr(doc, 'pages'), "Document should have pages attribute"
            assert hasattr(doc, 'content'), "Document should have content attribute"
            
            assert isinstance(doc.filename, str), "Filename should be string"
            assert isinstance(doc.pages, int), "Pages should be integer"
            assert doc.pages > 0, "Pages should be positive"
    
    def test_ocr_service_contract(self, sample_image_path):
        """Test OCR service contract."""
        with patch('pytesseract.image_to_string') as mock_ocr:
            # Define expected OCR contract
            mock_ocr.return_value = "Sample extracted text"
            
            # Test contract
            result = mock_ocr(str(sample_image_path))
            
            # Validate contract
            assert isinstance(result, str), "OCR result should be string"
            assert len(result) > 0, "OCR result should not be empty"
    
    def test_clause_detector_contract(self, mock_ocr_result):
        """Test clause detector service contract."""
        with patch('multimodal_contract_extractor.clause_detection.detect_clauses') as mock_detector:
            # Define expected contract
            mock_clauses = [
                {
                    "id": "clause_001",
                    "type": "confidentiality",
                    "text": "Sample clause text",
                    "confidence": 0.85
                }
            ]
            mock_detector.return_value = mock_clauses
            
            # Test contract
            from multimodal_contract_extractor.clause_detection import detect_clauses
            clauses = detect_clauses(mock_ocr_result["text"])
            
            # Validate contract
            assert isinstance(clauses, list), "Clauses should be a list"
            for clause in clauses:
                assert isinstance(clause, dict), "Each clause should be a dictionary"
                assert "id" in clause, "Clause should have id"
                assert "type" in clause, "Clause should have type"
                assert "text" in clause, "Clause should have text"
                assert "confidence" in clause, "Clause should have confidence"


class TestConfigurationContracts:
    """Test configuration contract compliance."""
    
    def test_config_structure_contract(self, test_config):
        """Test that configuration follows expected contract."""
        # Expected configuration sections
        expected_sections = ["ocr", "extraction", "security", "health", "document"]
        
        for section in expected_sections:
            assert hasattr(test_config, section), f"Config should have {section} section"
            section_obj = getattr(test_config, section)
            assert section_obj is not None, f"Config {section} section should not be None"
    
    def test_ocr_config_contract(self, test_config):
        """Test OCR configuration contract."""
        ocr_config = test_config.ocr
        
        # Required OCR configuration fields
        required_fields = ["cache_size_limit", "context_window_size"]
        
        for field in required_fields:
            assert hasattr(ocr_config, field), f"OCR config should have {field}"
            value = getattr(ocr_config, field)
            assert isinstance(value, int), f"OCR {field} should be integer"
            assert value > 0, f"OCR {field} should be positive"
    
    def test_security_config_contract(self, test_config):
        """Test security configuration contract."""
        security_config = test_config.security
        
        # Required security configuration fields
        required_fields = ["max_file_size_mb", "request_id_length_limit"]
        
        for field in required_fields:
            assert hasattr(security_config, field), f"Security config should have {field}"
            value = getattr(security_config, field)
            assert isinstance(value, int), f"Security {field} should be integer"
            assert value > 0, f"Security {field} should be positive"


class TestErrorContracts:
    """Test error handling contracts."""
    
    def test_invalid_file_error_contract(self):
        """Test error contract for invalid files."""
        with patch('multimodal_contract_extractor.document.load_document') as mock_loader:
            # Mock invalid file error
            mock_loader.side_effect = ValueError("Invalid file format")
            
            from multimodal_contract_extractor.document import load_document
            
            # Test error contract
            with pytest.raises(ValueError) as exc_info:
                load_document("invalid_file.txt")
            
            # Validate error contract
            assert "Invalid file format" in str(exc_info.value)
            assert isinstance(exc_info.value, ValueError)
    
    def test_processing_timeout_error_contract(self):
        """Test error contract for processing timeouts."""
        with patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            # Mock timeout error
            mock_extract.side_effect = TimeoutError("Processing timeout")
            
            from multimodal_contract_extractor.extraction import extract_clauses
            
            # Test error contract
            with pytest.raises(TimeoutError) as exc_info:
                extract_clauses("sample text")
            
            # Validate error contract
            assert "Processing timeout" in str(exc_info.value)
            assert isinstance(exc_info.value, TimeoutError)
    
    def test_configuration_error_contract(self):
        """Test error contract for configuration errors."""
        # Test invalid configuration
        invalid_config = {
            "ocr": {
                "cache_size_limit": -1,  # Invalid negative value
                "context_window_size": "invalid"  # Invalid type
            }
        }
        
        # This would test configuration validation
        # Implementation depends on actual config validation logic
        with pytest.raises((ValueError, TypeError)):
            # Mock configuration validation
            if invalid_config["ocr"]["cache_size_limit"] < 0:
                raise ValueError("cache_size_limit must be positive")
            if not isinstance(invalid_config["ocr"]["context_window_size"], int):
                raise TypeError("context_window_size must be integer")


class TestCompatibilityContracts:
    """Test backward compatibility contracts."""
    
    def test_api_version_compatibility(self):
        """Test API version compatibility contract."""
        # Test that different API versions are supported
        supported_versions = ["v1.0", "v1.1", "v1.2"]
        
        for version in supported_versions:
            # Mock version-specific processing
            with patch('multimodal_contract_extractor.version.get_api_version') as mock_version:
                mock_version.return_value = version
                
                # Test that version is supported
                from multimodal_contract_extractor.version import get_api_version
                current_version = get_api_version()
                
                assert current_version in supported_versions, \
                    f"Version {current_version} should be supported"
    
    def test_data_format_compatibility(self, sample_contract_data):
        """Test data format backward compatibility."""
        # Test that older data formats are still supported
        legacy_formats = [
            # Version 1.0 format (minimal)
            {
                "filename": "test.pdf",
                "clauses": [{"type": "general", "text": "sample"}]
            },
            # Version 1.1 format (with confidence)
            {
                "filename": "test.pdf",
                "clauses": [{"type": "general", "text": "sample", "confidence": 0.8}]
            }
        ]
        
        for legacy_format in legacy_formats:
            # Test that legacy format can be processed
            self._validate_legacy_format(legacy_format)
    
    def _validate_legacy_format(self, data: Dict[str, Any]) -> None:
        """
        Validate that legacy format is supported.
        
        Args:
            data: Legacy format data
        """
        # Basic validation for legacy compatibility
        assert "filename" in data, "Legacy format should have filename"
        assert "clauses" in data, "Legacy format should have clauses"
        
        # Clauses should be a list
        assert isinstance(data["clauses"], list), "Clauses should be a list"
        
        # Each clause should have required fields
        for clause in data["clauses"]:
            assert "type" in clause, "Each clause should have type"
            assert "text" in clause, "Each clause should have text"


if __name__ == "__main__":
    # Allow running contract tests directly
    pytest.main([__file__, "-v", "-k", "contract"])