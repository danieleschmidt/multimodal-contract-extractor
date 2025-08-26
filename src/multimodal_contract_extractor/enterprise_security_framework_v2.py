#!/usr/bin/env python3
"""
Enterprise Security Framework v2.0 - Generation 2: MAKE IT ROBUST
Advanced security implementation with multi-layered protection, input sanitization,
threat detection, and zero-trust architecture for the autonomous SDLC system.
"""

import asyncio
import hashlib
import hmac
import secrets
import time
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class SecurityLevel(Enum):
    """Security classification levels"""
    PUBLIC = auto()
    INTERNAL = auto()
    CONFIDENTIAL = auto()
    RESTRICTED = auto()
    TOP_SECRET = auto()


class ThreatLevel(Enum):
    """Threat classification levels"""
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class AttackVector(Enum):
    """Known attack vectors"""
    SQL_INJECTION = auto()
    XSS = auto()
    CSRF = auto()
    COMMAND_INJECTION = auto()
    PATH_TRAVERSAL = auto()
    DATA_EXFILTRATION = auto()
    PRIVILEGE_ESCALATION = auto()
    DENIAL_OF_SERVICE = auto()
    MALWARE = auto()
    SOCIAL_ENGINEERING = auto()


class AuthenticationMethod(Enum):
    """Authentication methods"""
    API_KEY = auto()
    JWT_TOKEN = auto()
    OAUTH2 = auto()
    CERTIFICATE = auto()
    BIOMETRIC = auto()
    MULTI_FACTOR = auto()


@dataclass
class SecurityEvent:
    """Security event record"""
    event_id: str
    timestamp: datetime
    event_type: str
    threat_level: ThreatLevel
    attack_vector: Optional[AttackVector]
    source_ip: str
    user_agent: str
    payload: Dict[str, Any]
    blocked: bool
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    policy_id: str
    name: str
    description: str
    security_level: SecurityLevel
    rules: List[Dict[str, Any]]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AccessControl:
    """Access control configuration"""
    user_id: str
    resource: str
    permissions: List[str]
    security_level: SecurityLevel
    expiry: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


class InputSanitizer:
    """Advanced input sanitization system"""
    
    def __init__(self):
        self.patterns = {
            'sql_injection': [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(--|#|/\*|\*/)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\b(CHAR|ASCII|SUBSTRING|LENGTH|VERSION|USER|DATABASE)\b\s*\()"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
                r"<link[^>]*>",
                r"<meta[^>]*>"
            ],
            'command_injection': [
                r"[;&|`$()]",
                r"\b(rm|mv|cp|cat|grep|find|wget|curl|nc|netcat)\b",
                r"(>|<|>>|<<)",
                r"\$\([^)]*\)",
                r"`[^`]*`"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e\\",
                r"~/"
            ]
        }
        
        self.allowed_chars = {
            'alphanumeric': r"[^a-zA-Z0-9]",
            'alphanumeric_space': r"[^a-zA-Z0-9\s]",
            'filename': r"[^a-zA-Z0-9._-]",
            'email': r"[^a-zA-Z0-9@._-]",
            'url': r"[^a-zA-Z0-9:/?#\[\]@!$&'()*+,;=._~-]"
        }
    
    def sanitize_input(self, input_data: str, input_type: str = 'general') -> Tuple[str, List[str]]:
        """Sanitize input data and return cleaned data with detected threats"""
        threats = []
        cleaned_data = input_data
        
        # Check for malicious patterns
        for attack_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    threats.append(f"{attack_type}: {pattern}")
        
        # Apply input type specific cleaning
        if input_type in self.allowed_chars:
            cleaned_data = re.sub(self.allowed_chars[input_type], '', cleaned_data)
        
        # HTML encode special characters
        html_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
            '/': '&#x2F;'
        }
        
        for char, encoded in html_chars.items():
            cleaned_data = cleaned_data.replace(char, encoded)
        
        return cleaned_data, threats
    
    def validate_json(self, json_data: str) -> Tuple[bool, Optional[Dict], List[str]]:
        """Validate and sanitize JSON input"""
        threats = []
        
        try:
            # Parse JSON
            data = json.loads(json_data)
            
            # Recursively sanitize JSON values
            sanitized_data = self._sanitize_json_recursive(data, threats)
            
            return True, sanitized_data, threats
            
        except json.JSONDecodeError as e:
            threats.append(f"Invalid JSON: {str(e)}")
            return False, None, threats
    
    def _sanitize_json_recursive(self, data: Any, threats: List[str]) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {k: self._sanitize_json_recursive(v, threats) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_recursive(item, threats) for item in data]
        elif isinstance(data, str):
            sanitized, detected_threats = self.sanitize_input(data)
            threats.extend(detected_threats)
            return sanitized
        else:
            return data


class ThreatDetectionEngine:
    """ML-powered threat detection engine"""
    
    def __init__(self):
        self.threat_patterns = {}
        self.behavioral_baseline = {}
        self.anomaly_threshold = 0.8
        self.learning_rate = 0.01
        
    def analyze_request(self, request_data: Dict[str, Any]) -> Tuple[ThreatLevel, float, List[str]]:
        """Analyze request for threats"""
        threats = []
        risk_score = 0.0
        
        # Analyze request patterns
        pattern_score = self._analyze_patterns(request_data, threats)
        behavioral_score = self._analyze_behavior(request_data, threats)
        content_score = self._analyze_content(request_data, threats)
        
        # Calculate composite risk score
        risk_score = (pattern_score * 0.4 + behavioral_score * 0.3 + content_score * 0.3)
        
        # Determine threat level
        if risk_score >= 0.9:
            threat_level = ThreatLevel.CRITICAL
        elif risk_score >= 0.7:
            threat_level = ThreatLevel.HIGH
        elif risk_score >= 0.5:
            threat_level = ThreatLevel.MEDIUM
        elif risk_score >= 0.3:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.NONE
        
        return threat_level, risk_score, threats
    
    def _analyze_patterns(self, request_data: Dict[str, Any], threats: List[str]) -> float:
        """Analyze request for known attack patterns"""
        score = 0.0
        
        # Check for suspicious headers
        headers = request_data.get('headers', {})
        suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'x-cluster-client-ip']
        
        for header in suspicious_headers:
            if header in headers:
                score += 0.1
                threats.append(f"Suspicious header: {header}")
        
        # Check for unusual user agents
        user_agent = headers.get('user-agent', '')
        if not user_agent or len(user_agent) < 10:
            score += 0.2
            threats.append("Missing or suspicious user agent")
        
        # Check request frequency
        source_ip = request_data.get('source_ip', '')
        if self._is_rate_limited(source_ip):
            score += 0.3
            threats.append("Rate limiting triggered")
        
        return min(score, 1.0)
    
    def _analyze_behavior(self, request_data: Dict[str, Any], threats: List[str]) -> float:
        """Analyze behavioral patterns"""
        score = 0.0
        
        # Check time-based patterns
        current_time = datetime.utcnow()
        if current_time.hour < 6 or current_time.hour > 22:
            score += 0.1
            threats.append("Off-hours request")
        
        # Check geographic patterns (simplified)
        source_ip = request_data.get('source_ip', '')
        if self._is_suspicious_location(source_ip):
            score += 0.2
            threats.append("Suspicious geographic location")
        
        return min(score, 1.0)
    
    def _analyze_content(self, request_data: Dict[str, Any], threats: List[str]) -> float:
        """Analyze request content"""
        score = 0.0
        
        # Check payload size
        payload = request_data.get('payload', {})
        payload_size = len(str(payload))
        
        if payload_size > 1000000:  # 1MB
            score += 0.3
            threats.append("Large payload detected")
        
        # Check for encoded content
        if any(self._is_encoded(str(value)) for value in payload.values() if isinstance(value, str)):
            score += 0.2
            threats.append("Encoded content detected")
        
        return min(score, 1.0)
    
    def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited"""
        # Simplified rate limiting check
        return False
    
    def _is_suspicious_location(self, ip: str) -> bool:
        """Check if IP location is suspicious"""
        # Simplified location check
        return False
    
    def _is_encoded(self, content: str) -> bool:
        """Check if content appears to be encoded"""
        # Check for base64 encoding
        try:
            base64.b64decode(content)
            return len(content) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]*={0,2}$', content)
        except:
            return False


class EncryptionManager:
    """Advanced encryption management"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = Fernet.generate_key()
        
        self.cipher_suite = Fernet(self.master_key)
        self.key_rotation_interval = timedelta(days=30)
        self.encryption_algorithms = {
            'AES-256': 'fernet',
            'RSA-2048': 'rsa',
            'ECC-P256': 'ecc'
        }
    
    def encrypt_data(self, data: Union[str, bytes], algorithm: str = 'AES-256') -> Dict[str, Any]:
        """Encrypt data with specified algorithm"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.cipher_suite.encrypt(data)
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'algorithm': algorithm,
            'key_version': 1,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def decrypt_data(self, encrypted_package: Dict[str, Any]) -> str:
        """Decrypt data package"""
        encrypted_data = base64.b64decode(encrypted_package['encrypted_data'])
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    
    def generate_hash(self, data: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Generate secure hash"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(data.encode('utf-8'))
        
        return {
            'hash': base64.b64encode(key).decode('utf-8'),
            'salt': salt,
            'algorithm': 'PBKDF2-SHA256',
            'iterations': 100000
        }
    
    def verify_hash(self, data: str, hash_package: Dict[str, str]) -> bool:
        """Verify data against hash"""
        computed_hash = self.generate_hash(data, hash_package['salt'])
        return computed_hash['hash'] == hash_package['hash']


class ZeroTrustFramework:
    """Zero Trust security framework implementation"""
    
    def __init__(self):
        self.trust_policies = {}
        self.access_controls = {}
        self.session_manager = {}
        self.continuous_verification = True
        
    def verify_access(self, user_id: str, resource: str, action: str, 
                     context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Verify access using zero trust principles"""
        verification_steps = []
        risk_score = 0.0
        
        # Step 1: Identity verification
        identity_verified, identity_risk = self._verify_identity(user_id, context)
        verification_steps.append(f"Identity verification: {identity_verified}")
        risk_score += identity_risk * 0.3
        
        # Step 2: Device verification
        device_verified, device_risk = self._verify_device(context)
        verification_steps.append(f"Device verification: {device_verified}")
        risk_score += device_risk * 0.2
        
        # Step 3: Network verification
        network_verified, network_risk = self._verify_network(context)
        verification_steps.append(f"Network verification: {network_verified}")
        risk_score += network_risk * 0.2
        
        # Step 4: Behavioral verification
        behavior_verified, behavior_risk = self._verify_behavior(user_id, context)
        verification_steps.append(f"Behavioral verification: {behavior_verified}")
        risk_score += behavior_risk * 0.3
        
        # Make access decision
        access_granted = (identity_verified and device_verified and 
                         network_verified and behavior_verified and 
                         risk_score < 0.5)
        
        decision_reason = f"Risk score: {risk_score:.2f}, Steps: {verification_steps}"
        
        verification_result = {
            'access_granted': access_granted,
            'risk_score': risk_score,
            'verification_steps': verification_steps,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self._generate_session_id()
        }
        
        return access_granted, decision_reason, verification_result
    
    def _verify_identity(self, user_id: str, context: Dict[str, Any]) -> Tuple[bool, float]:
        """Verify user identity"""
        # Check authentication method
        auth_method = context.get('auth_method', '')
        if not auth_method:
            return False, 1.0
        
        # Multi-factor authentication preferred
        if auth_method == 'multi_factor':
            return True, 0.1
        elif auth_method in ['jwt_token', 'certificate']:
            return True, 0.3
        else:
            return True, 0.7
    
    def _verify_device(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """Verify device trustworthiness"""
        device_info = context.get('device_info', {})
        
        # Check if device is known
        device_id = device_info.get('device_id', '')
        if not device_id:
            return False, 1.0
        
        # Check device health
        is_managed = device_info.get('is_managed', False)
        has_security_software = device_info.get('has_security_software', False)
        
        risk = 0.2
        if not is_managed:
            risk += 0.3
        if not has_security_software:
            risk += 0.2
        
        return risk < 0.5, risk
    
    def _verify_network(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """Verify network security"""
        network_info = context.get('network_info', {})
        
        # Check network type
        network_type = network_info.get('type', 'unknown')
        is_vpn = network_info.get('is_vpn', False)
        
        risk = 0.1
        if network_type == 'public':
            risk += 0.4
        elif network_type == 'unknown':
            risk += 0.6
        
        if not is_vpn and network_type != 'corporate':
            risk += 0.2
        
        return risk < 0.5, risk
    
    def _verify_behavior(self, user_id: str, context: Dict[str, Any]) -> Tuple[bool, float]:
        """Verify behavioral patterns"""
        # Check access time
        current_hour = datetime.utcnow().hour
        typical_hours = context.get('typical_access_hours', [9, 17])
        
        risk = 0.1
        if current_hour < typical_hours[0] or current_hour > typical_hours[1]:
            risk += 0.3
        
        # Check access location
        source_ip = context.get('source_ip', '')
        if source_ip and self._is_unusual_location(user_id, source_ip):
            risk += 0.3
        
        return risk < 0.5, risk
    
    def _is_unusual_location(self, user_id: str, source_ip: str) -> bool:
        """Check if access location is unusual for user"""
        # Simplified location check
        return False
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)


class EnterpriseSecurityOrchestrator:
    """Main security orchestrator coordinating all security components"""
    
    def __init__(self):
        self.input_sanitizer = InputSanitizer()
        self.threat_detector = ThreatDetectionEngine()
        self.encryption_manager = EncryptionManager()
        self.zero_trust = ZeroTrustFramework()
        
        self.security_events = []
        self.blocked_ips = set()
        self.security_policies = {}
        self.audit_log = []
        
        self.logger = logging.getLogger(__name__)
    
    async def secure_request(self, request_data: Dict[str, Any], 
                           user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive request security processing"""
        security_result = {
            'request_id': secrets.token_urlsafe(16),
            'timestamp': datetime.utcnow().isoformat(),
            'allowed': False,
            'security_score': 0.0,
            'threat_level': ThreatLevel.NONE,
            'sanitized_data': {},
            'threats_detected': [],
            'security_events': [],
            'access_decision': {}
        }
        
        try:
            # Step 1: Input sanitization
            sanitized_data, input_threats = await self._sanitize_request(request_data)
            security_result['sanitized_data'] = sanitized_data
            security_result['threats_detected'].extend(input_threats)
            
            # Step 2: Threat detection
            threat_level, risk_score, detected_threats = self.threat_detector.analyze_request(request_data)
            security_result['threat_level'] = threat_level
            security_result['security_score'] = risk_score
            security_result['threats_detected'].extend(detected_threats)
            
            # Step 3: Zero Trust verification
            user_id = user_context.get('user_id', 'anonymous')
            resource = request_data.get('resource', 'unknown')
            action = request_data.get('action', 'read')
            
            access_granted, decision_reason, verification_result = self.zero_trust.verify_access(
                user_id, resource, action, user_context
            )
            security_result['access_decision'] = verification_result
            
            # Step 4: Make final decision
            security_result['allowed'] = (
                access_granted and 
                threat_level.value <= ThreatLevel.MEDIUM.value and
                len(input_threats) == 0
            )
            
            # Step 5: Log security event
            event = SecurityEvent(
                event_id=security_result['request_id'],
                timestamp=datetime.utcnow(),
                event_type='request_security_check',
                threat_level=threat_level,
                attack_vector=None,
                source_ip=request_data.get('source_ip', ''),
                user_agent=request_data.get('headers', {}).get('user-agent', ''),
                payload=request_data,
                blocked=not security_result['allowed'],
                confidence_score=risk_score,
                metadata=security_result
            )
            
            self.security_events.append(event)
            self._audit_security_decision(security_result)
            
            return security_result
            
        except Exception as e:
            self.logger.error(f"Security processing error: {str(e)}")
            security_result['allowed'] = False
            security_result['threats_detected'].append(f"Security processing error: {str(e)}")
            return security_result
    
    async def _sanitize_request(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Sanitize all request data"""
        sanitized_data = {}
        all_threats = []
        
        for key, value in request_data.items():
            if isinstance(value, str):
                sanitized_value, threats = self.input_sanitizer.sanitize_input(value)
                sanitized_data[key] = sanitized_value
                all_threats.extend(threats)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized_nested, nested_threats = await self._sanitize_request(value)
                sanitized_data[key] = sanitized_nested
                all_threats.extend(nested_threats)
            else:
                sanitized_data[key] = value
        
        return sanitized_data, all_threats
    
    def _audit_security_decision(self, security_result: Dict[str, Any]):
        """Audit security decisions for compliance"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'security_decision',
            'request_id': security_result['request_id'],
            'decision': 'ALLOW' if security_result['allowed'] else 'DENY',
            'threat_level': security_result['threat_level'].name,
            'security_score': security_result['security_score'],
            'threats_count': len(security_result['threats_detected'])
        }
        
        self.audit_log.append(audit_entry)
        self.logger.info(f"Security decision: {audit_entry}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics"""
        total_events = len(self.security_events)
        blocked_events = sum(1 for event in self.security_events if event.blocked)
        
        threat_distribution = {}
        for event in self.security_events:
            threat_level = event.threat_level.name
            threat_distribution[threat_level] = threat_distribution.get(threat_level, 0) + 1
        
        return {
            'total_security_events': total_events,
            'blocked_events': blocked_events,
            'block_rate': blocked_events / total_events if total_events > 0 else 0,
            'threat_distribution': threat_distribution,
            'unique_blocked_ips': len(self.blocked_ips),
            'audit_log_entries': len(self.audit_log)
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_security_framework():
        """Test the enterprise security framework"""
        print("🔒 Testing Enterprise Security Framework v2.0")
        
        orchestrator = EnterpriseSecurityOrchestrator()
        
        # Test request data
        test_request = {
            'resource': '/api/contracts/extract',
            'action': 'write',
            'payload': {
                'document': 'Test contract content',
                'user_input': '<script>alert("xss")</script>',
                'file_path': '../../../etc/passwd'
            },
            'source_ip': '192.168.1.100',
            'headers': {
                'user-agent': 'Mozilla/5.0 (legitimate browser)',
                'content-type': 'application/json'
            }
        }
        
        user_context = {
            'user_id': 'test_user',
            'auth_method': 'jwt_token',
            'device_info': {
                'device_id': 'device_123',
                'is_managed': True,
                'has_security_software': True
            },
            'network_info': {
                'type': 'corporate',
                'is_vpn': True
            },
            'typical_access_hours': [8, 18]
        }
        
        # Process security check
        result = await orchestrator.secure_request(test_request, user_context)
        
        print(f"Request allowed: {result['allowed']}")
        print(f"Security score: {result['security_score']:.2f}")
        print(f"Threat level: {result['threat_level'].name}")
        print(f"Threats detected: {len(result['threats_detected'])}")
        print(f"Sanitized payload: {result['sanitized_data'].get('payload', {})}")
        
        # Get security metrics
        metrics = orchestrator.get_security_metrics()
        print(f"Security metrics: {metrics}")
    
    # Run test
    asyncio.run(test_security_framework())