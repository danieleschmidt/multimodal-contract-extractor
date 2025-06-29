import json
import subprocess
import sys
from pathlib import Path


def test_extract_cli_metrics_and_json_logs(tmp_path):
    input_file = tmp_path / "doc.txt"
    input_file.write_text("data")
    metrics_file = tmp_path / "metrics.txt"
    cmd = [
        sys.executable,
        "extract.py",
        "--file",
        str(input_file),
        "--json-logs",
        "--metrics-file",
        str(metrics_file),
    ]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    log_line = result.stderr.splitlines()[0]
    data = json.loads(log_line)
    assert data["level"] == "INFO"
    assert metrics_file.is_file()
    content = metrics_file.read_text()
    assert "processing_time_seconds" in content
