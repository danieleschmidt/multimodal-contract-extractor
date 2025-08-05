"""
Enhanced security framework for production-ready operation.

This module provides comprehensive security measures including input sanitization,
file upload security, virus scanning simulation, rate limiting, authentication,
authorization, audit logging, and secure temporary file handling.
"""

from __future__ import annotations

import functools
import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import jwt

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .config import get_config
from .security import SecurityError, validate_file_input

logger = logging.getLogger(__name__)


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""


class RateLimitExceededError(SecurityError):
    """Raised when rate limit is exceeded."""


class VirusScanError(SecurityError):
    """Raised when virus scanning fails."""


class SecurityLevel(Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionType(Enum):
    """Permission types for authorization."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DELETE = "delete"


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    permissions: Set[PermissionType] = field(default_factory=set)
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    authenticated: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    additional_claims: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_window: int = 100
    window_seconds: int = 60
    burst_allowance: int = 10
    block_duration_seconds: int = 300


@dataclass
class EnhancedSecurityConfig:
    """Enhanced security configuration."""
    max_file_size_mb: int = 100
    request_id_length_limit: int = 64
    enable_virus_scanning: bool = True
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True
    enable_encryption: bool = True
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    blocked_ips: Set[str] = field(default_factory=set)
    trusted_proxies: Set[str] = field(default_factory=set)
    min_password_length: int = 8
    require_https: bool = True
    session_timeout_minutes: int = 30


# Malicious file patterns (simplified virus signatures)
MALICIOUS_PATTERNS = [
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",  # EICAR test string
    b"\\x4d\\x5a\\x90\\x00",  # PE executable header
    b"\\x7f\\x45\\x4c\\x46",  # ELF executable header
    b"\\xca\\xfe\\xba\\xbe",  # Mach-O executable header
    b"<script",  # Basic script injection
    b"javascript:",  # JavaScript URL
    b"eval(",  # Code evaluation
    b"exec(",  # Code execution
]

# Dangerous file extensions
DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", ".jar",
    ".sh", ".ps1", ".app", ".deb", ".rpm", ".dmg", ".iso", ".msi"
}

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(union|select|insert|update|delete|drop|create|alter)\\s+",
    r"(or|and)\\s+\\d+\\s*=\\s*\\d+",
    r"'\\s*(or|and)\\s*'\\w*'\\s*=\\s*'\\w*'",
    r"--\\s*",
    r"/\\*.*\\*/",
    r"xp_cmdshell",
    r"sp_executesql"
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:\\s*",
    r"on\\w+\\s*=\\s*[\"'][^\"']*[\"']",
    r"<iframe[^>]*>.*?</iframe>",
    r"<embed[^>]*>",
    r"<object[^>]*>.*?</object>"
]


class VirusScanner:
    """Simulated virus scanner for file security."""

    def __init__(self):
        self.scan_count = 0
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.scan_counter = Counter(
                'virus_scans_total',
                'Total virus scans performed',
                ['result']
            )
            self.scan_duration = Histogram(
                'virus_scan_duration_seconds',
                'Time spent scanning files for viruses'
            )

    def scan_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Scan a file for viruses. Returns (is_clean, threat_name)."""
        start_time = time.time()

        with self._lock:
            self.scan_count += 1

        try:
            # Read file content for scanning
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 1024)  # Read first 1MB for performance

            # Check for malicious patterns
            for pattern in MALICIOUS_PATTERNS:
                if pattern in content:
                    threat_name = f"Malicious.Pattern.{pattern[:10].hex()}"
                    logger.warning(f"Virus detected in {file_path}: {threat_name}")

                    if PROMETHEUS_AVAILABLE:
                        self.scan_counter.labels(result='infected').inc()

                    return False, threat_name

            # Check file extension
            if file_path.suffix.lower() in DANGEROUS_EXTENSIONS:
                threat_name = f"Suspicious.Extension.{file_path.suffix}"
                logger.warning(f"Dangerous file extension detected: {file_path}")

                if PROMETHEUS_AVAILABLE:
                    self.scan_counter.labels(result='suspicious').inc()

                return False, threat_name

            # File is clean
            if PROMETHEUS_AVAILABLE:
                self.scan_counter.labels(result='clean').inc()

            return True, None

        except Exception as e:
            logger.error(f"Virus scan failed for {file_path}: {e}")

            if PROMETHEUS_AVAILABLE:
                self.scan_counter.labels(result='error').inc()

            raise VirusScanError(f"Virus scan failed: {e}")

        finally:
            duration = time.time() - start_time
            if PROMETHEUS_AVAILABLE:
                self.scan_duration.observe(duration)

    def get_stats(self) -> Dict[str, Any]:
        """Get virus scanner statistics."""
        return {
            "total_scans": self.scan_count,
            "scanner_version": "1.0.0",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "patterns_count": len(MALICIOUS_PATTERNS)
        }


class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, List[float]] = {}
        self.blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.rate_limit_counter = Counter(
                'rate_limit_checks_total',
                'Total rate limit checks',
                ['result', 'identifier']
            )
            self.blocked_requests = Counter(
                'rate_limited_requests_total',
                'Total rate limited requests',
                ['identifier']
            )

    def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed for the given identifier."""
        current_time = time.time()

        with self._lock:
            # Check if currently blocked
            if identifier in self.blocked_until:
                if current_time < self.blocked_until[identifier]:
                    if PROMETHEUS_AVAILABLE:
                        self.rate_limit_counter.labels(result='blocked', identifier=identifier).inc()
                        self.blocked_requests.labels(identifier=identifier).inc()

                    remaining_time = self.blocked_until[identifier] - current_time
                    return False, {
                        "blocked": True,
                        "reason": "Rate limit exceeded",
                        "retry_after": remaining_time,
                        "window_seconds": self.config.window_seconds
                    }
                else:
                    # Block period expired
                    del self.blocked_until[identifier]

            # Initialize request history for new identifier
            if identifier not in self.requests:
                self.requests[identifier] = []

            # Clean old requests outside the window
            window_start = current_time - self.config.window_seconds
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]

            # Check rate limit
            current_requests = len(self.requests[identifier])

            if current_requests >= self.config.requests_per_window:
                # Rate limit exceeded, block the identifier
                self.blocked_until[identifier] = current_time + self.config.block_duration_seconds

                if PROMETHEUS_AVAILABLE:
                    self.rate_limit_counter.labels(result='exceeded', identifier=identifier).inc()
                    self.blocked_requests.labels(identifier=identifier).inc()

                return False, {
                    "blocked": True,
                    "reason": "Rate limit exceeded",
                    "retry_after": self.config.block_duration_seconds,
                    "requests_in_window": current_requests,
                    "limit": self.config.requests_per_window,
                    "window_seconds": self.config.window_seconds
                }

            # Request is allowed
            self.requests[identifier].append(current_time)

            if PROMETHEUS_AVAILABLE:
                self.rate_limit_counter.labels(result='allowed', identifier=identifier).inc()

            remaining_requests = self.config.requests_per_window - (current_requests + 1)

            return True, {
                "blocked": False,
                "remaining_requests": remaining_requests,
                "reset_time": window_start + self.config.window_seconds,
                "window_seconds": self.config.window_seconds
            }

    def reset_identifier(self, identifier: str):
        """Reset rate limit for a specific identifier."""
        with self._lock:
            self.requests.pop(identifier, None)
            self.blocked_until.pop(identifier, None)
            logger.info(f"Rate limit reset for identifier: {identifier}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                "active_identifiers": len(self.requests),
                "blocked_identifiers": len(self.blocked_until),
                "config": {
                    "requests_per_window": self.config.requests_per_window,
                    "window_seconds": self.config.window_seconds,
                    "block_duration_seconds": self.config.block_duration_seconds
                }
            }


class AuthenticationManager:
    """JWT-based authentication manager."""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.active_sessions: Dict[str, SecurityContext] = {}
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.auth_attempts = Counter(
                'authentication_attempts_total',
                'Total authentication attempts',
                ['result']
            )
            self.active_sessions_gauge = Gauge(
                'active_sessions_count',
                'Number of currently active sessions'
            )

    def create_token(self, user_id: str, permissions: Set[PermissionType],
                    additional_claims: Dict[str, Any] = None) -> str:
        """Create a JWT token for a user."""
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(hours=24)  # TODO: Make configurable

        session_id = str(uuid4())

        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "permissions": [perm.value for perm in permissions],
            "iat": now.timestamp(),
            "exp": expiration.timestamp(),
            "iss": "multimodal-contract-extractor"
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm="HS256")

        # Store session context
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            permissions=permissions,
            authenticated=True,
            timestamp=now,
            additional_claims=additional_claims or {}
        )

        with self._lock:
            self.active_sessions[session_id] = context
            if PROMETHEUS_AVAILABLE:
                self.active_sessions_gauge.set(len(self.active_sessions))

        logger.info(f"Created authentication token for user: {user_id}")
        return token

    def verify_token(self, token: str) -> SecurityContext:
        """Verify a JWT token and return security context."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            session_id = payload.get("session_id")
            if not session_id:
                raise AuthenticationError("Invalid token: missing session_id")

            with self._lock:
                if session_id not in self.active_sessions:
                    raise AuthenticationError("Session not found or expired")

                context = self.active_sessions[session_id]

            # Update last activity
            context.timestamp = datetime.now(timezone.utc)

            if PROMETHEUS_AVAILABLE:
                self.auth_attempts.labels(result='success').inc()

            return context

        except jwt.ExpiredSignatureError:
            if PROMETHEUS_AVAILABLE:
                self.auth_attempts.labels(result='expired').inc()
            raise AuthenticationError("Token has expired")

        except jwt.InvalidTokenError as e:
            if PROMETHEUS_AVAILABLE:
                self.auth_attempts.labels(result='invalid').inc()
            raise AuthenticationError(f"Invalid token: {e}")

    def revoke_session(self, session_id: str):
        """Revoke a specific session."""
        with self._lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                if PROMETHEUS_AVAILABLE:
                    self.active_sessions_gauge.set(len(self.active_sessions))
                logger.info(f"Revoked session: {session_id}")

    def cleanup_expired_sessions(self, max_age_minutes: int = 30):
        """Clean up expired sessions."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

        with self._lock:
            expired_sessions = [
                session_id for session_id, context in self.active_sessions.items()
                if context.timestamp < cutoff_time
            ]

            for session_id in expired_sessions:
                del self.active_sessions[session_id]

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                if PROMETHEUS_AVAILABLE:
                    self.active_sessions_gauge.set(len(self.active_sessions))

    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        with self._lock:
            return {
                "active_sessions": len(self.active_sessions),
                "session_ids": list(self.active_sessions.keys())
            }


class SecurityAuditor:
    """Security audit logging system."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.audit_events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.max_events = 10000  # Keep last 10k events in memory

        # Setup audit logger
        self.audit_logger = logging.getLogger("security.audit")
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
            self.audit_logger.setLevel(logging.INFO)

        if PROMETHEUS_AVAILABLE:
            self.audit_events_counter = Counter(
                'security_audit_events_total',
                'Total security audit events',
                ['event_type', 'severity']
            )

    def log_event(self, event_type: str, severity: str, message: str,
                  context: Optional[SecurityContext] = None, **kwargs):
        """Log a security audit event."""
        timestamp = datetime.now(timezone.utc)

        event = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "user_id": context.user_id if context else None,
            "session_id": context.session_id if context else None,
            "ip_address": context.ip_address if context else None,
            **kwargs
        }

        with self._lock:
            self.audit_events.append(event)

            # Trim events if needed
            if len(self.audit_events) > self.max_events:
                self.audit_events = self.audit_events[-self.max_events:]

        # Log to file/console
        log_message = f"{event_type}: {message}"
        if context and context.user_id:
            log_message += f" (user: {context.user_id})"

        if severity == "high":
            self.audit_logger.error(log_message)
        elif severity == "medium":
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)

        if PROMETHEUS_AVAILABLE:
            self.audit_events_counter.labels(
                event_type=event_type,
                severity=severity
            ).inc()

    def get_recent_events(self, limit: int = 100,
                         event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent audit events."""
        with self._lock:
            events = self.audit_events.copy()

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]

        return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        with self._lock:
            total_events = len(self.audit_events)
            event_types = {}

            for event in self.audit_events:
                event_type = event["event_type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "total_events": total_events,
            "event_types": event_types,
            "log_file": self.log_file
        }


class SecureTempFileManager:
    """Secure temporary file manager."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir()) / "mce_secure"
        self.base_dir.mkdir(exist_ok=True, mode=0o700)  # Restrictive permissions
        self.active_files: Dict[str, Path] = {}
        self._lock = threading.Lock()

        if PROMETHEUS_AVAILABLE:
            self.temp_files_gauge = Gauge(
                'secure_temp_files_active',
                'Number of active secure temporary files'
            )

    @contextmanager
    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "secure_"):
        """Create a secure temporary file."""
        file_id = secrets.token_hex(16)
        file_path = self.base_dir / f"{prefix}{file_id}{suffix}"

        try:
            # Create file with restrictive permissions
            file_path.touch(mode=0o600)

            with self._lock:
                self.active_files[file_id] = file_path
                if PROMETHEUS_AVAILABLE:
                    self.temp_files_gauge.set(len(self.active_files))

            logger.debug(f"Created secure temp file: {file_path}")
            yield file_path

        finally:
            # Clean up
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temp file {file_path}: {e}")

            with self._lock:
                self.active_files.pop(file_id, None)
                if PROMETHEUS_AVAILABLE:
                    self.temp_files_gauge.set(len(self.active_files))

    def cleanup_all(self):
        """Clean up all temporary files."""
        with self._lock:
            files_to_clean = list(self.active_files.values())
            self.active_files.clear()

        cleaned_count = 0
        for file_path in files_to_clean:
            try:
                if file_path.exists():
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to clean up temp file {file_path}: {e}")

        logger.info(f"Cleaned up {cleaned_count} temporary files")

        if PROMETHEUS_AVAILABLE:
            self.temp_files_gauge.set(0)

    def get_stats(self) -> Dict[str, Any]:
        """Get temporary file statistics."""
        with self._lock:
            return {
                "active_files": len(self.active_files),
                "base_directory": str(self.base_dir)
            }


def sanitize_input_string(input_str: str, max_length: int = 1000) -> str:
    """Comprehensive input string sanitization."""
    if not input_str:
        return ""

    # Truncate to max length
    sanitized = input_str[:max_length]

    # Remove null bytes and control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {pattern}")
            raise SecurityError("Input contains potentially malicious SQL patterns")

    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE | re.DOTALL):
            logger.warning(f"Potential XSS detected: {pattern}")
            raise SecurityError("Input contains potentially malicious XSS patterns")

    return sanitized


def validate_ip_address(ip_str: str, allowed_private: bool = True) -> bool:
    """Validate and check IP address."""
    try:
        ip = ipaddress.ip_address(ip_str)

        # Check if private IP is allowed
        if not allowed_private and ip.is_private:
            return False

        # Check against blocked IPs (would be configurable)
        config = get_config()
        if hasattr(config, 'security') and hasattr(config.security, 'blocked_ips'):
            if ip_str in config.security.blocked_ips:
                return False

        return True

    except ValueError:
        return False


def generate_secure_hash(data: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generate a secure hash with salt."""
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 for password hashing
    hash_value = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
    return hash_value.hex(), salt


def verify_secure_hash(data: str, hash_value: str, salt: str) -> bool:
    """Verify a secure hash."""
    computed_hash, _ = generate_secure_hash(data, salt)
    return hmac.compare_digest(computed_hash, hash_value)


def check_authorization(context: SecurityContext, required_permission: PermissionType) -> bool:
    """Check if user has required permission."""
    if not context.authenticated:
        return False

    # Admin permission grants all access
    if PermissionType.ADMIN in context.permissions:
        return True

    return required_permission in context.permissions


def require_permission(required_permission: PermissionType):
    """Decorator to require specific permission."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context from kwargs or thread local
            context = kwargs.get('security_context')
            if not context:
                raise AuthorizationError("No security context provided")

            if not check_authorization(context, required_permission):
                raise AuthorizationError(f"Insufficient permissions. Required: {required_permission.value}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


class EnhancedSecurityManager:
    """Comprehensive security manager."""

    def __init__(self, config: Optional[EnhancedSecurityConfig] = None):
        self.config = config or EnhancedSecurityConfig()
        self.virus_scanner = VirusScanner() if self.config.enable_virus_scanning else None
        self.rate_limiter = RateLimiter(self.config.rate_limit) if self.config.enable_rate_limiting else None
        self.auth_manager = AuthenticationManager(self.config.jwt_secret_key)
        self.auditor = SecurityAuditor() if self.config.enable_audit_logging else None
        self.temp_file_manager = SecureTempFileManager()

        if PROMETHEUS_AVAILABLE:
            self.security_checks = Counter(
                'security_checks_total',
                'Total security checks performed',
                ['check_type', 'result']
            )

    def validate_file_upload(self, file_path: Path, context: Optional[SecurityContext] = None) -> Dict[str, Any]:
        """Comprehensive file upload validation."""
        validation_result = {
            "valid": True,
            "issues": [],
            "virus_scan": None,
            "file_info": {}
        }

        try:
            # Basic file validation
            validated_path = validate_file_input(file_path)

            # Virus scanning
            if self.virus_scanner:
                is_clean, threat_name = self.virus_scanner.scan_file(validated_path)
                validation_result["virus_scan"] = {
                    "clean": is_clean,
                    "threat": threat_name
                }

                if not is_clean:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Virus detected: {threat_name}")

                    if self.auditor:
                        self.auditor.log_event(
                            "virus_detected",
                            "high",
                            f"Virus detected in uploaded file: {threat_name}",
                            context,
                            file_path=str(file_path),
                            threat_name=threat_name
                        )

            # File info
            stat = file_path.stat()
            validation_result["file_info"] = {
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "extension": file_path.suffix.lower(),
                "mime_type": self._detect_mime_type(file_path)
            }

            if PROMETHEUS_AVAILABLE:
                result = "success" if validation_result["valid"] else "failure"
                self.security_checks.labels(check_type='file_upload', result=result).inc()

            return validation_result

        except Exception as e:
            logger.error(f"File validation failed: {e}")
            validation_result["valid"] = False
            validation_result["issues"].append(str(e))

            if PROMETHEUS_AVAILABLE:
                self.security_checks.labels(check_type='file_upload', result='error').inc()

            return validation_result

    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type based on file content."""
        try:
            from .security import FILE_SIGNATURES

            with open(file_path, 'rb') as f:
                header = f.read(16)

            for signature, file_type in FILE_SIGNATURES.items():
                if header.startswith(signature):
                    if file_type == "pdf":
                        return "application/pdf"
                    elif file_type == "image":
                        if signature == b"\x89PNG":
                            return "image/png"
                        elif signature == b"\xff\xd8\xff":
                            return "image/jpeg"
                        elif signature == b"GIF8":
                            return "image/gif"
                        else:
                            return "image/unknown"

            return "application/octet-stream"

        except Exception:
            return "unknown"

    def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit for identifier."""
        if not self.rate_limiter:
            return True, {"rate_limiting_disabled": True}

        return self.rate_limiter.is_allowed(identifier)

    def authenticate_request(self, token: str) -> SecurityContext:
        """Authenticate a request using JWT token."""
        context = self.auth_manager.verify_token(token)

        if self.auditor:
            self.auditor.log_event(
                "authentication",
                "low",
                "User authenticated successfully",
                context
            )

        return context

    def create_user_session(self, user_id: str, permissions: Set[PermissionType],
                           additional_claims: Dict[str, Any] = None) -> str:
        """Create authenticated user session."""
        token = self.auth_manager.create_token(user_id, permissions, additional_claims)

        if self.auditor:
            self.auditor.log_event(
                "session_created",
                "low",
                f"New session created for user: {user_id}",
                SecurityContext(user_id=user_id, permissions=permissions),
                permissions=[p.value for p in permissions]
            )

        return token

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "virus_scanning": self.virus_scanner.get_stats() if self.virus_scanner else {"enabled": False},
                "rate_limiting": self.rate_limiter.get_stats() if self.rate_limiter else {"enabled": False},
                "authentication": self.auth_manager.get_stats(),
                "audit_logging": self.auditor.get_stats() if self.auditor else {"enabled": False},
                "temp_files": self.temp_file_manager.get_stats()
            },
            "config": {
                "virus_scanning_enabled": self.config.enable_virus_scanning,
                "rate_limiting_enabled": self.config.enable_rate_limiting,
                "audit_logging_enabled": self.config.enable_audit_logging,
                "encryption_enabled": self.config.enable_encryption
            }
        }

        return status

    def cleanup(self):
        """Clean up security manager resources."""
        if self.temp_file_manager:
            self.temp_file_manager.cleanup_all()

        if self.auth_manager:
            self.auth_manager.cleanup_expired_sessions()

        logger.info("Security manager cleanup completed")


# Global security manager instance
_security_manager: Optional[EnhancedSecurityManager] = None


def get_security_manager() -> EnhancedSecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = EnhancedSecurityManager()
    return _security_manager


# Compatibility functions to maintain existing API
def enhanced_validate_file_input(file_path: Path, max_size_mb: int | None = None,
                                security_context: Optional[SecurityContext] = None) -> Path:
    """Enhanced file validation with security context."""
    manager = get_security_manager()

    # Basic validation first
    validated_path = validate_file_input(file_path, max_size_mb)

    # Enhanced validation
    validation_result = manager.validate_file_upload(validated_path, security_context)

    if not validation_result["valid"]:
        issues = ", ".join(validation_result["issues"])
        raise SecurityError(f"File validation failed: {issues}")

    return validated_path


# Example usage and testing
if __name__ == "__main__":
    # Example of using the enhanced security framework
    manager = get_security_manager()

    # Create a test user session
    permissions = {PermissionType.READ, PermissionType.WRITE}
    token = manager.create_user_session("test_user", permissions)
    print(f"Created token: {token[:50]}...")

    # Authenticate with the token
    try:
        context = manager.authenticate_request(token)
        print(f"Authenticated user: {context.user_id}")
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")

    # Test rate limiting
    allowed, info = manager.check_rate_limit("127.0.0.1")
    print(f"Rate limit check: {allowed}, info: {info}")

    # Get security status
    status = manager.get_security_status()
    print(f"Security status: {status['config']}")
