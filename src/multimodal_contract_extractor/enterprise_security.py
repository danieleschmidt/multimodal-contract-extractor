"""Enterprise Security Module for Contract Processing.

This module implements comprehensive security measures including advanced
encryption, secure key management, audit logging, threat detection,
and compliance frameworks for enterprise-grade contract processing.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import cryptography.fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field, SecretStr

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatLevel(Enum):
    """Threat levels for security monitoring."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event for audit logging."""

    event_id: str
    timestamp: float
    event_type: str
    severity: ThreatLevel
    user_id: Optional[str]
    source_ip: Optional[str]
    resource: str
    action: str
    outcome: str  # success, failure, blocked
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0


class EncryptionManager:
    """Advanced encryption manager for secure data handling."""

    def __init__(self):
        self.master_key: Optional[bytes] = None
        self.key_rotation_interval = 86400 * 30  # 30 days
        self.last_key_rotation = time.time()
        self.encryption_cache: Dict[str, bytes] = {}

    def initialize_master_key(self, password: Optional[str] = None) -> None:
        """Initialize or load master key."""
        key_file = Path.home() / ".mce" / "master.key"

        if key_file.exists() and password:
            # Load existing key
            self.master_key = self._load_master_key(key_file, password)
        else:
            # Generate new key
            self.master_key = self._generate_master_key()
            if password:
                self._save_master_key(key_file, self.master_key, password)

        logger.info("Master key initialized")

    def _generate_master_key(self) -> bytes:
        """Generate a new master key."""
        return secrets.token_bytes(32)  # 256-bit key

    def _save_master_key(self, key_file: Path, key: bytes, password: str) -> None:
        """Save master key encrypted with password."""
        key_file.parent.mkdir(parents=True, exist_ok=True)

        # Derive key from password
        salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = kdf.derive(password.encode())

        # Encrypt master key
        fernet = cryptography.fernet.Fernet(
            cryptography.fernet.base64.urlsafe_b64encode(derived_key)
        )
        encrypted_key = fernet.encrypt(key)

        # Save with salt
        with key_file.open("wb") as f:
            f.write(salt + encrypted_key)

        # Set restrictive permissions
        key_file.chmod(0o600)

    def _load_master_key(self, key_file: Path, password: str) -> bytes:
        """Load and decrypt master key."""
        with key_file.open("rb") as f:
            data = f.read()

        salt = data[:16]
        encrypted_key = data[16:]

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = kdf.derive(password.encode())

        # Decrypt master key
        fernet = cryptography.fernet.Fernet(
            cryptography.fernet.base64.urlsafe_b64encode(derived_key)
        )
        return fernet.decrypt(encrypted_key)

    def encrypt_data(self, data: bytes, context: str = "") -> Dict[str, Any]:
        """Encrypt data with context-specific encryption."""
        if not self.master_key:
            raise ValueError("Master key not initialized")

        # Generate unique key for this encryption
        salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=10000,
        )
        encryption_key = kdf.derive(self.master_key + context.encode())

        # Generate IV
        iv = secrets.token_bytes(16)

        # Encrypt data
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv)
        )
        encryptor = cipher.encryptor()

        # Add padding
        padding_length = 16 - (len(data) % 16)
        padded_data = data + bytes([padding_length]) * padding_length

        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # Create integrity hash
        integrity_hash = hmac.new(
            encryption_key[:16],
            encrypted_data,
            hashlib.sha256
        ).hexdigest()

        return {
            "encrypted_data": encrypted_data.hex(),
            "salt": salt.hex(),
            "iv": iv.hex(),
            "integrity_hash": integrity_hash,
            "context": context,
            "timestamp": time.time()
        }

    def decrypt_data(self, encrypted_package: Dict[str, Any]) -> bytes:
        """Decrypt data using encryption package."""
        if not self.master_key:
            raise ValueError("Master key not initialized")

        # Extract components
        encrypted_data = bytes.fromhex(encrypted_package["encrypted_data"])
        salt = bytes.fromhex(encrypted_package["salt"])
        iv = bytes.fromhex(encrypted_package["iv"])
        stored_hash = encrypted_package["integrity_hash"]
        context = encrypted_package["context"]

        # Derive decryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=10000,
        )
        encryption_key = kdf.derive(self.master_key + context.encode())

        # Verify integrity
        computed_hash = hmac.new(
            encryption_key[:16],
            encrypted_data,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(stored_hash, computed_hash):
            raise ValueError("Data integrity verification failed")

        # Decrypt data
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv)
        )
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]

    def rotate_master_key(self, new_password: Optional[str] = None) -> None:
        """Rotate master key for enhanced security."""
        if time.time() - self.last_key_rotation < self.key_rotation_interval:
            logger.info("Key rotation not needed yet")
            return

        old_key = self.master_key
        new_key = self._generate_master_key()

        # TODO: Re-encrypt all cached data with new key
        self.master_key = new_key
        self.last_key_rotation = time.time()
        self.encryption_cache.clear()

        if new_password:
            key_file = Path.home() / ".mce" / "master.key"
            self._save_master_key(key_file, new_key, new_password)

        logger.info("Master key rotated successfully")


class AuditLogger:
    """Comprehensive audit logging for security events."""

    def __init__(self):
        self.audit_events: List[SecurityEvent] = []
        self.max_events_memory = 10000
        self.log_file = Path.home() / ".mce" / "audit.log"
        self.encryption_manager = EncryptionManager()

    def log_security_event(
        self,
        event_type: str,
        severity: ThreatLevel,
        resource: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a security event."""
        event_id = secrets.token_hex(16)

        event = SecurityEvent(
            event_id=event_id,
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            source_ip=source_ip,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            risk_score=self._calculate_risk_score(event_type, severity, outcome)
        )

        # Add to memory
        self.audit_events.append(event)

        # Trim memory if needed
        if len(self.audit_events) > self.max_events_memory:
            self.audit_events = self.audit_events[-self.max_events_memory:]

        # Write to secure audit log
        self._write_audit_log(event)

        # Check for threat patterns
        self._analyze_threat_patterns(event)

        return event_id

    def _calculate_risk_score(
        self,
        event_type: str,
        severity: ThreatLevel,
        outcome: str
    ) -> float:
        """Calculate risk score for security event."""
        base_scores = {
            ThreatLevel.INFO: 0.1,
            ThreatLevel.LOW: 0.3,
            ThreatLevel.MEDIUM: 0.6,
            ThreatLevel.HIGH: 0.8,
            ThreatLevel.CRITICAL: 1.0
        }

        base_score = base_scores.get(severity, 0.5)

        # Adjust for outcome
        if outcome == "failure":
            base_score *= 1.5
        elif outcome == "blocked":
            base_score *= 0.8

        # Adjust for event type
        high_risk_events = [
            "authentication_failure",
            "unauthorized_access",
            "data_breach",
            "malware_detected"
        ]

        if event_type in high_risk_events:
            base_score *= 1.3

        return min(1.0, base_score)

    def _write_audit_log(self, event: SecurityEvent) -> None:
        """Write security event to encrypted audit log."""
        try:
            # Create audit log directory
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare event data
            event_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "iso_timestamp": datetime.fromtimestamp(
                    event.timestamp, timezone.utc
                ).isoformat(),
                "event_type": event.event_type,
                "severity": event.severity.value,
                "user_id": event.user_id,
                "source_ip": event.source_ip,
                "resource": event.resource,
                "action": event.action,
                "outcome": event.outcome,
                "details": event.details,
                "risk_score": event.risk_score
            }

            # Encrypt if encryption is available
            if self.encryption_manager.master_key:
                encrypted_data = self.encryption_manager.encrypt_data(
                    json.dumps(event_data).encode(),
                    context="audit_log"
                )
                log_entry = f"ENCRYPTED:{json.dumps(encrypted_data)}\n"
            else:
                log_entry = f"{json.dumps(event_data)}\n"

            # Append to audit log with proper permissions
            with self.log_file.open("a") as f:
                f.write(log_entry)

            # Set restrictive permissions
            self.log_file.chmod(0o600)

        except Exception as e:
            logger.error("Failed to write audit log: %s", e)

    def _analyze_threat_patterns(self, event: SecurityEvent) -> None:
        """Analyze event for threat patterns."""
        recent_events = [
            e for e in self.audit_events
            if time.time() - e.timestamp < 300  # Last 5 minutes
        ]

        # Check for brute force patterns
        if event.event_type == "authentication_failure":
            failures = [
                e for e in recent_events
                if e.event_type == "authentication_failure"
                and e.user_id == event.user_id
            ]

            if len(failures) >= 5:
                self.log_security_event(
                    event_type="brute_force_detected",
                    severity=ThreatLevel.HIGH,
                    resource="authentication_system",
                    action="pattern_detection",
                    outcome="threat_detected",
                    user_id=event.user_id,
                    source_ip=event.source_ip,
                    details={
                        "failure_count": len(failures),
                        "time_window": "5_minutes"
                    }
                )

        # Check for suspicious IP patterns
        if event.source_ip:
            ip_events = [
                e for e in recent_events
                if e.source_ip == event.source_ip
                and e.severity in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]
            ]

            if len(ip_events) >= 3:
                self.log_security_event(
                    event_type="suspicious_ip_activity",
                    severity=ThreatLevel.MEDIUM,
                    resource="network_security",
                    action="pattern_detection",
                    outcome="threat_detected",
                    source_ip=event.source_ip,
                    details={
                        "event_count": len(ip_events),
                        "time_window": "5_minutes"
                    }
                )

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security event summary."""
        if not self.audit_events:
            return {"total_events": 0}

        # Recent events (last 24 hours)
        recent_threshold = time.time() - 86400
        recent_events = [
            e for e in self.audit_events
            if e.timestamp >= recent_threshold
        ]

        # Count by severity
        severity_counts = {}
        for event in recent_events:
            severity_counts[event.severity.value] = (
                severity_counts.get(event.severity.value, 0) + 1
            )

        # Count by outcome
        outcome_counts = {}
        for event in recent_events:
            outcome_counts[event.outcome] = (
                outcome_counts.get(event.outcome, 0) + 1
            )

        # Calculate average risk score
        avg_risk_score = (
            sum(e.risk_score for e in recent_events) / len(recent_events)
            if recent_events else 0.0
        )

        return {
            "total_events": len(self.audit_events),
            "recent_events_24h": len(recent_events),
            "severity_distribution": severity_counts,
            "outcome_distribution": outcome_counts,
            "average_risk_score": round(avg_risk_score, 3),
            "high_risk_events": len([
                e for e in recent_events
                if e.risk_score > 0.7
            ])
        }


class ThreatDetector:
    """Advanced threat detection system."""

    def __init__(self):
        self.threat_patterns = {
            "sql_injection": [
                r"(?i)(union\s+select|insert\s+into|delete\s+from)",
                r"(?i)(drop\s+table|alter\s+table)",
                r"(?i)(exec\s*\(|execute\s*\()"
            ],
            "xss_attempt": [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=\s*[\"'][^\"']*[\"']"
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f"
            ]
        }
        self.suspicious_file_extensions = {
            ".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".jar"
        }

    def scan_input(self, input_data: str, context: str = "") -> Dict[str, Any]:
        """Scan input for threat patterns."""
        threats_detected = []
        risk_score = 0.0

        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, input_data):
                    threats_detected.append({
                        "type": threat_type,
                        "pattern": pattern,
                        "context": context
                    })
                    risk_score += 0.3  # Each threat increases risk

        return {
            "threats_detected": threats_detected,
            "risk_score": min(1.0, risk_score),
            "input_length": len(input_data),
            "scan_timestamp": time.time()
        }

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan file for security threats."""
        threats = []
        risk_score = 0.0

        # Check file extension
        if file_path.suffix.lower() in self.suspicious_file_extensions:
            threats.append({
                "type": "suspicious_file_extension",
                "details": f"File extension {file_path.suffix} is potentially dangerous"
            })
            risk_score += 0.5

        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                threats.append({
                    "type": "large_file_size",
                    "details": f"File size {file_size} bytes exceeds safe limits"
                })
                risk_score += 0.2
        except OSError:
            pass

        return {
            "file_path": str(file_path),
            "threats_detected": threats,
            "risk_score": min(1.0, risk_score),
            "scan_timestamp": time.time()
        }


class ComplianceManager:
    """Compliance framework manager for various regulations."""

    def __init__(self):
        self.compliance_frameworks = {
            "GDPR": {
                "data_retention_days": 2555,  # 7 years
                "requires_consent": True,
                "requires_encryption": True,
                "data_subject_rights": [
                    "access", "rectification", "erasure", "portability"
                ]
            },
            "CCPA": {
                "data_retention_days": 2555,
                "requires_consent": False,
                "requires_encryption": True,
                "data_subject_rights": ["access", "deletion", "opt_out"]
            },
            "HIPAA": {
                "data_retention_days": 2190,  # 6 years
                "requires_consent": True,
                "requires_encryption": True,
                "audit_requirements": ["access_logs", "modification_logs"]
            },
            "SOX": {
                "data_retention_days": 2555,  # 7 years
                "requires_encryption": True,
                "audit_requirements": [
                    "financial_data_access", "data_integrity", "change_control"
                ]
            }
        }
        self.active_frameworks: Set[str] = set()

    def enable_framework(self, framework: str) -> None:
        """Enable a compliance framework."""
        if framework in self.compliance_frameworks:
            self.active_frameworks.add(framework)
            logger.info("Enabled compliance framework: %s", framework)
        else:
            raise ValueError(f"Unknown compliance framework: {framework}")

    def check_compliance(self, operation: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check operation against active compliance frameworks."""
        compliance_results = {}
        overall_compliant = True

        for framework in self.active_frameworks:
            framework_config = self.compliance_frameworks[framework]
            result = self._check_framework_compliance(
                framework, framework_config, operation, data_context
            )
            compliance_results[framework] = result

            if not result["compliant"]:
                overall_compliant = False

        return {
            "overall_compliant": overall_compliant,
            "framework_results": compliance_results,
            "recommendations": self._generate_compliance_recommendations(compliance_results)
        }

    def _check_framework_compliance(
        self,
        framework: str,
        config: Dict[str, Any],
        operation: str,
        data_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance for a specific framework."""
        violations = []

        # Check encryption requirement
        if config.get("requires_encryption") and not data_context.get("encrypted"):
            violations.append("Data must be encrypted")

        # Check consent requirement
        if config.get("requires_consent") and not data_context.get("consent_obtained"):
            violations.append("User consent required")

        # Check data retention
        if "data_age_days" in data_context:
            max_retention = config.get("data_retention_days", 365)
            if data_context["data_age_days"] > max_retention:
                violations.append(f"Data exceeds retention period of {max_retention} days")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "framework": framework
        }

    def _generate_compliance_recommendations(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for compliance violations."""
        recommendations = []

        for framework, result in results.items():
            if not result["compliant"]:
                for violation in result["violations"]:
                    if "encrypted" in violation:
                        recommendations.append(
                            "Enable data encryption for all sensitive information"
                        )
                    elif "consent" in violation:
                        recommendations.append(
                            "Implement consent management system"
                        )
                    elif "retention" in violation:
                        recommendations.append(
                            "Implement automated data retention policies"
                        )

        return list(set(recommendations))  # Remove duplicates


# Global security components
_encryption_manager: Optional[EncryptionManager] = None
_audit_logger: Optional[AuditLogger] = None
_threat_detector: Optional[ThreatDetector] = None
_compliance_manager: Optional[ComplianceManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_threat_detector() -> ThreatDetector:
    """Get global threat detector."""
    global _threat_detector
    if _threat_detector is None:
        _threat_detector = ThreatDetector()
    return _threat_detector


def get_compliance_manager() -> ComplianceManager:
    """Get global compliance manager."""
    global _compliance_manager
    if _compliance_manager is None:
        _compliance_manager = ComplianceManager()
    return _compliance_manager


class EnterpriseSecurityConfig(BaseModel):
    """Configuration for enterprise security features."""

    enable_encryption: bool = True
    master_key_password: Optional[SecretStr] = None
    key_rotation_days: int = Field(default=30, ge=1, le=365)
    enable_audit_logging: bool = True
    enable_threat_detection: bool = True
    threat_detection_sensitivity: float = Field(default=0.7, ge=0.1, le=1.0)
    enable_compliance_checking: bool = True
    compliance_frameworks: List[str] = Field(default_factory=lambda: ["GDPR"])
    audit_retention_days: int = Field(default=2555, ge=30, le=3653)  # 7 years max
    max_file_size_mb: int = Field(default=100, ge=1, le=1000)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }
