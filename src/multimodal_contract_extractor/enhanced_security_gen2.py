"""Enhanced security features for Generation 2 - comprehensive protection."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from cryptography.fernet import Fernet

from .config import get_config

logger = logging.getLogger(__name__)

class SecureTempFileManager:
    """Secure temporary file management with automatic cleanup."""

    @staticmethod
    @contextmanager
    def secure_temp_file(suffix: str = "", prefix: str = "mce_") -> Generator[Path, None, None]:
        """Create secure temporary file with restricted permissions."""
        try:
            with tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix=suffix,
                prefix=prefix,
                delete=False
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

            # Set secure permissions (owner only)
            os.chmod(tmp_path, 0o600)

            yield tmp_path

        finally:
            # Secure deletion
            try:
                if tmp_path.exists():
                    # Overwrite with random data before deletion
                    with open(tmp_path, 'r+b') as f:
                        size = f.seek(0, 2)  # Get file size
                        f.seek(0)
                        f.write(secrets.token_bytes(size))
                        f.flush()
                        os.fsync(f.fileno())
                    tmp_path.unlink()
            except Exception as e:
                logger.warning("Failed to securely delete temp file %s: %s", tmp_path, e)

class FileValidator:
    """Advanced file validation and security checks."""

    ALLOWED_EXTENSIONS = {
        '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp'
    }

    DANGEROUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'<%',
        b'<?php',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec(',
    ]

    @classmethod
    def validate_file_security(cls, file_path: Path) -> dict[str, Any]:
        """Comprehensive file security validation."""
        validation_result = {
            'safe': True,
            'issues': [],
            'file_hash': '',
            'file_size': 0,
            'mime_type': ''
        }

        try:
            if not file_path.exists():
                validation_result['safe'] = False
                validation_result['issues'].append("File does not exist")
                return validation_result

            # Check file extension
            if file_path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
                validation_result['safe'] = False
                validation_result['issues'].append(f"Disallowed file extension: {file_path.suffix}")

            # Check file size
            file_size = file_path.stat().st_size
            validation_result['file_size'] = file_size

            max_size = get_config().security.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                validation_result['safe'] = False
                validation_result['issues'].append(f"File too large: {file_size} bytes")

            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_content = f.read()
                validation_result['file_hash'] = hashlib.sha256(file_content).hexdigest()

                # Scan for dangerous patterns
                content_lower = file_content.lower()
                for pattern in cls.DANGEROUS_PATTERNS:
                    if pattern in content_lower:
                        validation_result['safe'] = False
                        validation_result['issues'].append(f"Dangerous pattern detected: {pattern.decode('utf-8', errors='ignore')}")

            # Basic MIME type detection
            validation_result['mime_type'] = cls._detect_mime_type(file_path)

        except Exception as e:
            validation_result['safe'] = False
            validation_result['issues'].append(f"Validation error: {e}")

        return validation_result

    @staticmethod
    def _detect_mime_type(file_path: Path) -> str:
        """Simple MIME type detection based on file signature."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)

            if header.startswith(b'%PDF'):
                return 'application/pdf'
            elif header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG'):
                return 'image/png'
            elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
                return 'image/tiff'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            elif header.startswith(b'GIF8'):
                return 'image/gif'
            elif header.startswith(b'RIFF') and b'WEBP' in header:
                return 'image/webp'
            else:
                return 'application/octet-stream'

        except Exception:
            return 'unknown'

class EncryptionManager:
    """Encryption and decryption utilities for sensitive data."""

    def __init__(self):
        self.config = get_config()
        self._fernet_key = None

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self._fernet_key is not None:
            return self._fernet_key

        # Try to load key from environment or config
        key_source = os.environ.get('MCE_ENCRYPTION_KEY')

        if key_source:
            try:
                # Assume base64 encoded key
                import base64
                self._fernet_key = base64.urlsafe_b64decode(key_source)
            except Exception:
                # Generate new key if invalid
                self._fernet_key = Fernet.generate_key()
        else:
            # Generate new key
            self._fernet_key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Set MCE_ENCRYPTION_KEY for persistence.")

        return self._fernet_key

    def encrypt_data(self, data: str | bytes) -> bytes:
        """Encrypt sensitive data."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        fernet = Fernet(self._get_or_create_key())
        return fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        fernet = Fernet(self._get_or_create_key())
        decrypted_bytes = fernet.decrypt(encrypted_data)
        return decrypted_bytes.decode('utf-8')

class AuditLogger:
    """Comprehensive audit logging for security events."""

    def __init__(self):
        self.config = get_config()
        self.audit_logger = logging.getLogger('audit')

    def log_security_event(self,
                          event_type: str,
                          user_id: str = "system",
                          resource: str = "",
                          action: str = "",
                          outcome: str = "success",
                          risk_level: str = "low",
                          details: dict[str, Any] | None = None) -> None:
        """Log security-related events with comprehensive details."""

        event_details = {
            'timestamp': logger.info.__func__.__defaults__,
            'event_type': event_type,
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'outcome': outcome,
            'risk_level': risk_level,
            'process_id': os.getpid(),
            'details': details or {}
        }

        self.audit_logger.info("AUDIT_EVENT: %s", event_details)

    def log_file_access(self, file_path: str, action: str, outcome: str = "success") -> None:
        """Log file access events."""
        self.log_security_event(
            event_type="file_access",
            resource=file_path,
            action=action,
            outcome=outcome,
            risk_level="medium" if outcome != "success" else "low"
        )

    def log_processing_event(self, document_type: str, processing_time: float,
                           success: bool) -> None:
        """Log document processing events."""
        self.log_security_event(
            event_type="document_processing",
            resource=document_type,
            action="extract_clauses",
            outcome="success" if success else "failure",
            risk_level="low",
            details={"processing_time_seconds": processing_time}
        )

class SecurityValidator:
    """Comprehensive security validation for processing pipeline."""

    def __init__(self):
        self.file_validator = FileValidator()
        self.audit_logger = AuditLogger()

    def validate_processing_request(self, file_path: Path, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Comprehensive validation of processing request."""
        validation_result = {
            'allowed': True,
            'security_issues': [],
            'validation_details': {}
        }

        # File security validation
        file_validation = self.file_validator.validate_file_security(file_path)
        validation_result['validation_details']['file_security'] = file_validation

        if not file_validation['safe']:
            validation_result['allowed'] = False
            validation_result['security_issues'].extend(file_validation['issues'])

        # Log validation attempt
        self.audit_logger.log_file_access(
            file_path=str(file_path),
            action="security_validation",
            outcome="success" if validation_result['allowed'] else "blocked"
        )

        return validation_result

# Global instances
secure_temp_manager = SecureTempFileManager()
encryption_manager = EncryptionManager()
audit_logger = AuditLogger()
security_validator = SecurityValidator()

def validate_and_process_file(file_path: Path) -> dict[str, Any]:
    """High-level secure file processing validation."""
    return security_validator.validate_processing_request(file_path)
