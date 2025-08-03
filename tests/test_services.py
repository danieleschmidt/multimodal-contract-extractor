"""Unit tests for service layer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.processing_service import ProcessingService
from src.services.validation_service import ValidationService
from src.models.processing import ProcessingResult, ProcessingStatus, ValidationResult
from src.models.contract import Contract, ContractType


class TestValidationService:
    """Test ValidationService functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validation_service = ValidationService()
    
    def test_validate_existing_pdf_file(self, tmp_path):
        """Test validation of a valid PDF file."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nTest PDF content" + b"x" * 1000)  # Valid PDF header + content
        
        result = self.validation_service.validate_document(pdf_file)
        
        assert result.is_valid is True
        assert result.file_size_bytes > 0
        assert result.file_type is not None
    
    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        nonexistent_file = Path("/nonexistent/file.pdf")
        
        result = self.validation_service.validate_document(nonexistent_file)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]
    
    def test_validate_unsupported_file_type(self, tmp_path):
        """Test validation of unsupported file type."""
        unsupported_file = tmp_path / "test.txt"
        unsupported_file.write_text("This is a text file")
        
        result = self.validation_service.validate_document(unsupported_file)
        
        assert result.is_valid is False
        assert any("Unsupported file extension" in error for error in result.errors)
    
    def test_validate_file_too_large(self, tmp_path):
        """Test validation of oversized file."""
        # Create a large file (exceed the default limit)
        large_file = tmp_path / "large.pdf"
        large_content = b"%PDF-1.4\n" + b"x" * (101 * 1024 * 1024)  # 101MB
        large_file.write_bytes(large_content)
        
        result = self.validation_service.validate_document(large_file)
        
        assert result.is_valid is False
        assert any("too large" in error for error in result.errors)
    
    def test_validate_file_too_small(self, tmp_path):
        """Test validation of file that's too small."""
        small_file = tmp_path / "small.pdf"
        small_file.write_bytes(b"tiny")  # Less than minimum size
        
        result = self.validation_service.validate_document(small_file)
        
        assert result.is_valid is False
        assert any("too small" in error for error in result.errors)
    
    @patch('src.services.validation_service.Image.open')
    def test_validate_image_content(self, mock_image_open, tmp_path):
        """Test validation of image content."""
        # Mock PIL Image
        mock_image = Mock()
        mock_image.size = (800, 600)
        mock_image.mode = 'RGB'
        mock_image.verify.return_value = None
        mock_image_open.return_value.__enter__.return_value = mock_image
        
        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 1000)  # PNG header + content
        
        result = self.validation_service.validate_document(image_file)
        
        assert result.is_valid is True
        assert result.pages_detected == 1
    
    @patch('src.services.validation_service.Image.open')
    def test_validate_image_too_small(self, mock_image_open, tmp_path):
        """Test validation of image with dimensions too small."""
        mock_image = Mock()
        mock_image.size = (50, 50)  # Too small
        mock_image.mode = 'RGB'
        mock_image_open.return_value.__enter__.return_value = mock_image
        
        image_file = tmp_path / "small.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 1000)
        
        result = self.validation_service.validate_document(image_file)
        
        assert result.is_valid is False
        assert any("too small" in error for error in result.errors)
    
    def test_validate_output_path_valid(self, tmp_path):
        """Test validation of valid output path."""
        output_file = tmp_path / "output.json"
        
        result = self.validation_service.validate_output_path(output_file)
        
        assert result.is_valid is True
    
    def test_validate_output_path_invalid_directory(self):
        """Test validation of output path with nonexistent directory."""
        invalid_output = Path("/nonexistent/directory/output.json")
        
        result = self.validation_service.validate_output_path(invalid_output)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        results = [
            ValidationResult(is_valid=True, file_size_bytes=1000000),
            ValidationResult(is_valid=False, file_size_bytes=2000000),
            ValidationResult(is_valid=True, file_size_bytes=500000)
        ]
        results[1].add_warning("Test warning")
        
        summary = self.validation_service.get_validation_summary(results)
        
        assert summary["total"] == 3
        assert summary["valid"] == 2
        assert summary["invalid"] == 1
        assert summary["warnings"] == 1
        assert summary["total_size_mb"] == 3.5  # 3.5MB total


class TestProcessingService:
    """Test ProcessingService functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.processing_service = ProcessingService()
    
    @patch('src.services.processing_service.Path.exists')
    @patch('src.services.processing_service.Path.stat')
    def test_process_document_success(self, mock_stat, mock_exists, tmp_path):
        """Test successful document processing."""
        # Setup mocks
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1000000)
        
        # Mock dependencies
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text, \
             patch.object(self.processing_service.extraction_service, 'detect_clauses_from_document') as mock_detect_clauses, \
             patch.object(self.processing_service.extraction_service, 'get_last_ocr_confidence') as mock_ocr_confidence:
            
            # Configure mocks
            mock_validate.return_value = ValidationResult(
                is_valid=True, 
                pages_detected=3, 
                file_size_bytes=1000000
            )
            mock_extract_text.return_value = "Sample contract text with important clauses."
            mock_detect_clauses.return_value = []  # Empty clauses for simplicity
            mock_ocr_confidence.return_value = 0.85
            
            # Process document
            test_file = tmp_path / "test_contract.pdf"
            result = self.processing_service.process_document(test_file)
            
            # Verify results
            assert result.status == ProcessingStatus.COMPLETED
            assert result.is_successful()
            assert result.validation.is_valid
            assert result.metrics.pages_processed == 3
            assert result.metrics.ocr_confidence == 0.85
            assert result.contract is not None
            assert result.extracted_data is not None
    
    @patch('src.services.processing_service.Path.exists')
    def test_process_document_validation_failure(self, mock_exists, tmp_path):
        """Test document processing with validation failure."""
        mock_exists.return_value = True
        
        # Mock validation failure
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate:
            validation_result = ValidationResult(is_valid=False)
            validation_result.add_error("Invalid file format")
            mock_validate.return_value = validation_result
            
            test_file = tmp_path / "invalid_contract.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.FAILED
            assert not result.is_successful()
            assert not result.validation.is_valid
            assert len(result.errors) > 0
    
    @patch('src.services.processing_service.Path.exists')
    @patch('src.services.processing_service.Path.stat')
    def test_process_document_ocr_failure(self, mock_stat, mock_exists, tmp_path):
        """Test document processing with OCR failure."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1000000)
        
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text:
            
            # Valid file but OCR fails
            mock_validate.return_value = ValidationResult(is_valid=True, pages_detected=2)
            mock_extract_text.return_value = None  # OCR failure
            
            test_file = tmp_path / "problematic_contract.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.FAILED
            assert not result.is_successful()
            assert len(result.errors) > 0
            assert any("No text could be extracted" in error.message for error in result.errors)
    
    @patch('src.services.processing_service.Path.exists')
    @patch('src.services.processing_service.Path.stat')
    def test_process_document_with_clauses(self, mock_stat, mock_exists, tmp_path):
        """Test document processing with clause detection."""
        from src.models.clause import LegalClause, ClauseType
        
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1000000)
        
        # Create mock clauses
        mock_clauses = [
            LegalClause(
                type=ClauseType.COMPENSATION,
                text="Annual salary of $75,000",
                confidence=0.92
            ),
            LegalClause(
                type=ClauseType.TERMINATION,
                text="30 days notice required for termination",
                confidence=0.88
            )
        ]
        
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text, \
             patch.object(self.processing_service.extraction_service, 'detect_clauses_from_document') as mock_detect_clauses, \
             patch.object(self.processing_service.extraction_service, 'get_last_ocr_confidence') as mock_ocr_confidence:
            
            mock_validate.return_value = ValidationResult(is_valid=True, pages_detected=3)
            mock_extract_text.return_value = "Contract text with salary and termination clauses"
            mock_detect_clauses.return_value = mock_clauses
            mock_ocr_confidence.return_value = 0.90
            
            test_file = tmp_path / "contract_with_clauses.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.COMPLETED
            assert result.is_successful()
            assert result.metrics.clauses_detected == 2
            assert result.contract is not None
            assert len(result.contract.clauses) == 2
            assert result.contract.contract_type != ContractType.UNKNOWN  # Should be classified
    
    def test_process_document_exception_handling(self, tmp_path):
        """Test processing service exception handling."""
        # Mock an exception during validation
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate:
            mock_validate.side_effect = Exception("Unexpected validation error")
            
            test_file = tmp_path / "exception_test.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.FAILED
            assert not result.is_successful()
            assert len(result.errors) > 0
            assert "Unexpected validation error" in result.errors[0].message
    
    def test_processing_stages_tracking(self, tmp_path):
        """Test that processing stages are properly tracked."""
        from src.models.processing import ProcessingStage
        
        # Mock a partially successful processing
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text:
            
            mock_validate.return_value = ValidationResult(is_valid=True, pages_detected=1)
            mock_extract_text.side_effect = Exception("OCR failed")
            
            test_file = tmp_path / "stage_tracking_test.pdf"
            result = self.processing_service.process_document(test_file)
            
            # Should have completed validation stage
            assert ProcessingStage.VALIDATION.value in result.metrics.stage_times
            # Should have failed at OCR stage
            assert result.current_stage == ProcessingStage.OCR_EXTRACTION
            assert not result.is_successful()
    
    def test_contract_assembly_with_entities(self, tmp_path):
        """Test contract assembly with extracted entities."""
        from src.models.clause import LegalClause
        
        # Create clause with entities
        clause_with_entities = LegalClause(
            text="John Smith of ACME Corp agrees to confidentiality terms."
        )
        # Mock the entities that would be extracted
        clause_with_entities.entities = {
            'parties': ['John Smith', 'ACME Corp'],
            'organizations': ['ACME Corp'],
            'persons': ['John Smith']
        }
        
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text, \
             patch.object(self.processing_service.extraction_service, 'detect_clauses_from_document') as mock_detect_clauses, \
             patch.object(self.processing_service.extraction_service, 'get_last_ocr_confidence') as mock_ocr_confidence, \
             patch('src.services.processing_service.Path.exists') as mock_exists, \
             patch('src.services.processing_service.Path.stat') as mock_stat:
            
            mock_exists.return_value = True
            mock_stat.return_value = Mock(st_size=1000000)
            mock_validate.return_value = ValidationResult(is_valid=True, pages_detected=1)
            mock_extract_text.return_value = "Contract text"
            mock_detect_clauses.return_value = [clause_with_entities]
            mock_ocr_confidence.return_value = 0.85
            
            test_file = tmp_path / "entity_test.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.COMPLETED
            assert result.contract is not None
            # Should have extracted parties
            assert len(result.contract.parties) > 0
            # Should have party information
            party_names = [party.name for party in result.contract.parties]
            assert any('John Smith' in name for name in party_names)
    
    def test_processing_metrics_calculation(self, tmp_path):
        """Test processing metrics calculation."""
        from src.models.clause import LegalClause, ClauseType
        
        # Create clauses with different confidence levels
        clauses = [
            LegalClause(type=ClauseType.COMPENSATION, text="Salary clause", confidence=0.95),
            LegalClause(type=ClauseType.TERMINATION, text="Termination clause", confidence=0.87),
        ]
        
        with patch.object(self.processing_service.validation_service, 'validate_document') as mock_validate, \
             patch.object(self.processing_service.extraction_service, 'extract_text_from_document') as mock_extract_text, \
             patch.object(self.processing_service.extraction_service, 'detect_clauses_from_document') as mock_detect_clauses, \
             patch.object(self.processing_service.extraction_service, 'get_last_ocr_confidence') as mock_ocr_confidence, \
             patch('src.services.processing_service.Path.exists') as mock_exists, \
             patch('src.services.processing_service.Path.stat') as mock_stat:
            
            mock_exists.return_value = True
            mock_stat.return_value = Mock(st_size=1000000)
            mock_validate.return_value = ValidationResult(is_valid=True, pages_detected=2)
            mock_extract_text.return_value = "Sample contract text"
            mock_detect_clauses.return_value = clauses
            mock_ocr_confidence.return_value = 0.91
            
            test_file = tmp_path / "metrics_test.pdf"
            result = self.processing_service.process_document(test_file)
            
            assert result.status == ProcessingStatus.COMPLETED
            assert result.metrics.pages_processed == 2
            assert result.metrics.clauses_detected == 2
            assert result.metrics.ocr_confidence == 0.91
            assert result.metrics.clause_detection_confidence == 0.91  # Average of 0.95 and 0.87
            assert result.metrics.overall_confidence > 0  # Should be calculated
    
    def test_get_processing_status_placeholder(self):
        """Test processing status retrieval (placeholder implementation)."""
        result_id = "test-result-id"
        status = self.processing_service.get_processing_status(result_id)
        
        assert status is not None
        assert status["id"] == result_id
        assert status["status"] == "not_implemented"
    
    def test_cancel_processing_placeholder(self):
        """Test processing cancellation (placeholder implementation)."""
        result_id = "test-result-id"
        success = self.processing_service.cancel_processing(result_id)
        
        assert success is False  # Not implemented yet


class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    def test_validation_service_integration_with_processing(self, tmp_path):
        """Test integration between validation and processing services."""
        # Create a real file for testing
        test_file = tmp_path / "integration_test.pdf"
        test_file.write_bytes(b"%PDF-1.4\nTest content" + b"x" * 2000)
        
        validation_service = ValidationService()
        processing_service = ProcessingService()
        
        # First validate the file
        validation_result = validation_service.validate_document(test_file)
        assert validation_result.is_valid
        
        # Then process it (with mocked extraction services)
        with patch.object(processing_service.extraction_service, 'extract_text_from_document') as mock_extract, \
             patch.object(processing_service.extraction_service, 'detect_clauses_from_document') as mock_clauses, \
             patch.object(processing_service.extraction_service, 'get_last_ocr_confidence') as mock_confidence:
            
            mock_extract.return_value = "Sample contract text"
            mock_clauses.return_value = []
            mock_confidence.return_value = 0.80
            
            processing_result = processing_service.process_document(test_file)
            
            assert processing_result.is_successful()
            assert processing_result.validation.is_valid
            assert processing_result.document_path == str(test_file)
    
    def test_error_propagation_between_services(self, tmp_path):
        """Test error propagation from validation to processing service."""
        # Create an invalid file
        invalid_file = tmp_path / "invalid.txt"  # Wrong extension
        invalid_file.write_text("This is not a PDF")
        
        processing_service = ProcessingService()
        result = processing_service.process_document(invalid_file)
        
        assert not result.is_successful()
        assert result.status == ProcessingStatus.FAILED
        assert not result.validation.is_valid
        assert len(result.errors) > 0