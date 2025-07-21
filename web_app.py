from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import re
import os
import logging

logger = logging.getLogger(__name__)


class TempFileManager:
    """Context manager for secure temporary file handling with automatic cleanup."""
    
    def __init__(self, uploaded_file):
        """Initialize with an uploaded file object."""
        self.uploaded_file = uploaded_file
        self.temp_path = None
        
    def __enter__(self) -> Path:
        """Create and return temporary file path."""
        # Sanitize the file extension to prevent security issues
        original_suffix = Path(self.uploaded_file.name).suffix
        sanitized_suffix = re.sub(r"[^A-Za-z0-9._-]", "_", original_suffix)
        
        # Create temporary file with restricted permissions
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=sanitized_suffix,
            mode='wb'
        )
        
        try:
            # Write uploaded content to temp file
            content = self.uploaded_file.read()
            tmp_file.write(content)
            tmp_file.close()
            
            # Set restrictive permissions (owner read/write only)
            self.temp_path = Path(tmp_file.name)
            os.chmod(self.temp_path, 0o600)
            
            logger.debug(f"Created temporary file: {self.temp_path}")
            return self.temp_path
            
        except Exception as e:
            # Clean up on creation failure
            tmp_file.close()
            temp_path = Path(tmp_file.name)
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Failed to create temporary file: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary file."""
        if self.temp_path and self.temp_path.exists():
            try:
                self.temp_path.unlink()
                logger.debug(f"Cleaned up temporary file: {self.temp_path}")
            except OSError as e:
                # Log warning but don't raise - file might have been deleted already
                logger.warning(f"Could not delete temporary file {self.temp_path}: {e}")


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
        
        logger.info(f"Extraction completed for: {uploaded_file.name}")
        return extraction_result


def main() -> None:
    import streamlit as st  # Lazy import so tests don't require streamlit
    from multimodal_contract_extractor import (
        serialize_to_json,
        DocumentInfo,
        ExtractionResult,
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
                coordinates=clause_data["coordinates"]
            )
            for clause_data in extraction_result["clauses"]
        ]
        
        result = ExtractionResult(document_info=info, clauses=clauses)
        st.json(serialize_to_json(result, pretty=True))
        
        # Display processing summary
        st.success(f"✅ Processed {info.pages} pages in {info.processing_time:.2f}s")
        if clauses:
            st.info(f"📋 Found {len(clauses)} clauses with {info.confidence:.1%} average confidence")
        
    except Exception as e:
        st.error(f"❌ Error processing document: {str(e)}")
        logger.error(f"Document processing failed: {e}", exc_info=True)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
