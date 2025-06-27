"""Test package setup for path resolution."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src directory is importable when running tests without
# installing the package first.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

