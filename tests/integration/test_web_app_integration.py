"""Integration tests for the web application with real document processing."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.test_helpers import create_test_pdf
from web_app import TempFileManager, process_upload_with_cleanup


class TestWebAppIntegration:
    """Test complete web application workflows with real processing."""

    def test_process_upload_with_cleanup_full_workflow(self):
        """Test complete upload processing workflow with real extraction."""
        # Create mock uploaded file with contract content
        mock_uploaded = Mock()
        mock_uploaded.name = "employment_contract.pdf"

        # Create actual PDF content for processing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "EMPLOYMENT AGREEMENT\n\n"
                "Employee agrees to maintain confidentiality of company information.\n"
                "Employment may be terminated by either party with 2 weeks notice.\n"
                "Base salary is $75,000 annually, paid bi-weekly.",
            )

            # Read PDF content for mock
            pdf_content = tmp_path.read_bytes()
            mock_uploaded.read.return_value = pdf_content

        try:
            # Process upload with cleanup
            result = process_upload_with_cleanup(mock_uploaded)

            # Verify result structure
            assert isinstance(result, dict)
            assert "document_info" in result
            assert "clauses" in result
            assert "metadata" in result

            # Verify document info
            doc_info = result["document_info"]
            assert doc_info["filename"] == "employment_contract.pdf"
            assert doc_info["pages"] > 0
            assert doc_info["processing_time"] > 0
            assert 0 <= doc_info["overall_confidence"] <= 1

            # Should detect clauses from employment contract
            clauses = result["clauses"]
            assert len(clauses) > 0, "Should detect clauses in employment contract"

            # Verify clause structure
            for clause in clauses:
                assert "id" in clause
                assert "type" in clause
                assert "text" in clause
                assert "page" in clause
                assert "confidence" in clause
                assert clause["page"] > 0
                assert 0 <= clause["confidence"] <= 1

            # Verify metadata
            metadata = result["metadata"]
            assert "extraction_timestamp" in metadata
            assert "model_version" in metadata
            assert "processing_method" in metadata

        finally:
            # Clean up test PDF
            if tmp_path.exists():
                tmp_path.unlink()

    def test_temp_file_manager_with_real_processing(self):
        """Test TempFileManager context manager with actual document processing."""
        # Create mock uploaded file
        mock_uploaded = Mock()
        mock_uploaded.name = "nda_contract.pdf"

        # Create real PDF content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(
                tmp_path,
                "NON-DISCLOSURE AGREEMENT\n\n"
                "Recipient agrees to keep all confidential information secret.\n"
                "This agreement is effective for 5 years from signing date.\n"
                "Violation may result in immediate legal action.",
            )
            pdf_content = tmp_path.read_bytes()
            mock_uploaded.read.return_value = pdf_content

        temp_file_path = None

        try:
            # Use context manager for secure processing
            with TempFileManager(mock_uploaded) as temp_path:
                temp_file_path = temp_path

                # Verify temp file was created and has content
                assert temp_path.exists()
                assert temp_path.is_file()
                assert temp_path.stat().st_size > 0

                # Verify file permissions are restrictive (owner only)
                stat_info = temp_path.stat()
                if hasattr(stat_info, "st_mode"):
                    mode = stat_info.st_mode
                    # Should not be world-readable (no 0o004 bit)
                    assert not (mode & 0o004), "Temp file should not be world-readable"

                # Process the document
                from multimodal_contract_extractor import extract_from_document
                result = extract_from_document(temp_path)

                # Verify processing succeeded
                assert "document_info" in result
                assert "clauses" in result
                assert len(result["clauses"]) > 0

            # After context exit, temp file should be cleaned up
            assert not temp_file_path.exists(), "Temp file should be cleaned up"

        finally:
            # Clean up test PDF
            if tmp_path.exists():
                tmp_path.unlink()

    def test_web_app_error_handling_with_corrupted_file(self):
        """Test web app handles corrupted files gracefully."""
        mock_uploaded = Mock()
        mock_uploaded.name = "corrupted.pdf"
        mock_uploaded.read.return_value = b"This is not a valid PDF file"

        # Processing should raise an exception but temp file should still be cleaned
        with pytest.raises(Exception):
            process_upload_with_cleanup(mock_uploaded)

    def test_multiple_concurrent_uploads(self):
        """Test handling multiple file uploads concurrently."""
        upload_files = []

        # Create multiple mock uploads with different content
        contract_texts = [
            "Service Agreement: Payment due within 30 days.",
            "Lease Agreement: Tenant responsible for utilities.",
            "Purchase Order: Delivery within 2 weeks required.",
        ]

        for i, text in enumerate(contract_texts):
            mock_uploaded = Mock()
            mock_uploaded.name = f"contract_{i+1}.pdf"

            # Create real PDF content
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                create_test_pdf(tmp_path, text)
                pdf_content = tmp_path.read_bytes()
                mock_uploaded.read.return_value = pdf_content
                upload_files.append((mock_uploaded, tmp_path))

        results = []

        try:
            # Process all uploads
            for mock_uploaded, _ in upload_files:
                result = process_upload_with_cleanup(mock_uploaded)
                results.append(result)

            # Verify all processed successfully
            assert len(results) == 3

            for i, result in enumerate(results):
                assert "document_info" in result
                assert "clauses" in result
                assert result["document_info"]["filename"] == f"contract_{i+1}.pdf"

        finally:
            # Clean up test PDFs
            for _, tmp_path in upload_files:
                if tmp_path.exists():
                    tmp_path.unlink()

    def test_web_app_with_large_file(self):
        """Test web app processes larger PDF files correctly."""
        mock_uploaded = Mock()
        mock_uploaded.name = "large_contract.pdf"

        # Create PDF with substantial content to test streaming/chunking
        large_content = (
            "COMPREHENSIVE SERVICE AGREEMENT\n\n"
            "Section 1: Confidentiality\n"
            "All information shared must remain confidential.\n\n"
            "Section 2: Payment Terms\n"
            "Payment is due net 30 days from invoice.\n\n"
            "Section 3: Termination\n"
            "Either party may terminate with 60 days written notice.\n\n"
            "Section 4: Liability\n"
            "Liability is limited to the contract value.\n\n"
            "Section 5: Intellectual Property\n"
            "All IP created remains property of the company.\n\n" +
            # Repeat content to make it larger
            ("Additional terms and conditions follow. " * 100)
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, large_content)
            pdf_content = tmp_path.read_bytes()
            mock_uploaded.read.return_value = pdf_content

        try:
            result = process_upload_with_cleanup(mock_uploaded)

            # Verify processing succeeded
            assert "document_info" in result
            assert "clauses" in result
            assert result["document_info"]["pages"] > 0

            # Should find multiple clauses due to rich content
            assert len(result["clauses"]) > 1

            # Processing time should be reasonable (not timeout)
            assert result["document_info"]["processing_time"] < 60  # seconds

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @patch("streamlit.title")
    @patch("streamlit.file_uploader")
    @patch("streamlit.info")
    @patch("streamlit.json")
    @patch("streamlit.success")
    @patch("streamlit.error")
    def test_main_function_complete_workflow(self, mock_error, mock_success,
                                           mock_json, mock_info, mock_uploader, mock_title):
        """Test main function with complete Streamlit integration."""
        from web_app import main

        # Test with file upload
        mock_uploaded = Mock()
        mock_uploaded.name = "test_contract.pdf"

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            create_test_pdf(tmp_path, "Contract with confidentiality and payment terms.")
            pdf_content = tmp_path.read_bytes()
            mock_uploaded.read.return_value = pdf_content

        mock_uploader.return_value = mock_uploaded

        try:
            # Run main function
            main()

            # Verify Streamlit interactions
            mock_title.assert_called_once_with("Multimodal Contract Extractor")
            mock_uploader.assert_called_once_with("Upload contract file")
            mock_json.assert_called_once()  # JSON result displayed
            mock_success.assert_called_once()  # Success message shown
            mock_error.assert_not_called()  # No errors

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @patch("streamlit.title")
    @patch("streamlit.file_uploader")
    @patch("streamlit.info")
    @patch("streamlit.error")
    def test_main_function_error_handling(self, mock_error, mock_info,
                                        mock_uploader, mock_title):
        """Test main function handles processing errors gracefully."""
        from web_app import main

        # Test with corrupted file
        mock_uploaded = Mock()
        mock_uploaded.name = "corrupted.pdf"
        mock_uploaded.read.return_value = b"Invalid PDF content"
        mock_uploader.return_value = mock_uploaded

        # Run main function
        main()

        # Should display error message
        mock_error.assert_called_once()
        error_args = mock_error.call_args[0]
        assert "Error processing document" in error_args[0]
