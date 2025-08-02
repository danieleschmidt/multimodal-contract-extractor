"""
Test utilities for the Multimodal Contract Extractor test suite.

This module provides utility functions, decorators, and helpers for writing
comprehensive tests across the application.
"""

import functools
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import Mock, patch
import pytest
from PIL import Image
import numpy as np


# Test decorators

def with_temp_dir(func: Callable) -> Callable:
    """
    Decorator that provides a temporary directory to the test function.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated function with temp_dir parameter
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            kwargs['temp_dir'] = Path(temp_dir)
            return func(*args, **kwargs)
    return wrapper


def with_mock_config(config_data: Dict[str, Any]):
    """
    Decorator that provides a mock configuration to the test function.
    
    Args:
        config_data: Configuration data to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with patch('multimodal_contract_extractor.config.load_config') as mock_load:
                mock_config = Mock()
                mock_config.to_dict.return_value = config_data
                mock_load.return_value = mock_config
                kwargs['mock_config'] = mock_config
                return func(*args, **kwargs)
        return wrapper
    return decorator


def performance_test(max_duration: float = 10.0):
    """
    Decorator that measures test execution time and fails if it exceeds limit.
    
    Args:
        max_duration: Maximum allowed duration in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > max_duration:
                pytest.fail(f"Test {func.__name__} took {duration:.2f}s, exceeding limit of {max_duration}s")
            
            return result
        return wrapper
    return decorator


def skip_if_no_gpu(func: Callable) -> Callable:
    """
    Decorator that skips test if GPU is not available.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")
        except ImportError:
            pytest.skip("PyTorch not available")
        
        return func(*args, **kwargs)
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 0.1):
    """
    Decorator that retries test on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator


# File utilities

def create_test_pdf(file_path: Path, content: str = "Test PDF content") -> Path:
    """
    Create a test PDF file.
    
    Args:
        file_path: Path where to create the PDF
        content: Content to include in the PDF
        
    Returns:
        Path to created PDF file
    """
    # Simple PDF structure for testing
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(content)}
>>
stream
BT
/F1 12 Tf
100 700 Td
({content}) Tj
ET
endstream
endobj

%%EOF"""
    
    file_path.write_text(pdf_content.encode('utf-8').decode('latin1'))
    return file_path


def create_test_image(file_path: Path, width: int = 800, height: int = 600, 
                     text: str = "Test Document") -> Path:
    """
    Create a test image file with optional text.
    
    Args:
        file_path: Path where to create the image
        width: Image width in pixels
        height: Image height in pixels
        text: Text to include in the image
        
    Returns:
        Path to created image file
    """
    # Create image with text
    image = Image.new('RGB', (width, height), color='white')
    
    # Add text if PIL supports it
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Calculate text position (center)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 10  # Approximate
            text_height = 20
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
    except ImportError:
        # If ImageDraw is not available, just create a plain image
        pass
    
    # Save image
    image.save(file_path)
    return file_path


def create_test_contract_files(base_dir: Path, count: int = 5) -> List[Path]:
    """
    Create multiple test contract files.
    
    Args:
        base_dir: Directory to create files in
        count: Number of files to create
        
    Returns:
        List of created file paths
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    
    contract_types = ["nda", "employment", "service", "lease", "purchase"]
    created_files = []
    
    for i in range(count):
        contract_type = contract_types[i % len(contract_types)]
        
        # Create PDF
        pdf_path = base_dir / f"contract_{i+1}_{contract_type}.pdf"
        content = f"SAMPLE {contract_type.upper()} CONTRACT\n\nThis is a test contract of type {contract_type}."
        create_test_pdf(pdf_path, content)
        created_files.append(pdf_path)
        
        # Create corresponding image
        img_path = base_dir / f"contract_{i+1}_{contract_type}.png"
        create_test_image(img_path, text=f"{contract_type.upper()} CONTRACT")
        created_files.append(img_path)
    
    return created_files


# Data utilities

def load_test_data(file_name: str) -> Dict[str, Any]:
    """
    Load test data from JSON file.
    
    Args:
        file_name: Name of the test data file
        
    Returns:
        Loaded test data
    """
    test_data_dir = Path(__file__).parent / "fixtures"
    file_path = test_data_dir / file_name
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def save_test_data(data: Dict[str, Any], file_name: str) -> Path:
    """
    Save test data to JSON file.
    
    Args:
        data: Data to save
        file_name: Name of the file to save to
        
    Returns:
        Path to saved file
    """
    test_data_dir = Path(__file__).parent / "fixtures"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = test_data_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return file_path


def generate_random_contract_data(contract_type: str = "nda") -> Dict[str, Any]:
    """
    Generate random contract data for testing.
    
    Args:
        contract_type: Type of contract to generate
        
    Returns:
        Generated contract data
    """
    import random
    import string
    
    def random_string(length: int = 10) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def random_company() -> str:
        prefixes = ["Tech", "Global", "Advanced", "Dynamic", "Innovative"]
        suffixes = ["Corp", "Inc", "LLC", "Solutions", "Systems"]
        return f"{random.choice(prefixes)} {random_string(5)} {random.choice(suffixes)}"
    
    def random_name() -> str:
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    clauses = []
    
    if contract_type == "nda":
        clauses = [
            {
                "id": "clause_001",
                "type": "confidentiality",
                "title": "Confidential Information",
                "text": "The receiving party agrees to maintain confidentiality of all disclosed information.",
                "confidence": random.uniform(0.8, 0.95),
                "page": 1,
                "coordinates": [100, random.randint(100, 400), 700, random.randint(150, 450)]
            },
            {
                "id": "clause_002",
                "type": "term",
                "title": "Term of Agreement",
                "text": f"This agreement shall remain in effect for {random.randint(1, 5)} years.",
                "confidence": random.uniform(0.8, 0.95),
                "page": random.randint(1, 2),
                "coordinates": [100, random.randint(200, 500), 700, random.randint(250, 550)]
            }
        ]
    elif contract_type == "employment":
        clauses = [
            {
                "id": "clause_001",
                "type": "compensation",
                "title": "Salary and Benefits",
                "text": f"Employee shall receive annual salary of ${random.randint(50000, 150000):,}.",
                "confidence": random.uniform(0.8, 0.95),
                "page": 1,
                "coordinates": [100, random.randint(100, 400), 700, random.randint(150, 450)]
            },
            {
                "id": "clause_002",
                "type": "termination",
                "title": "Termination Clause",
                "text": f"Employment may be terminated with {random.randint(1, 4)} weeks notice.",
                "confidence": random.uniform(0.8, 0.95),
                "page": random.randint(1, 2),
                "coordinates": [100, random.randint(200, 500), 700, random.randint(250, 550)]
            }
        ]
    
    return {
        "document_info": {
            "filename": f"test_{contract_type}_{random_string(8)}.pdf",
            "pages": random.randint(1, 5),
            "processing_time": random.uniform(5.0, 30.0),
            "overall_confidence": random.uniform(0.75, 0.95),
            "document_type": contract_type
        },
        "parties": [
            {
                "role": "party_a",
                "name": random_company(),
                "address": f"{random.randint(1, 999)} {random_string(8)} St, {random_string(6)} City, {random_string(2).upper()} {random.randint(10000, 99999)}"
            },
            {
                "role": "party_b", 
                "name": random_name(),
                "address": f"{random.randint(1, 999)} {random_string(8)} Ave, {random_string(6)} Town, {random_string(2).upper()} {random.randint(10000, 99999)}"
            }
        ],
        "clauses": clauses,
        "metadata": {
            "extraction_timestamp": "2024-01-15T10:30:00Z",
            "model_version": "test-1.0.0",
            "processing_method": "test"
        }
    }


# Assertion utilities

def assert_contract_data_valid(contract_data: Dict[str, Any]) -> None:
    """
    Assert that contract data has the expected structure.
    
    Args:
        contract_data: Contract data to validate
    """
    # Check required top-level keys
    required_keys = ["document_info", "parties", "clauses", "metadata"]
    for key in required_keys:
        assert key in contract_data, f"Missing required key: {key}"
    
    # Check document_info structure
    doc_info = contract_data["document_info"]
    assert "filename" in doc_info
    assert "pages" in doc_info
    assert "processing_time" in doc_info
    assert "overall_confidence" in doc_info
    
    # Check parties structure
    parties = contract_data["parties"]
    assert isinstance(parties, list)
    assert len(parties) >= 1
    
    for party in parties:
        assert "role" in party
        assert "name" in party
    
    # Check clauses structure
    clauses = contract_data["clauses"]
    assert isinstance(clauses, list)
    
    for clause in clauses:
        assert "id" in clause
        assert "type" in clause
        assert "text" in clause
        assert "confidence" in clause
        assert isinstance(clause["confidence"], (int, float))
        assert 0 <= clause["confidence"] <= 1


def assert_processing_time_acceptable(start_time: float, max_duration: float = 30.0) -> None:
    """
    Assert that processing time is within acceptable limits.
    
    Args:
        start_time: Start time from time.time()
        max_duration: Maximum acceptable duration in seconds
    """
    duration = time.time() - start_time
    assert duration <= max_duration, f"Processing took {duration:.2f}s, exceeding limit of {max_duration}s"


def assert_confidence_scores_valid(data: Dict[str, Any], min_confidence: float = 0.5) -> None:
    """
    Assert that confidence scores are within valid ranges.
    
    Args:
        data: Data containing confidence scores
        min_confidence: Minimum acceptable confidence score
    """
    # Check overall confidence if present
    if "document_info" in data and "overall_confidence" in data["document_info"]:
        overall_conf = data["document_info"]["overall_confidence"]
        assert 0 <= overall_conf <= 1, f"Overall confidence {overall_conf} not in range [0, 1]"
        assert overall_conf >= min_confidence, f"Overall confidence {overall_conf} below minimum {min_confidence}"
    
    # Check clause confidences
    if "clauses" in data:
        for clause in data["clauses"]:
            if "confidence" in clause:
                conf = clause["confidence"]
                assert 0 <= conf <= 1, f"Clause confidence {conf} not in range [0, 1]"
                assert conf >= min_confidence, f"Clause confidence {conf} below minimum {min_confidence}"


# Test environment utilities

def setup_test_environment(temp_dir: Path) -> Dict[str, Any]:
    """
    Set up a complete test environment.
    
    Args:
        temp_dir: Temporary directory for test files
        
    Returns:
        Dictionary containing test environment setup info
    """
    # Create directory structure
    dirs = {
        "input": temp_dir / "input",
        "output": temp_dir / "output", 
        "cache": temp_dir / "cache",
        "logs": temp_dir / "logs"
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create test files
    test_files = create_test_contract_files(dirs["input"], count=3)
    
    # Create test configuration
    config_data = {
        "ocr": {"cache_size_limit": 10},
        "extraction": {"base_confidence_score": 0.7},
        "security": {"max_file_size_mb": 50}
    }
    
    config_file = temp_dir / "test_config.yml"
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(config_data, f)
    
    return {
        "directories": dirs,
        "test_files": test_files,
        "config_file": config_file,
        "config_data": config_data
    }


def cleanup_test_environment(test_env: Dict[str, Any]) -> None:
    """
    Clean up test environment.
    
    Args:
        test_env: Test environment info from setup_test_environment
    """
    # Remove test files
    for file_path in test_env.get("test_files", []):
        if file_path.exists():
            file_path.unlink()
    
    # Remove config file
    config_file = test_env.get("config_file")
    if config_file and config_file.exists():
        config_file.unlink()


# Performance testing utilities

class PerformanceMonitor:
    """Performance monitoring utility for tests."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = None
        self.end_time = None
        self.measurements = {}
    
    def start(self, name: str = "default") -> None:
        """Start timing measurement."""
        self.measurements[name] = {"start": time.time()}
    
    def stop(self, name: str = "default") -> float:
        """
        Stop timing measurement.
        
        Returns:
            Duration in seconds
        """
        if name in self.measurements:
            self.measurements[name]["end"] = time.time()
            duration = self.measurements[name]["end"] - self.measurements[name]["start"]
            self.measurements[name]["duration"] = duration
            return duration
        return 0.0
    
    def get_duration(self, name: str = "default") -> float:
        """Get duration for a measurement."""
        if name in self.measurements and "duration" in self.measurements[name]:
            return self.measurements[name]["duration"]
        return 0.0
    
    def get_all_measurements(self) -> Dict[str, float]:
        """Get all measurements."""
        return {name: data.get("duration", 0.0) for name, data in self.measurements.items()}


def benchmark_function(func: Callable, *args, iterations: int = 10, **kwargs) -> Dict[str, float]:
    """
    Benchmark a function over multiple iterations.
    
    Args:
        func: Function to benchmark
        *args: Arguments for function
        iterations: Number of iterations to run
        **kwargs: Keyword arguments for function
        
    Returns:
        Benchmark statistics
    """
    durations = []
    
    for _ in range(iterations):
        start_time = time.time()
        func(*args, **kwargs)
        duration = time.time() - start_time
        durations.append(duration)
    
    return {
        "min": min(durations),
        "max": max(durations),
        "avg": sum(durations) / len(durations),
        "total": sum(durations),
        "iterations": iterations,
        "durations": durations
    }


# Mock utilities

def create_mock_response(status_code: int = 200, json_data: Optional[Dict] = None) -> Mock:
    """
    Create a mock HTTP response.
    
    Args:
        status_code: HTTP status code
        json_data: JSON data to return
        
    Returns:
        Mock response object
    """
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = json.dumps(json_data or {})
    return mock_response


def patch_external_services():
    """
    Context manager that patches external services for testing.
    
    Returns:
        Dictionary of patched services
    """
    return patch.multiple(
        'multimodal_contract_extractor',
        ocr_service=Mock(),
        vlm_service=Mock(),
        storage_service=Mock(),
        metrics_service=Mock()
    )