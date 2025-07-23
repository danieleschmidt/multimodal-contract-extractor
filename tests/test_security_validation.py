"""Tests for security validation and input sanitization."""

from pathlib import Path

import pytest

from multimodal_contract_extractor.security import (
    SecurityError,
    check_file_size_limit,
    sanitize_file_path,
    validate_file_input,
    validate_file_type,
)


class TestFileValidation:
    """Test file input validation and sanitization."""

    def test_validate_file_input_valid_pdf(self, tmp_path):
        """Test validation of valid PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        result = validate_file_input(pdf_file)
        assert result == pdf_file

    def test_validate_file_input_valid_image(self, tmp_path):
        """Test validation of valid image file."""
        img_file = tmp_path / "test.png"
        # Simple PNG header
        img_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        result = validate_file_input(img_file)
        assert result == img_file

    def test_validate_file_input_nonexistent_file(self):
        """Test validation fails for nonexistent file."""
        with pytest.raises(SecurityError, match="File does not exist"):
            validate_file_input(Path("/nonexistent/file.pdf"))

    def test_validate_file_input_directory(self, tmp_path):
        """Test validation fails for directory."""
        with pytest.raises(SecurityError, match="Path is not a regular file"):
            validate_file_input(tmp_path)

    def test_validate_file_input_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()

        with pytest.raises(SecurityError, match="File is empty"):
            validate_file_input(empty_file)

    def test_validate_file_input_unsupported_type(self, tmp_path):
        """Test validation fails for unsupported file type."""
        exe_file = tmp_path / "malware.exe"
        exe_file.write_bytes(b"MZ\x90\x00")  # PE header

        with pytest.raises(SecurityError, match="Unsupported file type"):
            validate_file_input(exe_file)


class TestPathSanitization:
    """Test path sanitization functions."""

    def test_sanitize_file_path_normal(self):
        """Test sanitization of normal file path."""
        result = sanitize_file_path("document.pdf")
        assert result == "document.pdf"

    def test_sanitize_file_path_with_spaces(self):
        """Test sanitization replaces spaces with underscores."""
        result = sanitize_file_path("my document.pdf")
        assert result == "my_document.pdf"

    def test_sanitize_file_path_removes_dangerous_chars(self):
        """Test sanitization removes potentially dangerous characters."""
        result = sanitize_file_path("../../../etc/passwd")
        assert result == "______etc_passwd"

    def test_sanitize_file_path_removes_null_bytes(self):
        """Test sanitization removes null bytes."""
        result = sanitize_file_path("file\x00.pdf")
        assert result == "file_.pdf"

    def test_sanitize_file_path_preserves_extension(self):
        """Test sanitization preserves valid file extensions."""
        result = sanitize_file_path("document.PDF")
        assert result == "document.PDF"


class TestFileSizeLimit:
    """Test file size validation."""

    def test_check_file_size_limit_within_limit(self, tmp_path):
        """Test file size check passes for files within limit."""
        small_file = tmp_path / "small.pdf"
        small_file.write_bytes(b"small content")

        # Should not raise
        check_file_size_limit(small_file, max_size_mb=100)

    def test_check_file_size_limit_exceeds_limit(self, tmp_path):
        """Test file size check fails for files exceeding limit."""
        large_file = tmp_path / "large.pdf"
        large_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

        with pytest.raises(SecurityError, match="File size.*exceeds limit"):
            check_file_size_limit(large_file, max_size_mb=1)

    def test_check_file_size_limit_default_limit(self, tmp_path):
        """Test file size check uses default limit."""
        normal_file = tmp_path / "normal.pdf"
        normal_file.write_bytes(b"normal content")

        # Should not raise with default 100MB limit
        check_file_size_limit(normal_file)


class TestFileTypeValidation:
    """Test file type validation."""

    def test_validate_file_type_pdf(self, tmp_path):
        """Test PDF file type validation."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest content")

        assert validate_file_type(pdf_file) == "pdf"

    def test_validate_file_type_png(self, tmp_path):
        """Test PNG file type validation."""
        png_file = tmp_path / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\ntest")

        assert validate_file_type(png_file) == "image"

    def test_validate_file_type_jpeg(self, tmp_path):
        """Test JPEG file type validation."""
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(b"\xff\xd8\xff\xe0test")

        assert validate_file_type(jpg_file) == "image"

    def test_validate_file_type_unsupported(self, tmp_path):
        """Test unsupported file type detection."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("plain text")

        with pytest.raises(SecurityError, match="Unsupported file type"):
            validate_file_type(txt_file)

    def test_validate_file_type_by_extension_fallback(self, tmp_path):
        """Test file type validation falls back to extension."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("not a real pdf")  # Wrong content but .pdf extension

        # Should still validate based on extension as fallback
        assert validate_file_type(pdf_file) == "pdf"


class TestSecurityIntegration:
    """Test security validation integration."""

    def test_full_validation_pipeline(self, tmp_path):
        """Test complete security validation pipeline."""
        # Create a valid PDF file
        pdf_file = tmp_path / "contract.pdf"
        pdf_content = b"%PDF-1.4\n" + b"dummy content" * 100
        pdf_file.write_bytes(pdf_content)

        # Should pass all validations
        result = validate_file_input(pdf_file)
        assert result == pdf_file

    def test_validation_with_suspicious_filename(self, tmp_path):
        """Test validation handles suspicious filenames."""
        # Create file with normal name but test path sanitization separately
        normal_file = tmp_path / "normal.pdf"
        pdf_content = b"%PDF-1.4\ndummy content"
        normal_file.write_bytes(pdf_content)

        # Test that sanitization works on the filename
        suspicious_name = "../../../etc/passwd.pdf"
        sanitized_name = sanitize_file_path(suspicious_name)
        assert "___" in sanitized_name  # Path components are sanitized

        # Validation should work on actual file
        result = validate_file_input(normal_file)
        assert result == normal_file.resolve()
