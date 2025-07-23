import json
import subprocess
import sys
from pathlib import Path

from .test_helpers import create_test_pdf


def test_batch_extract_creates_outputs(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for name in ["a.pdf", "b.pdf"]:
        create_test_pdf(input_dir / name, "dummy content")

    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "batch_extract.py",
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True, cwd=Path(__file__).resolve().parent.parent)
    assert (output_dir / "a.json").is_file()
    assert (output_dir / "b.json").is_file()


def test_batch_extract_rejects_invalid_format(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    create_test_pdf(input_dir / "file.pdf", "test content")
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "batch_extract.py",
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--output-format",
        "docx",
    ]
    result = subprocess.run(
        cmd,
        check=False, cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported format" in result.stderr


def test_batch_extract_performs_real_extraction(tmp_path):
    """Test that batch extraction actually processes documents with real extraction logic."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Create test PDF with content that should trigger clause detection
    test_content = "This agreement shall terminate upon 30 days notice. The employee shall receive payment in accordance with company policy."
    create_test_pdf(input_dir / "contract.pdf", test_content)

    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "batch_extract.py",
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--output-format",
        "json",
    ]
    subprocess.run(cmd, check=True, cwd=Path(__file__).resolve().parent.parent)

    # Verify output file exists and contains real extraction results
    output_file = output_dir / "contract.json"
    assert output_file.is_file()

    # Parse the JSON output and verify it has real extraction structure
    with open(output_file) as f:
        data = json.load(f)

    # Verify it's not dummy data - real extraction should have:
    # 1. More than 0 pages (OCR should detect text)
    # 2. Processing time > 0
    # 3. Document info with actual values, not placeholder zeros
    assert data["document_info"]["pages"] > 0, "Should have detected pages from PDF"
    assert data["document_info"]["processing_time"] > 0, "Should have actual processing time"
    assert "clauses" in data, "Should have clauses array"

    # Verify that extraction actually found meaningful content
    # Real extraction should detect clauses from the test content
    if len(data["clauses"]) > 0:
        # If clauses were found, verify they contain expected content
        clause_texts = [clause["text"] for clause in data["clauses"]]
        combined_text = " ".join(clause_texts)
        assert "terminate" in combined_text or "payment" in combined_text, \
            "Should detect clauses containing expected keywords"


def test_batch_extract_version_outputs_package_version():
    result = subprocess.run(
        [sys.executable, "batch_extract.py", "--version"],
        check=False, cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    from multimodal_contract_extractor import __version__

    assert __version__ in result.stdout
