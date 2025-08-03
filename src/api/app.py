"""FastAPI application factory and configuration."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import get_db_connection
from .middleware import (
    AuthenticationMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from .routes import register_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Multimodal Contract Extractor API...")
    
    # Initialize database
    try:
        db = get_db_connection()
        db.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        raise
    
    # Create necessary directories
    for directory in ["data", "logs", "cache", "temp"]:
        Path(directory).mkdir(exist_ok=True)
    
    logger.info("API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    
    # Cleanup tasks
    try:
        # Clean up temporary files
        temp_dir = Path("temp")
        if temp_dir.exists():
            for temp_file in temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        logger.info("Cleanup completed")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
    
    logger.info("API shutdown completed")


def create_app(testing: bool = False) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        testing: Whether to configure app for testing
        
    Returns:
        Configured FastAPI application
    """
    # Application configuration
    app_config = {
        "title": "Multimodal Contract Extractor API",
        "description": "AI-powered contract analysis and clause extraction from PDFs and images",
        "version": "0.1.0",
        "docs_url": "/docs" if not testing else None,
        "redoc_url": "/redoc" if not testing else None,
        "openapi_url": "/openapi.json",
        "lifespan": lifespan,
    }
    
    if testing:
        app_config["lifespan"] = None  # Disable lifespan for testing
    
    app = FastAPI(**app_config)
    
    # Setup middleware
    setup_middleware(app, testing=testing)
    
    # Register routes
    register_routes(app)
    
    # Global exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI, testing: bool = False) -> None:
    """
    Setup middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        testing: Whether to configure for testing
    """
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS middleware
    if os.getenv("MCE_ENV") == "development" or testing:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production CORS settings
        allowed_origins = os.getenv("MCE_CORS_ORIGINS", "").split(",")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting middleware (skip in testing)
    if not testing:
        app.add_middleware(RateLimitMiddleware)
    
    # Authentication middleware (skip in testing)
    if not testing:
        app.add_middleware(AuthenticationMiddleware)
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_exception"
                }
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        """Handle ValueError exceptions."""
        logger.warning(f"ValueError: {str(exc)} - {request.url}")
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": 400,
                    "message": str(exc),
                    "type": "validation_error"
                }
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request, exc: FileNotFoundError):
        """Handle FileNotFoundError exceptions."""
        logger.warning(f"FileNotFoundError: {str(exc)} - {request.url}")
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": 404,
                    "message": "File not found",
                    "type": "file_not_found"
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle general exceptions."""
        logger.exception(f"Unhandled exception: {str(exc)} - {request.url}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "type": "internal_error"
                }
            }
        )


# Application factory for deployment
def get_app() -> FastAPI:
    """Get application instance for deployment."""
    return create_app(testing=False)