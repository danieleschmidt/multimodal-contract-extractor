from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image
from pdf2image import convert_from_path


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
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    if file_path.suffix.lower() == ".pdf":
        images = convert_from_path(str(file_path))
    else:
        images = [Image.open(file_path)]

    pages = [DocumentPage(image=img, number=i + 1) for i, img in enumerate(images)]
    return Document(path=file_path, pages=pages)
