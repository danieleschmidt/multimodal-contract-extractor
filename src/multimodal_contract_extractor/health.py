"""Health check and system monitoring functionality."""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .config import get_config

logger = logging.getLogger(__name__)


def get_health_status() -> dict[str, Any]:
    """Get comprehensive health status of the system.

    Returns
    -------
    Dict[str, Any]
        Health status including overall status, timestamp, version, and dependencies
    """
    start_time = time.perf_counter()

    # Check all dependencies
    dependencies = check_dependencies()

    # Determine overall health
    unhealthy_deps = [
        name for name, info in dependencies.items() if info["status"] != "available"
    ]

    if not unhealthy_deps:
        overall_status = "healthy"
    elif len(unhealthy_deps) < len(dependencies):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    check_time = time.perf_counter() - start_time

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "check_duration": round(check_time, 3),
        "dependencies": dependencies,
        "unhealthy_dependencies": unhealthy_deps,
    }


def check_dependencies() -> dict[str, dict[str, Any]]:
    """Check health of all system dependencies.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Status of each dependency with details
    """
    dependencies = {}

    # Check Tesseract OCR
    dependencies["tesseract"] = _check_tesseract()

    # Check Poppler utilities
    dependencies["poppler"] = _check_poppler()

    # Check Python packages
    dependencies["python_packages"] = _check_python_packages()

    return dependencies


def _check_tesseract() -> dict[str, Any]:
    """Check if Tesseract OCR is available and working."""
    try:
        # Find tesseract executable path for security
        tesseract_path = shutil.which("tesseract")
        if not tesseract_path:
            return {
                "status": "missing",
                "version": None,
                "message": "Tesseract OCR not found in PATH",
            }

        # Try to run tesseract --version with absolute path
        config = get_config()
        result = subprocess.run(
            [tesseract_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=config.health.check_timeout_seconds,
        )

        if result.returncode == 0:
            # Parse version from output
            version_line = result.stderr.split("\n")[0] if result.stderr else "Unknown"
            return {
                "status": "available",
                "version": version_line,
                "message": "Tesseract OCR is working",
            }
        return {
            "status": "error",
            "message": f"Tesseract returned non-zero exit code: {result.returncode}",
            "error": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Tesseract command timed out",
        }
    except FileNotFoundError:
        return {
            "status": "unavailable",
            "message": "Tesseract not found in PATH",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking Tesseract: {e}",
        }


def _check_poppler() -> dict[str, Any]:
    """Check if Poppler utilities are available."""
    try:
        # Find pdfinfo executable path for security
        pdfinfo_path = shutil.which("pdfinfo")
        if not pdfinfo_path:
            return {
                "status": "missing",
                "version": None,
                "message": "Poppler utilities (pdfinfo) not found in PATH",
            }

        # Try to get version with absolute path
        config = get_config()
        result = subprocess.run(
            [pdfinfo_path, "-v"],
            check=False,
            capture_output=True,
            text=True,
            timeout=config.health.check_timeout_seconds,
        )

        if result.returncode == 0:
            # pdfinfo -v writes to stderr
            version_info = result.stderr.strip() if result.stderr else "Unknown version"
            return {
                "status": "available",
                "version": version_info,
                "message": "Poppler utilities are working",
            }
        return {
            "status": "error",
            "version": None,
            "message": f"pdfinfo returned error code {result.returncode}",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Poppler command timed out",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking Poppler: {e}",
        }


def _check_python_packages() -> dict[str, Any]:
    """Check if required Python packages are available."""
    required_packages = [
        "PIL",
        "pdf2image",
        "pytesseract",
        "defusedxml",
    ]

    missing_packages = []
    available_packages = []

    for package in required_packages:
        try:
            __import__(package)
            available_packages.append(package)
        except ImportError:
            missing_packages.append(package)

    if not missing_packages:
        return {
            "status": "available",
            "available": available_packages,
            "message": f"All {len(available_packages)} required packages available",
        }
    return {
        "status": "error"
        if len(missing_packages) == len(required_packages)
        else "degraded",
        "available": available_packages,
        "missing": missing_packages,
        "message": f"Missing packages: {', '.join(missing_packages)}",
    }


def get_system_info() -> dict[str, Any]:
    """Get system information for diagnostics.

    Returns
    -------
    Dict[str, Any]
        System information including OS, Python version, etc.
    """
    import platform
    import sys

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "python_executable": sys.executable,
    }


def is_healthy() -> bool:
    """Quick health check returning boolean status.

    Returns
    -------
    bool
        True if system is healthy, False otherwise
    """
    try:
        status = get_health_status()
        return status["status"] == "healthy"
    except Exception:
        return False
