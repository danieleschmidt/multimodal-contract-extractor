import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_extract_cli_missing_input(tmp_path):
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(tmp_path / "missing.txt"),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Input file not found" in result.stderr


def test_extract_cli_output_dir_missing(tmp_path):
    input_file = tmp_path / "doc.txt"
    input_file.write_text("data")
    missing_dir = tmp_path / "missing" / "result.json"
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
        "--output",
        str(missing_dir),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Output directory not found" in result.stderr


def test_batch_extract_cli_missing_input_dir(tmp_path):
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "batch_extract.py",
        "--input-dir",
        str(tmp_path / "no"),
        "--output-dir",
        str(output_dir),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Input directory not found" in result.stderr
