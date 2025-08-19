#!/usr/bin/env python3
"""Run the FastAPI development server."""

import logging
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn

from src.api.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Run the API server."""
    # Environment configuration
    host = os.getenv("MCE_HOST", "0.0.0.0")
    port = int(os.getenv("MCE_PORT", "8000"))
    debug = os.getenv("MCE_DEBUG", "false").lower() == "true"
    workers = int(os.getenv("MCE_WORKERS", "1"))

    logger.info("Starting Multimodal Contract Extractor API")
    logger.info(f"Server will run on http://{host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Workers: {workers}")

    # Create FastAPI app
    app = create_app(testing=False)

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        workers=1 if debug else workers,
        access_log=True,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
