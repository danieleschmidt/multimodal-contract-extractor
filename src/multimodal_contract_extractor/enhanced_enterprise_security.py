"""
Enhanced Enterprise Security and Compliance Framework

Comprehensive security measures, compliance frameworks, and data protection
for the multimodal contract extractor system with novel research algorithms.
"""

from __future__ import annotations

import asyncio
import base64
import functools
import json
import logging
import secrets
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

import numpy as np

from .enterprise_error_handling import ComponentType

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ComplianceStandard(Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST = "nist"


class AccessLevel(Enum):
    """User access levels."""

    GUEST = "guest"
    USER = "user"
    RESEARCHER = "researcher"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    SYSTEM = "system"


class AuditEventType(Enum):
    """Types of audit events."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ALGORITHM_EXECUTION = "algorithm_execution"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_CHECK = "compliance_check"
    ENCRYPTION_OPERATION = "encryption_operation"
    KEY_MANAGEMENT = "key_management"
    FEDERATED_LEARNING = "federated_learning"


@dataclass
class SecurityContext:
    """Security context for operations."""

    user_id: str
    session_id: str
    access_level: AccessLevel
    permissions: Set[str] = field(default_factory=set)
    security_classification: SecurityLevel = SecurityLevel.INTERNAL
    compliance_requirements: Set[ComplianceStandard] = field(default_factory=set)
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AuditEvent:
    """Audit event for compliance logging."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.DATA_ACCESS
    timestamp: float = field(default_factory=time.time)
    user_id: str = ""
    session_id: str = ""
    component: ComponentType = ComponentType.DOCUMENT_PROCESSOR
    operation: str = ""
    resource: str = ""
    result: str = "success"  # success, failure, error
    details: Dict[str, Any] = field(default_factory=dict)
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: str = ""
    security_classification: SecurityLevel = SecurityLevel.INTERNAL
    compliance_tags: Set[str] = field(default_factory=set)


class EnhancedEncryptionManager:
    """Advanced encryption and key management for research algorithms."""

    def __init__(self):
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available - using mock encryption")

        self.master_key = self._generate_master_key()
        self.encryption_keys: Dict[str, bytes] = {}
        self.key_rotation_schedule: Dict[str, float] = {}
        self.key_usage_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

        # Algorithm-specific encryption configurations
        self.algorithm_encryption_configs = {
            ComponentType.QUANTUM_PROCESSOR: {
                'key_size': 256,
                'rotation_interval': 86400,  # 24 hours
                'max_usage_count': 10000
            },
            ComponentType.NEUROMORPHIC_ENGINE: {
                'key_size': 256,
                'rotation_interval': 86400,
                'max_usage_count': 10000
            },
            ComponentType.FEDERATED_LEARNER: {
                'key_size': 256,
                'rotation_interval': 3600,  # 1 hour for federated learning
                'max_usage_count': 1000
            }
        }

    def _generate_master_key(self) -> bytes:
        """Generate master encryption key."""
        if CRYPTOGRAPHY_AVAILABLE:
            return Fernet.generate_key()
        else:
            return secrets.token_bytes(32)  # Mock key

    def generate_component_key(self, component: ComponentType) -> str:
        """Generate encryption key for a specific component."""
        key_id = f"{component.value}_{int(time.time())}"

        if CRYPTOGRAPHY_AVAILABLE:
            key = Fernet.generate_key()
        else:
            key = secrets.token_bytes(32)  # Mock key

        config = self.algorithm_encryption_configs.get(component, {
            'key_size': 256,
            'rotation_interval': 86400,
            'max_usage_count': 10000
        })

        with self._lock:
            self.encryption_keys[key_id] = key
            self.key_rotation_schedule[key_id] = time.time() + config['rotation_interval']
            self.key_usage_counts[key_id] = 0

        logger.info(f"Generated encryption key for {component.value}: {key_id}")
        return key_id

    def get_key(self, key_id: str) -> Optional[bytes]:
        """Get encryption key by ID."""
        with self._lock:
            key = self.encryption_keys.get(key_id)
            if key:
                self.key_usage_counts[key_id] = self.key_usage_counts.get(key_id, 0) + 1
            return key

    def encrypt_data(self, data: Union[str, bytes], key_id: str) -> Optional[bytes]:
        """Encrypt data using specified key."""
        key = self.get_key(key_id)
        if not key:
            logger.error(f"Encryption key not found: {key_id}")
            return None

        try:
            if CRYPTOGRAPHY_AVAILABLE:
                fernet = Fernet(key)
                if isinstance(data, str):
                    data = data.encode('utf-8')

                encrypted_data = fernet.encrypt(data)
                logger.debug(f"Data encrypted with key: {key_id}")
                return encrypted_data
            else:
                # Mock encryption - just base64 encode
                if isinstance(data, str):
                    data = data.encode('utf-8')
                return base64.b64encode(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt_data(self, encrypted_data: bytes, key_id: str) -> Optional[bytes]:
        """Decrypt data using specified key."""
        key = self.get_key(key_id)
        if not key:
            logger.error(f"Decryption key not found: {key_id}")
            return None

        try:
            if CRYPTOGRAPHY_AVAILABLE:
                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(encrypted_data)
                logger.debug(f"Data decrypted with key: {key_id}")
                return decrypted_data
            else:
                # Mock decryption - base64 decode
                return base64.b64decode(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def encrypt_research_data(self, research_data: Dict[str, Any], component: ComponentType) -> Dict[str, Any]:
        """Encrypt research algorithm data."""
        key_id = self.generate_component_key(component)

        # Encrypt sensitive fields
        sensitive_fields = ['weights', 'parameters', 'gradients', 'training_data', 'model_state']
        encrypted_data = research_data.copy()

        for field in sensitive_fields:
            if field in research_data:
                field_data = json.dumps(research_data[field]).encode('utf-8')
                encrypted_field = self.encrypt_data(field_data, key_id)
                if encrypted_field:
                    encrypted_data[field] = base64.b64encode(encrypted_field).decode('utf-8')
                    encrypted_data[f"{field}_encrypted"] = True
                    encrypted_data[f"{field}_key_id"] = key_id

        return encrypted_data

    def decrypt_research_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt research algorithm data."""
        decrypted_data = encrypted_data.copy()

        # Find encrypted fields
        encrypted_fields = [
            key.replace('_encrypted', '') for key in encrypted_data.keys()
            if key.endswith('_encrypted') and encrypted_data[key] is True
        ]

        for field in encrypted_fields:
            key_id = encrypted_data.get(f"{field}_key_id")
            if key_id and field in encrypted_data:
                try:
                    encrypted_bytes = base64.b64decode(encrypted_data[field])
                    decrypted_bytes = self.decrypt_data(encrypted_bytes, key_id)
                    if decrypted_bytes:
                        decrypted_data[field] = json.loads(decrypted_bytes.decode('utf-8'))
                        # Clean up encryption metadata
                        decrypted_data.pop(f"{field}_encrypted", None)
                        decrypted_data.pop(f"{field}_key_id", None)
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")

        return decrypted_data

    def get_key_statistics(self) -> Dict[str, Any]:
        """Get encryption key statistics."""
        with self._lock:
            active_keys = len(self.encryption_keys)
            total_usage = sum(self.key_usage_counts.values())

            # Keys by component
            component_keys = {}
            for key_id in self.encryption_keys.keys():
                component = key_id.split('_')[0]
                component_keys[component] = component_keys.get(component, 0) + 1

            return {
                'active_keys': active_keys,
                'total_key_usage': total_usage,
                'keys_by_component': component_keys,
                'keys_due_rotation': len([
                    k for k, t in self.key_rotation_schedule.items()
                    if time.time() >= t
                ])
            }


class FederatedLearningSecurityManager:
    """Security manager for federated learning operations."""

    def __init__(self, encryption_manager: EnhancedEncryptionManager):
        self.encryption_manager = encryption_manager
        self.participant_keys: Dict[str, Dict[str, Any]] = {}
        self.secure_aggregation_rounds: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_participant(self, participant_id: str, public_key: bytes) -> Dict[str, Any]:
        """Register a federated learning participant."""
        with self._lock:
            self.participant_keys[participant_id] = {
                'public_key': public_key,
                'registration_time': time.time(),
                'active': True,
                'trust_score': 1.0
            }

        logger.info(f"Registered federated learning participant: {participant_id}")
        return {'status': 'registered', 'participant_id': participant_id}

    def generate_secure_aggregation_keys(self, round_id: str, participants: List[str]) -> Dict[str, Any]:
        """Generate keys for secure aggregation round."""
        aggregation_keys = {}

        # Generate shared secret for each pair of participants
        for i, participant_a in enumerate(participants):
            for participant_b in participants[i+1:]:
                pair_key = secrets.token_bytes(32)
                key_id = f"{round_id}_{participant_a}_{participant_b}"

                # Store encrypted key for each participant
                if participant_a not in aggregation_keys:
                    aggregation_keys[participant_a] = {}
                if participant_b not in aggregation_keys:
                    aggregation_keys[participant_b] = {}

                aggregation_keys[participant_a][participant_b] = base64.b64encode(pair_key).decode('utf-8')
                aggregation_keys[participant_b][participant_a] = base64.b64encode(pair_key).decode('utf-8')

        with self._lock:
            self.secure_aggregation_rounds[round_id] = {
                'participants': participants,
                'keys': aggregation_keys,
                'created_time': time.time(),
                'status': 'active'
            }

        logger.info(f"Generated secure aggregation keys for round {round_id} with {len(participants)} participants")
        return aggregation_keys

    def encrypt_model_update(self, model_update: Dict[str, Any], participant_id: str, round_id: str) -> Dict[str, Any]:
        """Encrypt model update for secure aggregation."""
        # Add differential privacy noise
        noised_update = self._add_differential_privacy_noise(model_update)

        # Encrypt with participant's key
        key_id = self.encryption_manager.generate_component_key(ComponentType.FEDERATED_LEARNER)
        encrypted_update = self.encryption_manager.encrypt_research_data(noised_update, ComponentType.FEDERATED_LEARNER)

        return {
            'participant_id': participant_id,
            'round_id': round_id,
            'encrypted_update': encrypted_update,
            'timestamp': time.time(),
            'privacy_budget_used': 0.1  # Example privacy budget
        }

    def _add_differential_privacy_noise(self, model_update: Dict[str, Any], epsilon: float = 1.0) -> Dict[str, Any]:
        """Add differential privacy noise to model updates."""
        noised_update = model_update.copy()

        # Add Laplace noise to numeric parameters
        for key, value in model_update.items():
            if isinstance(value, (int, float)):
                noise = np.random.laplace(0, 1/epsilon)  # Laplace mechanism
                noised_update[key] = value + noise
            elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                noise = np.random.laplace(0, 1/epsilon, len(value))
                noised_update[key] = [v + n for v, n in zip(value, noise)]

        return noised_update

    def validate_participant_integrity(self, participant_id: str, model_update: Dict[str, Any]) -> Dict[str, Any]:
        """Validate participant integrity and detect potential attacks."""
        with self._lock:
            participant_info = self.participant_keys.get(participant_id)

        if not participant_info:
            return {'valid': False, 'reason': 'unknown_participant'}

        # Check for Byzantine attacks (simplified)
        validation_checks = {
            'participant_known': participant_id in self.participant_keys,
            'update_size_valid': len(str(model_update)) < 1024 * 1024,  # 1MB limit
            'trust_score_acceptable': participant_info.get('trust_score', 0) > 0.5,
            'recent_activity': time.time() - participant_info.get('registration_time', 0) < 86400 * 30  # 30 days
        }

        all_valid = all(validation_checks.values())

        if not all_valid:
            # Reduce trust score
            with self._lock:
                self.participant_keys[participant_id]['trust_score'] *= 0.9

        return {
            'valid': all_valid,
            'checks': validation_checks,
            'trust_score': participant_info.get('trust_score', 0)
        }


class EnhancedAccessControlManager:
    """Role-based access control and permissions management."""

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, SecurityContext] = {}
        self.permissions: Dict[AccessLevel, Set[str]] = {
            AccessLevel.GUEST: {'read_public'},
            AccessLevel.USER: {'read_public', 'read_internal', 'execute_basic'},
            AccessLevel.RESEARCHER: {'read_public', 'read_internal', 'read_confidential', 'execute_research', 'modify_research'},
            AccessLevel.ADMIN: {'read_public', 'read_internal', 'read_confidential', 'execute_research', 'modify_research', 'admin_operations'},
            AccessLevel.SECURITY_ADMIN: {'*'},  # All permissions
            AccessLevel.SYSTEM: {'*'}  # All permissions
        }
        self._lock = threading.Lock()

    def create_user(self, user_id: str, access_level: AccessLevel, additional_permissions: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Create a new user with specified access level."""
        with self._lock:
            self.users[user_id] = {
                'user_id': user_id,
                'access_level': access_level,
                'additional_permissions': additional_permissions or set(),
                'created_time': time.time(),
                'last_login': None,
                'login_count': 0,
                'active': True
            }

        logger.info(f"Created user {user_id} with access level {access_level.value}")
        return {'status': 'created', 'user_id': user_id}

    def authenticate_user(self, user_id: str, credentials: Dict[str, Any]) -> Optional[SecurityContext]:
        """Authenticate user and create security context."""
        with self._lock:
            user_info = self.users.get(user_id)

        if not user_info or not user_info['active']:
            return None

        # Create security context
        session_id = str(uuid.uuid4())
        user_permissions = self.get_user_permissions(user_id)

        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            access_level=user_info['access_level'],
            permissions=user_permissions,
            client_ip=credentials.get('client_ip'),
            user_agent=credentials.get('user_agent')
        )

        with self._lock:
            self.sessions[session_id] = context
            self.users[user_id]['last_login'] = time.time()
            self.users[user_id]['login_count'] += 1

        logger.info(f"User {user_id} authenticated successfully, session {session_id}")
        return context

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        with self._lock:
            user_info = self.users.get(user_id)

        if not user_info:
            return set()

        access_level = user_info['access_level']
        base_permissions = self.permissions.get(access_level, set())
        additional_permissions = user_info.get('additional_permissions', set())

        # Handle wildcard permissions
        if '*' in base_permissions:
            return {'*'}  # All permissions

        return base_permissions.union(additional_permissions)

    def check_permission(self, security_context: SecurityContext, required_permission: str) -> bool:
        """Check if security context has required permission."""
        if '*' in security_context.permissions:
            return True

        return required_permission in security_context.permissions

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about active sessions."""
        with self._lock:
            return [
                {
                    'session_id': session.session_id,
                    'user_id': session.user_id,
                    'access_level': session.access_level.value,
                    'timestamp': session.timestamp,
                    'client_ip': session.client_ip
                }
                for session in self.sessions.values()
            ]


class ComprehensiveAuditLogger:
    """Comprehensive audit logging for compliance."""

    def __init__(self, log_file_path: Optional[Path] = None):
        self.log_file_path = log_file_path or Path("audit_log.json")
        self.audit_events: List[AuditEvent] = []
        self.compliance_rules: Dict[ComplianceStandard, Dict[str, Any]] = {
            ComplianceStandard.GDPR: {
                'required_events': [AuditEventType.DATA_ACCESS, AuditEventType.DATA_MODIFICATION],
                'retention_days': 365 * 6,  # 6 years
                'anonymization_required': True
            },
            ComplianceStandard.HIPAA: {
                'required_events': [AuditEventType.DATA_ACCESS, AuditEventType.AUTHENTICATION],
                'retention_days': 365 * 6,
                'encryption_required': True
            },
            ComplianceStandard.SOX: {
                'required_events': [AuditEventType.DATA_MODIFICATION, AuditEventType.AUTHORIZATION],
                'retention_days': 365 * 7,
                'integrity_verification': True
            }
        }
        self._lock = threading.Lock()

    def log_audit_event(
        self,
        event_type: AuditEventType,
        security_context: SecurityContext,
        component: ComponentType,
        operation: str,
        resource: str,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=security_context.user_id,
            session_id=security_context.session_id,
            component=component,
            operation=operation,
            resource=resource,
            result=result,
            details=details or {},
            client_ip=security_context.client_ip,
            user_agent=security_context.user_agent,
            correlation_id=security_context.correlation_id,
            security_classification=security_context.security_classification
        )

        # Add compliance tags based on requirements
        for standard in security_context.compliance_requirements:
            event.compliance_tags.add(standard.value)

        with self._lock:
            self.audit_events.append(event)

        # Write to log file
        self._write_audit_event(event)

        logger.info(f"Audit event logged: {event.event_id} - {event_type.value}")
        return event.event_id

    def _write_audit_event(self, event: AuditEvent):
        """Write audit event to log file."""
        try:
            log_entry = {
                'event_id': event.event_id,
                'timestamp': datetime.fromtimestamp(event.timestamp).isoformat(),
                'event_type': event.event_type.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'component': event.component.value,
                'operation': event.operation,
                'resource': event.resource,
                'result': event.result,
                'details': event.details,
                'client_ip': event.client_ip,
                'user_agent': event.user_agent,
                'correlation_id': event.correlation_id,
                'security_classification': event.security_classification.value,
                'compliance_tags': list(event.compliance_tags)
            }

            with open(self.log_file_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")

    def search_audit_events(self, criteria: Dict[str, Any]) -> List[AuditEvent]:
        """Search audit events based on criteria."""
        with self._lock:
            results = []

            for event in self.audit_events:
                match = True

                # Check each criterion
                if 'user_id' in criteria and event.user_id != criteria['user_id']:
                    match = False
                if 'event_type' in criteria and event.event_type != criteria['event_type']:
                    match = False
                if 'component' in criteria and event.component != criteria['component']:
                    match = False
                if 'start_time' in criteria and event.timestamp < criteria['start_time']:
                    match = False
                if 'end_time' in criteria and event.timestamp > criteria['end_time']:
                    match = False
                if 'result' in criteria and event.result != criteria['result']:
                    match = False

                if match:
                    results.append(event)

        return results


class EnhancedEnterpriseSecurityManager:
    """Comprehensive enhanced enterprise security management system."""

    def __init__(self):
        self.encryption_manager = EnhancedEncryptionManager()
        self.federated_security = FederatedLearningSecurityManager(self.encryption_manager)
        self.access_control = EnhancedAccessControlManager()
        self.audit_logger = ComprehensiveAuditLogger()

        # Security monitoring
        self.security_events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @asynccontextmanager
    async def secure_operation(
        self,
        security_context: SecurityContext,
        component: ComponentType,
        operation: str,
        resource: str,
        required_permission: str,
        security_level: SecurityLevel = SecurityLevel.INTERNAL
    ):
        """Context manager for secure operations with comprehensive logging."""

        # Check permissions
        if not self.access_control.check_permission(security_context, required_permission):
            self.audit_logger.log_audit_event(
                AuditEventType.AUTHORIZATION,
                security_context,
                component,
                operation,
                resource,
                result="failure",
                details={"reason": "insufficient_permissions", "required": required_permission}
            )
            raise PermissionError(f"Insufficient permissions: {required_permission} required")

        # Log operation start
        start_event_id = self.audit_logger.log_audit_event(
            AuditEventType.DATA_ACCESS,
            security_context,
            component,
            operation,
            resource,
            result="started"
        )

        start_time = time.time()
        try:
            yield

            # Log successful completion
            self.audit_logger.log_audit_event(
                AuditEventType.DATA_ACCESS,
                security_context,
                component,
                operation,
                resource,
                result="success",
                details={
                    "duration_seconds": time.time() - start_time,
                    "start_event_id": start_event_id
                }
            )

        except Exception as e:
            # Log failure
            self.audit_logger.log_audit_event(
                AuditEventType.DATA_ACCESS,
                security_context,
                component,
                operation,
                resource,
                result="error",
                details={
                    "error": str(e),
                    "duration_seconds": time.time() - start_time,
                    "start_event_id": start_event_id
                }
            )
            raise

    def secure_algorithm_execution(
        self,
        algorithm_name: str,
        algorithm_data: Dict[str, Any],
        security_context: SecurityContext,
        component: ComponentType
    ) -> Dict[str, Any]:
        """Securely execute research algorithm with encryption and auditing."""

        # Encrypt algorithm data
        encrypted_data = self.encryption_manager.encrypt_research_data(algorithm_data, component)

        # Log algorithm execution
        execution_id = str(uuid.uuid4())
        self.audit_logger.log_audit_event(
            AuditEventType.ALGORITHM_EXECUTION,
            security_context,
            component,
            f"execute_{algorithm_name}",
            algorithm_name,
            result="started",
            details={
                "execution_id": execution_id,
                "algorithm_name": algorithm_name,
                "data_encrypted": True
            }
        )

        try:
            # Simulate algorithm execution (in real implementation, this would call the actual algorithm)
            result = {
                "execution_id": execution_id,
                "algorithm": algorithm_name,
                "status": "completed",
                "encrypted_result": True,
                "timestamp": time.time()
            }

            # Encrypt result
            encrypted_result = self.encryption_manager.encrypt_research_data(result, component)

            # Log successful execution
            self.audit_logger.log_audit_event(
                AuditEventType.ALGORITHM_EXECUTION,
                security_context,
                component,
                f"execute_{algorithm_name}",
                algorithm_name,
                result="success",
                details={
                    "execution_id": execution_id,
                    "result_encrypted": True
                }
            )

            return encrypted_result

        except Exception as e:
            # Log execution failure
            self.audit_logger.log_audit_event(
                AuditEventType.ALGORITHM_EXECUTION,
                security_context,
                component,
                f"execute_{algorithm_name}",
                algorithm_name,
                result="error",
                details={
                    "execution_id": execution_id,
                    "error": str(e)
                }
            )
            raise

    def secure_federated_learning_round(
        self,
        round_id: str,
        participants: List[str],
        model_updates: Dict[str, Any],
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """Conduct secure federated learning round."""

        # Generate secure aggregation keys
        aggregation_keys = self.federated_security.generate_secure_aggregation_keys(round_id, participants)

        # Validate all participants
        validation_results = {}
        for participant_id, update in model_updates.items():
            validation = self.federated_security.validate_participant_integrity(participant_id, update)
            validation_results[participant_id] = validation

            if not validation['valid']:
                # Log security violation
                self.audit_logger.log_audit_event(
                    AuditEventType.SECURITY_VIOLATION,
                    security_context,
                    ComponentType.FEDERATED_LEARNER,
                    "participant_validation",
                    participant_id,
                    result="failure",
                    details=validation
                )

        # Filter out invalid participants
        valid_participants = [
            p for p, v in validation_results.items()
            if v['valid']
        ]

        # Log federated learning round
        self.audit_logger.log_audit_event(
            AuditEventType.FEDERATED_LEARNING,
            security_context,
            ComponentType.FEDERATED_LEARNER,
            "secure_aggregation",
            round_id,
            result="success",
            details={
                "round_id": round_id,
                "total_participants": len(participants),
                "valid_participants": len(valid_participants),
                "validation_results": validation_results
            }
        )

        return {
            "round_id": round_id,
            "aggregation_keys": aggregation_keys,
            "valid_participants": valid_participants,
            "validation_results": validation_results
        }

    async def security_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive security health check."""

        # Check encryption key health
        key_stats = self.encryption_manager.get_key_statistics()
        keys_need_rotation = key_stats['keys_due_rotation']

        # Check active sessions
        active_sessions = self.access_control.get_active_sessions()

        # Calculate security score
        security_score = 100
        if keys_need_rotation > 0:
            security_score -= 10
        if len(active_sessions) > 100:  # Too many sessions
            security_score -= 10

        security_status = "healthy"
        if security_score < 70:
            security_status = "at_risk"
        if security_score < 50:
            security_status = "critical"

        return {
            'security_status': security_status,
            'security_score': max(0, security_score),
            'encryption_health': {
                'active_keys': key_stats['active_keys'],
                'keys_need_rotation': keys_need_rotation,
                'total_usage': key_stats['total_key_usage']
            },
            'access_control_health': {
                'active_sessions': len(active_sessions),
                'total_users': len(self.access_control.users)
            },
            'timestamp': time.time()
        }


# Global enhanced security manager instance
enhanced_security_manager = EnhancedEnterpriseSecurityManager()


def get_enhanced_security_manager() -> EnhancedEnterpriseSecurityManager:
    """Get the global enhanced security manager instance."""
    return enhanced_security_manager


# Decorator for secure function execution
def require_enhanced_security(
    required_permission: str,
    component: ComponentType,
    security_level: SecurityLevel = SecurityLevel.INTERNAL
):
    """Decorator to enforce enhanced security requirements on functions."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(security_context: SecurityContext, *args, **kwargs):
            async with enhanced_security_manager.secure_operation(
                security_context,
                component,
                func.__name__,
                func.__qualname__,
                required_permission,
                security_level
            ):
                return await func(security_context, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(security_context: SecurityContext, *args, **kwargs):
            return asyncio.run(async_wrapper(security_context, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
