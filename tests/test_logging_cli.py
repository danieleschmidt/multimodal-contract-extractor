import subprocess
import sys
from pathlib import Path

from .test_helpers import create_test_pdf


def test_extract_cli_logs(tmp_path):
    input_file = tmp_path / "doc.pdf"
    create_test_pdf(input_file, "test content")
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
    ]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Processing file" in result.stderr


def test_extract_cli_debug_level(tmp_path):
    input_file = tmp_path / "doc.pdf"
    create_test_pdf(input_file, "test content")
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
        "--log-level",
        "debug",
    ]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "DEBUG" in result.stderr
