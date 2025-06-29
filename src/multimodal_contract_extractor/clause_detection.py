"""Clause detection via OCR and simple heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List
import logging

from .document import Document
from PIL import Image


@dataclass
class Clause:
    """Represents an extracted clause from a document."""

    type: str
    text: str
    page: int
    coordinates: tuple[int, int, int, int] | None = None


def _ocr_image(image: Image.Image) -> str:
    """Extract text from an image using Tesseract OCR."""
    try:
        import pytesseract
    except ImportError as exc:
        raise ImportError("pytesseract is required for OCR operations") from exc
    return pytesseract.image_to_string(image)


DEFAULT_KEYWORDS: Dict[str, List[str]] = {
    "confidentiality": ["confidential"],
    "termination": ["termination", "terminate"],
    "payment_terms": ["payment", "compensation"],
    "liability": ["liability"],
    "governing_law": ["governing law", "jurisdiction"],
    "dispute_resolution": ["dispute", "arbitration"],
}


logger = logging.getLogger(__name__)


def detect_clauses(
    document: Document, *, keywords: Dict[str, Iterable[str]] | None = None
) -> List[Clause]:
    """Detect clauses within a loaded :class:`Document`.

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

    logger.debug("Detecting clauses in %d pages", len(document.pages))

    clauses: List[Clause] = []
    for page in document.pages:
        text = _ocr_image(page.image)
        lower_text = text.lower()
        for clause_type, words in keywords.items():
            for word in words:
                if word.lower() in lower_text:
                    # capture surrounding text for context
                    pattern = re.compile(
                        rf"(.{{0,100}}{re.escape(word)}.{{0,100}})", re.IGNORECASE
                    )
                    match = pattern.search(text)
                    snippet = match.group(1).strip() if match else word
                    clause = Clause(type=clause_type, text=snippet, page=page.number)
                    clauses.append(clause)
                    logger.info(
                        "Detected %s clause on page %d", clause_type, page.number
                    )
                    break
    return clauses
