"""ClauseExtractor: Identifies and labels contract clauses by type.

Clause taxonomy:
  - payment         (payment terms, invoices, fees, pricing)
  - liability       (limitation of liability, indemnification, warranties)
  - termination     (termination for cause/convenience, notice periods)
  - data_protection (GDPR, data processing, privacy, personal data)
  - ip              (intellectual property, ownership, license, copyright)
  - confidentiality (NDA, non-disclosure, confidential information)

Uses regex pattern matching + heuristic paragraph scoring.
No external ML dependencies required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

CLAUSE_TYPES = [
    "payment",
    "liability",
    "termination",
    "data_protection",
    "ip",
    "confidentiality",
]


@dataclass
class ExtractedClause:
    """A labeled clause extracted from contract text."""

    clause_type: str
    text: str
    start_char: int
    end_char: int
    confidence: float  # 0.0 – 1.0
    matched_keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Patterns per clause type
# ---------------------------------------------------------------------------

_CLAUSE_PATTERNS: dict[str, list[str]] = {
    "payment": [
        r"\bpayment\b",
        r"\binvoice[sd]?\b",
        r"\bfee[s]?\b",
        r"\bpric(?:e|ing)\b",
        r"\bremuneration\b",
        r"\bcompensation\b",
        r"\bdue date\b",
        r"\bnet \d+\b",
        r"\binstalment[s]?\b",
        r"\binstallment[s]?\b",
        r"\bpayable\b",
        r"\boverdue\b",
        r"\bpurchase price\b",
        r"\bcontract price\b",
        r"\bservice fee\b",
    ],
    "liability": [
        r"\bliabilit(?:y|ies)\b",
        r"\bindemnif(?:y|ication|ied)\b",
        r"\blimit(?:ation)? of liability\b",
        r"\bwarrant(?:y|ies|ied)\b",
        r"\bdisclaimer\b",
        r"\bdamages\b",
        r"\bconsequential\b",
        r"\bpunitive\b",
        r"\bgross negligence\b",
        r"\bdefend.*harmless\b",
        r"\bhold harmless\b",
        r"\bexclusion[s]?\b",
        r"\bwillful misconduct\b",
    ],
    "termination": [
        r"\btermination\b",
        r"\bterminate[sd]?\b",
        r"\bterm(?:inate)? for cause\b",
        r"\bterm(?:inate)? for convenience\b",
        r"\bnotice period\b",
        r"\bnotice of termination\b",
        r"\bexpir(?:y|ation)\b",
        r"\bcancel(?:lation)?\b",
        r"\bwind(?:ing)? down\b",
        r"\bpost-termination\b",
        r"\beffect of termination\b",
        r"\bcure period\b",
        r"\bbreach.*cure\b",
    ],
    "data_protection": [
        r"\bpersonal data\b",
        r"\bdata protection\b",
        r"\bGDPR\b",
        r"\bdata processing\b",
        r"\bdata processor\b",
        r"\bdata controller\b",
        r"\bprivacy\b",
        r"\bdata subject[s]?\b",
        r"\bcookies?\b",
        r"\bdata breach\b",
        r"\bDPA\b",  # Data Processing Agreement
        r"\bCCPA\b",
        r"\banonymis(?:ation|ation)\b",
        r"\banonymiz(?:ation)?\b",
        r"\bpseudonymis(?:ation)?\b",
        r"\bpseudonymiz(?:ation)?\b",
        r"\bdata retention\b",
        r"\bdata transfer\b",
        r"\bstandard contractual clauses\b",
        r"\bSCC[s]?\b",
    ],
    "ip": [
        r"\bintellectual property\b",
        r"\bcopyright[s]?\b",
        r"\btrademark[s]?\b",
        r"\bpatent[s]?\b",
        r"\blicense[ds]?\b",
        r"\blicens(?:e|or|ee)\b",
        r"\btrade secret[s]?\b",
        r"\bwork for hire\b",
        r"\bworks? made for hire\b",
        r"\bIP rights\b",
        r"\bproprietary\b",
        r"\bownership of.*work[s]?\b",
        r"\bassignment of.*rights\b",
        r"\bmoral rights\b",
    ],
    "confidentiality": [
        r"\bconfidential(?:ity|information)?\b",
        r"\bnon-disclosure\b",
        r"\bNDA\b",
        r"\bproprietary information\b",
        r"\btrade secret[s]?\b",
        r"\bdisclos(?:ure|ed|ing)\b",
        r"\bnon-disparagement\b",
        r"\bsecret(?:s|ive)?\b",
        r"\bunder seal\b",
        r"\bconfidential treatment\b",
        r"\breceiving party\b",
        r"\bdisclosing party\b",
        r"\bobligations of confidentiality\b",
    ],
}

# Compile all patterns once
_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {
    clause_type: [re.compile(p, re.IGNORECASE) for p in patterns]
    for clause_type, patterns in _CLAUSE_PATTERNS.items()
}

# Section heading patterns that signal a clause start
_HEADING_RE = re.compile(
    r"^(?:\d+\.?\s+|[A-Z]\.?\s+)?([A-Z][A-Z\s]{3,50})\s*$",
    re.MULTILINE,
)

# Common heading keywords that map to clause types
_HEADING_KEYWORDS: dict[str, list[str]] = {
    "payment": ["PAYMENT", "FEES", "PRICING", "INVOICE", "COMPENSATION", "REMUNERATION"],
    "liability": ["LIABILITY", "INDEMNIF", "WARRANTY", "WARRANTIES", "DISCLAIMER"],
    "termination": ["TERMINATION", "CANCELLATION", "EXPIRY", "EXPIRATION"],
    "data_protection": ["DATA PROTECTION", "PRIVACY", "GDPR", "DATA PROCESSING", "DATA SECURITY"],
    "ip": ["INTELLECTUAL PROPERTY", "COPYRIGHT", "LICENSE", "OWNERSHIP", "IP"],
    "confidentiality": ["CONFIDENTIAL", "NON-DISCLOSURE", "NDA", "PROPRIETARY"],
}


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class ClauseExtractor:
    """Identifies and labels contract clauses by type using pattern matching.

    Algorithm:
    1. Split contract text into candidate paragraphs / sections
    2. For each paragraph, score against all clause type patterns
    3. Assign the highest-scoring type (if above threshold)
    4. Also detect section headings to boost confidence
    """

    def __init__(self, min_length: int = 30, score_threshold: float = 0.1):
        """
        Args:
            min_length: Minimum character length for a paragraph to be considered.
            score_threshold: Minimum pattern match density to assign a clause type.
        """
        self.min_length = min_length
        self.score_threshold = score_threshold

    def extract(self, text: str) -> list[ExtractedClause]:
        """Extract and label clauses from contract text.

        Args:
            text: Raw contract text.

        Returns:
            List of ExtractedClause objects.
        """
        segments = self._segment(text)
        clauses: list[ExtractedClause] = []

        for seg_text, start, end in segments:
            clause = self._classify_segment(seg_text, start, end)
            if clause is not None:
                clauses.append(clause)

        return clauses

    def _segment(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into segments at paragraph/section boundaries.

        Returns list of (segment_text, start_char, end_char).
        """
        segments: list[tuple[str, int, int]] = []
        # Split on double newlines (paragraph breaks)
        pattern = re.compile(r"\n\s*\n")
        pos = 0
        for m in pattern.finditer(text):
            seg = text[pos:m.start()].strip()
            if len(seg) >= self.min_length:
                # Find actual positions in original text
                seg_start = text.index(seg, pos) if seg in text[pos:] else pos
                seg_end = seg_start + len(seg)
                segments.append((seg, seg_start, seg_end))
            pos = m.end()

        # Capture tail
        tail = text[pos:].strip()
        if len(tail) >= self.min_length:
            tail_start = text.index(tail, pos) if tail in text[pos:] else pos
            tail_end = tail_start + len(tail)
            segments.append((tail, tail_start, tail_end))

        # If no paragraphs found, treat whole text as one segment
        if not segments and len(text.strip()) >= self.min_length:
            stripped = text.strip()
            segments.append((stripped, 0, len(stripped)))

        return segments

    def _classify_segment(
        self, text: str, start: int, end: int
    ) -> Optional[ExtractedClause]:
        """Score a text segment against all clause types and return best match."""
        scores: dict[str, float] = {}
        matched_kws: dict[str, list[str]] = {}

        words_in_seg = max(len(text.split()), 1)

        for clause_type, patterns in _COMPILED_PATTERNS.items():
            hits = []
            for pattern in patterns:
                found = pattern.findall(text)
                if found:
                    hits.extend(found)

            # Score = hit count normalised by segment length (density)
            density = len(hits) / words_in_seg
            scores[clause_type] = density
            matched_kws[clause_type] = list(dict.fromkeys(h if isinstance(h, str) else h[0] for h in hits))

        # Heading boost: check first ~100 chars for heading keywords
        heading_text = text[:100].upper()
        for clause_type, keywords in _HEADING_KEYWORDS.items():
            for kw in keywords:
                if kw in heading_text:
                    scores[clause_type] = scores.get(clause_type, 0) + 0.5
                    break

        if not scores:
            return None

        best_type = max(scores, key=lambda t: scores[t])
        best_score = scores[best_type]

        if best_score < self.score_threshold:
            return None

        # Confidence: sigmoid-like mapping of score into 0-1
        confidence = min(1.0, best_score / (best_score + 0.3))

        return ExtractedClause(
            clause_type=best_type,
            text=text,
            start_char=start,
            end_char=end,
            confidence=round(confidence, 3),
            matched_keywords=matched_kws.get(best_type, [])[:10],
        )
