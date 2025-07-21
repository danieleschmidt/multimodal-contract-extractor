from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import logging

from PIL import Image
from pdf2image import convert_from_path
from .config import get_config


@dataclass
class DocumentPage:
    """Represents a single page of a document as an image."""

    image: Image.Image
    number: int


@dataclass
class Document:
    """Container for a loaded document."""

    path: Path
    pages: List[DocumentPage]


SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


logger = logging.getLogger(__name__)


def load_document(path: str | Path) -> Document:
    """Load a PDF or image file into a :class:`Document`.

    Parameters
    ----------
    path:
        Path to the document file. Supported formats include PDFs and common
        image types (PNG, JPEG, TIFF, BMP).

    Returns
    -------
    Document
        The loaded document with each page represented as a :class:`DocumentPage`.
    """

    file_path = Path(path)
    logger.debug("Loading document from %s", file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    if file_path.suffix.lower() == ".pdf":
        images = convert_from_path(str(file_path))
    else:
        images = [Image.open(file_path)]

    pages = [DocumentPage(image=img, number=i + 1) for i, img in enumerate(images)]
    logger.info("Loaded %d pages from %s", len(pages), file_path)
    return Document(path=file_path, pages=pages)


def stream_document(path: str | Path, *, chunk_size: int = None) -> Iterable[DocumentPage]:
    """Yield :class:`DocumentPage` objects from ``path`` lazily.

    This helper loads PDF pages in chunks to limit memory usage. Image files are
    yielded as a single page.

    Parameters
    ----------
    path:
        Path to the document file.
    chunk_size:
        Number of pages to convert at a time for PDFs.
    """

    file_path = Path(path)
    if chunk_size is None:
        chunk_size = get_config().document.default_streaming_chunk_size
    logger.debug("Streaming document from %s", file_path)
    if file_path.suffix.lower() != ".pdf":
        yield DocumentPage(image=Image.open(file_path), number=1)
        return

    try:  # pdfinfo may not be available on all systems
        from pdf2image import pdfinfo_from_path

        info = pdfinfo_from_path(str(file_path))
        total_pages = int(info.get("Pages", 1))
    except Exception:  # pragma: no cover - fallback when pdfinfo missing
        images = convert_from_path(str(file_path))
        for i, img in enumerate(images, start=1):
            yield DocumentPage(image=img, number=i)
        return

    for start in range(1, total_pages + 1, chunk_size):
        end = min(start + chunk_size - 1, total_pages)
        images = convert_from_path(str(file_path), first_page=start, last_page=end)
        for i, img in enumerate(images, start=start):
            yield DocumentPage(image=img, number=i)
