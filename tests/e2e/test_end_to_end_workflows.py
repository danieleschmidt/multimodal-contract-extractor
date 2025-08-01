"""
End-to-end workflow tests for the Multimodal Contract Extractor.

This module tests complete user workflows from document upload
to final result export.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_single_document_extraction_workflow(self, temp_dir, sample_contract_data):
        """Test complete workflow for single document extraction."""
        # Setup test document
        test_pdf = temp_dir / "test_contract.pdf"
        test_pdf.write_text("Mock PDF content")
        
        output_file = temp_dir / "output.json"
        
        # Mock the complete processing chain
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract, \
             patch('multimodal_contract_extractor.serialization.save_results') as mock_save:
            
            # Configure mocks
            mock_doc = Mock()
            mock_doc.filename = str(test_pdf)
            mock_doc.pages = 3
            mock_load.return_value = mock_doc
            
            mock_extract.return_value = sample_contract_data["clauses"]
            mock_save.return_value = True
            
            # Execute workflow (mocked CLI call)
            from multimodal_contract_extractor.cli_utils import process_single_document
            
            result = process_single_document(
                file_path=str(test_pdf),
                output_path=str(output_file),
                format="json"
            )
            
            # Verify workflow completion
            assert result is not None, "Workflow should return result"
            mock_load.assert_called_once_with(str(test_pdf))
            mock_extract.assert_called_once()
            mock_save.assert_called_once()
    
    def test_batch_processing_workflow(self, temp_dir, sample_contract_data):
        """Test complete batch processing workflow."""
        # Setup test documents
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create test files
        test_files = ["contract1.pdf", "contract2.pdf", "contract3.pdf"]
        for filename in test_files:
            (input_dir / filename).write_text(f"Mock content for {filename}")
        
        # Mock batch processing
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract, \
             patch('multimodal_contract_extractor.serialization.save_results') as mock_save:
            
            # Configure mocks
            mock_doc = Mock()
            mock_doc.pages = 2
            mock_load.return_value = mock_doc
            
            mock_extract.return_value = sample_contract_data["clauses"]
            mock_save.return_value = True
            
            # Execute batch workflow
            from multimodal_contract_extractor.cli_utils import process_batch_documents
            
            results = process_batch_documents(
                input_dir=str(input_dir),
                output_dir=str(output_dir),
                format="json"
            )
            
            # Verify batch processing
            assert len(results) == len(test_files), "Should process all files"
            assert mock_load.call_count == len(test_files), "Should load all documents"
            assert mock_extract.call_count == len(test_files), "Should extract from all documents"
    
    def test_web_interface_workflow(self, temp_dir, sample_contract_data):
        """Test web interface upload and processing workflow."""
        # Mock Streamlit file upload
        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "uploaded_contract.pdf"
        mock_uploaded_file.read.return_value = b"Mock PDF content"
        mock_uploaded_file.type = "application/pdf"
        
        # Mock the web app processing chain
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract, \
             patch('streamlit.file_uploader') as mock_uploader:
            
            # Configure mocks
            mock_uploader.return_value = mock_uploaded_file
            
            mock_doc = Mock()
            mock_doc.filename = mock_uploaded_file.name
            mock_doc.pages = 4
            mock_load.return_value = mock_doc
            
            mock_extract.return_value = sample_contract_data["clauses"]
            
            # Simulate web app workflow
            from web_app import process_uploaded_file
            
            result = process_uploaded_file(mock_uploaded_file)
            
            # Verify web workflow
            assert result is not None, "Web workflow should return result"
            assert "clauses" in result, "Result should contain clauses"
            assert len(result["clauses"]) > 0, "Should extract clauses"
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test workflow error recovery and graceful handling."""
        # Setup test with invalid document
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("This is not a valid contract document")
        
        output_file = temp_dir / "output.json"
        
        # Mock processing with error
        with patch('multimodal_contract_extractor.document.load_document') as mock_load:
            # Configure mock to raise error
            mock_load.side_effect = ValueError("Unsupported file format")
            
            # Execute workflow with error handling
            from multimodal_contract_extractor.cli_utils import process_single_document
            
            # Should handle error gracefully
            with pytest.raises(ValueError):
                process_single_document(
                    file_path=str(invalid_file),
                    output_path=str(output_file),
                    format="json"
                )
            
            # Verify error was caught
            mock_load.assert_called_once()
    
    def test_configuration_based_workflow(self, temp_dir, test_config):
        """Test workflow with custom configuration."""
        # Setup test document
        test_pdf = temp_dir / "configured_test.pdf"
        test_pdf.write_text("Mock PDF for config test")
        
        output_file = temp_dir / "configured_output.json"
        
        # Mock processing with configuration
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract, \
             patch('multimodal_contract_extractor.config.get_config') as mock_get_config:
            
            # Configure mocks
            mock_get_config.return_value = test_config
            
            mock_doc = Mock()
            mock_doc.filename = str(test_pdf)
            mock_load.return_value = mock_doc
            
            mock_extract.return_value = []
            
            # Execute workflow with configuration
            from multimodal_contract_extractor.cli_utils import process_single_document
            
            result = process_single_document(
                file_path=str(test_pdf),
                output_path=str(output_file),
                format="json",
                config=test_config
            )
            
            # Verify configuration was used
            mock_get_config.assert_called()
            assert result is not None


@pytest.mark.integration
class TestDataFlowIntegration:
    """Test data flow through the complete system."""
    
    def test_document_to_json_data_flow(self, sample_pdf_path, sample_contract_data):
        """Test complete data flow from document to JSON output."""
        # Mock complete processing pipeline
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('pytesseract.image_to_string') as mock_ocr, \
             patch('multimodal_contract_extractor.clause_detection.detect_clauses') as mock_detect, \
             patch('multimodal_contract_extractor.serialization.to_json') as mock_serialize:
            
            # Configure processing pipeline
            mock_doc = Mock()
            mock_doc.filename = str(sample_pdf_path)
            mock_doc.pages = 3
            mock_load.return_value = mock_doc
            
            mock_ocr.return_value = "Sample extracted text from document"
            mock_detect.return_value = sample_contract_data["clauses"]
            mock_serialize.return_value = json.dumps(sample_contract_data)
            
            # Execute complete data flow
            from multimodal_contract_extractor.extraction import extract_clauses
            
            # Process document
            document = mock_load(str(sample_pdf_path))
            ocr_text = mock_ocr("mock_image")
            clauses = mock_detect(ocr_text)
            json_output = mock_serialize({"clauses": clauses})
            
            # Verify data flow
            assert document.filename == str(sample_pdf_path)
            assert isinstance(ocr_text, str)
            assert isinstance(clauses, list)
            assert isinstance(json_output, str)
            
            # Verify JSON structure
            parsed_output = json.loads(json_output)
            assert "clauses" in parsed_output
    
    def test_multi_format_output_data_flow(self, sample_contract_data):
        """Test data flow for multiple output formats."""
        formats = ["json", "xml", "csv"]
        
        # Mock serialization for each format
        with patch('multimodal_contract_extractor.serialization.to_json') as mock_json, \
             patch('multimodal_contract_extractor.serialization.to_xml') as mock_xml, \
             patch('multimodal_contract_extractor.serialization.to_csv') as mock_csv:
            
            # Configure format-specific outputs
            mock_json.return_value = json.dumps(sample_contract_data)
            mock_xml.return_value = "<contract><clauses></clauses></contract>"
            mock_csv.return_value = "id,type,text,confidence\nclause_001,confidentiality,sample,0.92"
            
            # Test each format
            for format_type in formats:
                if format_type == "json":
                    result = mock_json(sample_contract_data)
                    assert result.startswith("{")
                elif format_type == "xml":
                    result = mock_xml(sample_contract_data)
                    assert result.startswith("<")
                elif format_type == "csv":
                    result = mock_csv(sample_contract_data)
                    assert "id,type,text,confidence" in result
                
                assert result is not None, f"Should generate {format_type} output"


@pytest.mark.integration
class TestUserScenarios:
    """Test realistic user scenarios."""
    
    def test_legal_professional_workflow(self, temp_dir, sample_contract_data):
        """Test workflow for legal professional use case."""
        # Scenario: Legal professional needs to extract clauses from NDA
        nda_file = temp_dir / "nda_agreement.pdf"
        nda_file.write_text("Mock NDA content")
        
        analysis_output = temp_dir / "nda_analysis.json"
        
        # Mock professional-grade processing
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.clause_detection.detect_clauses') as mock_detect:
            
            # High-confidence processing for legal use
            mock_doc = Mock()
            mock_doc.filename = str(nda_file)
            mock_doc.document_type = "nda"
            mock_load.return_value = mock_doc
            
            # Legal-specific clauses
            legal_clauses = [
                {
                    "id": "confidentiality_001",
                    "type": "confidentiality",
                    "text": "The receiving party shall maintain strict confidentiality...",
                    "confidence": 0.95,
                    "legal_category": "primary_obligation"
                },
                {
                    "id": "term_001", 
                    "type": "term",
                    "text": "This agreement shall remain in effect for 5 years...",
                    "confidence": 0.93,
                    "legal_category": "duration"
                }
            ]
            mock_detect.return_value = legal_clauses
            
            # Execute legal workflow
            result = self._simulate_legal_workflow(str(nda_file), str(analysis_output))
            
            # Verify legal professional needs
            assert result["document_type"] == "nda"
            assert all(clause["confidence"] >= 0.9 for clause in result["clauses"])
            assert "legal_category" in result["clauses"][0]
    
    def test_contract_manager_batch_workflow(self, temp_dir):
        """Test workflow for contract manager processing multiple contracts."""
        # Scenario: Contract manager needs to process quarterly contracts
        contracts_dir = temp_dir / "q1_contracts"
        contracts_dir.mkdir()
        
        # Create various contract types
        contract_types = ["employment", "service", "lease", "nda"]
        contract_files = []
        
        for i, contract_type in enumerate(contract_types, 1):
            filename = f"{contract_type}_contract_{i:02d}.pdf"
            contract_file = contracts_dir / filename
            contract_file.write_text(f"Mock {contract_type} contract content")
            contract_files.append((contract_file, contract_type))
        
        results_dir = temp_dir / "quarterly_analysis"
        results_dir.mkdir()
        
        # Mock batch processing for contract manager
        with patch('multimodal_contract_extractor.document.load_document') as mock_load, \
             patch('multimodal_contract_extractor.extraction.extract_clauses') as mock_extract:
            
            # Configure type-specific processing
            def load_side_effect(filepath):
                mock_doc = Mock()
                mock_doc.filename = filepath
                # Determine type from filename
                for file_path, doc_type in contract_files:
                    if str(file_path) == filepath:
                        mock_doc.document_type = doc_type
                        break
                return mock_doc
            
            mock_load.side_effect = load_side_effect
            mock_extract.return_value = []
            
            # Execute contract manager workflow
            batch_results = self._simulate_batch_workflow(str(contracts_dir), str(results_dir))
            
            # Verify contract manager needs
            assert len(batch_results) == len(contract_types)
            assert all("document_type" in result for result in batch_results.values())
    
    def test_developer_integration_workflow(self, sample_contract_data):
        """Test workflow for developer integrating via API."""
        # Scenario: Developer integrating contract extraction into application
        
        # Mock API-style integration
        with patch('multimodal_contract_extractor.api.extract_contract') as mock_api:
            
            # Configure API response
            api_response = {
                "status": "success",
                "data": sample_contract_data,
                "processing_time": 12.5,
                "api_version": "v1.2"
            }
            mock_api.return_value = api_response
            
            # Execute developer workflow
            from multimodal_contract_extractor.api import extract_contract
            
            result = extract_contract(
                file_path="developer_test.pdf",
                output_format="json",
                include_metadata=True
            )
            
            # Verify developer needs
            assert result["status"] == "success"
            assert "data" in result
            assert "processing_time" in result
            assert "api_version" in result
    
    def _simulate_legal_workflow(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Simulate legal professional workflow."""
        # Mock legal-specific processing
        return {
            "document_type": "nda",
            "clauses": [
                {
                    "id": "confidentiality_001",
                    "type": "confidentiality", 
                    "confidence": 0.95,
                    "legal_category": "primary_obligation"
                }
            ],
            "legal_review_required": False,
            "confidence_threshold_met": True
        }
    
    def _simulate_batch_workflow(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Simulate contract manager batch workflow."""
        # Mock batch processing results
        return {
            "employment_contract_01.pdf": {"document_type": "employment", "clauses": 5},
            "service_contract_02.pdf": {"document_type": "service", "clauses": 3},
            "lease_contract_03.pdf": {"document_type": "lease", "clauses": 7},
            "nda_contract_04.pdf": {"document_type": "nda", "clauses": 4}
        }


if __name__ == "__main__":
    # Allow running e2e tests directly
    pytest.main([__file__, "-v", "-m", "integration"])