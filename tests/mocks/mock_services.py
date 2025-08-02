"""
Mock services for testing the Multimodal Contract Extractor.

This module provides mock implementations of external services and dependencies
to enable isolated testing without requiring actual external resources.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, MagicMock
from PIL import Image
import numpy as np


class MockOCREngine:
    """Mock OCR engine for testing."""
    
    def __init__(self, confidence: float = 0.85):
        """
        Initialize mock OCR engine.
        
        Args:
            confidence: Default confidence score for OCR results
        """
        self.confidence = confidence
        self.processed_count = 0
    
    def extract_text(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Mock text extraction from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict containing mock OCR results
        """
        self.processed_count += 1
        
        # Simulate processing time
        time.sleep(0.1)
        
        return {
            "text": "SAMPLE CONTRACT\n\nThis is a mock contract for testing purposes.\nConfidentiality clause: All information shall remain confidential.",
            "confidence": self.confidence,
            "words": [
                {"text": "SAMPLE", "confidence": 0.95, "bbox": [100, 50, 200, 80]},
                {"text": "CONTRACT", "confidence": 0.93, "bbox": [220, 50, 350, 80]},
                {"text": "This", "confidence": 0.89, "bbox": [100, 100, 130, 120]},
                {"text": "is", "confidence": 0.92, "bbox": [140, 100, 160, 120]},
                {"text": "a", "confidence": 0.91, "bbox": [170, 100, 180, 120]},
                {"text": "mock", "confidence": 0.87, "bbox": [190, 100, 230, 120]},
                {"text": "contract", "confidence": 0.94, "bbox": [240, 100, 320, 120]},
            ],
            "blocks": [
                {
                    "text": "SAMPLE CONTRACT",
                    "confidence": 0.94,
                    "bbox": [100, 50, 350, 80]
                },
                {
                    "text": "This is a mock contract for testing purposes.",
                    "confidence": 0.90,
                    "bbox": [100, 100, 550, 120]
                },
                {
                    "text": "Confidentiality clause: All information shall remain confidential.",
                    "confidence": 0.88,
                    "bbox": [100, 140, 650, 160]
                }
            ],
            "page_info": {
                "width": 800,
                "height": 600,
                "dpi": 300
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "avg_confidence": self.confidence,
            "engine_version": "mock-1.0.0"
        }


class MockVisionLanguageModel:
    """Mock Vision-Language Model for testing."""
    
    def __init__(self, accuracy: float = 0.92):
        """
        Initialize mock VLM.
        
        Args:
            accuracy: Model accuracy for clause detection
        """
        self.accuracy = accuracy
        self.predictions_made = 0
    
    def detect_clauses(self, text: str, image_data: Optional[bytes] = None) -> List[Dict[str, Any]]:
        """
        Mock clause detection.
        
        Args:
            text: Input text from OCR
            image_data: Optional image data for visual analysis
            
        Returns:
            List of detected clauses
        """
        self.predictions_made += 1
        
        # Simulate processing time
        time.sleep(0.2)
        
        # Generate mock clauses based on text content
        clauses = []
        
        if "confidential" in text.lower():
            clauses.append({
                "id": "clause_001",
                "type": "confidentiality",
                "title": "Confidentiality Clause",
                "text": "All information shall remain confidential.",
                "confidence": self.accuracy,
                "page": 1,
                "coordinates": [100, 140, 650, 160],
                "key_terms": ["confidential", "information", "remain"]
            })
        
        if "termination" in text.lower() or "terminate" in text.lower():
            clauses.append({
                "id": "clause_002",
                "type": "termination",
                "title": "Termination Clause",
                "text": "Either party may terminate this agreement with notice.",
                "confidence": self.accuracy - 0.05,
                "page": 1,
                "coordinates": [100, 200, 650, 220],
                "key_terms": ["termination", "party", "agreement", "notice"]
            })
        
        if "compensation" in text.lower() or "payment" in text.lower():
            clauses.append({
                "id": "clause_003",
                "type": "compensation",
                "title": "Compensation Clause",
                "text": "Payment terms and compensation details.",
                "confidence": self.accuracy - 0.03,
                "page": 1,
                "coordinates": [100, 260, 650, 280],
                "key_terms": ["compensation", "payment", "terms"]
            })
        
        return clauses
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": "mock-vlm-v1",
            "version": "1.0.0",
            "accuracy": self.accuracy,
            "predictions_made": self.predictions_made,
            "supported_languages": ["en", "fr", "es", "de"]
        }


class MockDocumentProcessor:
    """Mock document processor for testing."""
    
    def __init__(self):
        """Initialize mock document processor."""
        self.ocr_engine = MockOCREngine()
        self.vlm = MockVisionLanguageModel()
        self.processed_documents = []
    
    def process_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Mock document processing.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dict containing processing results
        """
        file_path = Path(file_path)
        
        # Simulate OCR processing
        ocr_result = self.ocr_engine.extract_text(file_path)
        
        # Simulate clause detection
        clauses = self.vlm.detect_clauses(ocr_result["text"])
        
        # Create result
        result = {
            "document_info": {
                "filename": file_path.name,
                "pages": 1,
                "processing_time": 0.5,
                "overall_confidence": ocr_result["confidence"],
                "document_type": "mock_contract"
            },
            "parties": [
                {
                    "role": "party_a",
                    "name": "Mock Company Inc.",
                    "address": "123 Test Street, Test City, TC 12345"
                },
                {
                    "role": "party_b",
                    "name": "Test Individual",
                    "address": "456 Example Ave, Example City, EC 67890"
                }
            ],
            "clauses": clauses,
            "metadata": {
                "extraction_timestamp": "2024-01-15T10:30:00Z",
                "model_version": "mock-1.0.0",
                "processing_method": "mock"
            },
            "ocr_results": ocr_result
        }
        
        self.processed_documents.append(result)
        return result
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "documents_processed": len(self.processed_documents),
            "ocr_stats": self.ocr_engine.get_stats(),
            "vlm_stats": self.vlm.get_model_info(),
            "avg_processing_time": 0.5,
            "success_rate": 1.0
        }


class MockHealthChecker:
    """Mock health checker for testing."""
    
    def __init__(self, healthy: bool = True):
        """
        Initialize mock health checker.
        
        Args:
            healthy: Whether the service should report as healthy
        """
        self.healthy = healthy
        self.check_count = 0
    
    def check_health(self) -> Dict[str, Any]:
        """
        Mock health check.
        
        Returns:
            Dict containing health status
        """
        self.check_count += 1
        
        if self.healthy:
            return {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "uptime": 3600,
                "checks": {
                    "database": "healthy",
                    "ocr_engine": "healthy",
                    "vlm": "healthy",
                    "storage": "healthy"
                }
            }
        else:
            return {
                "status": "unhealthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "uptime": 3600,
                "checks": {
                    "database": "healthy",
                    "ocr_engine": "unhealthy",
                    "vlm": "healthy",
                    "storage": "healthy"
                },
                "errors": ["OCR engine connection failed"]
            }
    
    def set_healthy(self, healthy: bool):
        """Set health status."""
        self.healthy = healthy


class MockMetricsCollector:
    """Mock metrics collector for testing."""
    
    def __init__(self):
        """Initialize mock metrics collector."""
        self.metrics = {
            "documents_processed_total": 0,
            "processing_time_seconds": [],
            "errors_total": 0,
            "confidence_scores": [],
            "clauses_detected_total": 0
        }
    
    def increment_counter(self, metric_name: str, value: float = 1.0):
        """Increment a counter metric."""
        if metric_name in self.metrics:
            if isinstance(self.metrics[metric_name], list):
                self.metrics[metric_name].append(value)
            else:
                self.metrics[metric_name] += value
    
    def record_histogram(self, metric_name: str, value: float):
        """Record a histogram metric."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        # Calculate averages for list metrics
        processed_metrics = {}
        for key, value in self.metrics.items():
            if isinstance(value, list) and value:
                processed_metrics[key] = {
                    "count": len(value),
                    "average": sum(value) / len(value),
                    "min": min(value),
                    "max": max(value),
                    "values": value
                }
            else:
                processed_metrics[key] = value
        
        return processed_metrics


class MockFileStorage:
    """Mock file storage for testing."""
    
    def __init__(self):
        """Initialize mock file storage."""
        self.stored_files = {}
        self.storage_stats = {
            "files_stored": 0,
            "total_size_bytes": 0,
            "last_cleanup": "2024-01-15T10:00:00Z"
        }
    
    def store_file(self, file_path: Union[str, Path], content: bytes) -> str:
        """
        Mock file storage.
        
        Args:
            file_path: Path where file should be stored
            content: File content
            
        Returns:
            Storage ID for the file
        """
        file_path = str(file_path)
        storage_id = f"mock_storage_{len(self.stored_files)}"
        
        self.stored_files[storage_id] = {
            "path": file_path,
            "content": content,
            "size": len(content),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        self.storage_stats["files_stored"] += 1
        self.storage_stats["total_size_bytes"] += len(content)
        
        return storage_id
    
    def retrieve_file(self, storage_id: str) -> Optional[bytes]:
        """
        Mock file retrieval.
        
        Args:
            storage_id: ID of file to retrieve
            
        Returns:
            File content or None if not found
        """
        if storage_id in self.stored_files:
            return self.stored_files[storage_id]["content"]
        return None
    
    def delete_file(self, storage_id: str) -> bool:
        """
        Mock file deletion.
        
        Args:
            storage_id: ID of file to delete
            
        Returns:
            True if file was deleted, False if not found
        """
        if storage_id in self.stored_files:
            file_info = self.stored_files.pop(storage_id)
            self.storage_stats["files_stored"] -= 1
            self.storage_stats["total_size_bytes"] -= file_info["size"]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self.storage_stats.copy()


class MockConfiguration:
    """Mock configuration for testing."""
    
    def __init__(self):
        """Initialize mock configuration."""
        self.config = {
            "ocr": {
                "cache_size_limit": 50,
                "context_window_size": 100,
                "confidence_threshold": 0.7
            },
            "extraction": {
                "base_confidence_score": 0.75,
                "length_bonus_divisor": 1000,
                "max_confidence_cap": 0.95,
                "file_size_threshold_mb": 10,
                "streaming_chunk_size": 5
            },
            "security": {
                "max_file_size_mb": 100,
                "request_id_length_limit": 64,
                "allowed_extensions": [".pdf", ".png", ".jpg", ".jpeg"]
            },
            "health": {
                "check_timeout_seconds": 5,
                "check_interval_seconds": 30
            },
            "document": {
                "default_streaming_chunk_size": 10
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self.config.copy()


# Factory functions for creating mock objects

def create_mock_document_processor(**kwargs) -> MockDocumentProcessor:
    """Create a mock document processor with optional customization."""
    processor = MockDocumentProcessor()
    
    # Customize OCR confidence if provided
    if "ocr_confidence" in kwargs:
        processor.ocr_engine.confidence = kwargs["ocr_confidence"]
    
    # Customize VLM accuracy if provided
    if "vlm_accuracy" in kwargs:
        processor.vlm.accuracy = kwargs["vlm_accuracy"]
    
    return processor


def create_mock_health_checker(**kwargs) -> MockHealthChecker:
    """Create a mock health checker with optional customization."""
    return MockHealthChecker(healthy=kwargs.get("healthy", True))


def create_mock_metrics_collector(**kwargs) -> MockMetricsCollector:
    """Create a mock metrics collector with optional initial metrics."""
    collector = MockMetricsCollector()
    
    # Set initial metrics if provided
    if "initial_metrics" in kwargs:
        collector.metrics.update(kwargs["initial_metrics"])
    
    return collector


def create_mock_file_storage(**kwargs) -> MockFileStorage:
    """Create a mock file storage with optional initial files."""
    storage = MockFileStorage()
    
    # Add initial files if provided
    if "initial_files" in kwargs:
        for file_path, content in kwargs["initial_files"].items():
            storage.store_file(file_path, content)
    
    return storage


def create_mock_configuration(**kwargs) -> MockConfiguration:
    """Create a mock configuration with optional overrides."""
    config = MockConfiguration()
    
    # Apply configuration overrides if provided
    if "config_overrides" in kwargs:
        for key, value in kwargs["config_overrides"].items():
            config.set(key, value)
    
    return config


# Utility functions for test data generation

def generate_mock_image(width: int = 800, height: int = 600, format: str = "PNG") -> bytes:
    """
    Generate mock image data for testing.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Image data as bytes
    """
    # Create a simple test image with text
    image = Image.new('RGB', (width, height), color='white')
    
    # Save to bytes
    import io
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def generate_mock_pdf_content() -> bytes:
    """
    Generate mock PDF content for testing.
    
    Returns:
        PDF-like content as bytes
    """
    # Simple PDF-like structure for testing
    pdf_content = b"""%PDF-1.4
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
>>
endobj

%%EOF"""
    
    return pdf_content


def generate_mock_contract_text(contract_type: str = "nda") -> str:
    """
    Generate mock contract text for testing.
    
    Args:
        contract_type: Type of contract to generate
        
    Returns:
        Mock contract text
    """
    base_text = "CONFIDENTIALITY AGREEMENT\n\n"
    
    if contract_type == "nda":
        base_text += """This Non-Disclosure Agreement ("Agreement") is entered into between Company A and Company B.

CONFIDENTIALITY CLAUSE: The receiving party agrees to maintain the confidentiality of all disclosed information.

TERM: This agreement shall remain in effect for a period of two (2) years.

TERMINATION: Either party may terminate this agreement with thirty (30) days written notice."""
    
    elif contract_type == "employment":
        base_text = "EMPLOYMENT AGREEMENT\n\n"
        base_text += """This Employment Agreement is between Employer Corp and Employee Name.

COMPENSATION: Employee shall receive an annual salary of $75,000.

TERMINATION: Employment may be terminated by either party with two weeks notice.

CONFIDENTIALITY: Employee agrees to maintain confidentiality of company information."""
    
    elif contract_type == "service":
        base_text = "SERVICE AGREEMENT\n\n"
        base_text += """This Service Agreement is between Service Provider and Client.

SERVICES: Provider shall deliver consulting services as outlined in Schedule A.

PAYMENT: Client shall pay $150 per hour for services rendered.

TERMINATION: Either party may terminate with 30 days written notice."""
    
    return base_text