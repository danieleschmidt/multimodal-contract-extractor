"""Clause detection via OCR and simple heuristics."""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List
import logging

from .document import Document
from PIL import Image
from .config import get_config

logger = logging.getLogger(__name__)

# Module-level OCR cache
_ocr_cache: Dict[str, str] = {}


@dataclass
class Clause:
    """Represents an extracted clause from a document."""

    type: str
    text: str
    page: int
    coordinates: tuple[int, int, int, int] | None = None


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
        raise ImportError("pytesseract is required for OCR operations") from exc
    
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


def get_ocr_cache_stats() -> Dict[str, int]:
    """Get OCR cache statistics."""
    return {
        "cache_size": len(_ocr_cache),
        "max_size": 100
    }


DEFAULT_KEYWORDS: Dict[str, List[str]] = {
    "confidentiality": ["confidential"],
    "termination": ["termination", "terminate"],
    "payment_terms": ["payment", "compensation"],
    "liability": ["liability"],
    "governing_law": ["governing law", "jurisdiction"],
    "dispute_resolution": ["dispute", "arbitration"],
}

# Cache for compiled regex patterns
_pattern_cache: Dict[str, re.Pattern] = {}


def detect_clauses(
    document: Document, *, keywords: Dict[str, Iterable[str]] | None = None
) -> List[Clause]:
    """Detect clauses within a loaded :class:`Document`.
    
    Uses optimized clause detection with combined regex patterns for better performance.

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
    # Use optimized detection by default
    return _detect_clauses_optimized(document, keywords=keywords)


def _detect_clauses_legacy(
    document: Document, *, keywords: Dict[str, Iterable[str]] | None = None
) -> List[Clause]:
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

    clauses: List[Clause] = []
    for page in document.pages:
        text = _ocr_image(page.image)
        lower_text = text.lower()
        for clause_type, words in keywords.items():
            for word in words:
                if word.lower() in lower_text:
                    # capture surrounding text for context
                    pattern = re.compile(
                        rf"(.{{0,{get_config().ocr.context_window_size}}}{re.escape(word)}.{{0,{get_config().ocr.context_window_size}}})", re.IGNORECASE
                    )
                    match = pattern.search(text)
                    snippet = match.group(1).strip() if match else word
                    clause = Clause(type=clause_type, text=snippet, page=page.number)
                    clauses.append(clause)
                    logger.info(
                        "Detected %s clause on page %d (legacy)", clause_type, page.number
                    )
                    break
    return clauses


def _detect_clauses_optimized(
    document: Document, *, keywords: Dict[str, Iterable[str]] | None = None
) -> List[Clause]:
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

    clauses: List[Clause] = []
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
                
                clause = Clause(type=clause_type, text=snippet, page=page.number)
                clauses.append(clause)
                logger.info(
                    "Detected %s clause on page %d (optimized)", clause_type, page.number
                )
    
    return clauses


def _get_cached_pattern(keywords: Dict[str, Iterable[str]]) -> re.Pattern:
    """Get a cached compiled regex pattern for the given keywords."""
    # Create a cache key based on the keywords
    cache_key = _create_cache_key(keywords)
    
    if cache_key not in _pattern_cache:
        _pattern_cache[cache_key] = _build_combined_pattern(keywords)
        logger.debug("Compiled and cached regex pattern for %d clause types", len(keywords))
    else:
        logger.debug("Using cached regex pattern")
    
    return _pattern_cache[cache_key]


def _create_cache_key(keywords: Dict[str, Iterable[str]]) -> str:
    """Create a cache key for the keywords dictionary."""
    # Sort by clause type for consistent key
    items = []
    for clause_type in sorted(keywords.keys()):
        words = sorted(keywords[clause_type])
        items.append(f"{clause_type}:{','.join(words)}")
    return "|".join(items)


def _build_combined_pattern(keywords: Dict[str, Iterable[str]]) -> re.Pattern:
    """Build a single regex pattern that matches all keywords."""
    if not keywords:
        # Return a pattern that matches nothing
        return re.compile(r'(?!.*)', re.IGNORECASE)
    
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
    pattern_str = r'\b(' + '|'.join(escaped_keywords) + r')'
    
    return re.compile(pattern_str, re.IGNORECASE)


def _build_keyword_mapping(keywords: Dict[str, Iterable[str]]) -> Dict[str, str]:
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
