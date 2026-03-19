"""EntityExtractor: Extracts named entities from contract clause text.

Entity taxonomy:
  - party          (contracting parties, company names)
  - date           (contract dates, deadlines, notice periods)
  - amount         (monetary values, prices, fees)
  - jurisdiction   (governing law, courts, countries)
  - data_category  (types of personal data in data protection clauses)

Uses regex + keyword heuristics. No ML dependencies required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .clause_extractor import ExtractedClause


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

ENTITY_TYPES = [
    "party",
    "date",
    "amount",
    "jurisdiction",
    "data_category",
]


@dataclass
class ExtractedEntity:
    """A named entity extracted from a clause."""

    entity_type: str
    value: str
    normalized: Optional[str] = None  # e.g. ISO date, ISO currency+amount
    clause_type: Optional[str] = None  # which clause this came from
    context: Optional[str] = None      # surrounding text snippet


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Party patterns — company names, "hereinafter referred to as X"
_PARTY_PATTERNS = [
    # "ABC Corp." / "XYZ Ltd." / "Foo Inc." / "Bar LLC"
    re.compile(
        r"\b([A-Z][A-Za-z0-9&',\.\-\s]{2,60}?(?:Corp(?:oration)?|Inc(?:orporated)?|Ltd|LLC|LLP|GmbH|AG|BV|SAS|SA|SRL|PLC|LP|Co\.?))\b"
    ),
    # "referred to as 'Contractor'" / "hereinafter 'Client'"
    re.compile(
        r"""(?:referred to as|hereinafter|collectively[,\s]+(?:the|as)?)\s+["\']([A-Z][A-Za-z\s]+)["\']""",
        re.IGNORECASE,
    ),
    # "the Licensor" / "the Licensee" / "the Customer" / "the Supplier"
    re.compile(
        r"""\b(the\s+(?:Licensor|Licensee|Customer|Supplier|Vendor|Buyer|Seller|Contractor|Client|Company|Party|Processor|Controller|Employer|Employee))\b""",
        re.IGNORECASE,
    ),
]

# Date patterns
_DATE_PATTERNS = [
    # ISO: 2024-01-15
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    # US: January 15, 2024 / Jan 15, 2024
    re.compile(
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    ),
    # EU: 15 January 2024 / 15 Jan 2024
    re.compile(
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4})\b",
        re.IGNORECASE,
    ),
    # Relative durations: "30 days", "6 months", "2 years"
    re.compile(r"\b(\d+\s+(?:calendar\s+)?(?:day|week|month|year)s?)\b", re.IGNORECASE),
    # Deadline phrases: "within 14 days of"
    re.compile(r"\b(within\s+\d+\s+(?:day|week|month|year)s?)\b", re.IGNORECASE),
]

# Amount patterns
_AMOUNT_PATTERNS = [
    # $1,234.56 / €500 / £1,000,000
    re.compile(r"([$€£¥₹]\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?)\b", re.IGNORECASE),
    # USD 1,234.56 / EUR 500.00
    re.compile(
        r"\b((?:USD|EUR|GBP|JPY|CAD|AUD|CHF|CNY)\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?)\b",
        re.IGNORECASE,
    ),
    # "1,234.56 USD" / "500.00 EUR"
    re.compile(
        r"\b([\d,]+(?:\.\d{1,2})?\s+(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|CNY))\b",
        re.IGNORECASE,
    ),
    # Percentage: 5% / 10 percent
    re.compile(r"\b(\d+(?:\.\d+)?\s*%(?:\s+per\s+annum)?)", re.IGNORECASE),
    re.compile(r"\b(\d+(?:\.\d+)?\s+percent(?:\s+per\s+annum)?)\b", re.IGNORECASE),
]

# Jurisdiction patterns
_JURISDICTION_PATTERNS = [
    # "governed by the laws of England" / "under the laws of California"
    re.compile(
        r"(?:governed\s+by|subject\s+to|under)\s+(?:the\s+)?laws?\s+of\s+([A-Z][A-Za-z\s,]{2,50}?)(?:[,;\.]|$)",
        re.IGNORECASE,
    ),
    # "jurisdiction of the courts of X"
    re.compile(
        r"(?:exclusive\s+)?jurisdiction\s+of\s+(?:the\s+)?courts?\s+of\s+([A-Z][A-Za-z\s,]{2,50}?)(?:[,;\.]|$)",
        re.IGNORECASE,
    ),
    # "courts of New York" / "courts of England and Wales"
    re.compile(
        r"\bcourts?\s+of\s+([A-Z][A-Za-z\s,&]{2,50}?)(?:[,;\.]|$)",
        re.IGNORECASE,
    ),
    # Common jurisdiction names (standalone)
    re.compile(
        r"\b(England(?:\s+and\s+Wales)?|Scotland|Ireland|Germany|France|Netherlands|"
        r"United\s+States(?:\s+of\s+America)?|California|New\s+York|Texas|Delaware|"
        r"European\s+Union|Singapore|Hong\s+Kong|Switzerland|Australia)\b",
        re.IGNORECASE,
    ),
]

# Data category patterns (for data protection clauses)
_DATA_CATEGORY_PATTERNS = [
    re.compile(
        r"\b(personal\s+data|sensitive\s+(?:personal\s+)?data|special\s+categories?\s+of\s+(?:personal\s+)?data|"
        r"health\s+data|biometric\s+data|genetic\s+data|financial\s+data|"
        r"contact\s+(?:data|details|information)|location\s+data|behavioral\s+data|"
        r"usage\s+data|IP\s+address(?:es)?|device\s+(?:data|identifiers?)|"
        r"name[s]?\s+and\s+address(?:es)?|email\s+address(?:es)?|"
        r"passport\s+(?:number[s]?|data)|identification\s+(?:number[s]?|data)|"
        r"date[s]?\s+of\s+birth|payment\s+(?:card\s+)?(?:data|information)|"
        r"racial\s+or\s+ethnic\s+origin|political\s+opinion[s]?|"
        r"religious\s+(?:or\s+philosophical\s+)?belief[s]?|trade\s+union\s+membership|"
        r"criminal\s+conviction[s]?)\b",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Entity extractor
# ---------------------------------------------------------------------------

class EntityExtractor:
    """Extracts named entities from contract clause text.

    Operates on individual ExtractedClause objects or raw text strings.
    Uses pure-regex approach — no external NLP dependencies.
    """

    def extract_from_clause(self, clause: ExtractedClause) -> list[ExtractedEntity]:
        """Extract entities from a single clause.

        Args:
            clause: An ExtractedClause from ClauseExtractor.

        Returns:
            List of ExtractedEntity objects.
        """
        return self.extract_from_text(clause.text, clause_type=clause.clause_type)

    def extract_from_text(
        self, text: str, clause_type: Optional[str] = None
    ) -> list[ExtractedEntity]:
        """Extract entities from raw text.

        Args:
            text: Contract text.
            clause_type: Optional hint about the clause type (enables targeted extraction).

        Returns:
            List of ExtractedEntity objects.
        """
        entities: list[ExtractedEntity] = []

        entities.extend(self._extract_parties(text, clause_type))
        entities.extend(self._extract_dates(text, clause_type))
        entities.extend(self._extract_amounts(text, clause_type))
        entities.extend(self._extract_jurisdictions(text, clause_type))

        # Data categories only relevant for data_protection clauses (or unconstrained)
        if clause_type is None or clause_type == "data_protection":
            entities.extend(self._extract_data_categories(text, clause_type))

        return self._deduplicate(entities)

    def extract_from_clauses(
        self, clauses: list[ExtractedClause]
    ) -> list[ExtractedEntity]:
        """Extract entities from a list of clauses.

        Args:
            clauses: Output of ClauseExtractor.extract().

        Returns:
            All entities across all clauses.
        """
        all_entities: list[ExtractedEntity] = []
        for clause in clauses:
            all_entities.extend(self.extract_from_clause(clause))
        return all_entities

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    def _extract_parties(self, text: str, clause_type: Optional[str]) -> list[ExtractedEntity]:
        entities = []
        seen: set[str] = set()
        for pattern in _PARTY_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(1).strip()
                val_key = val.lower()
                if val_key not in seen and len(val) >= 3:
                    seen.add(val_key)
                    ctx = self._context(text, m.start(), m.end())
                    entities.append(
                        ExtractedEntity(
                            entity_type="party",
                            value=val,
                            clause_type=clause_type,
                            context=ctx,
                        )
                    )
        return entities

    def _extract_dates(self, text: str, clause_type: Optional[str]) -> list[ExtractedEntity]:
        entities = []
        seen: set[str] = set()
        for pattern in _DATE_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(1).strip()
                val_key = val.lower()
                if val_key not in seen:
                    seen.add(val_key)
                    ctx = self._context(text, m.start(), m.end())
                    entities.append(
                        ExtractedEntity(
                            entity_type="date",
                            value=val,
                            clause_type=clause_type,
                            context=ctx,
                        )
                    )
        return entities

    def _extract_amounts(self, text: str, clause_type: Optional[str]) -> list[ExtractedEntity]:
        entities = []
        seen: set[str] = set()
        for pattern in _AMOUNT_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(1).strip()
                val_key = val.lower()
                if val_key not in seen:
                    seen.add(val_key)
                    ctx = self._context(text, m.start(), m.end())
                    entities.append(
                        ExtractedEntity(
                            entity_type="amount",
                            value=val,
                            clause_type=clause_type,
                            context=ctx,
                        )
                    )
        return entities

    def _extract_jurisdictions(self, text: str, clause_type: Optional[str]) -> list[ExtractedEntity]:
        entities = []
        seen: set[str] = set()
        for pattern in _JURISDICTION_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(1).strip().rstrip(".,;")
                val_key = val.lower()
                if val_key not in seen and len(val) >= 3:
                    seen.add(val_key)
                    ctx = self._context(text, m.start(), m.end())
                    entities.append(
                        ExtractedEntity(
                            entity_type="jurisdiction",
                            value=val,
                            clause_type=clause_type,
                            context=ctx,
                        )
                    )
        return entities

    def _extract_data_categories(self, text: str, clause_type: Optional[str]) -> list[ExtractedEntity]:
        entities = []
        seen: set[str] = set()
        for pattern in _DATA_CATEGORY_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(1).strip()
                val_key = val.lower()
                if val_key not in seen:
                    seen.add(val_key)
                    ctx = self._context(text, m.start(), m.end())
                    entities.append(
                        ExtractedEntity(
                            entity_type="data_category",
                            value=val,
                            clause_type=clause_type,
                            context=ctx,
                        )
                    )
        return entities

    @staticmethod
    def _context(text: str, start: int, end: int, window: int = 60) -> str:
        """Return surrounding text context for a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        snippet = text[ctx_start:ctx_end].replace("\n", " ").strip()
        if ctx_start > 0:
            snippet = "…" + snippet
        if ctx_end < len(text):
            snippet = snippet + "…"
        return snippet

    @staticmethod
    def _deduplicate(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
        """Remove duplicate entities (same type + value)."""
        seen: set[tuple] = set()
        result: list[ExtractedEntity] = []
        for e in entities:
            key = (e.entity_type, e.value.lower())
            if key not in seen:
                seen.add(key)
                result.append(e)
        return result
