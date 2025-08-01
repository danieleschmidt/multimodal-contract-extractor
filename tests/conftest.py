"""
Pytest configuration and fixtures for the Multimodal Contract Extractor test suite.

This module provides common fixtures, test configuration, and utilities
used across all test modules.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from multimodal_contract_extractor.config import Config, load_config
from multimodal_contract_extractor.document import Document


@pytest.fixture(scope="session")
def test_config() -> Config:
    """
    Provide a test configuration with safe defaults.
    
    Returns:
        Config: Test-specific configuration object
    """
    config_data = {
        "ocr": {
            "cache_size_limit": 10,
            "context_window_size": 50,
        },
        "extraction": {
            "base_confidence_score": 0.6,
            "length_bonus_divisor": 1000,
            "max_confidence_cap": 0.95,
            "file_size_threshold_mb": 5,
            "streaming_chunk_size": 2,
        },
        "security": {
            "max_file_size_mb": 10,
            "request_id_length_limit": 32,
        },
        "health": {
            "check_timeout_seconds": 1,
        },
        "document": {
            "default_streaming_chunk_size": 3,
        },
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        config = load_config(temp_config_path)
        yield config
    finally:
        Path(temp_config_path).unlink(missing_ok=True)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Provide a temporary directory for test files.
    
    Yields:
        Path: Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """
    Create a sample PDF file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path: Path to sample PDF file
    """
    pdf_path = temp_dir / "sample_contract.pdf"
    
    # Create a minimal PDF-like file for testing
    # Note: This is a mock file, real PDF generation would require reportlab
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    
    return pdf_path


@pytest.fixture
def sample_image_path(temp_dir: Path) -> Path:
    """
    Create a sample image file for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path: Path to sample image file
    """
    image_path = temp_dir / "sample_document.png"
    
    # Create a minimal test image
    image = Image.new('RGB', (800, 600), color='white')
    image.save(image_path, 'PNG')
    
    return image_path


@pytest.fixture
def sample_contract_data() -> Dict[str, Any]:
    """
    Provide sample contract data for testing.
    
    Returns:
        Dict[str, Any]: Sample contract data structure
    """
    return {
        "document_info": {
            "filename": "test_contract.pdf",
            "pages": 3,
            "processing_time": 12.5,
            "overall_confidence": 0.87,
            "document_type": "nda"
        },
        "parties": [
            {
                "role": "disclosing_party",
                "name": "Test Company Inc.",
                "address": "123 Test Street, Test City, TC 12345"
            },
            {
                "role": "receiving_party",
                "name": "Jane Doe",
                "address": "456 Example Ave, Example City, EC 67890"
            }
        ],
        "clauses": [
            {
                "id": "clause_001",
                "type": "confidentiality",
                "title": "Confidential Information",
                "text": "The receiving party agrees to maintain confidentiality...",
                "page": 1,
                "coordinates": [100, 200, 700, 300],
                "confidence": 0.92,
                "key_terms": ["confidentiality", "receiving party", "maintain"]
            },
            {
                "id": "clause_002",
                "type": "term",
                "title": "Term of Agreement",
                "text": "This agreement shall remain in effect for a period of...",
                "page": 2,
                "coordinates": [100, 400, 700, 500],
                "confidence": 0.89,
                "key_terms": ["agreement", "period", "effect"]
            }
        ],
        "metadata": {
            "extraction_timestamp": "2024-01-15T10:30:00Z",
            "model_version": "v1.0.0",
            "processing_method": "test"
        }
    }


@pytest.fixture
def mock_ocr_result() -> Dict[str, Any]:
    """
    Provide mock OCR results for testing.
    
    Returns:
        Dict[str, Any]: Mock OCR result data
    """
    return {
        "text": "CONFIDENTIALITY AGREEMENT\n\nThis agreement is made between Test Company Inc. and Jane Doe...",
        "confidence": 0.91,
        "words": [
            {"text": "CONFIDENTIALITY", "confidence": 0.95, "bbox": [100, 50, 300, 80]},
            {"text": "AGREEMENT", "confidence": 0.93, "bbox": [320, 50, 450, 80]},
            {"text": "This", "confidence": 0.89, "bbox": [100, 100, 130, 120]},
            {"text": "agreement", "confidence": 0.92, "bbox": [140, 100, 220, 120]},
        ],
        "blocks": [
            {
                "text": "CONFIDENTIALITY AGREEMENT",
                "confidence": 0.94,
                "bbox": [100, 50, 450, 80]
            }
        ]
    }


@pytest.fixture
def mock_document(sample_contract_data: Dict[str, Any]) -> Mock:
    """
    Create a mock Document object for testing.
    
    Args:
        sample_contract_data: Sample contract data fixture
        
    Returns:
        Mock: Mock Document object
    """
    mock_doc = Mock(spec=Document)
    mock_doc.filename = sample_contract_data["document_info"]["filename"]
    mock_doc.pages = sample_contract_data["document_info"]["pages"]
    mock_doc.to_dict.return_value = sample_contract_data
    return mock_doc


@pytest.fixture
def api_test_client():
    """
    Provide a test client for API testing.
    
    Note: This would be implemented when API endpoints are added
    """
    # Placeholder for future API testing
    return Mock()


@pytest.fixture(autouse=True)
def reset_caches():
    """
    Reset any global caches before each test.
    
    This fixture runs automatically before each test to ensure clean state.
    """
    # Clear any module-level caches
    with patch.dict('sys.modules'):
        # Reset any cached imports or state
        pass
    yield
    # Cleanup after test


@pytest.fixture
def performance_timer():
    """
    Provide a performance timer for benchmarking tests.
    
    Returns:
        callable: Timer function that returns elapsed time
    """
    import time
    
    start_times = {}
    
    def timer(name: str = "default") -> float:
        if name not in start_times:
            start_times[name] = time.time()
            return 0.0
        else:
            elapsed = time.time() - start_times[name]
            del start_times[name]
            return elapsed
    
    return timer


@pytest.fixture
def test_data_factory():
    """
    Factory for creating various test data structures.
    
    Returns:
        callable: Factory function for test data generation
    """
    def create_test_data(data_type: str, **kwargs) -> Any:
        """
        Create test data of the specified type.
        
        Args:
            data_type: Type of test data to create
            **kwargs: Additional parameters for data creation
            
        Returns:
            Any: Generated test data
        """
        if data_type == "contract":
            return {
                "filename": kwargs.get("filename", "test.pdf"),
                "content": kwargs.get("content", "Sample contract content"),
                "clauses": kwargs.get("clauses", []),
                "confidence": kwargs.get("confidence", 0.85)
            }
        elif data_type == "clause":
            return {
                "id": kwargs.get("id", "test_clause"),
                "type": kwargs.get("type", "general"),
                "text": kwargs.get("text", "Sample clause text"),
                "confidence": kwargs.get("confidence", 0.80)
            }
        else:
            raise ValueError(f"Unknown data type: {data_type}")
    
    return create_test_data


@pytest.fixture
def integration_markers():
    """
    Provide marker utilities for integration tests.
    
    Returns:
        callable: Function to check if running integration tests
    """
    def is_integration_test() -> bool:
        """Check if current test is marked as integration test."""
        return hasattr(pytest.current_test, "pytestmark") and \
               any(mark.name == "integration" for mark in pytest.current_test.pytestmark)
    
    return is_integration_test


# Test data constants
TEST_CONTRACT_TYPES = [
    "nda",
    "employment",
    "service_agreement",
    "lease",
    "purchase_order"
]

TEST_CLAUSE_TYPES = [
    "confidentiality",
    "termination",
    "compensation",
    "term",
    "liability",
    "governing_law"
]

# Performance test thresholds
PERFORMANCE_THRESHOLDS = {
    "document_processing": 30.0,  # seconds
    "clause_extraction": 10.0,    # seconds
    "ocr_processing": 15.0,       # seconds
    "batch_processing": 60.0      # seconds per document
}

# Mock external service responses
MOCK_EXTERNAL_RESPONSES = {
    "health_check": {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"},
    "metrics": {"processed_documents": 100, "success_rate": 0.95},
}


def pytest_configure(config):
    """
    Configure pytest with custom settings.
    
    Args:
        config: Pytest configuration object
    """
    # Add custom markers
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add automatic markers.
    
    Args:
        config: Pytest configuration object
        items: List of collected test items
    """
    for item in items:
        # Automatically mark tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Automatically mark performance tests
        if "performance" in str(item.fspath) or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)
        
        # Automatically mark security tests
        if "security" in str(item.fspath) or "security" in item.name:
            item.add_marker(pytest.mark.security)


def pytest_runtest_setup(item):
    """
    Setup hook called before each test.
    
    Args:
        item: Test item being executed
    """
    # Skip GPU tests if no GPU available
    if "gpu" in [mark.name for mark in item.iter_markers()]:
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")
        except ImportError:
            pytest.skip("PyTorch not available for GPU testing")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up the test environment before running tests.
    
    This fixture runs once per test session and sets up the environment.
    """
    # Ensure test directories exist
    test_dirs = [
        "tests/fixtures",
        "tests/mocks", 
        "tests/performance",
        "tests/e2e",
        "tests/contracts"
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup after all tests
    # Remove any temporary test files or state