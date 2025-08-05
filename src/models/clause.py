"""Clause data models with legal-specific validation and analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ClauseType(Enum):
    """Legal clause types commonly found in contracts."""

    # Core contract elements
    PARTIES = "parties"
    RECITALS = "recitals"
    DEFINITIONS = "definitions"

    # Financial terms
    COMPENSATION = "compensation"
    PAYMENT_TERMS = "payment_terms"
    EXPENSES = "expenses"
    PENALTIES = "penalties"

    # Legal terms
    TERMINATION = "termination"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"

    # Confidentiality and IP
    CONFIDENTIALITY = "confidentiality"
    NON_DISCLOSURE = "non_disclosure"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    NON_COMPETE = "non_compete"

    # Employment specific
    JOB_DUTIES = "job_duties"
    BENEFITS = "benefits"
    VACATION = "vacation"
    WORK_SCHEDULE = "work_schedule"

    # Service specific
    SCOPE_OF_WORK = "scope_of_work"
    DELIVERABLES = "deliverables"
    PERFORMANCE_STANDARDS = "performance_standards"

    # Real estate specific
    RENT_PAYMENT = "rent_payment"
    LEASE_TERM = "lease_term"
    SECURITY_DEPOSIT = "security_deposit"
    MAINTENANCE = "maintenance"

    # General
    FORCE_MAJEURE = "force_majeure"
    AMENDMENTS = "amendments"
    SEVERABILITY = "severability"
    ENTIRE_AGREEMENT = "entire_agreement"
    SIGNATURES = "signatures"

    # Catch-all
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass
class LegalClause:
    """Enhanced clause model with legal-specific analysis and validation."""

    # Core identification
    id: UUID = field(default_factory=uuid4)
    type: ClauseType = ClauseType.UNKNOWN
    title: Optional[str] = None

    # Content
    text: str = ""
    page: int = 1
    coordinates: List[float] = field(default_factory=list)  # [x1, y1, x2, y2]

    # Analysis results
    confidence: float = 0.0
    key_terms: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)  # Named entities

    # Legal analysis
    obligations: List[str] = field(default_factory=list)  # Legal obligations
    conditions: List[str] = field(default_factory=list)  # Conditional terms
    dates: List[datetime] = field(default_factory=list)  # Important dates
    amounts: List[str] = field(default_factory=list)  # Financial amounts

    # Metadata
    section_number: Optional[str] = None
    parent_section: Optional[str] = None
    is_mandatory: bool = True
    risk_level: str = "medium"  # low, medium, high, critical

    def __post_init__(self) -> None:
        """Validate and enrich clause data after initialization."""
        if not self.text.strip():
            raise ValueError("Clause text cannot be empty")

        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        if self.page < 1:
            raise ValueError("Page number must be positive")

        # Auto-extract entities and terms if not provided
        if not self.key_terms:
            self.key_terms = self._extract_key_terms()

        if not self.entities:
            self.entities = self._extract_entities()

        if not self.obligations:
            self.obligations = self._extract_obligations()

        if not self.conditions:
            self.conditions = self._extract_conditions()

        if not self.dates:
            self.dates = self._extract_dates()

        if not self.amounts:
            self.amounts = self._extract_amounts()

        # Auto-classify clause type if unknown
        if self.type == ClauseType.UNKNOWN:
            self.type = self._classify_clause_type()

        # Assess risk level
        self.risk_level = self._assess_risk_level()

    def _extract_key_terms(self) -> List[str]:
        """Extract key legal terms from clause text."""
        text_lower = self.text.lower()
        key_terms = []

        # Legal action terms
        legal_actions = [
            'shall', 'must', 'required', 'obligated', 'responsible',
            'liable', 'entitled', 'authorized', 'prohibited', 'forbidden'
        ]

        # Time-related terms
        time_patterns = [
            r'\b\d+\s*(?:days?|weeks?|months?|years?)\b',
            r'\b(?:immediately|forthwith|promptly|within)\b',
            r'\b(?:annually|monthly|weekly|daily)\b'
        ]

        # Find legal action terms
        for term in legal_actions:
            if term in text_lower:
                # Find actual case in original text
                start_idx = text_lower.find(term)
                if start_idx >= 0:
                    actual_term = self.text[start_idx:start_idx + len(term)]
                    key_terms.append(actual_term)

        # Find time-related terms
        for pattern in time_patterns:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            key_terms.extend(matches)

        return list(set(key_terms))

    def _extract_entities(self) -> Dict[str, List[str]]:
        """Extract named entities (simplified NER)."""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'amounts': []
        }

        # Person names (simple heuristic)
        person_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        persons = re.findall(person_pattern, self.text)
        entities['persons'] = persons

        # Organizations (ending with Corp, Inc, LLC, etc.)
        org_pattern = r'\b[A-Z][a-zA-Z\s]+(?:Corp|Inc|LLC|Ltd|Company|Corporation)\.?\b'
        orgs = re.findall(org_pattern, self.text)
        entities['organizations'] = orgs

        # Locations (capitalized place names)
        location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:State|County|City|Street|Avenue|Road))\b'
        locations = re.findall(location_pattern, self.text)
        entities['locations'] = locations

        # Dates
        date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        dates = re.findall(date_pattern, self.text)
        entities['dates'] = dates

        # Amounts
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, self.text)
        entities['amounts'] = amounts

        return entities

    def _extract_obligations(self) -> List[str]:
        """Extract legal obligations from clause text."""
        obligations = []
        text = self.text

        # Pattern for obligations (shall/must + action)
        obligation_patterns = [
            r'(?:shall|must|will|agrees? to|is (?:required|obligated) to)\s+([^.!?;]+)',
            r'(?:Employee|Contractor|Party|Company)\s+(?:shall|must|will)\s+([^.!?;]+)'
        ]

        for pattern in obligation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            obligations.extend([match.strip() for match in matches])

        return list(set(obligations))

    def _extract_conditions(self) -> List[str]:
        """Extract conditional terms from clause text."""
        conditions = []
        text = self.text

        # Pattern for conditions (if/unless/provided that)
        condition_patterns = [
            r'(?:if|unless|provided that|in the event that)\s+([^,;.!?]+)',
            r'(?:subject to|contingent upon|dependent on)\s+([^,;.!?]+)'
        ]

        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend([match.strip() for match in matches])

        return list(set(conditions))

    def _extract_dates(self) -> List[datetime]:
        """Extract and parse dates from clause text."""
        dates = []

        # Various date formats
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try different parsing formats
                    formats = ['%m/%d/%Y', '%Y/%m/%d', '%m-%d-%Y', '%Y-%m-%d', '%B %d, %Y', '%B %d %Y']
                    for fmt in formats:
                        try:
                            date_obj = datetime.strptime(match, fmt)
                            dates.append(date_obj)
                            break
                        except ValueError:
                            continue
                except ValueError:
                    pass  # Skip unparseable dates

        return dates

    def _extract_amounts(self) -> List[str]:
        """Extract financial amounts from clause text."""
        # Pattern for various amount formats
        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # $1,000.00
            r'(?:USD|EUR|GBP)\s*[\d,]+(?:\.\d{2})?',  # USD 1,000.00
            r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?\b',  # 1,000 dollars
            r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:hundred|thousand|million)\s*dollars?\b'  # written amounts
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            amounts.extend(matches)

        return list(set(amounts))

    def _classify_clause_type(self) -> ClauseType:
        """Automatically classify clause type based on content."""
        text_lower = self.text.lower()

        # Define keywords for each clause type
        type_keywords = {
            ClauseType.COMPENSATION: ['salary', 'wage', 'compensation', 'pay', 'remuneration'],
            ClauseType.TERMINATION: ['terminate', 'termination', 'end', 'expire', 'dissolution'],
            ClauseType.CONFIDENTIALITY: ['confidential', 'proprietary', 'non-disclosure', 'secret'],
            ClauseType.LIABILITY: ['liable', 'liability', 'damages', 'responsible', 'fault'],
            ClauseType.PAYMENT_TERMS: ['payment', 'invoice', 'billing', 'due', 'payable'],
            ClauseType.GOVERNING_LAW: ['governing law', 'jurisdiction', 'governed by', 'laws of'],
            ClauseType.DISPUTE_RESOLUTION: ['dispute', 'arbitration', 'mediation', 'litigation'],
            ClauseType.INTELLECTUAL_PROPERTY: ['intellectual property', 'copyright', 'patent', 'trademark'],
            ClauseType.NON_COMPETE: ['non-compete', 'competition', 'competitive', 'solicit'],
            ClauseType.FORCE_MAJEURE: ['force majeure', 'act of god', 'unforeseeable', 'beyond control'],
            ClauseType.INDEMNIFICATION: ['indemnify', 'indemnification', 'hold harmless', 'defend'],
            ClauseType.SIGNATURES: ['signature', 'executed', 'signed', 'witness'],
        }

        # Score each type based on keyword matches
        type_scores = {}
        for clause_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[clause_type] = score

        # Return type with highest score, or UNKNOWN if no matches
        if type_scores:
            return max(type_scores, key=type_scores.get)

        return ClauseType.UNKNOWN

    def _assess_risk_level(self) -> str:
        """Assess the risk level of this clause."""
        text_lower = self.text.lower()

        # High-risk indicators
        high_risk_terms = [
            'unlimited liability', 'personal guarantee', 'criminal',
            'breach', 'default', 'penalty', 'liquidated damages',
            'immediate termination', 'forfeit', 'indemnify'
        ]

        # Critical risk indicators
        critical_risk_terms = [
            'personal liability', 'unlimited damages', 'criminal liability',
            'gross negligence', 'willful misconduct', 'bankruptcy'
        ]

        # Check for critical risk
        if any(term in text_lower for term in critical_risk_terms):
            return "critical"

        # Check for high risk
        if any(term in text_lower for term in high_risk_terms):
            return "high"

        # Check for moderate complexity indicators
        moderate_risk_terms = [
            'shall', 'must', 'required', 'obligated', 'responsible',
            'conditions', 'subject to', 'provided that'
        ]

        if any(term in text_lower for term in moderate_risk_terms):
            return "medium"

        return "low"

    def get_next_action_date(self) -> Optional[datetime]:
        """Extract the next actionable date from the clause."""
        if not self.dates:
            return None

        now = datetime.now()
        future_dates = [date for date in self.dates if date > now]

        return min(future_dates) if future_dates else None

    def has_deadline(self) -> bool:
        """Check if clause contains deadline-related language."""
        deadline_terms = ['deadline', 'due date', 'by', 'within', 'before', 'no later than']
        text_lower = self.text.lower()
        return any(term in text_lower for term in deadline_terms)

    def is_financial_clause(self) -> bool:
        """Check if clause is primarily financial in nature."""
        financial_types = {
            ClauseType.COMPENSATION, ClauseType.PAYMENT_TERMS,
            ClauseType.EXPENSES, ClauseType.PENALTIES
        }
        return self.type in financial_types or bool(self.amounts)

    def get_clause_summary(self) -> Dict[str, Any]:
        """Generate a summary of the clause."""
        return {
            'id': str(self.id),
            'type': self.type.value,
            'title': self.title,
            'page': self.page,
            'confidence': self.confidence,
            'risk_level': self.risk_level,
            'is_mandatory': self.is_mandatory,
            'has_obligations': bool(self.obligations),
            'has_conditions': bool(self.conditions),
            'has_dates': bool(self.dates),
            'has_amounts': bool(self.amounts),
            'is_financial': self.is_financial_clause(),
            'has_deadline': self.has_deadline(),
            'next_action_date': self.get_next_action_date().isoformat() if self.get_next_action_date() else None,
            'key_terms_count': len(self.key_terms),
            'text_length': len(self.text),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert clause to dictionary representation."""
        return {
            'id': str(self.id),
            'type': self.type.value,
            'title': self.title,
            'text': self.text,
            'page': self.page,
            'coordinates': self.coordinates,
            'confidence': self.confidence,
            'key_terms': self.key_terms,
            'entities': self.entities,
            'obligations': self.obligations,
            'conditions': self.conditions,
            'dates': [date.isoformat() for date in self.dates],
            'amounts': self.amounts,
            'section_number': self.section_number,
            'parent_section': self.parent_section,
            'is_mandatory': self.is_mandatory,
            'risk_level': self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LegalClause:
        """Create LegalClause instance from dictionary."""
        # Parse dates
        dates = []
        for date_str in data.get('dates', []):
            try:
                dates.append(datetime.fromisoformat(date_str))
            except ValueError:
                pass  # Skip invalid dates

        return cls(
            id=UUID(data['id']) if data.get('id') else uuid4(),
            type=ClauseType(data.get('type', 'unknown')),
            title=data.get('title'),
            text=data.get('text', ''),
            page=data.get('page', 1),
            coordinates=data.get('coordinates', []),
            confidence=data.get('confidence', 0.0),
            key_terms=data.get('key_terms', []),
            entities=data.get('entities', {}),
            obligations=data.get('obligations', []),
            conditions=data.get('conditions', []),
            dates=dates,
            amounts=data.get('amounts', []),
            section_number=data.get('section_number'),
            parent_section=data.get('parent_section'),
            is_mandatory=data.get('is_mandatory', True),
            risk_level=data.get('risk_level', 'medium'),
        )


# Backward compatibility alias
Clause = LegalClause
