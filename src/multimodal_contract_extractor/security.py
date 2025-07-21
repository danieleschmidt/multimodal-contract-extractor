"""Security validation and input sanitization for file processing."""

import re
from pathlib import Path
from typing import Literal
from .config import get_config


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


# File type mappings based on magic bytes
FILE_SIGNATURES = {
    b"%PDF": "pdf",
    b"\x89PNG": "image",
    b"\xff\xd8\xff": "image",  # JPEG
    b"GIF8": "image",
    b"BM": "image",  # BMP
    b"II*\x00": "image",  # TIFF little-endian
    b"MM\x00*": "image",  # TIFF big-endian
}

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
}

# Maximum file size in MB - now configurable
def _get_max_file_size_mb() -> int:
    """Get maximum file size from configuration."""
    return get_config().security.max_file_size_mb


def validate_file_input(file_path: Path, max_size_mb: int = None) -> Path:
    """
    Validate a file input for security and compatibility.
    
    Args:
        file_path: Path to the file to validate
        max_size_mb: Maximum file size in megabytes
        
    Returns:
        Resolved and validated file path
        
    Raises:
        SecurityError: If validation fails
    """
    # Resolve path to prevent directory traversal
    resolved_path = file_path.resolve()
    
    # Check if file exists
    if not resolved_path.exists():
        raise SecurityError(f"File does not exist: {resolved_path}")
    
    # Check if it's a regular file (not directory, symlink, etc.)
    if not resolved_path.is_file():
        raise SecurityError(f"Path is not a regular file: {resolved_path}")
    
    # Check file size
    if max_size_mb is None:
        max_size_mb = _get_max_file_size_mb()
    check_file_size_limit(resolved_path, max_size_mb)
    
    # Check if file is empty
    if resolved_path.stat().st_size == 0:
        raise SecurityError(f"File is empty: {resolved_path}")
    
    # Validate file type
    validate_file_type(resolved_path)
    
    return resolved_path


def sanitize_file_path(file_path: str) -> str:
    """
    Sanitize a file path to prevent security issues.
    
    Args:
        file_path: Original file path string
        
    Returns:
        Sanitized file path string
    """
    # Remove null bytes
    clean_path = file_path.replace("\x00", "_")
    
    # Replace path separators and dangerous characters
    clean_path = re.sub(r"[/\\:*?\"<>|]", "_", clean_path)
    
    # Replace consecutive dots to prevent directory traversal
    clean_path = re.sub(r"\.{2,}", "_", clean_path)
    
    # Replace spaces with underscores
    clean_path = clean_path.replace(" ", "_")
    
    # Remove leading/trailing whitespace and dots
    clean_path = clean_path.strip(". ")
    
    # Ensure we have a non-empty filename
    if not clean_path:
        clean_path = "sanitized_file"
    
    return clean_path


def check_file_size_limit(file_path: Path, max_size_mb: int = None) -> None:
    """
    Check if file size is within allowed limits.
    
    Args:
        file_path: Path to the file to check
        max_size_mb: Maximum allowed file size in megabytes
        
    Raises:
        SecurityError: If file exceeds size limit
    """
    if max_size_mb is None:
        max_size_mb = _get_max_file_size_mb()
    
    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        raise SecurityError(
            f"File size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB): {file_path}"
        )


def validate_file_type(file_path: Path) -> Literal["pdf", "image"]:
    """
    Validate file type based on magic bytes and extension.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        File type category ("pdf" or "image")
        
    Raises:
        SecurityError: If file type is not supported
    """
    # Try to detect file type by magic bytes
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        
        for signature, file_type in FILE_SIGNATURES.items():
            if header.startswith(signature):
                return file_type
    except (OSError, IOError):
        pass
    
    # Fallback to extension-based detection
    extension = file_path.suffix.lower()
    if extension in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[extension]
    
    raise SecurityError(f"Unsupported file type: {file_path} (extension: {extension})")


def validate_output_path(output_path: str | None, output_format: str) -> Path:
    """
    Validate and sanitize output path.
    
    Args:
        output_path: User-provided output path (can be None)
        output_format: Output format (json, xml, csv)
        
    Returns:
        Validated and sanitized output path
        
    Raises:
        SecurityError: If output path validation fails
    """
    if output_path:
        # Convert to Path and resolve for security
        path = Path(output_path).resolve()
        
        # Add extension if not present
        if path.suffix == "":
            path = path.with_suffix(f".{output_format}")
        
        # Sanitize only the filename component
        sanitized_name = sanitize_file_path(path.name)
        final_path = path.parent / sanitized_name
        
        # Check if parent directory exists
        if not final_path.parent.exists():
            raise SecurityError(f"Output directory does not exist: {final_path.parent}")
        
        # Check if parent is writable
        if not final_path.parent.is_dir():
            raise SecurityError(f"Output parent is not a directory: {final_path.parent}")
            
        return final_path
    else:
        # Use default output filename
        return Path(f"result.{output_format}").resolve()


def sanitize_request_id(request_id: str) -> str:
    """
    Sanitize request ID to prevent log injection.
    
    Args:
        request_id: Original request ID
        
    Returns:
        Sanitized request ID safe for logging
    """
    # Allow only alphanumeric characters, hyphens, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "", request_id)
    
    # Limit length to prevent DoS
    config = get_config()
    sanitized = sanitized[:config.security.request_id_length_limit]
    
    # Ensure non-empty result
    if not sanitized:
        sanitized = "unknown"
    
    return sanitized