"""
Advanced security validation and threat detection for Generation 2.
Comprehensive security measures with input sanitization and threat detection.
"""
from __future__ import annotations

import logging
import mimetypes
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityViolationType(Enum):
    """Types of security violations."""
    MALICIOUS_FILE = "malicious_file"
    SUSPICIOUS_CONTENT = "suspicious_content"
    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    INVALID_FORMAT = "invalid_format"
    PATH_TRAVERSAL = "path_traversal"
    INJECTION_ATTEMPT = "injection_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class SecurityThreat:
    """Security threat detection result."""
    threat_id: str = field(default_factory=lambda: f"threat_{int(time.time()*1000)}")
    violation_type: SecurityViolationType = SecurityViolationType.SUSPICIOUS_CONTENT
    level: ThreatLevel = ThreatLevel.MEDIUM
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    blocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "threat_id": self.threat_id,
            "violation_type": self.violation_type.value,
            "level": self.level.value,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp,
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "blocked": self.blocked
        }


class FileSecurityValidator:
    """Advanced file security validation."""

    # Allowed file extensions and MIME types
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/png', 'image/jpeg', 'image/tiff', 'image/bmp', 'image/gif'
    }

    # Malicious file signatures (simplified examples)
    MALICIOUS_SIGNATURES = {
        b'%PDF': {'type': 'pdf', 'max_size': 100 * 1024 * 1024},  # 100MB max for PDF
        b'\x89PNG': {'type': 'png', 'max_size': 50 * 1024 * 1024},  # 50MB max for PNG
        b'\xff\xd8\xff': {'type': 'jpeg', 'max_size': 50 * 1024 * 1024},  # 50MB max for JPEG
    }

    # Suspicious patterns in file content
    SUSPICIOUS_PATTERNS = [
        rb'javascript:',
        rb'<script',
        rb'eval\s*\(',
        rb'exec\s*\(',
        rb'system\s*\(',
        rb'shell_exec',
        rb'passthru',
        rb'`.*`',  # Command substitution
    ]

    def __init__(self, max_file_size: int = 200 * 1024 * 1024):  # 200MB default
        self.max_file_size = max_file_size
        self.threat_log: List[SecurityThreat] = []

    def validate_file_path(self, file_path: Union[str, Path]) -> Optional[SecurityThreat]:
        """Validate file path for security issues."""
        path = Path(file_path)

        # Check for path traversal attempts
        path_str = str(path)
        if '..' in path_str or path_str.startswith('/') and not path_str.startswith('/tmp'):
            return SecurityThreat(
                violation_type=SecurityViolationType.PATH_TRAVERSAL,
                level=ThreatLevel.HIGH,
                description=f"Path traversal attempt detected: {path_str}",
                details={"path": path_str},
                blocked=True
            )

        # Check file extension
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            return SecurityThreat(
                violation_type=SecurityViolationType.INVALID_FORMAT,
                level=ThreatLevel.MEDIUM,
                description=f"Disallowed file extension: {path.suffix}",
                details={"extension": path.suffix, "allowed": list(self.ALLOWED_EXTENSIONS)},
                blocked=True
            )

        return None

    def validate_file_content(self, file_path: Union[str, Path]) -> Optional[SecurityThreat]:
        """Validate file content for malicious patterns."""
        path = Path(file_path)

        if not path.exists():
            return SecurityThreat(
                violation_type=SecurityViolationType.MALICIOUS_FILE,
                level=ThreatLevel.HIGH,
                description=f"File does not exist: {path}",
                details={"path": str(path)},
                blocked=True
            )

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            return SecurityThreat(
                violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                level=ThreatLevel.MEDIUM,
                description=f"File size {file_size} exceeds limit {self.max_file_size}",
                details={"file_size": file_size, "limit": self.max_file_size},
                blocked=True
            )

        # Read file header for signature validation
        try:
            with open(path, 'rb') as f:
                header = f.read(1024)  # Read first 1KB

            # Check file signature
            signature_valid = False
            for signature, info in self.MALICIOUS_SIGNATURES.items():
                if header.startswith(signature):
                    signature_valid = True
                    # Check size against type-specific limits
                    if file_size > info['max_size']:
                        return SecurityThreat(
                            violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                            level=ThreatLevel.MEDIUM,
                            description=f"File size {file_size} exceeds {info['type']} limit {info['max_size']}",
                            details={"file_size": file_size, "type": info['type'], "limit": info['max_size']},
                            blocked=True
                        )
                    break

            if not signature_valid:
                return SecurityThreat(
                    violation_type=SecurityViolationType.MALICIOUS_FILE,
                    level=ThreatLevel.HIGH,
                    description="Invalid or suspicious file signature",
                    details={"header": header[:20].hex()},
                    blocked=True
                )

            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
                return SecurityThreat(
                    violation_type=SecurityViolationType.INVALID_FORMAT,
                    level=ThreatLevel.MEDIUM,
                    description=f"Disallowed MIME type: {mime_type}",
                    details={"mime_type": mime_type, "allowed": list(self.ALLOWED_MIME_TYPES)},
                    blocked=True
                )

            # Scan for suspicious content patterns
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, header, re.IGNORECASE):
                    return SecurityThreat(
                        violation_type=SecurityViolationType.SUSPICIOUS_CONTENT,
                        level=ThreatLevel.HIGH,
                        description="Suspicious content pattern detected",
                        details={"pattern": pattern.decode('ascii', errors='ignore')},
                        blocked=True
                    )

        except Exception as e:
            logger.error(f"Error validating file content: {e}")
            return SecurityThreat(
                violation_type=SecurityViolationType.MALICIOUS_FILE,
                level=ThreatLevel.HIGH,
                description=f"File content validation failed: {str(e)}",
                details={"error": str(e)},
                blocked=True
            )

        return None

    def validate_file(self, file_path: Union[str, Path]) -> List[SecurityThreat]:
        """Comprehensive file validation."""
        threats = []

        # Path validation
        path_threat = self.validate_file_path(file_path)
        if path_threat:
            threats.append(path_threat)
            self.threat_log.append(path_threat)
            return threats  # Don't proceed if path is invalid

        # Content validation
        content_threat = self.validate_file_content(file_path)
        if content_threat:
            threats.append(content_threat)
            self.threat_log.append(content_threat)

        return threats


class InputSanitizer:
    """Input sanitization and validation."""

    # Patterns for various injection attempts
    SQL_INJECTION_PATTERNS = [
        r'(\bunion\s+select\b)',
        r'(\bdrop\s+table\b)',
        r'(\bdelete\s+from\b)',
        r'(\binsert\s+into\b)',
        r'(\bupdate\s+set\b)',
        r'(\bselect\s+.*\bfrom\b)',
        r'(\'\s*or\s+\'\d+\'\s*=\s*\'\d+)',
        r'(\'\s*or\s+\d+=\d+)',
    ]

    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]

    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$()]',
        r'(\bcat\s+)',
        r'(\bls\s+)',
        r'(\bps\s+)',
        r'(\bkill\s+)',
        r'(\brm\s+)',
        r'(\bmv\s+)',
        r'(\bcp\s+)',
    ]

    def __init__(self):
        self.threat_log: List[SecurityThreat] = []

    def sanitize_string(self, input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(input_str, str):
            input_str = str(input_str)

        # Length check
        if len(input_str) > max_length:
            input_str = input_str[:max_length]

        # Remove null bytes
        input_str = input_str.replace('\x00', '')

        # Remove or escape control characters
        input_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)

        return input_str.strip()

    def detect_injection_attempts(self, input_str: str) -> List[SecurityThreat]:
        """Detect various injection attempts."""
        threats = []
        input_lower = input_str.lower()

        # SQL injection detection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                threat = SecurityThreat(
                    violation_type=SecurityViolationType.INJECTION_ATTEMPT,
                    level=ThreatLevel.HIGH,
                    description="SQL injection attempt detected",
                    details={"pattern": pattern, "input": input_str[:200]},
                    blocked=True
                )
                threats.append(threat)
                self.threat_log.append(threat)

        # XSS detection
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                threat = SecurityThreat(
                    violation_type=SecurityViolationType.INJECTION_ATTEMPT,
                    level=ThreatLevel.HIGH,
                    description="XSS attempt detected",
                    details={"pattern": pattern, "input": input_str[:200]},
                    blocked=True
                )
                threats.append(threat)
                self.threat_log.append(threat)

        # Command injection detection
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                threat = SecurityThreat(
                    violation_type=SecurityViolationType.INJECTION_ATTEMPT,
                    level=ThreatLevel.HIGH,
                    description="Command injection attempt detected",
                    details={"pattern": pattern, "input": input_str[:200]},
                    blocked=True
                )
                threats.append(threat)
                self.threat_log.append(threat)

        return threats


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_buckets: Dict[str, List[float]] = {}
        self.hour_buckets: Dict[str, List[float]] = {}
        self.threat_log: List[SecurityThreat] = []

    def is_rate_limited(self, client_id: str) -> Optional[SecurityThreat]:
        """Check if client is rate limited."""
        now = time.time()

        # Clean old entries
        self._clean_buckets(client_id, now)

        # Check minute limit
        if client_id in self.minute_buckets:
            minute_requests = len(self.minute_buckets[client_id])
            if minute_requests >= self.requests_per_minute:
                threat = SecurityThreat(
                    violation_type=SecurityViolationType.RATE_LIMIT_EXCEEDED,
                    level=ThreatLevel.MEDIUM,
                    description=f"Rate limit exceeded: {minute_requests}/{self.requests_per_minute} per minute",
                    details={"client_id": client_id, "requests": minute_requests, "limit": self.requests_per_minute},
                    blocked=True
                )
                self.threat_log.append(threat)
                return threat

        # Check hour limit
        if client_id in self.hour_buckets:
            hour_requests = len(self.hour_buckets[client_id])
            if hour_requests >= self.requests_per_hour:
                threat = SecurityThreat(
                    violation_type=SecurityViolationType.RATE_LIMIT_EXCEEDED,
                    level=ThreatLevel.HIGH,
                    description=f"Rate limit exceeded: {hour_requests}/{self.requests_per_hour} per hour",
                    details={"client_id": client_id, "requests": hour_requests, "limit": self.requests_per_hour},
                    blocked=True
                )
                self.threat_log.append(threat)
                return threat

        # Record request
        if client_id not in self.minute_buckets:
            self.minute_buckets[client_id] = []
        if client_id not in self.hour_buckets:
            self.hour_buckets[client_id] = []

        self.minute_buckets[client_id].append(now)
        self.hour_buckets[client_id].append(now)

        return None

    def _clean_buckets(self, client_id: str, now: float):
        """Clean expired entries from rate limit buckets."""
        # Clean minute bucket (keep last 60 seconds)
        if client_id in self.minute_buckets:
            self.minute_buckets[client_id] = [
                timestamp for timestamp in self.minute_buckets[client_id]
                if now - timestamp < 60
            ]

        # Clean hour bucket (keep last 3600 seconds)
        if client_id in self.hour_buckets:
            self.hour_buckets[client_id] = [
                timestamp for timestamp in self.hour_buckets[client_id]
                if now - timestamp < 3600
            ]


class SecurityAuditLogger:
    """Security event logging and auditing."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.security_logger = logging.getLogger('security_audit')

        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.security_logger.addHandler(handler)
            self.security_logger.setLevel(logging.INFO)

    def log_threat(self, threat: SecurityThreat):
        """Log security threat."""
        threat_dict = threat.to_dict()

        if threat.level == ThreatLevel.CRITICAL:
            self.security_logger.critical(f"CRITICAL THREAT: {threat.description}", extra=threat_dict)
        elif threat.level == ThreatLevel.HIGH:
            self.security_logger.error(f"HIGH THREAT: {threat.description}", extra=threat_dict)
        elif threat.level == ThreatLevel.MEDIUM:
            self.security_logger.warning(f"MEDIUM THREAT: {threat.description}", extra=threat_dict)
        else:
            self.security_logger.info(f"LOW THREAT: {threat.description}", extra=threat_dict)

    def log_access_attempt(self, client_id: str, endpoint: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Log access attempt."""
        log_data = {
            "client_id": client_id,
            "endpoint": endpoint,
            "success": success,
            "timestamp": time.time(),
            "details": details or {}
        }

        if success:
            self.security_logger.info(f"Access granted: {client_id} -> {endpoint}", extra=log_data)
        else:
            self.security_logger.warning(f"Access denied: {client_id} -> {endpoint}", extra=log_data)


class SecurityManager:
    """Centralized security management."""

    def __init__(self, log_file: Optional[str] = None):
        self.file_validator = FileSecurityValidator()
        self.input_sanitizer = InputSanitizer()
        self.rate_limiter = RateLimiter()
        self.audit_logger = SecurityAuditLogger(log_file)
        self.all_threats: List[SecurityThreat] = []

    def validate_file_upload(self, file_path: Union[str, Path]) -> List[SecurityThreat]:
        """Comprehensive file upload validation."""
        threats = self.file_validator.validate_file(file_path)

        for threat in threats:
            self.audit_logger.log_threat(threat)
            self.all_threats.append(threat)

        return threats

    def sanitize_and_validate_input(self, input_str: str, max_length: int = 1000) -> tuple[str, List[SecurityThreat]]:
        """Sanitize input and detect threats."""
        sanitized = self.input_sanitizer.sanitize_string(input_str, max_length)
        threats = self.input_sanitizer.detect_injection_attempts(input_str)

        for threat in threats:
            self.audit_logger.log_threat(threat)
            self.all_threats.append(threat)

        return sanitized, threats

    def check_rate_limit(self, client_id: str) -> Optional[SecurityThreat]:
        """Check rate limiting for client."""
        threat = self.rate_limiter.is_rate_limited(client_id)

        if threat:
            self.audit_logger.log_threat(threat)
            self.all_threats.append(threat)

        return threat

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        if not self.all_threats:
            return {"total_threats": 0}

        threat_counts = {}
        level_counts = {}
        recent_threats = 0
        blocked_threats = 0

        one_hour_ago = time.time() - 3600

        for threat in self.all_threats:
            # Count by type
            threat_type = threat.violation_type.value
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

            # Count by level
            threat_level = threat.level.value
            level_counts[threat_level] = level_counts.get(threat_level, 0) + 1

            # Recent threats (last hour)
            if threat.timestamp > one_hour_ago:
                recent_threats += 1

            # Blocked threats
            if threat.blocked:
                blocked_threats += 1

        return {
            "total_threats": len(self.all_threats),
            "recent_threats": recent_threats,
            "blocked_threats": blocked_threats,
            "threat_types": threat_counts,
            "threat_levels": level_counts,
            "block_rate": blocked_threats / len(self.all_threats) if self.all_threats else 0
        }


# Global security manager
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def secure_file_validation(file_path: Union[str, Path]) -> bool:
    """Quick file validation function."""
    manager = get_security_manager()
    threats = manager.validate_file_upload(file_path)
    return len([t for t in threats if t.blocked]) == 0
