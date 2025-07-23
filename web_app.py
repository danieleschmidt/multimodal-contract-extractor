from __future__ import annotations

import logging
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileValidationResult:
    """Result of file validation."""

    is_valid: bool
    error_message: str | None = None
    file_size_mb: float | None = None
    file_type: str | None = None


@dataclass
class FilePreview:
    """File preview information."""

    filename: str
    file_size_mb: float
    file_type: str
    is_valid: bool
    error_message: str | None = None


class ProcessingStatusTracker:
    """Track processing progress and current operation."""

    def __init__(self):
        self.progress: float = 0.0
        self.operation: str = "Initializing..."
        self.completed: bool = False
        self.error: str | None = None

    def update_progress(self, progress: float) -> None:
        """Update progress percentage (0-100)."""
        self.progress = max(0.0, min(100.0, progress))

    def set_operation(self, operation: str) -> None:
        """Set current operation description."""
        self.operation = operation

    def set_completed(self) -> None:
        """Mark processing as completed."""
        self.progress = 100.0
        self.operation = "Completed"
        self.completed = True

    def set_error(self, error: str) -> None:
        """Set error status."""
        self.error = error
        self.operation = f"Error: {error}"

    def get_status(self) -> dict[str, Any]:
        """Get current status as dictionary."""
        return {
            "progress": self.progress,
            "operation": self.operation,
            "completed": self.completed,
            "error": self.error,
        }


def validate_upload(uploaded) -> FileValidationResult:
    """Validate uploaded file for processing."""
    from multimodal_contract_extractor.config import get_config

    config = get_config()
    max_size_mb = config.security.max_file_size_mb

    # Get file info
    filename = uploaded.name
    file_size_bytes = len(uploaded.read())
    uploaded.seek(0)  # Reset file pointer
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Determine file type
    suffix = Path(filename).suffix.lower()
    file_type = _get_file_type(suffix)

    # Validate file type
    supported_types = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
    if suffix not in supported_types:
        return FileValidationResult(
            is_valid=False,
            error_message=f"Unsupported file type '{suffix}'. Supported types: {', '.join(sorted(supported_types))}",
            file_size_mb=file_size_mb,
            file_type=file_type,
        )

    # Validate file size
    if file_size_mb > max_size_mb:
        return FileValidationResult(
            is_valid=False,
            error_message=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)",
            file_size_mb=file_size_mb,
            file_type=file_type,
        )

    # Validate file content (basic checks)
    content_start = uploaded.read(1024)
    uploaded.seek(0)  # Reset file pointer

    if not _validate_file_content(suffix, content_start):
        return FileValidationResult(
            is_valid=False,
            error_message="File content does not match the expected format",
            file_size_mb=file_size_mb,
            file_type=file_type,
        )

    return FileValidationResult(
        is_valid=True,
        file_size_mb=file_size_mb,
        file_type=file_type,
    )


def generate_preview(uploaded) -> FilePreview:
    """Generate preview information for uploaded file."""
    validation = validate_upload(uploaded)

    return FilePreview(
        filename=uploaded.name,
        file_size_mb=validation.file_size_mb or 0.0,
        file_type=validation.file_type or "Unknown",
        is_valid=validation.is_valid,
        error_message=validation.error_message,
    )


def _get_file_type(suffix: str) -> str:
    """Get human-readable file type from file extension."""
    type_map = {
        ".pdf": "PDF Document",
        ".jpg": "JPEG Image",
        ".jpeg": "JPEG Image",
        ".png": "PNG Image",
        ".tiff": "TIFF Image",
        ".tif": "TIFF Image",
        ".bmp": "BMP Image",
    }
    return type_map.get(suffix.lower(), "Unknown")


def _validate_file_content(suffix: str, content: bytes) -> bool:
    """Basic validation of file content based on file headers."""
    if suffix == ".pdf":
        return content.startswith(b"%PDF")
    if suffix in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if suffix == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".tiff", ".tif"}:
        return content.startswith((b"II*\x00", b"MM\x00*"))
    if suffix == ".bmp":
        return content.startswith(b"BM")

    return True  # Unknown format, allow through


def handle_processing_error(error: Exception) -> dict[str, Any]:
    """Handle processing errors and return user-friendly information."""
    error_type = type(error).__name__
    original_message = str(error)

    # Map error types to user-friendly messages
    user_message = format_error_message(error)
    suggestions = get_error_suggestion(error_type.lower())

    return {
        "user_message": user_message,
        "error_type": error_type,
        "suggestions": suggestions,
        "technical_details": original_message,
    }


def format_error_message(error: Exception) -> str:
    """Convert technical errors to user-friendly messages."""
    error_type = type(error).__name__.lower()
    error_message = str(error).lower()

    # Map common errors to user-friendly messages
    if "tesseract" in error_message or error_type == "filenotfounderror":
        return "Unable to process the document. The OCR system is not available."
    if "poppler" in error_message or "pdfinfo" in error_message:
        return "Unable to read PDF file. The PDF processing system is not available."
    if "memory" in error_message or "memoryerror" in error_type:
        return "The document is too large to process. Please try a smaller file."
    if "timeout" in error_message:
        return (
            "Document processing took too long. Please try again or use a smaller file."
        )
    if "permission" in error_message or "access" in error_message:
        return "Unable to access the file. Please check file permissions."
    if "corrupt" in error_message or "invalid" in error_message:
        return "The document appears to be corrupted or in an unsupported format."
    return "An error occurred while processing the document. Please try again."


def get_error_suggestion(error_code: str) -> str:
    """Get recovery suggestions for specific error types."""
    suggestions = {
        "filenotfounderror": "Please ensure the OCR system is properly installed and configured.",
        "tesseract_not_found": "Install Tesseract OCR or check that it's available in your system PATH.",
        "poppler_not_found": "Install Poppler utilities for PDF processing.",
        "memoryerror": "Try processing a smaller document or free up system memory.",
        "timeouterror": "Reduce document size or increase processing timeout limits.",
        "permissionerror": "Check file permissions and ensure the application has access rights.",
        "valueerror": "Verify the document format is supported (PDF, JPEG, PNG, TIFF, BMP).",
    }

    return suggestions.get(
        error_code,
        "Check the document format and size, then try again. If the problem persists, contact support.",
    )


def format_results_display(result: dict[str, Any]) -> dict[str, Any]:
    """Format extraction results for enhanced display."""
    document_info = result.get("document_info", {})
    clauses = result.get("clauses", [])

    # Group clauses by type
    grouped_clauses = group_clauses_by_type(clauses)

    # Calculate statistics
    total_clauses = len(clauses)
    avg_confidence = sum(clause.get("confidence", 0.0) for clause in clauses) / max(
        1, total_clauses
    )
    high_confidence_count = sum(
        1 for clause in clauses if clause.get("confidence", 0.0) > 0.9
    )

    # Document summary
    document_summary = {
        "filename": document_info.get("filename", "Unknown"),
        "pages": document_info.get("pages", 0),
        "processing_time": document_info.get("processing_time", 0.0),
        "overall_confidence": document_info.get("confidence", avg_confidence),
    }

    # Statistics
    statistics = {
        "total_clauses": total_clauses,
        "average_confidence": avg_confidence,
        "high_confidence_clauses": high_confidence_count,
        "clause_types": list(grouped_clauses.keys()),
    }

    return {
        "document_summary": document_summary,
        "grouped_clauses": grouped_clauses,
        "statistics": statistics,
        "raw_data": result,
    }


def group_clauses_by_type(clauses: list) -> dict[str, list]:
    """Group clauses by their type for better organization."""
    grouped = {}

    for clause in clauses:
        clause_type = clause.get("type", "unknown")
        if clause_type not in grouped:
            grouped[clause_type] = []

        # Format each clause for display
        formatted_clause = format_clause_display(clause)
        grouped[clause_type].append(formatted_clause)

    # Sort clauses within each group by confidence (highest first)
    for clause_type in grouped:
        grouped[clause_type].sort(
            key=lambda x: x.get("confidence", 0.0),
            reverse=True,
        )

    return grouped


def format_clause_display(clause: dict[str, Any]) -> dict[str, Any]:
    """Format a single clause for display with confidence highlighting."""
    confidence = clause.get("confidence", 0.0)

    # Determine confidence level for visual highlighting
    if confidence >= 0.9:
        confidence_level = "high"
        confidence_color = "#28a745"  # Green
    elif confidence >= 0.7:
        confidence_level = "medium"
        confidence_color = "#ffc107"  # Yellow
    else:
        confidence_level = "low"
        confidence_color = "#dc3545"  # Red

    return {
        "type": clause.get("type", "unknown"),
        "text": clause.get("text", ""),
        "confidence": confidence,
        "confidence_level": confidence_level,
        "confidence_color": confidence_color,
        "page": clause.get("page"),
        "coordinates": clause.get("coordinates"),
        "key_terms": clause.get("key_terms", []),
    }


class TempFileManager:
    """Context manager for secure temporary file handling with automatic cleanup.

    Creates temporary files with restricted permissions and ensures cleanup
    even when exceptions occur during processing.

    Usage:
        with TempFileManager(uploaded_file) as temp_path:
            # Process the file using temp_path
            result = process_document(temp_path)
        # File is automatically cleaned up here
    """

    def __init__(self, uploaded_file):
        """Initialize with an uploaded file object.

        Args:
            uploaded_file: File object with .name and .read() methods
        """
        self.uploaded_file = uploaded_file
        self.temp_path: Path | None = None

    def __enter__(self) -> Path:
        """Create secure temporary file and return its path."""
        # Sanitize file extension for security
        original_name = getattr(self.uploaded_file, "name", "upload.bin")
        suffix = re.sub(r"[^A-Za-z0-9._-]", "_", Path(original_name).suffix)

        # Create temporary file with restricted permissions (owner-only access)
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            mode="wb",
        )

        try:
            # Write uploaded content to temporary file
            content = self.uploaded_file.read()
            tmp_file.write(content)
            tmp_file.close()

            # Set secure permissions (0o600 = owner read/write only)
            self.temp_path = Path(tmp_file.name)
            self.temp_path.chmod(0o600)

            return self.temp_path

        except Exception:
            # Clean up on error during setup
            tmp_file.close()
            if hasattr(tmp_file, "name") and Path(tmp_file.name).exists():
                Path(tmp_file.name).unlink()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary file."""
        if self.temp_path and self.temp_path.exists():
            try:
                self.temp_path.unlink()
            except OSError:
                # File cleanup failed, but don't raise exception
                # as this could mask the original exception
                pass


def save_upload(uploaded) -> Path:
    """Save an uploaded file to a temporary location and return the path.

    DEPRECATED: Use TempFileManager context manager instead for proper cleanup.
    This function is kept for backward compatibility but does not clean up files.
    """
    suffix = re.sub(r"[^A-Za-z0-9._-]", "_", Path(uploaded.name).suffix)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_file.write(uploaded.read())
    tmp_file.close()
    return Path(tmp_file.name)


def process_upload_with_cleanup(uploaded_file) -> dict:
    """Process an uploaded file with proper temporary file cleanup.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Dictionary containing extraction results

    Raises:
        Exception: If document processing fails
    """
    from multimodal_contract_extractor import extract_from_document

    with TempFileManager(uploaded_file) as tmp_path:
        logger.info(f"Processing uploaded file: {uploaded_file.name}")

        # Perform document extraction
        extraction_result = extract_from_document(tmp_path)

        # Preserve original filename in result
        if "document_info" in extraction_result:
            extraction_result["document_info"]["filename"] = uploaded_file.name

        logger.info(f"Extraction completed for: {uploaded_file.name}")
        return extraction_result


def main() -> None:
    import streamlit as st  # Lazy import so tests don't require streamlit

    from multimodal_contract_extractor import (
        DocumentInfo,
        ExtractionResult,
        serialize_to_json,
    )
    from multimodal_contract_extractor.clause_detection import Clause

    st.title("Multimodal Contract Extractor")
    uploaded = st.file_uploader("Upload contract file")
    if uploaded is None:
        st.info("Please upload a PDF or image document.")
        return

    try:
        # Use secure processing with automatic cleanup
        extraction_result = process_upload_with_cleanup(uploaded)

        # Convert to legacy format for serialization compatibility
        info = DocumentInfo(
            filename=extraction_result["document_info"]["filename"],
            pages=extraction_result["document_info"]["pages"],
            processing_time=extraction_result["document_info"]["processing_time"],
            confidence=extraction_result["document_info"]["overall_confidence"],
        )

        # Convert clauses to Clause objects
        clauses = [
            Clause(
                type=clause_data["type"],
                text=clause_data["text"],
                page=clause_data["page"],
                coordinates=clause_data["coordinates"],
            )
            for clause_data in extraction_result["clauses"]
        ]

        result = ExtractionResult(document_info=info, clauses=clauses)
        st.json(serialize_to_json(result, pretty=True))

        # Display processing summary
        st.success(f"✅ Processed {info.pages} pages in {info.processing_time:.2f}s")
        if clauses:
            st.info(
                f"📋 Found {len(clauses)} clauses with {info.confidence:.1%} average confidence"
            )

    except Exception as e:
        st.error(f"❌ Error processing document: {e!s}")
        logger.error(f"Document processing failed: {e}", exc_info=True)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
