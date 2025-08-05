"""
Automated audit trail and compliance logging system.
Comprehensive audit logging for governance and regulatory compliance.
"""

import hashlib
import json
import logging
import os
import threading
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class AuditEventType(Enum):
    """Types of audit events."""
    ACCESS = "access"
    MODIFICATION = "modification"
    CREATION = "creation"
    DELETION = "deletion"
    EXECUTION = "execution"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    DATA_ACCESS = "data_access"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    SYSTEM = "system"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditOutcome(Enum):
    """Audit event outcomes."""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    timestamp: str
    event_type: AuditEventType
    actor: str  # User, system, or service performing the action
    action: str  # What action was performed
    resource: str  # What resource was affected
    outcome: AuditOutcome
    severity: AuditSeverity
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    compliance_tags: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['outcome'] = self.outcome.value
        data['severity'] = self.severity.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    def get_checksum(self) -> str:
        """Generate checksum for integrity verification."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


@dataclass
class AuditQuery:
    """Query parameters for audit log searches."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[AuditEventType]] = None
    actors: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    outcomes: Optional[List[AuditOutcome]] = None
    severities: Optional[List[AuditSeverity]] = None
    compliance_tags: Optional[List[str]] = None
    limit: int = 1000
    offset: int = 0


class AuditLogger:
    """Main audit logging system."""

    def __init__(self, storage_directory: str = "governance/audit_logs"):
        self.storage_path = Path(storage_directory)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # Configuration
        self.max_log_file_size = int(os.getenv('AUDIT_MAX_FILE_SIZE', '10485760'))  # 10MB
        self.max_log_files = int(os.getenv('AUDIT_MAX_FILES', '100'))
        self.retention_days = int(os.getenv('AUDIT_RETENTION_DAYS', '2555'))  # 7 years default
        self.enable_integrity_checks = os.getenv('AUDIT_INTEGRITY_CHECKS', 'true').lower() == 'true'

        # Current log file
        self.current_log_file = self._get_current_log_file()

        # Initialize integrity file if enabled
        if self.enable_integrity_checks:
            self.integrity_file = self.storage_path / "audit_integrity.json"
            self._initialize_integrity_tracking()

    def _get_current_log_file(self) -> Path:
        """Get the current log file path."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return self.storage_path / f"audit_{date_str}.jsonl"

    def _initialize_integrity_tracking(self) -> None:
        """Initialize integrity tracking system."""
        if not self.integrity_file.exists():
            with open(self.integrity_file, 'w') as f:
                json.dump({
                    'created': datetime.now(timezone.utc).isoformat(),
                    'files': {},
                    'last_verification': None
                }, f, indent=2)

    def log_event(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        resource: str,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        **kwargs
    ) -> str:
        """Log an audit event."""
        event_id = str(uuid.uuid4())

        audit_event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            severity=severity,
            **kwargs
        )

        self._write_event(audit_event)
        return event_id

    def _write_event(self, event: AuditEvent) -> None:
        """Write audit event to log file."""
        with self._lock:
            # Check if we need to rotate log file
            current_file = self._get_current_log_file()
            if current_file != self.current_log_file:
                self.current_log_file = current_file

            # Check file size and rotate if necessary
            if self.current_log_file.exists() and self.current_log_file.stat().st_size > self.max_log_file_size:
                self._rotate_log_files()

            # Write event
            try:
                with open(self.current_log_file, 'a', encoding='utf-8') as f:
                    f.write(event.to_json() + '\n')

                # Update integrity tracking
                if self.enable_integrity_checks:
                    self._update_integrity_tracking(event)

                self.logger.debug(f"Audit event logged: {event.event_id}")

            except Exception as e:
                self.logger.error(f"Failed to write audit event: {e}")
                # Try to log to emergency backup location
                self._write_to_emergency_log(event, str(e))

    def _rotate_log_files(self) -> None:
        """Rotate log files when they become too large."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_name = f"audit_{timestamp}.jsonl"
        rotated_path = self.storage_path / rotated_name

        try:
            self.current_log_file.rename(rotated_path)
            self.logger.info(f"Rotated audit log to {rotated_name}")

            # Clean up old files if we exceed the limit
            self._cleanup_old_files()

        except Exception as e:
            self.logger.error(f"Failed to rotate audit log: {e}")

    def _cleanup_old_files(self) -> None:
        """Clean up old audit log files."""
        try:
            # Get all audit log files
            audit_files = list(self.storage_path.glob("audit_*.jsonl"))
            audit_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove files beyond retention limit
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            files_to_remove = []
            for audit_file in audit_files:
                file_time = datetime.fromtimestamp(audit_file.stat().st_mtime)
                if file_time < cutoff_date or len(audit_files) > self.max_log_files:
                    files_to_remove.append(audit_file)

            for file_to_remove in files_to_remove:
                file_to_remove.unlink()
                self.logger.info(f"Removed old audit log: {file_to_remove.name}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit files: {e}")

    def _update_integrity_tracking(self, event: AuditEvent) -> None:
        """Update integrity tracking information."""
        try:
            if not self.integrity_file.exists():
                self._initialize_integrity_tracking()

            with open(self.integrity_file) as f:
                integrity_data = json.load(f)

            file_name = self.current_log_file.name
            if file_name not in integrity_data['files']:
                integrity_data['files'][file_name] = {
                    'created': datetime.now(timezone.utc).isoformat(),
                    'event_count': 0,
                    'last_checksum': None,
                    'checksums': []
                }

            file_info = integrity_data['files'][file_name]
            file_info['event_count'] += 1
            file_info['last_modified'] = datetime.now(timezone.utc).isoformat()

            # Store event checksum
            event_checksum = event.get_checksum()
            file_info['checksums'].append({
                'event_id': event.event_id,
                'checksum': event_checksum,
                'timestamp': event.timestamp
            })

            # Keep only recent checksums to avoid file growth
            if len(file_info['checksums']) > 1000:
                file_info['checksums'] = file_info['checksums'][-1000:]

            with open(self.integrity_file, 'w') as f:
                json.dump(integrity_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to update integrity tracking: {e}")

    def _write_to_emergency_log(self, event: AuditEvent, error: str) -> None:
        """Write to emergency backup log when main logging fails."""
        emergency_file = self.storage_path / "audit_emergency.jsonl"

        try:
            emergency_event = {
                'original_event': event.to_dict(),
                'error': error,
                'emergency_timestamp': datetime.now(timezone.utc).isoformat()
            }

            with open(emergency_file, 'a') as f:
                f.write(json.dumps(emergency_event) + '\n')

        except Exception as e:
            # Last resort - log to system logger
            self.logger.critical(f"Emergency audit logging failed: {e}")

    def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events based on criteria."""
        events = []

        try:
            # Get all audit log files
            audit_files = list(self.storage_path.glob("audit_*.jsonl"))
            audit_files.sort(key=lambda x: x.name, reverse=True)

            events_collected = 0

            for audit_file in audit_files:
                if events_collected >= query.limit:
                    break

                try:
                    with open(audit_file) as f:
                        for line_num, line in enumerate(f):
                            if line_num < query.offset:
                                continue

                            if events_collected >= query.limit:
                                break

                            try:
                                event_data = json.loads(line.strip())
                                event = self._dict_to_audit_event(event_data)

                                if self._matches_query(event, query):
                                    events.append(event)
                                    events_collected += 1

                            except json.JSONDecodeError:
                                self.logger.warning(f"Invalid JSON in {audit_file}:{line_num}")
                                continue

                except Exception as e:
                    self.logger.error(f"Failed to read audit file {audit_file}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to query audit events: {e}")

        return events

    def _dict_to_audit_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Convert dictionary to AuditEvent object."""
        return AuditEvent(
            event_id=data['event_id'],
            timestamp=data['timestamp'],
            event_type=AuditEventType(data['event_type']),
            actor=data['actor'],
            action=data['action'],
            resource=data['resource'],
            outcome=AuditOutcome(data['outcome']),
            severity=AuditSeverity(data['severity']),
            source_ip=data.get('source_ip'),
            user_agent=data.get('user_agent'),
            session_id=data.get('session_id'),
            correlation_id=data.get('correlation_id'),
            details=data.get('details'),
            before_state=data.get('before_state'),
            after_state=data.get('after_state'),
            compliance_tags=data.get('compliance_tags')
        )

    def _matches_query(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check if event matches query criteria."""
        # Time range check
        if query.start_time or query.end_time:
            event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))

            if query.start_time and event_time < query.start_time:
                return False
            if query.end_time and event_time > query.end_time:
                return False

        # Event type check
        if query.event_types and event.event_type not in query.event_types:
            return False

        # Actor check
        if query.actors and event.actor not in query.actors:
            return False

        # Resource check
        if query.resources and event.resource not in query.resources:
            return False

        # Outcome check
        if query.outcomes and event.outcome not in query.outcomes:
            return False

        # Severity check
        if query.severities and event.severity not in query.severities:
            return False

        # Compliance tags check
        if query.compliance_tags and event.compliance_tags:
            if not any(tag in event.compliance_tags for tag in query.compliance_tags):
                return False

        return True

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of audit logs."""
        if not self.enable_integrity_checks:
            return {'status': 'disabled', 'message': 'Integrity checking is disabled'}

        verification_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'success',
            'files_verified': 0,
            'files_failed': 0,
            'issues': []
        }

        try:
            if not self.integrity_file.exists():
                verification_results['status'] = 'error'
                verification_results['issues'].append('Integrity tracking file not found')
                return verification_results

            with open(self.integrity_file) as f:
                integrity_data = json.load(f)

            for file_name, file_info in integrity_data['files'].items():
                file_path = self.storage_path / file_name

                if not file_path.exists():
                    verification_results['issues'].append(f'Audit file missing: {file_name}')
                    verification_results['files_failed'] += 1
                    continue

                # Verify event count and checksums
                try:
                    with open(file_path) as f:
                        actual_events = [json.loads(line.strip()) for line in f if line.strip()]

                    expected_count = file_info['event_count']
                    actual_count = len(actual_events)

                    if actual_count != expected_count:
                        verification_results['issues'].append(
                            f'Event count mismatch in {file_name}: expected {expected_count}, found {actual_count}'
                        )
                        verification_results['files_failed'] += 1
                        continue

                    # Verify checksums for recent events
                    stored_checksums = {cs['event_id']: cs['checksum'] for cs in file_info.get('checksums', [])}

                    for event_data in actual_events[-100:]:  # Check last 100 events
                        event_id = event_data['event_id']
                        if event_id in stored_checksums:
                            expected_checksum = stored_checksums[event_id]
                            actual_checksum = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

                            if actual_checksum != expected_checksum:
                                verification_results['issues'].append(
                                    f'Checksum mismatch for event {event_id} in {file_name}'
                                )
                                verification_results['files_failed'] += 1
                                break
                    else:
                        verification_results['files_verified'] += 1

                except Exception as e:
                    verification_results['issues'].append(f'Failed to verify {file_name}: {str(e)}')
                    verification_results['files_failed'] += 1

            # Update verification timestamp
            integrity_data['last_verification'] = verification_results['timestamp']
            with open(self.integrity_file, 'w') as f:
                json.dump(integrity_data, f, indent=2)

        except Exception as e:
            verification_results['status'] = 'error'
            verification_results['issues'].append(f'Integrity verification failed: {str(e)}')

        if verification_results['files_failed'] > 0:
            verification_results['status'] = 'failed'

        return verification_results

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        compliance_framework: str = "general"
    ) -> Dict[str, Any]:
        """Generate compliance report for audit activities."""
        query = AuditQuery(
            start_time=start_date,
            end_time=end_date,
            limit=10000  # High limit for comprehensive report
        )

        events = self.query_events(query)

        # Analyze events
        report = {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'compliance_framework': compliance_framework,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_events': len(events),
            'summary': {
                'by_type': defaultdict(int),
                'by_severity': defaultdict(int),
                'by_outcome': defaultdict(int),
                'by_actor': defaultdict(int)
            },
            'security_events': [],
            'failed_events': [],
            'high_risk_activities': [],
            'recommendations': []
        }

        # Analyze events
        for event in events:
            report['summary']['by_type'][event.event_type.value] += 1
            report['summary']['by_severity'][event.severity.value] += 1
            report['summary']['by_outcome'][event.outcome.value] += 1
            report['summary']['by_actor'][event.actor] += 1

            # Collect security events
            if event.event_type == AuditEventType.SECURITY:
                report['security_events'].append(event.to_dict())

            # Collect failed events
            if event.outcome in [AuditOutcome.FAILURE, AuditOutcome.ERROR]:
                report['failed_events'].append(event.to_dict())

            # Collect high-risk activities
            if event.severity == AuditSeverity.CRITICAL:
                report['high_risk_activities'].append(event.to_dict())

        # Generate recommendations
        report['recommendations'] = self._generate_compliance_recommendations(report)

        return report

    def _generate_compliance_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations based on audit analysis."""
        recommendations = []

        # Check for high failure rates
        total_events = report['total_events']
        failed_events = len(report['failed_events'])

        if total_events > 0:
            failure_rate = (failed_events / total_events) * 100
            if failure_rate > 5:
                recommendations.append(
                    f"High failure rate detected ({failure_rate:.1f}%). "
                    "Review system reliability and error handling procedures."
                )

        # Check for security events
        if len(report['security_events']) > 0:
            recommendations.append(
                "Security events detected. Review security incident response procedures."
            )

        # Check for high-risk activities
        if len(report['high_risk_activities']) > 0:
            recommendations.append(
                "Critical severity events detected. Ensure proper approval workflows are in place."
            )

        # Check for actor diversity
        unique_actors = len(report['summary']['by_actor'])
        if unique_actors < 2:
            recommendations.append(
                "Limited number of system actors. Consider implementing proper role separation."
            )

        if not recommendations:
            recommendations.append("No significant compliance issues detected in this reporting period.")

        return recommendations


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger()

    return _audit_logger


def audit_log(
    event_type: AuditEventType,
    actor: str,
    action: str,
    resource: str,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    **kwargs
) -> str:
    """Convenience function for logging audit events."""
    return get_audit_logger().log_event(event_type, actor, action, resource, outcome, **kwargs)


# Decorator for automatic audit logging
def audit_trail(
    event_type: AuditEventType,
    action: str,
    resource_from_args: Optional[Union[int, str, Callable]] = None,
    actor: str = "system"
):
    """Decorator for automatic audit trail logging."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Determine resource
            resource = f"{func.__module__}.{func.__name__}"
            if resource_from_args is not None:
                if isinstance(resource_from_args, int) and len(args) > resource_from_args:
                    resource = str(args[resource_from_args])
                elif isinstance(resource_from_args, str) and resource_from_args in kwargs:
                    resource = str(kwargs[resource_from_args])
                elif callable(resource_from_args):
                    resource = resource_from_args(*args, **kwargs)

            start_time = datetime.now()
            outcome = AuditOutcome.SUCCESS
            details = {}

            try:
                result = func(*args, **kwargs)
                details['execution_time'] = (datetime.now() - start_time).total_seconds()
                return result
            except Exception as e:
                outcome = AuditOutcome.ERROR
                details['error'] = str(e)
                details['execution_time'] = (datetime.now() - start_time).total_seconds()
                raise
            finally:
                audit_log(
                    event_type=event_type,
                    actor=actor,
                    action=action,
                    resource=resource,
                    outcome=outcome,
                    details=details
                )

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize audit logger
    audit_logger = get_audit_logger()

    # Log some example events
    audit_logger.log_event(
        event_type=AuditEventType.ACCESS,
        actor="user123",
        action="login",
        resource="/auth/login",
        outcome=AuditOutcome.SUCCESS,
        source_ip="192.168.1.100",
        details={"method": "password"}
    )

    audit_logger.log_event(
        event_type=AuditEventType.MODIFICATION,
        actor="admin",
        action="update_config",
        resource="/config/database",
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.HIGH,
        before_state={"timeout": 30},
        after_state={"timeout": 60},
        compliance_tags=["SOX", "GDPR"]
    )

    # Query events
    query = AuditQuery(
        start_time=datetime.now() - timedelta(hours=1),
        event_types=[AuditEventType.ACCESS, AuditEventType.MODIFICATION],
        limit=10
    )

    events = audit_logger.query_events(query)
    print(f"Found {len(events)} events")

    # Verify integrity
    integrity_result = audit_logger.verify_integrity()
    print(f"Integrity verification: {integrity_result['status']}")

    # Generate compliance report
    report = audit_logger.generate_compliance_report(
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now(),
        compliance_framework="SOX"
    )

    print(f"Compliance report generated with {report['total_events']} events")
