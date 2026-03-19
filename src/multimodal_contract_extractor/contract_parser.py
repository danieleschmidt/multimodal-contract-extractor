"""ContractParser: Extracts raw text from PDFs and images.

Uses pdfplumber if available, falls back to basic extraction.
Uses pytesseract for OCR if available, falls back to simulated text input.
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


def _try_import_pdfplumber():
    try:
        import pdfplumber
        return pdfplumber
    except ImportError:
        return None


def _try_import_pytesseract():
    try:
        import pytesseract
        return pytesseract
    except ImportError:
        return None


def _try_import_pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


class ContractParser:
    """Extracts raw text from contract documents (PDFs and images).

    Supports:
    - PDF files via pdfplumber (if installed) or pypdf fallback
    - Image files via pytesseract OCR (if installed)
    - Direct text input for testing/simulation
    """

    def __init__(self):
        self.pdfplumber = _try_import_pdfplumber()
        self.pytesseract = _try_import_pytesseract()
        self.PIL_Image = _try_import_pil()

        logger.info(
            "ContractParser initialized | pdfplumber=%s | pytesseract=%s | PIL=%s",
            self.pdfplumber is not None,
            self.pytesseract is not None,
            self.PIL_Image is not None,
        )

    def parse_file(self, file_path: Union[str, Path]) -> str:
        """Parse a contract file and return extracted text.

        Args:
            file_path: Path to PDF or image file.

        Returns:
            Extracted text as a single string.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Contract file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self.parse_pdf(path)
        elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            return self.parse_image(path)
        else:
            # Attempt to read as plain text
            logger.warning("Unknown file type %s — reading as plain text", suffix)
            return path.read_text(encoding="utf-8", errors="replace")

    def parse_pdf(self, path: Union[str, Path]) -> str:
        """Extract text from a PDF file.

        Args:
            path: Path to the PDF file.

        Returns:
            Concatenated text from all pages.
        """
        path = Path(path)
        if self.pdfplumber:
            return self._parse_pdf_pdfplumber(path)
        else:
            return self._parse_pdf_fallback(path)

    def _parse_pdf_pdfplumber(self, path: Path) -> str:
        """Extract text using pdfplumber."""
        pages = []
        with self.pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append(f"[Page {i + 1}]\n{text}")
        return "\n\n".join(pages)

    def _parse_pdf_fallback(self, path: Path) -> str:
        """Fallback: try pypdf, else return placeholder."""
        try:
            import pypdf  # type: ignore
            reader = pypdf.PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append(f"[Page {i + 1}]\n{text}")
            return "\n\n".join(pages)
        except ImportError:
            pass

        # Last resort: raw byte extraction of text strings
        logger.warning("No PDF parser available — attempting raw text extraction")
        raw = path.read_bytes()
        # Extract printable text sequences from PDF bytes
        texts = re.findall(rb"\(([^\)]{5,})\)", raw)
        decoded = []
        for t in texts:
            try:
                decoded.append(t.decode("latin-1"))
            except Exception:
                pass
        return " ".join(decoded)

    def parse_image(self, path: Union[str, Path]) -> str:
        """Extract text from an image via OCR.

        Args:
            path: Path to the image file.

        Returns:
            OCR-extracted text, or empty string if OCR unavailable.
        """
        path = Path(path)
        if self.pytesseract and self.PIL_Image:
            image = self.PIL_Image.open(path)
            text = self.pytesseract.image_to_string(image)
            return text
        elif self.PIL_Image:
            logger.warning(
                "pytesseract not available — cannot OCR image %s. "
                "Pass text directly via parse_text().",
                path.name,
            )
            return ""
        else:
            logger.warning("PIL not available — cannot open image %s.", path.name)
            return ""

    def parse_text(self, text: str) -> str:
        """Pass through raw text (for testing or pre-extracted content).

        Args:
            text: Raw contract text.

        Returns:
            The same text, lightly normalized.
        """
        # Normalize whitespace
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def capabilities(self) -> dict:
        """Return a dict describing available parsing capabilities."""
        return {
            "pdf": "pdfplumber" if self.pdfplumber else "fallback",
            "image_ocr": self.pytesseract is not None,
            "image_open": self.PIL_Image is not None,
        }
