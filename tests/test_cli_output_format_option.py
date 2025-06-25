import subprocess
import sys
from pathlib import Path


def test_cli_writes_result_json(tmp_path):
    input_file = tmp_path / "dummy.txt"
    input_file.write_text("test")
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
    input_file = tmp_path / "dummy.txt"
    input_file.write_text("test")
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
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported format" in result.stderr
