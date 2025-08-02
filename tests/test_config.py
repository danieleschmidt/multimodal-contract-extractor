"""
Test configuration for different testing environments.

This module provides configuration classes and utilities for setting up
test environments with appropriate settings for unit, integration, 
performance, and end-to-end tests.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class TestConfig:
    """Base test configuration class."""
    
    # Test environment
    test_env: str = "unit"
    debug_mode: bool = True
    verbose_logging: bool = False
    
    # File and directory settings
    temp_dir: Optional[Path] = None
    test_data_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    
    # OCR settings for testing
    ocr_cache_size_limit: int = 10
    ocr_context_window_size: int = 50
    ocr_confidence_threshold: float = 0.6
    
    # Extraction settings for testing
    extraction_base_confidence: float = 0.6
    extraction_max_confidence: float = 0.95
    extraction_chunk_size: int = 2
    
    # Security settings for testing
    max_file_size_mb: int = 10
    request_id_length_limit: int = 32
    allowed_extensions: List[str] = None
    
    # Performance settings
    processing_timeout: int = 30
    health_check_timeout: int = 1
    
    # Test data settings
    use_real_files: bool = False
    mock_external_services: bool = True
    generate_test_data: bool = True
    
    def __post_init__(self):
        """Initialize default values."""
        if self.allowed_extensions is None:
            self.allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]
        
        if self.test_data_dir is None:
            self.test_data_dir = Path(__file__).parent / "fixtures"
        
        if self.output_dir is None:
            self.output_dir = Path(__file__).parent / "output"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "ocr": {
                "cache_size_limit": self.ocr_cache_size_limit,
                "context_window_size": self.ocr_context_window_size,
                "confidence_threshold": self.ocr_confidence_threshold
            },
            "extraction": {
                "base_confidence_score": self.extraction_base_confidence,
                "max_confidence_cap": self.extraction_max_confidence,
                "streaming_chunk_size": self.extraction_chunk_size,
                "file_size_threshold_mb": 5
            },
            "security": {
                "max_file_size_mb": self.max_file_size_mb,
                "request_id_length_limit": self.request_id_length_limit,
                "allowed_extensions": self.allowed_extensions
            },
            "health": {
                "check_timeout_seconds": self.health_check_timeout
            },
            "document": {
                "default_streaming_chunk_size": self.extraction_chunk_size
            },
            "test": {
                "debug_mode": self.debug_mode,
                "verbose_logging": self.verbose_logging,
                "mock_external_services": self.mock_external_services,
                "processing_timeout": self.processing_timeout,
                "use_real_files": self.use_real_files
            }
        }


@dataclass
class UnitTestConfig(TestConfig):
    """Configuration for unit tests."""
    
    test_env: str = "unit"
    debug_mode: bool = True
    verbose_logging: bool = False
    mock_external_services: bool = True
    use_real_files: bool = False
    generate_test_data: bool = True
    
    # Faster settings for unit tests
    ocr_cache_size_limit: int = 5
    ocr_context_window_size: int = 25
    extraction_chunk_size: int = 1
    processing_timeout: int = 5
    health_check_timeout: int = 1


@dataclass
class IntegrationTestConfig(TestConfig):
    """Configuration for integration tests."""
    
    test_env: str = "integration"
    debug_mode: bool = True
    verbose_logging: bool = True
    mock_external_services: bool = False
    use_real_files: bool = True
    generate_test_data: bool = True
    
    # More realistic settings for integration tests
    ocr_cache_size_limit: int = 25
    ocr_context_window_size: int = 75
    extraction_chunk_size: int = 3
    processing_timeout: int = 30
    health_check_timeout: int = 3
    max_file_size_mb: int = 25


@dataclass
class PerformanceTestConfig(TestConfig):
    """Configuration for performance tests."""
    
    test_env: str = "performance"
    debug_mode: bool = False
    verbose_logging: bool = False
    mock_external_services: bool = False
    use_real_files: bool = True
    generate_test_data: bool = False
    
    # Production-like settings for performance tests
    ocr_cache_size_limit: int = 100
    ocr_context_window_size: int = 100
    extraction_chunk_size: int = 5
    processing_timeout: int = 60
    health_check_timeout: int = 5
    max_file_size_mb: int = 100


@dataclass
class E2ETestConfig(TestConfig):
    """Configuration for end-to-end tests."""
    
    test_env: str = "e2e"
    debug_mode: bool = True
    verbose_logging: bool = True
    mock_external_services: bool = False
    use_real_files: bool = True
    generate_test_data: bool = False
    
    # Full production settings for E2E tests
    ocr_cache_size_limit: int = 100
    ocr_context_window_size: int = 100
    extraction_chunk_size: int = 10
    processing_timeout: int = 120
    health_check_timeout: int = 5
    max_file_size_mb: int = 100


# Configuration factory

def get_test_config(test_type: str = None, **overrides) -> TestConfig:
    """
    Get test configuration based on test type.
    
    Args:
        test_type: Type of test configuration to get
        **overrides: Configuration value overrides
        
    Returns:
        TestConfig instance
    """
    # Determine test type from environment or parameter
    if test_type is None:
        test_type = os.environ.get("TEST_TYPE", "unit")
    
    # Create appropriate configuration
    if test_type == "unit":
        config = UnitTestConfig()
    elif test_type == "integration":
        config = IntegrationTestConfig()
    elif test_type == "performance":
        config = PerformanceTestConfig()
    elif test_type == "e2e":
        config = E2ETestConfig()
    else:
        config = TestConfig(test_env=test_type)
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config