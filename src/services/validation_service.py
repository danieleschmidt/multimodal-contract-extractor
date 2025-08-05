"""Document validation service with comprehensive security and format checks."""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import List, Optional, Set

from PIL import Image

from ..models.processing import ValidationResult

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating input documents before processing."""

    # Supported file types and extensions
    SUPPORTED_EXTENSIONS: Set[str] = {
        '.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'
    }

    SUPPORTED_MIME_TYPES: Set[str] = {
        'application/pdf',
        'image/png', 'image/jpeg', 'image/tiff', 'image/bmp'
    }

    # Security limits
    MAX_FILE_SIZE_MB: int = 100
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Content validation
    MIN_FILE_SIZE_BYTES: int = 100  # Minimum viable file size
    MAX_PAGES: int = 500  # Maximum pages to process

    def __init__(self, max_file_size_mb: Optional[int] = None):
        """
        Initialize validation service.
        
        Args:
            max_file_size_mb: Override default maximum file size
        """
        if max_file_size_mb:
            self.MAX_FILE_SIZE_MB = max_file_size_mb
            self.MAX_FILE_SIZE_BYTES = max_file_size_mb * 1024 * 1024

    def validate_document(self, file_path: Path) -> ValidationResult:
        """
        Perform comprehensive validation of a document file.
        
        Args:
            file_path: Path to the document to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult(is_valid=True)

        try:
            # Basic file existence and accessibility
            if not self._validate_file_existence(file_path, result):
                return result

            # File size validation
            if not self._validate_file_size(file_path, result):
                return result

            # File type and extension validation
            if not self._validate_file_type(file_path, result):
                return result

            # Content validation (format-specific)
            if not self._validate_file_content(file_path, result):
                return result

            # Security validation
            if not self._validate_security(file_path, result):
                return result

            # Performance validation (file complexity)
            self._validate_performance_factors(file_path, result)

            logger.info(f"Document validation passed for {file_path}")
            return result

        except Exception as e:
            logger.exception(f"Validation failed for {file_path}: {str(e)}")
            result.add_error(f"Validation error: {str(e)}")
            return result

    def _validate_file_existence(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate that file exists and is accessible."""
        if not file_path.exists():
            result.add_error(f"File does not exist: {file_path}")
            return False

        if not file_path.is_file():
            result.add_error(f"Path is not a file: {file_path}")
            return False

        if not os.access(file_path, os.R_OK):
            result.add_error(f"File is not readable: {file_path}")
            return False

        return True

    def _validate_file_size(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate file size within acceptable limits."""
        try:
            file_size = file_path.stat().st_size
            result.file_size_bytes = file_size

            if file_size < self.MIN_FILE_SIZE_BYTES:
                result.add_error(f"File too small: {file_size} bytes (minimum: {self.MIN_FILE_SIZE_BYTES})")
                return False

            if file_size > self.MAX_FILE_SIZE_BYTES:
                result.add_error(
                    f"File too large: {file_size // (1024*1024)}MB "
                    f"(maximum: {self.MAX_FILE_SIZE_MB}MB)"
                )
                return False

            # Add warning for large files
            if file_size > 50 * 1024 * 1024:  # 50MB
                result.add_warning(
                    f"Large file detected: {file_size // (1024*1024)}MB. "
                    "Processing may take longer."
                )

            return True

        except OSError as e:
            result.add_error(f"Could not read file size: {str(e)}")
            return False

    def _validate_file_type(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate file type and extension."""
        # Check file extension
        extension = file_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            result.add_error(
                f"Unsupported file extension: {extension}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
            return False

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        result.file_type = mime_type

        if mime_type and mime_type not in self.SUPPORTED_MIME_TYPES:
            result.add_warning(
                f"Unexpected MIME type: {mime_type}. "
                "File will be processed based on extension."
            )

        return True

    def _validate_file_content(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate file content and structure."""
        extension = file_path.suffix.lower()

        if extension == '.pdf':
            return self._validate_pdf_content(file_path, result)
        elif extension in {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}:
            return self._validate_image_content(file_path, result)

        # Should not reach here due to earlier type validation
        result.add_error("Unsupported file type for content validation")
        return False

    def _validate_pdf_content(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate PDF file content and structure."""
        try:
            from pdf2image import convert_from_path, pdfinfo_from_path

            # Get PDF info
            try:
                info = pdfinfo_from_path(str(file_path))
                pages = int(info.get('Pages', 0))
                result.pages_detected = pages

                if pages == 0:
                    result.add_error("PDF contains no pages")
                    return False

                if pages > self.MAX_PAGES:
                    result.add_error(
                        f"PDF has too many pages: {pages} (maximum: {self.MAX_PAGES})"
                    )
                    return False

                if pages > 100:
                    result.add_warning(
                        f"Large PDF detected: {pages} pages. "
                        "Consider using streaming processing."
                    )

            except Exception as e:
                result.add_warning(f"Could not read PDF metadata: {str(e)}")

            # Test PDF conversion (first page only)
            try:
                images = convert_from_path(str(file_path), first_page=1, last_page=1)
                if not images:
                    result.add_error("PDF conversion failed - no images generated")
                    return False

                # Validate the converted image
                test_image = images[0]
                if test_image.size[0] < 100 or test_image.size[1] < 100:
                    result.add_warning("PDF pages appear to be very small")

            except Exception as e:
                result.add_error(f"PDF conversion test failed: {str(e)}")
                return False

            return True

        except ImportError:
            result.add_error("PDF processing libraries not available")
            return False
        except Exception as e:
            result.add_error(f"PDF validation failed: {str(e)}")
            return False

    def _validate_image_content(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate image file content and properties."""
        try:
            with Image.open(file_path) as img:
                result.pages_detected = 1

                # Check image dimensions
                width, height = img.size

                if width < 100 or height < 100:
                    result.add_error(
                        f"Image too small: {width}x{height} "
                        "(minimum: 100x100 pixels)"
                    )
                    return False

                if width > 10000 or height > 10000:
                    result.add_warning(
                        f"Very large image: {width}x{height} pixels. "
                        "Processing may be slow."
                    )

                # Check image mode
                if img.mode not in {'RGB', 'RGBA', 'L', 'P'}:
                    result.add_warning(
                        f"Unusual image mode: {img.mode}. "
                        "Image will be converted for processing."
                    )

                # Verify image can be processed
                try:
                    img.verify()
                except Exception as e:
                    result.add_error(f"Image verification failed: {str(e)}")
                    return False

            return True

        except Exception as e:
            result.add_error(f"Image validation failed: {str(e)}")
            return False

    def _validate_security(self, file_path: Path, result: ValidationResult) -> bool:
        """Perform security validation checks."""
        # Check for suspicious file names
        filename = file_path.name.lower()

        suspicious_patterns = [
            'script', 'exec', 'cmd', 'bash', 'sh',
            '..', '__', 'system', 'root'
        ]

        for pattern in suspicious_patterns:
            if pattern in filename:
                result.add_warning(f"Suspicious filename pattern detected: {pattern}")

        # Check file permissions (Unix systems)
        try:
            stat_info = file_path.stat()

            # Check if file is executable
            if stat_info.st_mode & 0o111:
                result.add_warning("File has executable permissions")

        except Exception:
            pass  # Ignore permission check failures on non-Unix systems

        # Basic magic number validation
        if not self._validate_magic_numbers(file_path, result):
            return False

        return True

    def _validate_magic_numbers(self, file_path: Path, result: ValidationResult) -> bool:
        """Validate file magic numbers match expected format."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)

            extension = file_path.suffix.lower()

            # PDF magic number
            if extension == '.pdf':
                if not header.startswith(b'%PDF'):
                    result.add_error("File does not appear to be a valid PDF")
                    return False

            # Image magic numbers
            elif extension in {'.png'}:
                if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                    result.add_error("File does not appear to be a valid PNG")
                    return False

            elif extension in {'.jpg', '.jpeg'}:
                if not header.startswith(b'\xff\xd8\xff'):
                    result.add_error("File does not appear to be a valid JPEG")
                    return False

            # For other formats, rely on PIL validation

            return True

        except Exception as e:
            result.add_warning(f"Could not validate file magic numbers: {str(e)}")
            return True  # Don't fail validation for this

    def _validate_performance_factors(self, file_path: Path, result: ValidationResult) -> None:
        """Assess factors that might impact processing performance."""
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            # Large file warnings
            if file_size_mb > 20:
                result.add_warning(
                    f"Large file ({file_size_mb:.1f}MB) may require additional processing time"
                )

            # Page count warnings (for PDFs)
            if result.pages_detected and result.pages_detected > 50:
                result.add_warning(
                    f"Large document ({result.pages_detected} pages) may require batch processing"
                )

        except Exception:
            pass  # Ignore performance assessment failures

    def validate_output_path(self, output_path: Path) -> ValidationResult:
        """Validate output path for writing results."""
        result = ValidationResult(is_valid=True)

        try:
            # Check if parent directory exists and is writable
            parent_dir = output_path.parent

            if not parent_dir.exists():
                result.add_error(f"Output directory does not exist: {parent_dir}")
                return result

            if not os.access(parent_dir, os.W_OK):
                result.add_error(f"Output directory is not writable: {parent_dir}")
                return result

            # Check if file already exists
            if output_path.exists():
                result.add_warning(f"Output file already exists and will be overwritten: {output_path}")

            return result

        except Exception as e:
            result.add_error(f"Output path validation failed: {str(e)}")
            return result

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, any]:
        """Generate a summary of multiple validation results."""
        if not results:
            return {"total": 0, "valid": 0, "invalid": 0, "warnings": 0}

        valid_count = sum(1 for r in results if r.is_valid)
        warning_count = sum(len(r.warnings) for r in results)
        total_size = sum(r.file_size_bytes or 0 for r in results)

        return {
            "total": len(results),
            "valid": valid_count,
            "invalid": len(results) - valid_count,
            "warnings": warning_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_mb": round(total_size / (len(results) * 1024 * 1024), 2),
        }
