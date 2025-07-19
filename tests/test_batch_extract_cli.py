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
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported format" in result.stderr


def test_batch_extract_version_outputs_package_version():
    result = subprocess.run(
        [sys.executable, "batch_extract.py", "--version"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    from multimodal_contract_extractor import __version__

    assert __version__ in result.stdout
