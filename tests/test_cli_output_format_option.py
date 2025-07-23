import subprocess
import sys
from pathlib import Path

from .test_helpers import create_test_pdf


def test_cli_writes_result_json(tmp_path):
    input_file = tmp_path / "dummy.pdf"
    create_test_pdf(input_file, "test content")
    output_base = tmp_path / "result"
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
        "--output-format",
        "json",
        "--output",
        str(output_base),
    ]
    subprocess.run(cmd, check=True, cwd=Path(__file__).resolve().parent.parent)
    assert (tmp_path / "result.json").is_file()


def test_cli_rejects_invalid_format(tmp_path):
    input_file = tmp_path / "dummy.pdf"
    create_test_pdf(input_file, "test content")
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
        "--output-format",
        "docx",
    ]
    result = subprocess.run(
        cmd,
        check=False,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported format" in result.stderr


def test_cli_version_outputs_package_version():
    result = subprocess.run(
        [sys.executable, "extract.py", "--version"],
        check=False,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    from multimodal_contract_extractor import __version__

    assert __version__ in result.stdout
