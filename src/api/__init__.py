"""REST API for contract processing."""

from .app import create_app
from .middleware import setup_middleware
from .routes import register_routes

__all__ = [
    "create_app",
    "setup_middleware",
    "register_routes",
]
