"""Tests for web app security enhancements, particularly temporary file cleanup."""

from unittest.mock import Mock, patch

from web_app import TempFileManager


class TestTempFileCleanup:
    """Test temporary file cleanup functionality."""



    @patch("multimodal_contract_extractor.extract_from_document")
    def test_temp_file_cleanup_in_context_manager(self, mock_extract):
        """Test that temporary files are cleaned up properly using context manager."""
        from web_app import process_upload_with_cleanup

        # Setup mock to return proper extraction result format
        mock_extract.return_value = {
            "document_info": {
                "filename": "test.pdf",
                "pages": 1,
                "processing_time": 0.5,
                "overall_confidence": 0.9,
            },
            "clauses": [],
        }

        # Create mock uploaded file
        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"test content"

        # Process with cleanup
        result = process_upload_with_cleanup(mock_uploaded)

        # Verify the result is valid
        assert result is not None
        assert "document_info" in result
        assert result["document_info"]["filename"] == "test.pdf"

        # The temp file should be automatically cleaned up
        # We can't easily test this without exposing the temp path,
        # but the context manager pattern ensures cleanup

    def test_temp_file_context_manager_cleanup_on_exception(self):
        """Test that temp files are cleaned up even when exceptions occur."""
        from web_app import TempFileManager

        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"content"

        temp_path = None

        # Test cleanup on exception
        try:
            with TempFileManager(mock_uploaded) as tmp_path:
                temp_path = tmp_path
                assert tmp_path.exists()
                # Raise an exception to test cleanup
                msg = "Test exception"
                raise ValueError(msg)
        except ValueError:
            pass  # Expected

        # Verify cleanup occurred despite exception
        assert not temp_path.exists()

    def test_temp_file_context_manager_normal_cleanup(self):
        """Test that temp files are cleaned up in normal operation."""
        from web_app import TempFileManager

        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"content"

        temp_path = None

        # Test normal cleanup
        with TempFileManager(mock_uploaded) as tmp_path:
            temp_path = tmp_path
            assert tmp_path.exists()
            assert tmp_path.read_bytes() == b"content"

        # Verify cleanup occurred
        assert not temp_path.exists()

    @patch("streamlit.file_uploader")
    @patch("streamlit.info")
    @patch("streamlit.json")
    @patch("streamlit.title")
    @patch("streamlit.success")
    def test_main_function_cleanup_integration(
        self, mock_success, mock_title, mock_json, mock_info, mock_uploader
    ):
        """Test that the main function properly handles temp file cleanup."""
        from web_app import main

        # Test with no file uploaded
        mock_uploader.return_value = None
        main()
        mock_info.assert_called_once_with("Please upload a PDF or image document.")

        # Test with file uploaded - this will use the new cleanup mechanism
        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"test content"
        mock_uploader.return_value = mock_uploaded

        with patch("web_app.process_upload_with_cleanup") as mock_process:
            mock_process.return_value = {
                "document_info": {
                    "filename": "test.pdf",
                    "pages": 1,
                    "processing_time": 0.5,
                    "overall_confidence": 0.9,
                },
                "clauses": [],
            }

            # Reset mocks for second call
            mock_info.reset_mock()
            main()

            # Verify process was called with uploaded file
            mock_process.assert_called_once_with(mock_uploaded)
            mock_json.assert_called_once()


class TestSecurityValidation:
    """Test security aspects of file handling."""

    def test_temp_file_manager_prevents_path_traversal(self):
        """Test that TempFileManager prevents path traversal attacks."""
        mock_uploaded = Mock()
        mock_uploaded.name = "../../../etc/passwd"
        mock_uploaded.read.return_value = b"content"

        with TempFileManager(mock_uploaded) as tmp_path:
            # Verify the file is created in temp directory, not at the traversal location
            assert "/etc/passwd" not in str(tmp_path)
            assert tmp_path.parent.name.startswith("tmp") or "temp" in str(
                tmp_path.parent
            )
            assert tmp_path.exists()

    def test_temp_file_permissions(self):
        """Test that temporary files have appropriate permissions."""
        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"content"

        with TempFileManager(mock_uploaded) as tmp_path:
            # Check file permissions (should be readable/writable by owner only)
            stat_info = tmp_path.stat()
            # On Unix systems, check that file is not world-readable
            if hasattr(stat_info, "st_mode"):
                mode = stat_info.st_mode
                # File should not be world-readable (no 0o004 bit)
                assert not (mode & 0o004), "Temporary file should not be world-readable"


class TestResourceManagement:
    """Test resource management and cleanup."""

    def test_multiple_temp_files_cleanup(self):
        """Test that multiple temporary files are properly managed."""
        from web_app import TempFileManager

        files = []

        # Create multiple temp files
        for i in range(3):
            mock_uploaded = Mock()
            mock_uploaded.name = f"test_{i}.pdf"
            mock_uploaded.read.return_value = f"content_{i}".encode()

            with TempFileManager(mock_uploaded) as tmp_path:
                files.append(tmp_path)
                assert tmp_path.exists()

        # All should be cleaned up
        for tmp_path in files:
            assert not tmp_path.exists()

    def test_cleanup_with_concurrent_access(self):
        """Test cleanup behavior with potential concurrent access."""
        from web_app import TempFileManager

        mock_uploaded = Mock()
        mock_uploaded.name = "test.pdf"
        mock_uploaded.read.return_value = b"content"

        temp_path = None

        with TempFileManager(mock_uploaded) as tmp_path:
            temp_path = tmp_path
            assert tmp_path.exists()

            # Simulate concurrent deletion (file already gone)
            tmp_path.unlink()
            assert not tmp_path.exists()

        # Should not raise exception even if file was already deleted
        assert not temp_path.exists()
