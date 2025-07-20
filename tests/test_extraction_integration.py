"""Integration tests for end-to-end extraction functionality."""

import tempfile
from pathlib import Path

from multimodal_contract_extractor.document import load_document
from multimodal_contract_extractor.clause_detection import detect_clauses
from tests.test_helpers import create_test_pdf


class TestExtractionIntegration:
    """Test complete extraction pipeline from document to JSON output."""

    def test_extract_clauses_from_pdf(self):
        """Test that we can extract clauses from a PDF and get structured output."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, "This contract contains confidentiality clauses and termination terms.")
        
        try:
            # Load document and detect clauses
            document = load_document(tmp_path)
            clauses = detect_clauses(document)
            
            # Should find at least one clause
            assert len(clauses) > 0
            
            # Verify clause structure
            clause = clauses[0]
            assert hasattr(clause, 'type')
            assert hasattr(clause, 'text')
            assert hasattr(clause, 'page')
            assert clause.page > 0
            
        finally:
            tmp_path.unlink()

    def test_extraction_creates_proper_json_structure(self):
        """Test that extraction output matches the documented JSON format."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, "Confidential information must be protected. Payment terms are net 30.")
        
        try:
            # This will test our new extraction function
            from multimodal_contract_extractor import extract_from_document
            
            result = extract_from_document(tmp_path)
            
            # Verify top-level structure
            assert 'document_info' in result
            assert 'clauses' in result
            assert 'metadata' in result
            
            # Verify document_info structure
            doc_info = result['document_info']
            assert 'filename' in doc_info
            assert 'pages' in doc_info
            assert 'processing_time' in doc_info
            assert 'overall_confidence' in doc_info
            
            # Verify clauses structure
            if result['clauses']:
                clause = result['clauses'][0]
                assert 'id' in clause
                assert 'type' in clause
                assert 'text' in clause
                assert 'page' in clause
                assert 'confidence' in clause
            
            # Verify metadata structure
            metadata = result['metadata']
            assert 'extraction_timestamp' in metadata
            assert 'model_version' in metadata
            assert 'processing_method' in metadata
            
        finally:
            tmp_path.unlink()

    def test_extraction_handles_no_clauses_found(self):
        """Test extraction when no clauses are detected."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, "This is just plain text with no legal clauses.")
        
        try:
            from multimodal_contract_extractor import extract_from_document
            
            result = extract_from_document(tmp_path)
            
            # Should still have valid structure
            assert 'document_info' in result
            assert 'clauses' in result
            assert 'metadata' in result
            
            # Clauses array should be empty
            assert isinstance(result['clauses'], list)
            assert len(result['clauses']) == 0
            
        finally:
            tmp_path.unlink()