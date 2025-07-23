from pathlib import Path

import pytest
from PIL import Image

from multimodal_contract_extractor import clause_detection
from multimodal_contract_extractor.document import (
    Document,
    DocumentPage,
    load_document,
    stream_document,
)


def create_image(path: Path, color=(255, 255, 255)) -> None:
    Image.new("RGB", (10, 10), color=color).save(path)


def test_load_document_image(tmp_path):
    img_path = tmp_path / "doc.png"
    create_image(img_path)
    doc = load_document(img_path)
    assert len(doc.pages) == 1
    assert doc.pages[0].number == 1


def test_load_document_invalid_extension(tmp_path):
    txt = tmp_path / "bad.txt"
    txt.write_text("oops")
    with pytest.raises(ValueError):
        load_document(txt)


def test_stream_document_pdf(monkeypatch, tmp_path):
    pdf_path = tmp_path / "multi.pdf"
    pdf_path.write_bytes(b"%PDF")
    images = [Image.new("RGB", (10, 10)) for _ in range(3)]

    def fake_info(_):
        return {"Pages": "3"}

    def fake_convert(path, first_page=None, last_page=None):
        start = first_page or 1
        end = last_page or len(images)
        return images[start - 1 : end]

    monkeypatch.setattr("pdf2image.pdfinfo_from_path", fake_info)
    monkeypatch.setattr(
        "multimodal_contract_extractor.document.convert_from_path", fake_convert
    )

    pages = list(stream_document(pdf_path, chunk_size=1))
    assert len(pages) == 3
    assert pages[0].number == 1
    assert pages[-1].number == 3


def test_detect_clauses(monkeypatch):
    img = Image.new("RGB", (10, 10))
    doc = Document(path=Path("dummy"), pages=[DocumentPage(image=img, number=1)])
    monkeypatch.setattr(
        clause_detection, "_ocr_image", lambda _: "Termination is possible"
    )
    clauses = clause_detection.detect_clauses(doc)
    assert clauses
    assert clauses[0].type == "termination"
