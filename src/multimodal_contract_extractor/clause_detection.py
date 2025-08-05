"""Clause detection via OCR and simple heuristics."""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, Optional

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


def _extract_text_coordinates(text_to_find: str, ocr_data: dict) -> Optional[list[int]]:
    """Extract coordinates for specific text from OCR data.
    
    Args:
        text_to_find: Text to locate in OCR results
        ocr_data: OCR data with text, left, top, width, height arrays
        
    Returns:
        [left, top, right, bottom] coordinates or None if not found
    """
    if not ocr_data.get('text'):
        return None

    words_to_find = text_to_find.lower().split()
    if not words_to_find:
        return None

    # Find consecutive word matches
    for i in range(len(ocr_data['text']) - len(words_to_find) + 1):
        # Check if we have a match starting at position i
        match = True
        for j, word in enumerate(words_to_find):
            ocr_word = ocr_data['text'][i + j].lower().strip()
            if not ocr_word or word not in ocr_word:
                match = False
                break

        if match:
            # Calculate bounding box for the matched text span
            left = ocr_data['left'][i]
            top = ocr_data['top'][i]

            # Find rightmost and bottommost coordinates
            right = left
            bottom = top

            for j in range(len(words_to_find)):
                word_idx = i + j
                word_right = ocr_data['left'][word_idx] + ocr_data['width'][word_idx]
                word_bottom = ocr_data['top'][word_idx] + ocr_data['height'][word_idx]
                right = max(right, word_right)
                bottom = max(bottom, word_bottom)

            return [left, top, right, bottom]

    return None


def _ocr_image(image: Image.Image, language_code: str = "en") -> str:
    """Extract text from an image using Tesseract OCR with caching and language support.
    
    Args:
        image: PIL Image to process
        language_code: Language code for OCR processing (e.g., "en", "es", "fr")
        
    Returns:
        Extracted text from the image
    """
    # Create a hash of the image and language for caching
    image_hash = _hash_image_with_language(image, language_code)

    # Check cache first
    if image_hash in _ocr_cache:
        logger.debug("OCR cache hit for image hash: %s (lang: %s)", image_hash[:8], language_code)
        _record_cache_hit()
        return _ocr_cache[image_hash]

    # Perform OCR and cache result
    logger.debug("OCR cache miss, performing OCR for hash: %s (lang: %s)", image_hash[:8], language_code)
    _record_cache_miss()

    try:
        import pytesseract
    except ImportError as exc:
        msg = "pytesseract is required for OCR operations"
        raise ImportError(msg) from exc

    # Get language-specific OCR configuration
    from .language_detection import (
        get_ocr_config_for_language,
        get_tesseract_language_string,
    )

    tesseract_lang = get_tesseract_language_string([language_code])
    ocr_config = get_ocr_config_for_language(language_code)

    # Build Tesseract configuration string
    config_str = " ".join([f"--{key} {value}" for key, value in ocr_config.items()])

    try:
        text = pytesseract.image_to_string(image, lang=tesseract_lang, config=config_str)
        logger.debug("OCR completed with language %s, extracted %d characters", language_code, len(text))
    except Exception as e:
        logger.warning("OCR failed with language %s, falling back to English: %s", language_code, str(e))
        # Fallback to English if language-specific OCR fails
        text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")

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


def _hash_image_with_language(image: Image.Image, language_code: str) -> str:
    """Create a hash of the image and language combination for cache key."""
    # Convert image to bytes and include language in hash
    image_bytes = image.tobytes()
    combined = image_bytes + language_code.encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


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

# Multi-language keyword mappings
MULTILANGUAGE_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "en": {
        "confidentiality": ["confidential", "proprietary", "non-disclosure", "nda", "confidential information"],
        "termination": ["termination", "terminate", "end", "expire", "dissolution", "breach"],
        "payment_terms": ["payment", "compensation", "salary", "fee", "remuneration", "consideration"],
        "liability": ["liability", "liable", "damages", "responsible", "indemnify", "indemnification"],
        "governing_law": ["governing law", "jurisdiction", "governed by", "applicable law"],
        "dispute_resolution": ["dispute", "arbitration", "mediation", "court", "litigation"],
        "licensing": ["license", "licensing", "intellectual property", "patent", "trademark", "copyright"],
        "merger_acquisition": ["merger", "acquisition", "purchase", "buy", "acquire", "consolidation"],
        "trade_agreement": ["trade", "import", "export", "customs", "tariff", "international trade"],
    },
    "es": {
        "confidentiality": ["confidencial", "privado", "secreto", "información confidencial"],
        "termination": ["terminación", "terminar", "finalizar", "rescisión", "extinción"],
        "payment_terms": ["pago", "compensación", "salario", "remuneración", "honorarios"],
        "liability": ["responsabilidad", "liable", "daños", "indemnización"],
        "governing_law": ["ley aplicable", "jurisdicción", "derecho aplicable"],
        "dispute_resolution": ["disputa", "arbitraje", "mediación", "tribunal", "litigio"],
        "licensing": ["licencia", "propiedad intelectual", "patente", "marca", "derechos de autor"],
        "merger_acquisition": ["fusión", "adquisición", "compra", "adquirir", "consolidación"],
        "trade_agreement": ["comercio", "importación", "exportación", "aduanas", "aranceles"],
    },
    "fr": {
        "confidentiality": ["confidentiel", "privé", "secret", "information confidentielle"],
        "termination": ["résiliation", "terminer", "fin", "expiration", "dissolution"],
        "payment_terms": ["paiement", "compensation", "salaire", "rémunération", "honoraires"],
        "liability": ["responsabilité", "responsable", "dommages", "indemnisation"],
        "governing_law": ["loi applicable", "juridiction", "droit applicable"],
        "dispute_resolution": ["litige", "arbitrage", "médiation", "tribunal"],
        "licensing": ["licence", "propriété intellectuelle", "brevet", "marque", "droit d'auteur"],
        "merger_acquisition": ["fusion", "acquisition", "achat", "acquérir", "consolidation"],
        "trade_agreement": ["commerce", "importation", "exportation", "douanes", "tarifs"],
    },
    "de": {
        "confidentiality": ["vertraulich", "geheim", "vertrauliche informationen"],
        "termination": ["kündigung", "beendigung", "auflösung", "termination"],
        "payment_terms": ["zahlung", "vergütung", "gehalt", "honorar", "entschädigung"],
        "liability": ["haftung", "verantwortlich", "schäden", "entschädigung"],
        "governing_law": ["anwendbares recht", "gerichtsbarkeit", "rechtsprechung"],
        "dispute_resolution": ["streit", "schiedsverfahren", "mediation", "gericht"],
        "licensing": ["lizenz", "geistiges eigentum", "patent", "marke", "urheberrecht"],
        "merger_acquisition": ["fusion", "übernahme", "kauf", "erwerben", "konsolidierung"],
        "trade_agreement": ["handel", "import", "export", "zoll", "tarife"],
    },
    "ja": {
        "confidentiality": ["機密", "秘密", "非開示", "機密情報"],
        "termination": ["終了", "解約", "満了", "破棄"],
        "payment_terms": ["支払い", "報酬", "給与", "手数料", "対価"],
        "liability": ["責任", "損害", "賠償", "補償"],
        "governing_law": ["準拠法", "管轄", "適用法"],
        "dispute_resolution": ["紛争", "仲裁", "調停", "裁判所"],
        "licensing": ["ライセンス", "知的財産", "特許", "商標", "著作権"],
        "merger_acquisition": ["合併", "買収", "取得", "統合"],
        "trade_agreement": ["貿易", "輸入", "輸出", "関税", "通商"],
    },
    "zh": {
        "confidentiality": ["保密", "机密", "秘密", "保密信息"],
        "termination": ["终止", "解除", "期满", "废止"],
        "payment_terms": ["付款", "报酬", "工资", "费用", "对价"],
        "liability": ["责任", "损害", "赔偿", "补偿"],
        "governing_law": ["适用法", "管辖", "适用法律"],
        "dispute_resolution": ["争议", "仲裁", "调解", "法院"],
        "licensing": ["许可", "知识产权", "专利", "商标", "版权"],
        "merger_acquisition": ["合并", "收购", "购买", "获得", "整合"],
        "trade_agreement": ["贸易", "进口", "出口", "关税", "商贸"],
    },
}

# Cache for compiled regex patterns
_pattern_cache: dict[str, re.Pattern] = {}


def detect_clauses(
    document,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
    language_code: str | None = None,
    auto_detect_language: bool = True,
) -> list[Clause]:
    """Detect clauses within a loaded :class:`Document` or document stream.

    Uses optimized clause detection with combined regex patterns for better performance.
    Supports multi-language documents with automatic language detection.

    Parameters
    ----------
    document:
        Document produced by :func:`load_document` or generator from :func:`stream_document`.
    keywords:
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.
    language_code:
        Specific language code to use for OCR. If None and auto_detect_language is True,
        language will be auto-detected from the document.
    auto_detect_language:
        Whether to automatically detect document language if language_code is not provided.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    # Check if document is a generator (from stream_document) or Document object
    if hasattr(document, "pages"):
        # Standard Document object
        return _detect_clauses_optimized(document, keywords=keywords,
                                        language_code=language_code,
                                        auto_detect_language=auto_detect_language)
    # Generator from stream_document
    return _detect_clauses_streaming(document, keywords=keywords,
                                   language_code=language_code,
                                   auto_detect_language=auto_detect_language)


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

                    # Extract coordinates from OCR data
                    try:
                        import pytesseract
                        ocr_data = pytesseract.image_to_data(
                            page.image, output_type=pytesseract.Output.DICT, config='--psm 6'
                        )
                        coordinates = _extract_text_coordinates(snippet[:50], ocr_data)
                    except ImportError:
                        coordinates = None

                    # Fallback to page-relative coordinates if OCR coordinates not found
                    if coordinates is None:
                        coordinates = [
                            50,
                            100 + len(clauses) * 50,
                            550,
                            150 + len(clauses) * 50,
                        ]

                    clause = Clause(
                        type=clause_type,
                        text=snippet,
                        page=page.number,
                        coordinates=coordinates,
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
    language_code: str | None = None,
    auto_detect_language: bool = True,
) -> list[Clause]:
    """Optimized clause detection using combined regex patterns with multi-language support.

    This optimized version builds a single combined regex pattern to find all
    keywords in one pass, rather than searching for each keyword individually.
    Supports automatic language detection and language-specific OCR processing.

    Parameters
    ----------
    document : Document
        The document to search for clauses in.
    keywords : dict[str, list[str]] | None, optional
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.
    language_code : str, optional
        Specific language code to use. If None, language will be detected automatically.
    auto_detect_language : bool
        Whether to automatically detect the document language.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    logger.debug("Detecting clauses in %d pages (optimized, multi-language)", len(document.pages))

    # Detect document language if not specified
    detected_language = language_code
    if not detected_language and auto_detect_language:
        detected_language = _detect_document_language(document)
        logger.info("Auto-detected document language: %s", detected_language)

    # Use English as fallback
    if not detected_language:
        detected_language = "en"

    # Get language-appropriate keywords
    effective_keywords = _get_localized_keywords(keywords, detected_language)

    # Build combined pattern for all keywords
    combined_pattern = _get_cached_pattern(effective_keywords)
    keyword_to_type = _build_keyword_mapping(effective_keywords)

    clauses: list[Clause] = []
    for page in document.pages:
        # Use language-specific OCR
        text = _ocr_image(page.image, detected_language)

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

                # Extract coordinates from OCR data with language-specific config
                coordinates = _extract_coordinates_multilang(page.image, snippet[:50], detected_language)

                # Fallback to page-relative coordinates if OCR coordinates not found
                if coordinates is None:
                    coordinates = [
                        50,
                        100 + len(clauses) * 50,
                        550,
                        150 + len(clauses) * 50,
                    ]

                clause = Clause(
                    type=clause_type,
                    text=snippet,
                    page=page.number,
                    coordinates=coordinates,
                    id=clause_id,
                    confidence=confidence,
                    key_terms=key_terms,
                )
                clauses.append(clause)
                logger.info(
                    "Detected %s clause on page %d (optimized, lang: %s)",
                    clause_type,
                    page.number,
                    detected_language,
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


def _detect_document_language(document: Document) -> str:
    """Detect the primary language of a document by sampling text from first few pages."""
    from .language_detection import detect_document_language

    # Sample text from first 2-3 pages for language detection
    sample_pages = min(3, len(document.pages))
    sample_text = ""

    for i in range(sample_pages):
        page_text = _ocr_image(document.pages[i].image, "en")  # Use English for initial sampling
        sample_text += " " + page_text[:500]  # Take first 500 chars from each page

        if len(sample_text) > 1000:  # Stop if we have enough text for detection
            break

    language_code, confidence = detect_document_language(sample_text)
    logger.debug("Detected language: %s (confidence: %.2f)", language_code, confidence)

    return language_code


def _get_localized_keywords(keywords: dict[str, Iterable[str]], language_code: str) -> dict[str, list[str]]:
    """Get keywords appropriate for the detected language."""
    # If we have language-specific keywords, use them
    if language_code in MULTILANGUAGE_KEYWORDS:
        localized = MULTILANGUAGE_KEYWORDS[language_code].copy()

        # Merge with any custom keywords provided
        if keywords and keywords != DEFAULT_KEYWORDS:
            for clause_type, terms in keywords.items():
                if clause_type in localized:
                    localized[clause_type].extend(terms)
                else:
                    localized[clause_type] = list(terms)

        return localized

    # Fallback to provided keywords or default English keywords
    return dict(keywords) if keywords else DEFAULT_KEYWORDS.copy()


def _extract_coordinates_multilang(image: Image.Image, text_snippet: str, language_code: str) -> Optional[list[int]]:
    """Extract coordinates using language-specific OCR configuration."""
    try:
        import pytesseract

        from .language_detection import (
            get_ocr_config_for_language,
            get_tesseract_language_string,
        )

        tesseract_lang = get_tesseract_language_string([language_code])
        ocr_config = get_ocr_config_for_language(language_code)
        config_str = " ".join([f"--{key} {value}" for key, value in ocr_config.items()])

        ocr_data = pytesseract.image_to_data(
            image,
            lang=tesseract_lang,
            output_type=pytesseract.Output.DICT,
            config=config_str
        )
        return _extract_text_coordinates(text_snippet, ocr_data)
    except (ImportError, Exception) as e:
        logger.debug("Failed to extract coordinates with language %s: %s", language_code, str(e))
        return None


def _detect_clauses_streaming(
    document_stream,
    *,
    keywords: dict[str, Iterable[str]] | None = None,
    language_code: str | None = None,
    auto_detect_language: bool = True,
) -> list[Clause]:
    """Detect clauses from a streaming document with multi-language support.

    This function processes document pages from a stream/generator, suitable for
    large documents that are processed with stream_document().

    Parameters
    ----------
    document_stream : generator
        Generator that yields DocumentPage objects from stream_document().
    keywords : dict[str, list[str]] | None, optional
        Mapping of clause types to lists of search keywords. If ``None``,
        ``DEFAULT_KEYWORDS`` is used.
    language_code : str, optional
        Specific language code to use. If None, language will be detected automatically.
    auto_detect_language : bool
        Whether to automatically detect the document language.

    Returns
    -------
    list[Clause]
        Detected clauses with their page numbers.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    config = get_config()
    clauses = []
    detected_language = language_code or "en"
    language_detected = False

    logger.debug("Processing streamed document for clause detection (multi-language)")

    # Process each page from the stream
    for page_idx, page in enumerate(document_stream):
        # Detect language from first few pages if not specified
        if not language_code and auto_detect_language and not language_detected and page_idx < 3:
            # Sample text for language detection
            sample_text = _ocr_image(page.image, "en")[:500]
            if len(sample_text.strip()) > 50:  # Need sufficient text for detection
                from .language_detection import detect_document_language
                detected_lang, confidence = detect_document_language(sample_text)
                if confidence > 0.6:  # Only use if confident enough
                    detected_language = detected_lang
                    language_detected = True
                    logger.info("Auto-detected language for streaming document: %s (confidence: %.2f)",
                              detected_language, confidence)

        # Get language-appropriate keywords
        if page_idx == 0 or not language_detected:  # Update keywords when language is determined
            effective_keywords = _get_localized_keywords(keywords, detected_language)
            pattern = _get_cached_pattern(effective_keywords)
            keyword_mapping = _build_keyword_mapping(effective_keywords)

        # Extract text using language-specific OCR
        page_text = _ocr_image(page.image, detected_language)

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
                    "Detected %s clause on page %d (streaming, lang: %s)",
                    clause_type,
                    page.number,
                    detected_language,
                )

    return clauses
