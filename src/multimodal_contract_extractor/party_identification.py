"""Advanced contract party identification and extraction.

Generation 1 Enhanced Feature: Intelligently identifies and extracts
contract parties, their roles, contact information, and relationships.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Contact information for a party."""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None


@dataclass
class ContractParty:
    """Represents a party in a contract."""
    name: str
    role: str
    party_type: str  # individual, company, government, etc.
    contact_info: ContactInfo = field(default_factory=ContactInfo)
    aliases: List[str] = field(default_factory=list)
    confidence: float = 0.0
    location_in_document: Optional[str] = None
    legal_entity_type: Optional[str] = None
    registration_info: Dict[str, str] = field(default_factory=dict)


@dataclass
class PartyRelationship:
    """Relationship between parties."""
    party1: str
    party2: str
    relationship_type: str
    confidence: float
    description: str


class ContractPartyExtractor:
    """Advanced contract party identification system."""
    
    def __init__(self):
        """Initialize party extractor with patterns and rules."""
        self.entity_patterns = self._load_entity_patterns()
        self.role_patterns = self._load_role_patterns()
        self.contact_patterns = self._load_contact_patterns()
        self.legal_entity_patterns = self._load_legal_entity_patterns()
        
    def extract_parties(self, document_text: str, 
                       clauses: List[Any]) -> List[ContractParty]:
        """Extract all parties from contract text and clauses.
        
        Args:
            document_text: Full contract text
            clauses: Extracted contract clauses
            
        Returns:
            List of identified contract parties
        """
        parties = []
        
        # Extract from structured party sections
        parties.extend(self._extract_from_party_sections(document_text))
        
        # Extract from signature blocks
        parties.extend(self._extract_from_signatures(document_text))
        
        # Extract from clause analysis
        parties.extend(self._extract_from_clauses(clauses))
        
        # Extract from document headers/metadata
        parties.extend(self._extract_from_headers(document_text))
        
        # Consolidate and deduplicate parties
        consolidated_parties = self._consolidate_parties(parties)
        
        # Enhance with additional information
        enhanced_parties = self._enhance_party_information(consolidated_parties, document_text)
        
        # Validate and score parties
        validated_parties = self._validate_and_score_parties(enhanced_parties, document_text)
        
        logger.info("Extracted %d contract parties", len(validated_parties))
        return validated_parties
        
    def _extract_from_party_sections(self, text: str) -> List[ContractParty]:
        """Extract parties from dedicated party sections."""
        parties = []
        
        # Look for common party section headers
        party_section_patterns = [
            r'(?:PARTIES|parties):\s*\n((?:.|\n)*?)(?:\n\s*\n|\n[A-Z])',
            r'(?:BETWEEN|between):\s*((?:.|\n)*?)(?:WHEREAS|AND)',
            r'(?:CONTRACTOR|contractor):\s*(.*?)(?:\n|$)',
            r'(?:CLIENT|client):\s*(.*?)(?:\n|$)',
            r'(?:VENDOR|vendor):\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in party_section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                party_text = match.group(1).strip()
                extracted_parties = self._parse_party_text(party_text, "party_section")
                parties.extend(extracted_parties)
                
        return parties
        
    def _extract_from_signatures(self, text: str) -> List[ContractParty]:
        """Extract parties from signature blocks."""
        parties = []
        
        # Pattern for signature blocks
        signature_patterns = [
            r'(.*?)\s*\n.*?(?:Signature|signature):\s*[_\s]*\n.*?(?:Date|date):\s*[_\s]*',
            r'(?:Signed|signed)\s*(?:by|BY):\s*(.*?)(?:\n|$)',
            r'(.*?)\s*\n.*?/s/\s*(.*?)(?:\n|$)',
            r'(?:Name|NAME):\s*(.*?)(?:\n|$).*?(?:Title|TITLE):\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in signature_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 1:
                    name = match.group(1).strip()
                    if self._is_valid_party_name(name):
                        party = ContractParty(
                            name=name,
                            role="signatory",
                            party_type="individual",
                            location_in_document="signature_block",
                            confidence=0.8
                        )
                        parties.append(party)
                        
        return parties
        
    def _extract_from_clauses(self, clauses: List[Any]) -> List[ContractParty]:
        """Extract parties mentioned in contract clauses."""
        parties = []
        
        for clause in clauses:
            if not hasattr(clause, 'text'):
                continue
                
            clause_text = clause.text
            
            # Look for party references in different clause types
            if hasattr(clause, 'type'):
                if clause.type in ['payment_terms', 'termination', 'liability']:
                    # These clauses often mention parties
                    clause_parties = self._extract_parties_from_text(clause_text, clause.type)
                    parties.extend(clause_parties)
                    
        return parties
        
    def _extract_from_headers(self, text: str) -> List[ContractParty]:
        """Extract parties from document headers and metadata."""
        parties = []
        
        # Look at the beginning of the document for party information
        header_text = text[:2000]  # First 2000 characters
        
        # Common header patterns
        header_patterns = [
            r'(?:Agreement|Contract|CONTRACT)\s+(?:between|BETWEEN)\s+(.*?)\s+(?:and|AND)\s+(.*?)(?:\n|$)',
            r'(?:This|THIS)\s+.*?(?:between|BETWEEN)\s+(.*?)\s+(?:and|AND)\s+(.*?)(?:\.|,)',
            r'(?:Entered into|ENTERED INTO)\s+.*?(?:by and between|BY AND BETWEEN)\s+(.*?)\s+(?:and|AND)\s+(.*?)(?:\.|,|\n)'
        ]
        
        for pattern in header_patterns:
            matches = re.finditer(pattern, header_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                party1_text = match.group(1).strip()
                party2_text = match.group(2).strip()
                
                if self._is_valid_party_name(party1_text):
                    parties.append(ContractParty(
                        name=party1_text,
                        role="party",
                        party_type=self._determine_party_type(party1_text),
                        location_in_document="header",
                        confidence=0.9
                    ))
                    
                if self._is_valid_party_name(party2_text):
                    parties.append(ContractParty(
                        name=party2_text,
                        role="party",
                        party_type=self._determine_party_type(party2_text),
                        location_in_document="header",
                        confidence=0.9
                    ))
                    
        return parties
        
    def _parse_party_text(self, party_text: str, source: str) -> List[ContractParty]:
        """Parse text containing party information."""
        parties = []
        
        # Split on common delimiters
        potential_parties = re.split(r'\n\s*\n|\nAND\n|\n(?=\d+\.)', party_text)
        
        for party_section in potential_parties:
            party_section = party_section.strip()
            if not party_section or len(party_section) < 10:
                continue
                
            # Extract name (usually first line or after numbering)
            lines = party_section.split('\n')
            name_line = lines[0].strip()
            
            # Remove numbering
            name_line = re.sub(r'^\d+\.\s*', '', name_line)
            
            if self._is_valid_party_name(name_line):
                # Extract additional information
                contact_info = self._extract_contact_info(party_section)
                legal_entity_type = self._extract_legal_entity_type(party_section)
                
                party = ContractParty(
                    name=name_line,
                    role=self._determine_role_from_context(party_section),
                    party_type=self._determine_party_type(name_line),
                    contact_info=contact_info,
                    location_in_document=source,
                    legal_entity_type=legal_entity_type,
                    confidence=0.85
                )
                
                parties.append(party)
                
        return parties
        
    def _extract_parties_from_text(self, text: str, context: str) -> List[ContractParty]:
        """Extract party references from general text."""
        parties = []
        
        # Look for company name patterns
        company_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc\.|LLC\.|Corp\.|Ltd\.)\b',
            r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\b'  # All caps company names
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                company_name = match.group(0).strip()
                if self._is_valid_party_name(company_name) and len(company_name) > 5:
                    party = ContractParty(
                        name=company_name,
                        role=self._determine_role_from_context(context),
                        party_type="company",
                        location_in_document=context,
                        confidence=0.7
                    )
                    parties.append(party)
                    
        return parties
        
    def _extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information from text."""
        contact_info = ContactInfo()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info.email = email_match.group(0)
            
        # Phone pattern
        phone_pattern = r'(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info.phone = phone_match.group(0)
            
        # Address pattern (simplified)
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
            r'P\.?O\.?\s+Box\s+\d+',
            r'\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5}'
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, text, re.IGNORECASE)
            if address_match:
                contact_info.address = address_match.group(0)
                break
                
        # Website pattern
        website_pattern = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|net|edu|gov)'
        website_match = re.search(website_pattern, text, re.IGNORECASE)
        if website_match:
            contact_info.website = website_match.group(0)
            
        return contact_info
        
    def _extract_legal_entity_type(self, text: str) -> Optional[str]:
        """Extract legal entity type from text."""
        entity_patterns = {
            'corporation': r'\b(?:Corporation|Corp\.?|Incorporated|Inc\.?)\b',
            'llc': r'\b(?:LLC|L\.L\.C\.?|Limited Liability Company)\b',
            'partnership': r'\b(?:Partnership|LLP|L\.L\.P\.?)\b',
            'sole_proprietorship': r'\b(?:Sole Proprietorship|DBA|d/b/a)\b',
            'government': r'\b(?:Government|Gov|Municipality|County|State|Federal)\b',
            'nonprofit': r'\b(?:Non-profit|Nonprofit|501\(c\))\b'
        }
        
        text_lower = text.lower()
        for entity_type, pattern in entity_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return entity_type
                
        return None
        
    def _determine_party_type(self, name: str) -> str:
        """Determine if party is individual, company, government, etc."""
        name_lower = name.lower()
        
        # Company indicators
        company_suffixes = ['inc', 'corp', 'llc', 'ltd', 'company', 'corporation', 'limited']
        if any(suffix in name_lower for suffix in company_suffixes):
            return "company"
            
        # Government indicators
        gov_indicators = ['government', 'department', 'agency', 'county', 'state', 'city', 'municipality']
        if any(indicator in name_lower for indicator in gov_indicators):
            return "government"
            
        # Individual name patterns (simplified)
        if len(name.split()) == 2 and all(word.istitle() for word in name.split()):
            return "individual"
            
        # Default to organization
        return "organization"
        
    def _determine_role_from_context(self, context: str) -> str:
        """Determine party role from context."""
        context_lower = context.lower()
        
        role_indicators = {
            'contractor': ['contractor', 'service provider', 'vendor'],
            'client': ['client', 'customer', 'buyer', 'purchaser'],
            'employer': ['employer', 'company'],
            'employee': ['employee', 'worker'],
            'lessor': ['lessor', 'landlord', 'owner'],
            'lessee': ['lessee', 'tenant', 'renter'],
            'licensor': ['licensor', 'grantor'],
            'licensee': ['licensee', 'grantee']
        }
        
        for role, indicators in role_indicators.items():
            if any(indicator in context_lower for indicator in indicators):
                return role
                
        return "party"
        
    def _is_valid_party_name(self, name: str) -> bool:
        """Validate if text represents a valid party name."""
        if not name or len(name.strip()) < 3:
            return False
            
        name = name.strip()
        
        # Exclude common false positives
        false_positives = [
            'signature', 'date', 'name', 'title', 'address', 'phone', 'email',
            'page', 'section', 'clause', 'exhibit', 'attachment', 'schedule',
            'whereas', 'therefore', 'hereby', 'witness', 'whereof'
        ]
        
        if name.lower() in false_positives:
            return False
            
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
            
        # Exclude pure numbers or dates
        if re.match(r'^\d+$', name) or re.match(r'^\d+/\d+/\d+$', name):
            return False
            
        return True
        
    def _consolidate_parties(self, parties: List[ContractParty]) -> List[ContractParty]:
        """Consolidate duplicate parties."""
        consolidated = {}
        
        for party in parties:
            # Normalize name for comparison
            normalized_name = self._normalize_name(party.name)
            
            if normalized_name in consolidated:
                # Merge with existing party
                existing = consolidated[normalized_name]
                
                # Keep higher confidence party as base
                if party.confidence > existing.confidence:
                    consolidated[normalized_name] = party
                    # Add existing as alias
                    if existing.name not in party.aliases:
                        party.aliases.append(existing.name)
                else:
                    # Add current as alias to existing
                    if party.name not in existing.aliases:
                        existing.aliases.append(party.name)
                        
                # Merge contact info
                self._merge_contact_info(consolidated[normalized_name], party)
                
            else:
                consolidated[normalized_name] = party
                
        return list(consolidated.values())
        
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        # Remove common business suffixes for comparison
        normalized = re.sub(r'\b(?:Inc|Corp|LLC|Ltd|Company|Corporation|Limited)\.?\b', '', name, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized.lower()
        
    def _merge_contact_info(self, target: ContractParty, source: ContractParty):
        """Merge contact information from source to target."""
        if not target.contact_info.email and source.contact_info.email:
            target.contact_info.email = source.contact_info.email
        if not target.contact_info.phone and source.contact_info.phone:
            target.contact_info.phone = source.contact_info.phone
        if not target.contact_info.address and source.contact_info.address:
            target.contact_info.address = source.contact_info.address
        if not target.contact_info.website and source.contact_info.website:
            target.contact_info.website = source.contact_info.website
            
    def _enhance_party_information(self, parties: List[ContractParty], 
                                  document_text: str) -> List[ContractParty]:
        """Enhance party information with additional context."""
        for party in parties:
            # Look for additional mentions of the party in the document
            party_mentions = self._find_party_mentions(party.name, document_text)
            
            # Extract additional context from mentions
            for mention in party_mentions:
                # Look for role clarifications
                role_context = self._extract_role_context(mention)
                if role_context and party.role == "party":
                    party.role = role_context
                    
                # Look for additional contact info
                mention_contact = self._extract_contact_info(mention)
                self._merge_contact_info(party, ContractParty(
                    name="", role="", party_type="", contact_info=mention_contact
                ))
                
        return parties
        
    def _find_party_mentions(self, party_name: str, text: str) -> List[str]:
        """Find all mentions of a party in the document."""
        mentions = []
        
        # Create a pattern that matches the party name with some context
        normalized_name = re.escape(party_name)
        pattern = rf'.{{0,100}}{normalized_name}.{{0,100}}'
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            mentions.append(match.group(0))
            
        return mentions
        
    def _extract_role_context(self, text: str) -> Optional[str]:
        """Extract role information from context text."""
        role_patterns = {
            'contractor': r'(?:as|acting as|serving as)?\s*(?:the\s+)?contractor',
            'client': r'(?:as|acting as|serving as)?\s*(?:the\s+)?client',
            'vendor': r'(?:as|acting as|serving as)?\s*(?:the\s+)?vendor',
            'employer': r'(?:as|acting as|serving as)?\s*(?:the\s+)?employer',
            'lessor': r'(?:as|acting as|serving as)?\s*(?:the\s+)?lessor',
            'lessee': r'(?:as|acting as|serving as)?\s*(?:the\s+)?lessee'
        }
        
        text_lower = text.lower()
        for role, pattern in role_patterns.items():
            if re.search(pattern, text_lower):
                return role
                
        return None
        
    def _validate_and_score_parties(self, parties: List[ContractParty], 
                                   document_text: str) -> List[ContractParty]:
        """Validate and score party confidence."""
        validated_parties = []
        
        for party in parties:
            # Calculate confidence score based on multiple factors
            confidence_factors = {
                'name_validity': 0.3 if self._is_valid_party_name(party.name) else 0.0,
                'contact_info': 0.2 if self._has_contact_info(party) else 0.0,
                'role_clarity': 0.2 if party.role != "party" else 0.1,
                'multiple_mentions': 0.2 if self._count_mentions(party.name, document_text) > 1 else 0.0,
                'legal_entity': 0.1 if party.legal_entity_type else 0.0
            }
            
            # Calculate final confidence
            final_confidence = sum(confidence_factors.values()) + (party.confidence * 0.3)
            party.confidence = min(1.0, final_confidence)
            
            # Only include parties with reasonable confidence
            if party.confidence >= 0.3:
                validated_parties.append(party)
                
        # Sort by confidence
        validated_parties.sort(key=lambda p: p.confidence, reverse=True)
        
        return validated_parties
        
    def _has_contact_info(self, party: ContractParty) -> bool:
        """Check if party has any contact information."""
        return any([
            party.contact_info.email,
            party.contact_info.phone,
            party.contact_info.address,
            party.contact_info.website
        ])
        
    def _count_mentions(self, party_name: str, text: str) -> int:
        """Count mentions of party name in document."""
        return len(re.findall(re.escape(party_name), text, re.IGNORECASE))
        
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load entity recognition patterns."""
        return {
            'person': [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
                r'\b(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
            ],
            'company': [
                r'\b[A-Z][a-zA-Z\s&]+(?:Inc|Corp|LLC|Ltd|Company|Corporation)\.?\b',
                r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\s+(?:Inc|Corp|LLC|Ltd)\b'
            ]
        }
        
    def _load_role_patterns(self) -> Dict[str, List[str]]:
        """Load role identification patterns."""
        return {
            'contractor': ['contractor', 'service provider', 'vendor', 'supplier'],
            'client': ['client', 'customer', 'buyer', 'purchaser'],
            'employer': ['employer', 'company'],
            'employee': ['employee', 'worker', 'staff']
        }
        
    def _load_contact_patterns(self) -> Dict[str, str]:
        """Load contact information patterns."""
        return {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)',
            'website': r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|net|edu|gov)'
        }
        
    def _load_legal_entity_patterns(self) -> Dict[str, str]:
        """Load legal entity type patterns."""
        return {
            'corporation': r'\b(?:Corporation|Corp\.?|Incorporated|Inc\.?)\b',
            'llc': r'\b(?:LLC|L\.L\.C\.?|Limited Liability Company)\b',
            'partnership': r'\b(?:Partnership|LLP|L\.L\.P\.?)\b',
            'government': r'\b(?:Government|Gov|Municipality|County|State)\b'
        }