"""Clause detection via OCR and simple heuristics."""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

from .config import get_config

if TYPE_CHECKING:
    from PIL import Image

    from .document import Document

logger = logging.getLogger(__name__)

# Module-level OCR cache
_ocr_cache: dict[str, str] = {}


@dataclass
class Clause:
    """Represents an extracted clause from a document."""

    type: str
    text: str
    page: int
    coordinates: list[int] | None = None
    id: str = ""
    confidence: float = 0.0
    key_terms: list[str] = field(default_factory=list)


def _ocr_image(image: Image.Image) -> str:
    """Extract text from an image using Tesseract OCR with caching."""
    # Create a hash of the image for caching
    image_hash = _hash_image(image)

    # Check cache first
    if image_hash in _ocr_cache:
        logger.debug("OCR cache hit for image hash: %s", image_hash[:8])
        _record_cache_hit()
        return _ocr_cache[image_hash]

    # Perform OCR and cache result
    logger.debug("OCR cache miss, performing OCR for hash: %s", image_hash[:8])
    _record_cache_miss()

    try:
        import pytesseract
    except ImportError as exc:
        msg = "pytesseract is required for OCR operations"
        raise ImportError(msg) from exc

    text = pytesseract.image_to_string(image)

    # Cache the result (with size limit to prevent unbounded growth)
    config = get_config()
    if len(_ocr_cache) < config.ocr.cache_size_limit:
        _ocr_cache[image_hash] = text

    return text


def _record_cache_hit():
    """Record OCR cache hit metric."""
    try:
        from .metrics import record_ocr_cache_hit

        record_ocr_cache_hit()
    except ImportError:
        # Metrics module not available, ignore
        pass


def _record_cache_miss():
    """Record OCR cache miss metric."""
    try:
        from .metrics import record_ocr_cache_miss

        record_ocr_cache_miss()
    except ImportError:
        # Metrics module not available, ignore
        pass


def _hash_image(image: Image.Image) -> str:
    """Create a hash of the image for use as a cache key."""
    # Convert image to bytes and hash with secure algorithm
    image_bytes = image.tobytes()
    return hashlib.sha256(image_bytes).hexdigest()


def clear_ocr_cache() -> None:
    """Clear the OCR cache. Useful for testing and memory management."""
    global _ocr_cache
    _ocr_cache.clear()
    logger.debug("OCR cache cleared")


def get_ocr_cache_stats() -> dict[str, int]:
    """Get OCR cache statistics."""
    return {
        "cache_size": len(_ocr_cache),
        "max_size": 100,
    }


DEFAULT_KEYWORDS: dict[str, list[str]] = {
    "confidentiality": ["confidential"],
    "termination": ["termination", "terminate"],
    "payment_terms": ["payment", "compensation"],
    "liability": ["liability"],
    "governing_law": ["governing law", "jurisdiction"],
    "dispute_resolution": ["dispute", "arbitration"],
}

# Cache for compiled regex patterns
_pattern_cache: dict[str, re.Pattern] = {}


def detect_clauses(
    document,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
) -> list[Clause]:
    """Detect clauses within a loaded :class:`Document` or document stream.

    Uses optimized clause detection with combined regex patterns for better performance.

    Parameters
    ----------
    document:
        Document produced by :func:`load_document` or generator from :func:`stream_document`.
    keywords:
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    # Check if document is a generator (from stream_document) or Document object
    if hasattr(document, "pages"):
        # Standard Document object
        return _detect_clauses_optimized(document, keywords=keywords)
    # Generator from stream_document
    return _detect_clauses_streaming(document, keywords=keywords)


def _detect_clauses_legacy(
    document: Document,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
) -> list[Clause]:
    """Legacy clause detection implementation (for reference/fallback).

    This is the original implementation that searches for each keyword individually.
    Kept for compatibility and as a fallback if needed.

    Parameters
    ----------
    document:
        Document produced by :func:`load_document`.
    keywords:
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """

    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    logger.debug("Detecting clauses in %d pages (legacy)", len(document.pages))

    clauses: list[Clause] = []
    for page in document.pages:
        text = _ocr_image(page.image)
        lower_text = text.lower()
        for clause_type, words in keywords.items():
            for word in words:
                if word.lower() in lower_text:
                    # capture surrounding text for context
                    pattern = re.compile(
                        rf"(.{{0,{get_config().ocr.context_window_size}}}{re.escape(word)}.{{0,{get_config().ocr.context_window_size}}})",
                        re.IGNORECASE,
                    )
                    match = pattern.search(text)
                    snippet = match.group(1).strip() if match else word

                    # Generate unique ID for this clause
                    clause_id = f"clause_{uuid.uuid4().hex[:8]}"

                    # Calculate confidence score
                    config = get_config()
                    confidence = _calculate_clause_confidence_score(
                        snippet, word, config
                    )

                    # Extract key terms (the matched keyword and surrounding relevant terms)
                    key_terms = _extract_key_terms(snippet, word)

                    # For now, use placeholder coordinates (would need OCR layout analysis for real coords)
                    placeholder_coords = [
                        50,
                        100 + len(clauses) * 50,
                        550,
                        150 + len(clauses) * 50,
                    ]

                    clause = Clause(
                        type=clause_type,
                        text=snippet,
                        page=page.number,
                        coordinates=placeholder_coords,
                        id=clause_id,
                        confidence=confidence,
                        key_terms=key_terms,
                    )
                    clauses.append(clause)
                    logger.info(
                        "Detected %s clause on page %d (legacy)",
                        clause_type,
                        page.number,
                    )
                    break
    return clauses


def _detect_clauses_optimized(
    document: Document,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
) -> list[Clause]:
    """Optimized clause detection using combined regex patterns.

    This optimized version builds a single combined regex pattern to find all
    keywords in one pass, rather than searching for each keyword individually.

    Parameters
    ----------
    document : Document
        The document to search for clauses in.
    keywords : dict[str, list[str]] | None, optional
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    logger.debug("Detecting clauses in %d pages (optimized)", len(document.pages))

    # Build combined pattern for all keywords
    combined_pattern = _get_cached_pattern(keywords)
    keyword_to_type = _build_keyword_mapping(keywords)

    clauses: list[Clause] = []
    for page in document.pages:
        text = _ocr_image(page.image)

        # Find all matches in one pass
        for match in combined_pattern.finditer(text):
            matched_text = match.group().lower()

            # Determine which clause type this keyword belongs to
            clause_type = keyword_to_type.get(matched_text)
            if clause_type:
                # Extract surrounding context
                config = get_config()
                context_size = config.ocr.context_window_size
                start = max(0, match.start() - context_size)
                end = min(len(text), match.end() + context_size)
                snippet = text[start:end].strip()

                # Generate unique ID for this clause
                clause_id = f"clause_{uuid.uuid4().hex[:8]}"

                # Calculate confidence score
                config = get_config()
                confidence = _calculate_clause_confidence_score(
                    snippet, matched_text, config
                )

                # Extract key terms (the matched keyword and surrounding relevant terms)
                key_terms = _extract_key_terms(snippet, matched_text)

                # For now, use placeholder coordinates (would need OCR layout analysis for real coords)
                placeholder_coords = [
                    50,
                    100 + len(clauses) * 50,
                    550,
                    150 + len(clauses) * 50,
                ]

                clause = Clause(
                    type=clause_type,
                    text=snippet,
                    page=page.number,
                    coordinates=placeholder_coords,
                    id=clause_id,
                    confidence=confidence,
                    key_terms=key_terms,
                )
                clauses.append(clause)
                logger.info(
                    "Detected %s clause on page %d (optimized)",
                    clause_type,
                    page.number,
                )

    return clauses


def _get_cached_pattern(keywords: dict[str, Iterable[str]]) -> re.Pattern:
    """Get a cached compiled regex pattern for the given keywords."""
    # Create a cache key based on the keywords
    cache_key = _create_cache_key(keywords)

    if cache_key not in _pattern_cache:
        _pattern_cache[cache_key] = _build_combined_pattern(keywords)
        logger.debug(
            "Compiled and cached regex pattern for %d clause types", len(keywords)
        )
    else:
        logger.debug("Using cached regex pattern")

    return _pattern_cache[cache_key]


def _create_cache_key(keywords: dict[str, Iterable[str]]) -> str:
    """Create a cache key for the keywords dictionary."""
    # Sort by clause type for consistent key
    items = []
    for clause_type in sorted(keywords.keys()):
        words = sorted(keywords[clause_type])
        items.append(f"{clause_type}:{','.join(words)}")
    return "|".join(items)


def _build_combined_pattern(keywords: dict[str, Iterable[str]]) -> re.Pattern:
    """Build a single regex pattern that matches all keywords."""
    if not keywords:
        # Return a pattern that matches nothing
        return re.compile(r"(?!.*)", re.IGNORECASE)

    # Collect all unique keywords
    all_keywords = []
    for words in keywords.values():
        for word in words:
            if word not in all_keywords:
                all_keywords.append(word)

    # Sort by length (longest first) to avoid partial matches
    all_keywords.sort(key=len, reverse=True)

    # Build pattern that allows partial word matches (like legacy version)
    # Use word boundaries only at the start to avoid matching within other words
    escaped_keywords = [re.escape(word) for word in all_keywords]
    pattern_str = r"\b(" + "|".join(escaped_keywords) + r")"

    return re.compile(pattern_str, re.IGNORECASE)


def _build_keyword_mapping(keywords: dict[str, Iterable[str]]) -> dict[str, str]:
    """Build a mapping from keyword to clause type."""
    mapping = {}
    for clause_type, words in keywords.items():
        for word in words:
            mapping[word.lower()] = clause_type
    return mapping


def clear_pattern_cache() -> None:
    """Clear the regex pattern cache. Useful for testing and memory management."""
    global _pattern_cache
    _pattern_cache.clear()
    logger.debug("Regex pattern cache cleared")


def _calculate_clause_confidence_score(
    text: str, matched_keyword: str, config
) -> float:
    """Calculate confidence score for a detected clause based on text length and keyword match quality.

    Args:
        text: The extracted clause text
        matched_keyword: The keyword that triggered this clause detection
        config: Configuration object with scoring parameters

    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Start with base confidence
    confidence = config.extraction.base_confidence_score

    # Add bonus for longer text (more context usually means better detection)
    length_bonus = len(text) / config.extraction.length_bonus_divisor
    confidence += length_bonus

    # Add bonus for exact keyword match quality
    if matched_keyword.lower() in text.lower():
        confidence += 0.1  # Bonus for containing the matched keyword

    # Cap the confidence at the maximum allowed
    confidence = min(confidence, config.extraction.max_confidence_cap)

    # Ensure confidence is within valid range
    return max(0.0, min(1.0, confidence))


def _extract_key_terms(text: str, matched_keyword: str) -> list[str]:
    """Extract key terms from the clause text including the matched keyword.

    Args:
        text: The clause text to extract terms from
        matched_keyword: The keyword that triggered this clause detection

    Returns:
        List of relevant key terms found in the text
    """
    key_terms = []

    # Always include the matched keyword
    key_terms.append(matched_keyword.lower())

    # Extract other potentially relevant terms (simple heuristic)
    # Look for words that might be important in legal contexts
    important_patterns = [
        r"\b\d+\s*(?:days?|months?|years?)\b",  # Time periods
        r"\$\d+(?:,\d{3})*(?:\.\d{2})?",  # Dollar amounts
        r"\b\d+%\b",  # Percentages
        r"\b(?:annual|monthly|daily|weekly)\b",  # Frequency terms
        r"\b(?:shall|must|will|may|cannot)\b",  # Legal modal verbs
    ]

    for pattern in important_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        key_terms.extend([match.lower() for match in matches])

    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in key_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return unique_terms


def _detect_clauses_streaming(
    document_stream,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
) -> list[Clause]:
    """Detect clauses from a streaming document (generator of DocumentPage objects).

    This function processes document pages from a stream/generator, suitable for
    large documents that are processed with stream_document().

    Parameters
    ----------
    document_stream : generator
        Generator that yields DocumentPage objects from stream_document().
    keywords : dict[str, list[str]] | None, optional
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    config = get_config()
    clauses = []

    # Use the same optimized pattern as the regular version
    pattern = _get_cached_pattern(keywords)
    keyword_mapping = _build_keyword_mapping(keywords)

    logger.debug("Processing streamed document for clause detection")

    # Process each page from the stream
    for page in document_stream:
        # Extract text using OCR (same as optimized version)
        page_text = _ocr_image(page.image)

        # Use combined regex to find all matches at once
        matches = pattern.finditer(page_text)

        for match in matches:
            matched_text = match.group(1).lower()
            clause_type = keyword_mapping.get(matched_text)

            if clause_type:
                # Extract surrounding context
                context_size = config.ocr.context_window_size
                start_pos = max(0, match.start() - context_size)
                end_pos = min(len(page_text), match.end() + context_size)
                clause_text = page_text[start_pos:end_pos].strip()

                # Calculate confidence score
                confidence = _calculate_clause_confidence_score(
                    clause_text,
                    matched_text,
                    config,
                )

                # Extract key terms from the clause text
                key_terms = _extract_key_terms(clause_text, matched_text)

                # Create clause with enhanced fields
                clause = Clause(
                    type=clause_type,
                    text=clause_text,
                    page=page.number,
                    coordinates=None,  # Placeholder for future OCR layout analysis
                    id=str(uuid.uuid4()),
                    confidence=confidence,
                    key_terms=key_terms,
                )

                clauses.append(clause)
                logger.info(
                    "Detected %s clause on page %d (streaming)",
                    clause_type,
                    page.number,
                )

    return clauses
