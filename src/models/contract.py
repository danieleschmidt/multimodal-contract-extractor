"""Contract data models with validation and business logic."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ContractType(Enum):
    """Standard contract types supported by the system."""

    NDA = "nda"
    EMPLOYMENT = "employment_agreement"
    SERVICE = "service_agreement"
    LEASE = "lease_agreement"
    PURCHASE = "purchase_order"
    PARTNERSHIP = "partnership_agreement"
    LICENSE = "licensing_agreement"
    GENERAL = "general_contract"
    UNKNOWN = "unknown"


@dataclass
class ContractParty:
    """Represents a party (individual or entity) in a contract."""

    name: str
    role: str  # e.g., "employer", "employee", "buyer", "seller"
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    entity_type: Optional[str] = None  # "individual", "corporation", "llc", etc.

    def __post_init__(self) -> None:
        """Validate party data after initialization."""
        if not self.name.strip():
            raise ValueError("Party name cannot be empty")
        if not self.role.strip():
            raise ValueError("Party role cannot be empty")

        # Validate email format if provided
        if self.email and not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def to_dict(self) -> Dict[str, Any]:
        """Convert party to dictionary representation."""
        return {
            "name": self.name,
            "role": self.role,
            "address": self.address,
            "email": self.email,
            "phone": self.phone,
            "entity_type": self.entity_type,
        }


@dataclass
class Contract:
    """Main contract model with business logic and validation."""

    # Core identifiers
    id: UUID = field(default_factory=uuid4)
    title: Optional[str] = None
    contract_type: ContractType = ContractType.UNKNOWN

    # Document metadata
    filename: Optional[str] = None
    pages: int = 0
    file_size_bytes: Optional[int] = None

    # Parties involved
    parties: List[ContractParty] = field(default_factory=list)

    # Contract dates
    created_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None

    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_seconds: float = 0.0
    overall_confidence: float = 0.0

    # Extracted content
    clauses: List[Any] = field(default_factory=list)  # Will be LegalClause objects
    key_terms: Dict[str, Any] = field(default_factory=dict)

    # Additional metadata
    language: str = "en"
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate contract data after initialization."""
        if self.pages < 0:
            raise ValueError("Pages cannot be negative")
        if self.processing_time_seconds < 0:
            raise ValueError("Processing time cannot be negative")
        if not 0 <= self.overall_confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    def add_party(self, party: ContractParty) -> None:
        """Add a party to the contract with validation."""
        if not isinstance(party, ContractParty):
            raise TypeError("Party must be a ContractParty instance")

        # Check for duplicate parties (same name and role)
        for existing_party in self.parties:
            if existing_party.name == party.name and existing_party.role == party.role:
                raise ValueError(f"Party already exists: {party.name} as {party.role}")

        self.parties.append(party)

    def get_party_by_role(self, role: str) -> Optional[ContractParty]:
        """Get the first party with the specified role."""
        for party in self.parties:
            if party.role.lower() == role.lower():
                return party
        return None

    def get_parties_by_role(self, role: str) -> List[ContractParty]:
        """Get all parties with the specified role."""
        return [party for party in self.parties if party.role.lower() == role.lower()]

    def is_expired(self) -> bool:
        """Check if the contract has expired."""
        if not self.expiration_date:
            return False
        return datetime.utcnow() > self.expiration_date

    def is_effective(self) -> bool:
        """Check if the contract is currently effective."""
        now = datetime.utcnow()

        # Check if effective date has passed
        if self.effective_date and now < self.effective_date:
            return False

        # Check if not expired
        if self.expiration_date and now > self.expiration_date:
            return False

        return True

    def duration_days(self) -> Optional[int]:
        """Calculate contract duration in days."""
        if not self.effective_date or not self.expiration_date:
            return None
        return (self.expiration_date - self.effective_date).days

    def classify_contract_type(self) -> ContractType:
        """Automatically classify contract type based on clauses and content."""
        if not self.clauses:
            return ContractType.UNKNOWN

        clause_types = {clause.type for clause in self.clauses if hasattr(clause, 'type')}
        clause_texts = [clause.text.lower() for clause in self.clauses if hasattr(clause, 'text')]
        all_text = ' '.join(clause_texts)

        # NDA classification
        if self._has_nda_indicators(clause_types, all_text):
            return ContractType.NDA

        # Employment agreement classification
        if self._has_employment_indicators(clause_types, all_text):
            return ContractType.EMPLOYMENT

        # Service agreement classification
        if self._has_service_indicators(clause_types, all_text):
            return ContractType.SERVICE

        # Lease agreement classification
        if self._has_lease_indicators(clause_types, all_text):
            return ContractType.LEASE

        return ContractType.GENERAL

    def _has_nda_indicators(self, clause_types: set, text: str) -> bool:
        """Check for NDA-specific indicators."""
        nda_clauses = {'confidentiality', 'non_disclosure', 'proprietary_information'}
        nda_keywords = ['confidential', 'proprietary', 'non-disclosure', 'trade secret']

        return (
            bool(clause_types & nda_clauses) or
            any(keyword in text for keyword in nda_keywords)
        )

    def _has_employment_indicators(self, clause_types: set, text: str) -> bool:
        """Check for employment agreement indicators."""
        employment_clauses = {'compensation', 'termination', 'job_duties', 'benefits'}
        employment_keywords = ['employee', 'employer', 'salary', 'benefits', 'vacation']

        return (
            bool(clause_types & employment_clauses) or
            any(keyword in text for keyword in employment_keywords)
        )

    def _has_service_indicators(self, clause_types: set, text: str) -> bool:
        """Check for service agreement indicators."""
        service_clauses = {'scope_of_work', 'payment_terms', 'deliverables'}
        service_keywords = ['services', 'contractor', 'deliverables', 'statement of work']

        return (
            bool(clause_types & service_clauses) or
            any(keyword in text for keyword in service_keywords)
        )

    def _has_lease_indicators(self, clause_types: set, text: str) -> bool:
        """Check for lease agreement indicators."""
        lease_clauses = {'rent_payment', 'lease_term', 'security_deposit'}
        lease_keywords = ['lease', 'rent', 'tenant', 'landlord', 'premises']

        return (
            bool(clause_types & lease_clauses) or
            any(keyword in text for keyword in lease_keywords)
        )

    def extract_financial_terms(self) -> Dict[str, Any]:
        """Extract financial information from the contract."""
        financial_terms = {
            'amounts': [],
            'payment_terms': [],
            'currencies': set(),
        }

        # Pattern for monetary amounts
        money_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        currency_pattern = r'\b(USD|EUR|GBP|CAD|AUD)\b'

        for clause in self.clauses:
            if hasattr(clause, 'text'):
                # Find monetary amounts
                amounts = re.findall(money_pattern, clause.text)
                financial_terms['amounts'].extend(amounts)

                # Find currencies
                currencies = re.findall(currency_pattern, clause.text, re.IGNORECASE)
                financial_terms['currencies'].update(currencies)

                # Extract payment terms
                if hasattr(clause, 'type') and 'payment' in str(clause.type).lower():
                    financial_terms['payment_terms'].append({
                        'clause_id': getattr(clause, 'id', None),
                        'text': clause.text,
                        'amounts': amounts,
                    })

        financial_terms['currencies'] = list(financial_terms['currencies'])
        return financial_terms

    def get_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive contract summary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'type': self.contract_type.value,
            'parties_count': len(self.parties),
            'clauses_count': len(self.clauses),
            'pages': self.pages,
            'confidence': self.overall_confidence,
            'is_effective': self.is_effective(),
            'is_expired': self.is_expired(),
            'duration_days': self.duration_days(),
            'processing_time': self.processing_time_seconds,
            'financial_terms': self.extract_financial_terms(),
            'key_parties': [
                {'name': party.name, 'role': party.role}
                for party in self.parties[:3]  # Top 3 parties
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary representation."""
        return {
            'id': str(self.id),
            'title': self.title,
            'contract_type': self.contract_type.value,
            'filename': self.filename,
            'pages': self.pages,
            'file_size_bytes': self.file_size_bytes,
            'parties': [party.to_dict() for party in self.parties],
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'processed_at': self.processed_at.isoformat(),
            'processing_time_seconds': self.processing_time_seconds,
            'overall_confidence': self.overall_confidence,
            'clauses': [clause.to_dict() if hasattr(clause, 'to_dict') else str(clause) for clause in self.clauses],
            'key_terms': self.key_terms,
            'language': self.language,
            'jurisdiction': self.jurisdiction,
            'governing_law': self.governing_law,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Contract:
        """Create Contract instance from dictionary."""
        # Parse dates
        created_date = datetime.fromisoformat(data['created_date']) if data.get('created_date') else None
        effective_date = datetime.fromisoformat(data['effective_date']) if data.get('effective_date') else None
        expiration_date = datetime.fromisoformat(data['expiration_date']) if data.get('expiration_date') else None
        processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else datetime.utcnow()

        # Parse parties
        parties = [ContractParty(**party_data) for party_data in data.get('parties', [])]

        return cls(
            id=UUID(data['id']) if data.get('id') else uuid4(),
            title=data.get('title'),
            contract_type=ContractType(data.get('contract_type', 'unknown')),
            filename=data.get('filename'),
            pages=data.get('pages', 0),
            file_size_bytes=data.get('file_size_bytes'),
            parties=parties,
            created_date=created_date,
            effective_date=effective_date,
            expiration_date=expiration_date,
            processed_at=processed_at,
            processing_time_seconds=data.get('processing_time_seconds', 0.0),
            overall_confidence=data.get('overall_confidence', 0.0),
            clauses=data.get('clauses', []),
            key_terms=data.get('key_terms', {}),
            language=data.get('language', 'en'),
            jurisdiction=data.get('jurisdiction'),
            governing_law=data.get('governing_law'),
        )
