"""Version management for the multimodal contract extractor."""

from __future__ import annotations

__version__ = "0.1.0"
__api_version__ = "v1"

def get_version() -> str:
    """Get the current version."""
    return __version__

def get_api_version() -> str:
    """Get the current API version."""
    return __api_version__
