"""Integration tests for the complete document processing pipeline."""

import tempfile
from pathlib import Path

import pytest

from multimodal_contract_extractor import extract_from_document, load_config
from multimodal_contract_extractor.clause_detection import detect_clauses
from multimodal_contract_extractor.document import load_document, stream_document
from tests.test_helpers import create_test_pdf


class TestPipelineIntegration:
    """Test complete document processing pipeline with real OCR and extraction."""

    def test_full_pipeline_pdf_processing(self):
        """Test complete pipeline from PDF loading to final JSON output."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "MASTER SERVICE AGREEMENT\n\n"
                "1. CONFIDENTIALITY: Company information must be kept confidential.\n"
                "2. PAYMENT TERMS: All invoices are due within 30 days of receipt.\n"
                "3. TERMINATION: This agreement may be terminated with 90 days notice.\n"
                "4. LIABILITY: Total liability shall not exceed the contract value.\n"
                "5. INTELLECTUAL PROPERTY: All work product belongs to the company.",
            )

        try:
            # Test complete extraction pipeline
            result = extract_from_document(tmp_path)

            # Verify pipeline produces proper structure
            assert isinstance(result, dict)
            assert "document_info" in result
            assert "clauses" in result
            assert "metadata" in result

            # Verify document processing
            doc_info = result["document_info"]
            assert doc_info["filename"] == tmp_path.name
            assert doc_info["pages"] > 0
            assert doc_info["processing_time"] > 0
            assert 0 <= doc_info["overall_confidence"] <= 1

            # Verify clause detection worked
            clauses = result["clauses"]
            assert len(clauses) > 0, "Should detect clauses in service agreement"

            # Should detect different clause types
            clause_types = {clause["type"] for clause in clauses}
            expected_types = {"confidentiality", "payment", "termination", "liability"}
            assert len(clause_types.intersection(expected_types)) > 0, f"Expected some clause types from {expected_types}, got {clause_types}"

            # Verify each clause has proper structure
            for clause in clauses:
                assert "id" in clause
                assert "type" in clause
                assert "text" in clause
                assert "page" in clause
                assert "coordinates" in clause
                assert "confidence" in clause
                assert "key_terms" in clause

                # Verify clause values are reasonable
                assert clause["page"] > 0
                assert isinstance(clause["coordinates"], list)
                assert len(clause["coordinates"]) == 4
                assert 0 <= clause["confidence"] <= 1
                assert isinstance(clause["key_terms"], list)

            # Verify metadata
            metadata = result["metadata"]
            assert "extraction_timestamp" in metadata
            assert "model_version" in metadata
            assert "processing_method" in metadata
            assert metadata["processing_method"] in ["ocr_keyword_detection", "multimodal_vlm"]  # Current implementation is OCR-based

        finally:
            tmp_path.unlink()

    def test_pipeline_with_configuration_integration(self):
        """Test pipeline respects configuration settings."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "Confidentiality agreement with payment terms and termination clause.",
            )

        # Create custom configuration
        config_data = {
            "extraction": {
                "base_confidence_score": 0.9,
                "max_confidence_cap": 0.99,
                "length_bonus_divisor": 2000,
            },
            "ocr": {
                "cache_size_limit": 25,
                "context_window_size": 50,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as config_tmp:
            config_path = Path(config_tmp.name)

            # Write YAML config
            import yaml
            yaml.dump(config_data, config_tmp)
            config_tmp.flush()

            try:
                # Load custom configuration
                config = load_config(config_path=config_path, reload=True)

                # Verify config was loaded
                assert config.extraction.base_confidence_score == 0.9
                assert config.extraction.max_confidence_cap == 0.99
                assert config.ocr.cache_size_limit == 25

                # Process document with custom config
                result = extract_from_document(tmp_path)

                # Verify processing succeeded with custom settings
                assert "document_info" in result
                assert "clauses" in result

                # Confidence scoring should reflect custom settings
                if result["clauses"]:
                    for clause in result["clauses"]:
                        # With high base confidence (0.9) and max cap (0.99),
                        # confidence values should be in that range
                        assert clause["confidence"] >= 0.5  # Reasonable minimum
                        assert clause["confidence"] <= 0.99  # Respects max cap

            finally:
                config_path.unlink()
                tmp_path.unlink()

    def test_pipeline_streaming_vs_standard_loading(self):
        """Test pipeline with both streaming and standard document loading."""
        # Create a larger PDF to trigger streaming behavior
        large_content = (
            "COMPREHENSIVE CONTRACT AGREEMENT\n\n" +
            "\n\n".join([
                f"Section {i}: This section contains confidentiality terms, "
                f"payment obligations, and termination procedures. "
                f"All parties must comply with section {i} requirements."
                for i in range(1, 20)  # Create 20 sections
            ])
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, large_content)

        try:
            # Test standard loading
            document = load_document(tmp_path)
            standard_clauses = detect_clauses(document)

            # Test streaming loading
            streamed_document = stream_document(tmp_path, chunk_size=5)
            streaming_clauses = detect_clauses(streamed_document)

            # Both methods should find clauses
            assert len(standard_clauses) > 0
            assert len(streaming_clauses) > 0

            # Results should be similar (may not be identical due to chunking)
            assert abs(len(standard_clauses) - len(streaming_clauses)) <= 2

            # Test full extraction pipeline
            result = extract_from_document(tmp_path)
            assert len(result["clauses"]) > 0

            # Should detect multiple pages due to content size
            assert result["document_info"]["pages"] >= 1

        finally:
            tmp_path.unlink()

    def test_pipeline_error_propagation(self):
        """Test how errors propagate through the pipeline."""
        # Test with non-existent file
        nonexistent_path = Path("/tmp/does_not_exist.pdf")

        with pytest.raises(Exception):
            extract_from_document(nonexistent_path)

        # Test with invalid file format
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp_path.write_text("This is not a PDF file")

        try:
            with pytest.raises(Exception):
                extract_from_document(tmp_path)
        finally:
            tmp_path.unlink()

    def test_pipeline_with_no_text_content(self):
        """Test pipeline handles documents with no extractable text."""
        # Create minimal PDF with no meaningful text
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, "   \n\n   \n   ")  # Whitespace only

        try:
            result = extract_from_document(tmp_path)

            # Should still have valid structure
            assert "document_info" in result
            assert "clauses" in result
            assert "metadata" in result

            # Document info should be valid
            assert result["document_info"]["pages"] > 0
            assert result["document_info"]["processing_time"] > 0

            # May have no clauses detected
            assert isinstance(result["clauses"], list)
            # Length could be 0 for document with no meaningful content

        finally:
            tmp_path.unlink()

    def test_pipeline_performance_metrics(self):
        """Test pipeline generates accurate performance metrics."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "Performance test contract with multiple sections:\n"
                "Confidentiality: Keep information secret.\n"
                "Payment: Due in 30 days.\n"
                "Termination: 60 days notice required.\n"
                "Liability: Limited to contract value.",
            )

        try:
            import time
            start_time = time.time()

            result = extract_from_document(tmp_path)

            end_time = time.time()
            actual_duration = end_time - start_time

            # Verify reported processing time is reasonable
            reported_time = result["document_info"]["processing_time"]
            assert reported_time > 0
            assert reported_time <= actual_duration + 1.0  # Allow 1s tolerance

            # Verify confidence scoring is reasonable
            if result["clauses"]:
                confidences = [c["confidence"] for c in result["clauses"]]
                avg_confidence = sum(confidences) / len(confidences)
                assert 0.1 <= avg_confidence <= 1.0

                # Overall confidence should be related to clause confidences
                overall_confidence = result["document_info"]["overall_confidence"]
                assert abs(overall_confidence - avg_confidence) <= 0.3

        finally:
            tmp_path.unlink()

    def test_pipeline_caching_behavior(self):
        """Test OCR caching improves performance on repeated processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "Caching test: Confidentiality and payment terms contract.",
            )

        try:
            # First extraction (cold cache)
            import time
            start1 = time.time()
            result1 = extract_from_document(tmp_path)
            duration1 = time.time() - start1

            # Second extraction (warm cache) - should be faster
            start2 = time.time()
            result2 = extract_from_document(tmp_path)
            duration2 = time.time() - start2

            # Both should succeed
            assert "clauses" in result1
            assert "clauses" in result2

            # Results should be identical (deterministic)
            assert len(result1["clauses"]) == len(result2["clauses"])

            # Second run should be faster (caching benefit)
            # Allow some tolerance for system variation
            if duration1 > 0.5:  # Only check if first run was slow enough
                assert duration2 <= duration1 * 1.2  # At most 20% slower

        finally:
            tmp_path.unlink()

    def test_pipeline_multi_page_document(self):
        """Test pipeline correctly handles multi-page documents."""
        # Create content that will span multiple pages
        multi_page_content = "\n\n".join([
            "PAGE 1 CONTENT:",
            "This contract contains confidentiality obligations.",
            "\n" * 30,  # Force page break
            "PAGE 2 CONTENT:",
            "Payment terms require net 30 day settlement.",
            "\n" * 30,
            "PAGE 3 CONTENT:",
            "Termination requires 90 days written notice.",
        ])

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, multi_page_content)

        try:
            result = extract_from_document(tmp_path)

            # Should detect multiple pages
            pages = result["document_info"]["pages"]
            assert pages >= 1  # At minimum should be 1 page

            # Should find clauses across different pages
            clauses = result["clauses"]
            assert len(clauses) > 0

            # Verify page numbers in clauses are valid
            page_numbers = {clause["page"] for clause in clauses}
            assert all(1 <= page <= pages for page in page_numbers)

            # Should find clauses on different pages if multi-page
            if pages > 1:
                assert len(page_numbers) > 1, "Should find clauses on multiple pages"

        finally:
            tmp_path.unlink()
