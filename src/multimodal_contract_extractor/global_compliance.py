"""Global compliance and regulatory framework for contract processing.

This module implements comprehensive compliance with international regulations
including GDPR, CCPA, PDPA, and other privacy frameworks.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """Data classification levels for compliance."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PERSONAL = "personal"
    SENSITIVE_PERSONAL = "sensitive_personal"


class ProcessingLawfulBasis(Enum):
    """GDPR lawful basis for processing personal data."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class RetentionPolicy(Enum):
    """Data retention policies."""
    IMMEDIATE_DELETE = "immediate"
    SHORT_TERM = "30_days"
    MEDIUM_TERM = "1_year"
    LONG_TERM = "7_years"
    INDEFINITE = "indefinite"
    LEGAL_REQUIREMENT = "legal_requirement"


class ComplianceRegion(Enum):
    """Supported compliance regions."""
    EU = "eu"           # GDPR
    USA = "usa"         # CCPA, state laws
    UK = "uk"           # UK GDPR
    CANADA = "canada"   # PIPEDA
    SINGAPORE = "singapore"  # PDPA
    AUSTRALIA = "australia"  # Privacy Act
    BRAZIL = "brazil"   # LGPD
    GLOBAL = "global"   # Universal compliance


@dataclass
class DataSubject:
    """Represents a data subject for privacy compliance."""

    subject_id: str
    region: ComplianceRegion
    consent_status: Dict[str, bool] = field(default_factory=dict)
    consent_timestamp: Dict[str, datetime] = field(default_factory=dict)
    opt_out_requests: List[datetime] = field(default_factory=list)
    data_exports: List[Dict[str, Any]] = field(default_factory=list)
    deletion_requests: List[datetime] = field(default_factory=list)
    access_requests: List[datetime] = field(default_factory=list)

    def has_valid_consent(self, purpose: str) -> bool:
        """Check if subject has valid consent for purpose."""
        if purpose not in self.consent_status:
            return False

        if not self.consent_status[purpose]:
            return False

        # Check consent age (2 years max for GDPR)
        if purpose in self.consent_timestamp:
            consent_age = datetime.now() - self.consent_timestamp[purpose]
            if consent_age > timedelta(days=730):  # 2 years
                return False

        return True


@dataclass
class ProcessingRecord:
    """Record of personal data processing activity."""

    record_id: str
    processing_purpose: str
    lawful_basis: ProcessingLawfulBasis
    data_categories: List[str]
    data_subjects: List[str]
    recipients: List[str] = field(default_factory=list)
    retention_period: RetentionPolicy = RetentionPolicy.MEDIUM_TERM
    security_measures: List[str] = field(default_factory=list)
    processing_start: datetime = field(default_factory=datetime.now)
    processing_end: Optional[datetime] = None
    cross_border_transfers: List[Dict[str, str]] = field(default_factory=list)
    automated_decision_making: bool = False
    profiling: bool = False

    def is_expired(self) -> bool:
        """Check if processing record has expired."""
        if self.processing_end is None:
            return False

        retention_days = {
            RetentionPolicy.IMMEDIATE_DELETE: 0,
            RetentionPolicy.SHORT_TERM: 30,
            RetentionPolicy.MEDIUM_TERM: 365,
            RetentionPolicy.LONG_TERM: 2555,  # 7 years
            RetentionPolicy.INDEFINITE: float('inf'),
            RetentionPolicy.LEGAL_REQUIREMENT: 2555
        }

        max_age = retention_days.get(self.retention_period, 365)
        if max_age == float('inf'):
            return False

        age = (datetime.now() - self.processing_end).days
        return age > max_age


@dataclass
class ComplianceAuditTrail:
    """Audit trail for compliance monitoring."""

    audit_id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    data_subject_id: Optional[str]
    processing_details: Dict[str, Any]
    compliance_status: str
    region: ComplianceRegion
    risk_level: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "data_subject_id": self.data_subject_id,
            "processing_details": self.processing_details,
            "compliance_status": self.compliance_status,
            "region": self.region.value,
            "risk_level": self.risk_level
        }


class PersonalDataDetector:
    """Detects personal and sensitive data in documents."""

    def __init__(self):
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "passport": r'\b[A-Z]{1,2}[0-9]{6,9}\b',
            "driver_license": r'\b[A-Z]{1,2}[0-9]{6,8}\b',
            "bank_account": r'\b[0-9]{8,17}\b',
            "date_of_birth": r'\b(?:0[1-9]|1[0-2])[/\-.](?:0[1-9]|[12][0-9]|3[01])[/\-.]\d{4}\b',
            "address": r'\b\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b'
        }

        self.sensitive_keywords = {
            "medical": ["diagnosis", "treatment", "medical", "health", "patient", "doctor"],
            "financial": ["income", "salary", "credit", "debt", "financial", "account"],
            "biometric": ["fingerprint", "facial", "iris", "biometric", "dna", "genetic"],
            "racial": ["race", "ethnicity", "religion", "political", "union"],
            "criminal": ["conviction", "criminal", "offense", "court", "legal"]
        }

    def detect_personal_data(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Detect personal data in text."""
        findings = {}

        # Detect PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            pii_matches = []

            for match in matches:
                pii_matches.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.9,
                    "classification": DataClassification.PERSONAL
                })

            if pii_matches:
                findings[pii_type] = pii_matches

        # Detect sensitive categories
        for category, keywords in self.sensitive_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if category not in findings:
                        findings[category] = []

                    findings[category].append({
                        "type": f"sensitive_{category}",
                        "value": keyword,
                        "start": text.lower().find(keyword.lower()),
                        "end": text.lower().find(keyword.lower()) + len(keyword),
                        "confidence": 0.7,
                        "classification": DataClassification.SENSITIVE_PERSONAL
                    })

        return findings

    def classify_document_sensitivity(self, personal_data: Dict[str, List[Dict[str, Any]]]) -> DataClassification:
        """Classify document sensitivity based on detected personal data."""
        if not personal_data:
            return DataClassification.PUBLIC

        # Check for sensitive personal data
        sensitive_categories = {"medical", "biometric", "racial", "criminal"}
        for category in personal_data.keys():
            if category in sensitive_categories:
                return DataClassification.SENSITIVE_PERSONAL

        # Check for regular personal data
        personal_categories = {"email", "phone", "ssn", "credit_card", "passport", "driver_license"}
        for category in personal_data.keys():
            if category in personal_categories:
                return DataClassification.PERSONAL

        # Check for potentially personal data
        if personal_data:
            return DataClassification.CONFIDENTIAL

        return DataClassification.INTERNAL


class GlobalComplianceManager:
    """Manages global compliance requirements and data protection."""

    def __init__(self, default_region: ComplianceRegion = ComplianceRegion.GLOBAL):
        self.default_region = default_region
        self.data_subjects: Dict[str, DataSubject] = {}
        self.processing_records: Dict[str, ProcessingRecord] = {}
        self.audit_trail: List[ComplianceAuditTrail] = []
        self.pii_detector = PersonalDataDetector()
        self.anonymization_enabled = True
        self.retention_policies: Dict[str, RetentionPolicy] = {}

        # Initialize region-specific requirements
        self.region_requirements = self._initialize_region_requirements()

    def _initialize_region_requirements(self) -> Dict[ComplianceRegion, Dict[str, Any]]:
        """Initialize region-specific compliance requirements."""
        return {
            ComplianceRegion.EU: {
                "consent_required": True,
                "right_to_erasure": True,
                "data_portability": True,
                "breach_notification_hours": 72,
                "max_retention_years": 7,
                "cross_border_restrictions": True,
                "dpo_required": True,
                "privacy_by_design": True
            },
            ComplianceRegion.USA: {
                "consent_required": False,  # Varies by state
                "opt_out_required": True,
                "breach_notification_hours": 72,
                "ccpa_compliance": True,
                "sector_specific_rules": True,
                "state_variations": True
            },
            ComplianceRegion.UK: {
                "consent_required": True,
                "right_to_erasure": True,
                "data_portability": True,
                "breach_notification_hours": 72,
                "ico_registration": True,
                "adequacy_decisions": True
            },
            ComplianceRegion.SINGAPORE: {
                "consent_required": True,
                "notification_required": True,
                "data_breach_notification": True,
                "dpo_appointment": True,
                "cross_border_transfer_approval": True
            },
            ComplianceRegion.GLOBAL: {
                "consent_required": True,
                "right_to_erasure": True,
                "data_portability": True,
                "breach_notification_hours": 24,
                "max_retention_years": 2,
                "privacy_by_design": True,
                "cross_border_restrictions": True
            }
        }

    def register_data_subject(self, subject_id: str, region: ComplianceRegion) -> DataSubject:
        """Register a data subject for compliance tracking."""
        data_subject = DataSubject(subject_id=subject_id, region=region)
        self.data_subjects[subject_id] = data_subject

        self._audit_event(
            event_type="data_subject_registration",
            data_subject_id=subject_id,
            processing_details={"region": region.value},
            compliance_status="registered"
        )

        return data_subject

    def request_consent(self, subject_id: str, purpose: str,
                       explicit_consent: bool = True) -> bool:
        """Request consent from data subject."""
        if subject_id not in self.data_subjects:
            raise ValueError(f"Data subject {subject_id} not registered")

        data_subject = self.data_subjects[subject_id]

        # In real implementation, this would trigger consent request UI
        # For now, we simulate consent based on region requirements
        region_reqs = self.region_requirements.get(data_subject.region, {})

        if region_reqs.get("consent_required", True):
            # Simulate consent (in real app, would be user-provided)
            consent_granted = True  # Placeholder

            data_subject.consent_status[purpose] = consent_granted
            data_subject.consent_timestamp[purpose] = datetime.now()

            self._audit_event(
                event_type="consent_request",
                data_subject_id=subject_id,
                processing_details={
                    "purpose": purpose,
                    "explicit_consent": explicit_consent,
                    "consent_granted": consent_granted
                },
                compliance_status="consent_obtained" if consent_granted else "consent_denied"
            )

            return consent_granted

        return True  # Consent not required in this region

    def create_processing_record(self, purpose: str, lawful_basis: ProcessingLawfulBasis,
                               data_categories: List[str], data_subjects: List[str],
                               retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM_TERM) -> ProcessingRecord:
        """Create a processing record for compliance tracking."""
        record_id = str(uuid.uuid4())

        record = ProcessingRecord(
            record_id=record_id,
            processing_purpose=purpose,
            lawful_basis=lawful_basis,
            data_categories=data_categories,
            data_subjects=data_subjects,
            retention_period=retention_policy,
            security_measures=["encryption", "access_control", "audit_logging"],
            automated_decision_making=True,  # Contract processing uses automation
            profiling=False
        )

        self.processing_records[record_id] = record

        self._audit_event(
            event_type="processing_record_created",
            processing_details={
                "record_id": record_id,
                "purpose": purpose,
                "lawful_basis": lawful_basis.value,
                "data_categories": data_categories,
                "subject_count": len(data_subjects)
            },
            compliance_status="active"
        )

        return record

    def process_document_with_compliance(self, document_text: str,
                                       subject_id: Optional[str] = None,
                                       purpose: str = "contract_analysis",
                                       region: ComplianceRegion = None) -> Dict[str, Any]:
        """Process document with full compliance checking."""
        region = region or self.default_region
        processing_start = datetime.now()

        # Detect personal data
        personal_data = self.pii_detector.detect_personal_data(document_text)
        data_classification = self.pii_detector.classify_document_sensitivity(personal_data)

        # Check compliance requirements
        compliance_checks = self._perform_compliance_checks(
            personal_data, data_classification, subject_id, purpose, region
        )

        # Create processing record if personal data found
        processing_record = None
        if personal_data and data_classification in [DataClassification.PERSONAL, DataClassification.SENSITIVE_PERSONAL]:
            processing_record = self.create_processing_record(
                purpose=purpose,
                lawful_basis=ProcessingLawfulBasis.LEGITIMATE_INTERESTS,
                data_categories=list(personal_data.keys()),
                data_subjects=[subject_id] if subject_id else [],
                retention_policy=self.retention_policies.get(purpose, RetentionPolicy.MEDIUM_TERM)
            )

        # Apply data minimization and anonymization if required
        processed_text = document_text
        if self.anonymization_enabled and personal_data:
            processed_text = self._anonymize_text(document_text, personal_data)

        processing_result = {
            "processed_text": processed_text,
            "personal_data_detected": personal_data,
            "data_classification": data_classification.value,
            "compliance_checks": compliance_checks,
            "processing_record_id": processing_record.record_id if processing_record else None,
            "anonymized": self.anonymization_enabled and bool(personal_data),
            "processing_time": (datetime.now() - processing_start).total_seconds(),
            "region": region.value
        }

        self._audit_event(
            event_type="document_processed",
            data_subject_id=subject_id,
            processing_details=processing_result,
            compliance_status="compliant" if compliance_checks["compliant"] else "non_compliant",
            risk_level=self._assess_risk_level(data_classification, compliance_checks)
        )

        return processing_result

    def _perform_compliance_checks(self, personal_data: Dict[str, Any],
                                 data_classification: DataClassification,
                                 subject_id: Optional[str], purpose: str,
                                 region: ComplianceRegion) -> Dict[str, Any]:
        """Perform comprehensive compliance checks."""
        checks = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "requirements_met": []
        }

        region_reqs = self.region_requirements.get(region, {})

        # Check consent requirements
        if region_reqs.get("consent_required", False) and subject_id:
            if subject_id in self.data_subjects:
                data_subject = self.data_subjects[subject_id]
                if not data_subject.has_valid_consent(purpose):
                    checks["violations"].append("Missing or expired consent")
                    checks["compliant"] = False
                else:
                    checks["requirements_met"].append("Valid consent obtained")
            else:
                checks["violations"].append("Data subject not registered")
                checks["compliant"] = False

        # Check data minimization
        if len(personal_data) > 10:  # Arbitrary threshold
            checks["warnings"].append("High volume of personal data detected - review data minimization")

        # Check retention policy
        if data_classification in [DataClassification.SENSITIVE_PERSONAL]:
            max_retention = region_reqs.get("max_retention_years", 7)
            if max_retention < 7:
                checks["requirements_met"].append("Appropriate retention period")
            else:
                checks["warnings"].append("Consider shorter retention for sensitive data")

        # Check cross-border transfer restrictions
        if region_reqs.get("cross_border_restrictions", False):
            checks["requirements_met"].append("Cross-border transfer restrictions noted")

        # Check privacy by design
        if region_reqs.get("privacy_by_design", False):
            checks["requirements_met"].append("Privacy by design principles applied")

        return checks

    def _anonymize_text(self, text: str, personal_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Anonymize personal data in text."""
        anonymized_text = text

        # Sort matches by position (reverse order to maintain positions)
        all_matches = []
        for category, matches in personal_data.items():
            all_matches.extend(matches)

        all_matches.sort(key=lambda x: x["start"], reverse=True)

        # Replace personal data with anonymized versions
        anonymization_map = {
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "ssn": "[SSN]",
            "credit_card": "[CREDIT_CARD]",
            "ip_address": "[IP_ADDRESS]",
            "passport": "[PASSPORT]",
            "driver_license": "[LICENSE]",
            "bank_account": "[ACCOUNT]",
            "date_of_birth": "[DOB]",
            "address": "[ADDRESS]"
        }

        for match in all_matches:
            start, end = match["start"], match["end"]
            pii_type = match["type"]

            replacement = anonymization_map.get(pii_type, "[REDACTED]")
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]

        return anonymized_text

    def handle_data_subject_request(self, subject_id: str, request_type: str) -> Dict[str, Any]:
        """Handle data subject rights requests."""
        if subject_id not in self.data_subjects:
            return {"error": "Data subject not found", "success": False}

        data_subject = self.data_subjects[subject_id]
        response = {"success": True, "request_type": request_type}

        if request_type == "access":
            # Right to access - provide all data
            data_subject.access_requests.append(datetime.now())

            # Collect all processing records for this subject
            subject_records = [
                record for record in self.processing_records.values()
                if subject_id in record.data_subjects
            ]

            response["data"] = {
                "subject_info": {
                    "subject_id": subject_id,
                    "region": data_subject.region.value,
                    "consent_status": data_subject.consent_status,
                    "consent_timestamps": {k: v.isoformat() for k, v in data_subject.consent_timestamp.items()}
                },
                "processing_records": [
                    {
                        "record_id": record.record_id,
                        "purpose": record.processing_purpose,
                        "lawful_basis": record.lawful_basis.value,
                        "data_categories": record.data_categories,
                        "processing_start": record.processing_start.isoformat(),
                        "retention_period": record.retention_period.value
                    }
                    for record in subject_records
                ]
            }

        elif request_type == "erasure":
            # Right to be forgotten
            data_subject.deletion_requests.append(datetime.now())

            # Mark processing records for deletion
            deletion_count = 0
            for record in self.processing_records.values():
                if subject_id in record.data_subjects:
                    record.processing_end = datetime.now()
                    deletion_count += 1

            response["deleted_records"] = deletion_count
            response["message"] = f"Marked {deletion_count} processing records for deletion"

        elif request_type == "portability":
            # Right to data portability
            subject_records = [
                record for record in self.processing_records.values()
                if subject_id in record.data_subjects
            ]

            # Create portable data format (JSON)
            portable_data = {
                "data_subject": {
                    "id": subject_id,
                    "region": data_subject.region.value,
                    "export_date": datetime.now().isoformat()
                },
                "processing_activities": [
                    {
                        "purpose": record.processing_purpose,
                        "data_categories": record.data_categories,
                        "processing_period": {
                            "start": record.processing_start.isoformat(),
                            "end": record.processing_end.isoformat() if record.processing_end else None
                        }
                    }
                    for record in subject_records
                ]
            }

            data_subject.data_exports.append({
                "timestamp": datetime.now(),
                "format": "json",
                "record_count": len(subject_records)
            })

            response["portable_data"] = portable_data

        elif request_type == "rectification":
            # Right to rectification
            response["message"] = "Rectification request received - manual review required"

        elif request_type == "restrict":
            # Right to restrict processing
            restricted_count = 0
            for record in self.processing_records.values():
                if subject_id in record.data_subjects:
                    # Add restriction flag (would be implemented in actual processing)
                    restricted_count += 1

            response["restricted_records"] = restricted_count

        self._audit_event(
            event_type=f"data_subject_request_{request_type}",
            data_subject_id=subject_id,
            processing_details=response,
            compliance_status="processed"
        )

        return response

    def _assess_risk_level(self, data_classification: DataClassification,
                          compliance_checks: Dict[str, Any]) -> str:
        """Assess risk level for audit trail."""
        if not compliance_checks["compliant"]:
            return "high"

        if data_classification == DataClassification.SENSITIVE_PERSONAL:
            return "high"
        elif data_classification == DataClassification.PERSONAL:
            return "medium"
        elif compliance_checks["warnings"]:
            return "medium"
        else:
            return "low"

    def _audit_event(self, event_type: str, data_subject_id: Optional[str] = None,
                    user_id: Optional[str] = None, processing_details: Dict[str, Any] = None,
                    compliance_status: str = "unknown", risk_level: str = "low"):
        """Record audit event."""
        audit_entry = ComplianceAuditTrail(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            data_subject_id=data_subject_id,
            processing_details=processing_details or {},
            compliance_status=compliance_status,
            region=self.default_region,
            risk_level=risk_level
        )

        self.audit_trail.append(audit_entry)

        # Log high-risk events
        if risk_level == "high":
            logger.warning(f"High-risk compliance event: {event_type}")

    def generate_compliance_report(self, start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        # Filter audit trail by date range
        relevant_audits = [
            audit for audit in self.audit_trail
            if start_date <= audit.timestamp <= end_date
        ]

        # Calculate statistics
        total_events = len(relevant_audits)
        event_types = {}
        compliance_status_counts = {}
        risk_level_counts = {}

        for audit in relevant_audits:
            event_types[audit.event_type] = event_types.get(audit.event_type, 0) + 1
            compliance_status_counts[audit.compliance_status] = compliance_status_counts.get(audit.compliance_status, 0) + 1
            risk_level_counts[audit.risk_level] = risk_level_counts.get(audit.risk_level, 0) + 1

        # Check for expired processing records
        expired_records = [
            record for record in self.processing_records.values()
            if record.is_expired()
        ]

        # Data subject statistics
        consent_stats = {}
        for subject in self.data_subjects.values():
            region = subject.region.value
            if region not in consent_stats:
                consent_stats[region] = {"total": 0, "with_consent": 0}

            consent_stats[region]["total"] += 1
            if any(subject.consent_status.values()):
                consent_stats[region]["with_consent"] += 1

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "total_data_subjects": len(self.data_subjects),
                "active_processing_records": len([r for r in self.processing_records.values() if r.processing_end is None]),
                "expired_records": len(expired_records),
                "compliance_violations": sum(1 for audit in relevant_audits if audit.compliance_status == "non_compliant")
            },
            "event_breakdown": event_types,
            "compliance_status": compliance_status_counts,
            "risk_levels": risk_level_counts,
            "data_subject_consent": consent_stats,
            "expired_processing_records": [r.record_id for r in expired_records],
            "recommendations": self._generate_compliance_recommendations(relevant_audits, expired_records)
        }

        return report

    def _generate_compliance_recommendations(self, audits: List[ComplianceAuditTrail],
                                          expired_records: List[ProcessingRecord]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        # Check for high-risk events
        high_risk_events = [audit for audit in audits if audit.risk_level == "high"]
        if high_risk_events:
            recommendations.append(f"Review {len(high_risk_events)} high-risk events requiring immediate attention")

        # Check for expired records
        if expired_records:
            recommendations.append(f"Delete or review {len(expired_records)} expired processing records")

        # Check consent status
        subjects_without_consent = [
            subject for subject in self.data_subjects.values()
            if not any(subject.consent_status.values())
        ]
        if subjects_without_consent:
            recommendations.append(f"Obtain consent for {len(subjects_without_consent)} data subjects")

        # Check for violations
        violations = [audit for audit in audits if audit.compliance_status == "non_compliant"]
        if violations:
            recommendations.append(f"Address {len(violations)} compliance violations")

        # General recommendations
        recommendations.extend([
            "Conduct regular compliance training for staff",
            "Review and update privacy policies quarterly",
            "Implement privacy impact assessments for new processing activities",
            "Maintain up-to-date data mapping and processing inventories"
        ])

        return recommendations

    def export_audit_log(self, filepath: str, format: str = "json") -> bool:
        """Export audit log to file."""
        try:
            audit_data = [audit.to_dict() for audit in self.audit_trail]

            if format.lower() == "json":
                with open(filepath, 'w') as f:
                    json.dump(audit_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")

            return True
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return False


# Global compliance manager instance
_compliance_manager: Optional[GlobalComplianceManager] = None


def get_compliance_manager(region: ComplianceRegion = ComplianceRegion.GLOBAL) -> GlobalComplianceManager:
    """Get or create global compliance manager instance."""
    global _compliance_manager
    if _compliance_manager is None:
        _compliance_manager = GlobalComplianceManager(region)
    return _compliance_manager


def process_document_compliant(document_text: str, subject_id: Optional[str] = None,
                             purpose: str = "contract_analysis",
                             region: ComplianceRegion = ComplianceRegion.GLOBAL) -> Dict[str, Any]:
    """Process document with full compliance checking."""
    compliance_manager = get_compliance_manager(region)
    return compliance_manager.process_document_with_compliance(
        document_text, subject_id, purpose, region
    )


def handle_privacy_request(subject_id: str, request_type: str) -> Dict[str, Any]:
    """Handle data subject privacy rights request."""
    compliance_manager = get_compliance_manager()
    return compliance_manager.handle_data_subject_request(subject_id, request_type)


def generate_privacy_report(days: int = 30) -> Dict[str, Any]:
    """Generate privacy compliance report."""
    compliance_manager = get_compliance_manager()
    start_date = datetime.now() - timedelta(days=days)
    return compliance_manager.generate_compliance_report(start_date)
