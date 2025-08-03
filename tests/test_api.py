"""Integration tests for the REST API."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.models.processing import ProcessingResult, ProcessingStatus, ValidationResult
from src.models.contract import Contract, ContractType


@pytest.fixture
def api_client():
    """Create test client for API testing."""
    app = create_app(testing=True)
    return TestClient(app)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\nSample PDF content for testing" + b"x" * 1000


@pytest.fixture
def sample_image_content():
    """Sample PNG content for testing."""
    return b"\x89PNG\r\n\x1a\n" + b"sample image content" + b"x" * 1000


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    def test_health_check(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "database_status" in data
    
    def test_metrics_endpoint(self, api_client):
        """Test metrics endpoint."""
        response = api_client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "placeholder_metrics" in data
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Multimodal Contract Extractor API"
        assert data["version"] == "0.1.0"
        assert "docs_url" in data


class TestProcessingEndpoints:
    """Test document processing endpoints."""
    
    @patch('src.api.routes.ProcessingService.process_document')
    @patch('src.api.routes.ProcessingResultRepository.save')
    @patch('src.api.routes.ContractRepository.save')
    def test_process_pdf_document(self, mock_contract_save, mock_result_save, mock_process, api_client, sample_pdf_content):
        """Test processing a PDF document."""
        # Mock successful processing
        mock_result = ProcessingResult()
        mock_result.status = ProcessingStatus.COMPLETED
        mock_result.contract = Contract(
            filename="test.pdf",
            contract_type=ContractType.EMPLOYMENT
        )
        mock_result.extracted_data = {"test": "data"}
        mock_process.return_value = mock_result
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            
            # Test the endpoint
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/process",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={
                        "enable_ocr_cache": "true",
                        "confidence_threshold": "0.8"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_id" in data
        assert data["status"] == "completed"
        assert data["message"] == "Processing completed"
        
        # Verify mocks were called
        mock_process.assert_called_once()
        mock_result_save.assert_called_once()
        mock_contract_save.assert_called_once()
        
        # Clean up
        Path(temp_file.name).unlink()
    
    @patch('src.api.routes.ProcessingService.process_document')
    @patch('src.api.routes.ProcessingResultRepository.save')
    def test_process_image_document(self, mock_result_save, mock_process, api_client, sample_image_content):
        """Test processing an image document."""
        # Mock successful processing
        mock_result = ProcessingResult()
        mock_result.status = ProcessingStatus.COMPLETED
        mock_process.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(sample_image_content)
            temp_file.flush()
            
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/process",
                    files={"file": ("test.png", f, "image/png")},
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_id" in data
        
        Path(temp_file.name).unlink()
    
    def test_process_unsupported_file_type(self, api_client):
        """Test processing an unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is a text file")
            temp_file.flush()
            
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/process",
                    files={"file": ("test.txt", f, "text/plain")},
                )
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file type" in data["detail"]
        
        Path(temp_file.name).unlink()
    
    def test_process_no_file(self, api_client):
        """Test processing without providing a file."""
        response = api_client.post("/api/v1/process")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @patch('src.api.routes.ProcessingService.process_document')
    def test_process_document_error(self, mock_process, api_client, sample_pdf_content):
        """Test processing with an error."""
        # Mock processing failure
        mock_process.side_effect = Exception("Processing failed")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/process",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
        
        assert response.status_code == 500
        data = response.json()
        assert "Processing failed" in data["detail"]
        
        Path(temp_file.name).unlink()
    
    @patch('src.api.routes.ProcessingResultRepository.find_by_id')
    def test_get_processing_status(self, mock_find, api_client):
        """Test getting processing status."""
        # Mock processing result
        mock_result = ProcessingResult()
        mock_result.status = ProcessingStatus.COMPLETED
        mock_result.current_stage = mock_result.current_stage
        mock_find.return_value = mock_result
        
        response = api_client.get("/api/v1/process/test-id/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0
        assert "current_stage" in data
    
    @patch('src.api.routes.ProcessingResultRepository.find_by_id')
    def test_get_processing_status_not_found(self, mock_find, api_client):
        """Test getting status for non-existent processing request."""
        mock_find.return_value = None
        
        response = api_client.get("/api/v1/process/nonexistent-id/status")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('src.api.routes.ProcessingResultRepository.find_by_id')
    def test_get_processing_result(self, mock_find, api_client):
        """Test getting processing result."""
        # Mock completed processing result
        mock_result = ProcessingResult()
        mock_result.status = ProcessingStatus.COMPLETED
        mock_result.extracted_data = {"test": "result data"}
        mock_find.return_value = mock_result
        
        response = api_client.get("/api/v1/process/test-id/result")
        
        assert response.status_code == 200
        data = response.json()
        assert data["test"] == "result data"
    
    @patch('src.api.routes.ProcessingResultRepository.find_by_id')
    def test_get_processing_result_not_completed(self, mock_find, api_client):
        """Test getting result for incomplete processing."""
        # Mock in-progress processing result
        mock_result = ProcessingResult()
        mock_result.status = ProcessingStatus.IN_PROGRESS
        mock_find.return_value = mock_result
        
        response = api_client.get("/api/v1/process/test-id/result")
        
        assert response.status_code == 400
        data = response.json()
        assert "not completed" in data["detail"]


class TestContractEndpoints:
    """Test contract management endpoints."""
    
    @patch('src.api.routes.ContractRepository.find_recent')
    def test_list_contracts(self, mock_find, api_client):
        """Test listing contracts."""
        # Mock contract data
        mock_contracts = [
            Contract(
                filename="test1.pdf",
                contract_type=ContractType.EMPLOYMENT,
                pages=3,
                overall_confidence=0.92
            ),
            Contract(
                filename="test2.pdf", 
                contract_type=ContractType.NDA,
                pages=2,
                overall_confidence=0.88
            )
        ]
        mock_find.return_value = mock_contracts
        
        response = api_client.get("/api/v1/contracts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["filename"] == "test1.pdf"
        assert data[0]["contract_type"] == "employment_agreement"
        assert data[1]["filename"] == "test2.pdf"
        assert data[1]["contract_type"] == "nda"
    
    @patch('src.api.routes.ContractRepository.find_by_type')
    def test_list_contracts_by_type(self, mock_find, api_client):
        """Test listing contracts filtered by type."""
        mock_contracts = [
            Contract(
                filename="nda1.pdf",
                contract_type=ContractType.NDA
            )
        ]
        mock_find.return_value = mock_contracts
        
        response = api_client.get("/api/v1/contracts?contract_type=nda")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["contract_type"] == "nda"
        
        mock_find.assert_called_once_with("nda")
    
    @patch('src.api.routes.ContractRepository.find_by_filename')
    def test_list_contracts_by_filename(self, mock_find, api_client):
        """Test listing contracts filtered by filename."""
        mock_contracts = [
            Contract(filename="specific.pdf")
        ]
        mock_find.return_value = mock_contracts
        
        response = api_client.get("/api/v1/contracts?filename=specific.pdf")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "specific.pdf"
        
        mock_find.assert_called_once_with("specific.pdf")
    
    @patch('src.api.routes.ContractRepository.find_by_id')
    def test_get_contract(self, mock_find, api_client):
        """Test getting a specific contract."""
        mock_contract = Contract(
            filename="test.pdf",
            contract_type=ContractType.SERVICE,
            pages=5
        )
        mock_find.return_value = mock_contract
        
        response = api_client.get("/api/v1/contracts/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["contract_type"] == "service_agreement"
        assert data["pages"] == 5
    
    @patch('src.api.routes.ContractRepository.find_by_id')
    def test_get_contract_not_found(self, mock_find, api_client):
        """Test getting non-existent contract."""
        mock_find.return_value = None
        
        response = api_client.get("/api/v1/contracts/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('src.api.routes.ContractRepository.delete')
    def test_delete_contract(self, mock_delete, api_client):
        """Test deleting a contract."""
        mock_delete.return_value = True
        
        response = api_client.delete("/api/v1/contracts/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        mock_delete.assert_called_once_with("test-id")
    
    @patch('src.api.routes.ContractRepository.delete')
    def test_delete_contract_not_found(self, mock_delete, api_client):
        """Test deleting non-existent contract."""
        mock_delete.return_value = False
        
        response = api_client.delete("/api/v1/contracts/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestValidationEndpoints:
    """Test validation endpoints."""
    
    @patch('src.api.routes.ValidationService.validate_document')
    def test_validate_document(self, mock_validate, api_client, sample_pdf_content):
        """Test document validation endpoint."""
        # Mock validation result
        mock_result = ValidationResult(
            is_valid=True,
            file_size_bytes=len(sample_pdf_content),
            file_type="application/pdf",
            pages_detected=1
        )
        mock_validate.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/validate",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["file_type"] == "application/pdf"
        assert data["pages_detected"] == 1
        
        Path(temp_file.name).unlink()
    
    @patch('src.api.routes.ValidationService.validate_document')
    def test_validate_invalid_document(self, mock_validate, api_client, sample_pdf_content):
        """Test validation of invalid document."""
        # Mock validation failure
        mock_result = ValidationResult(is_valid=False)
        mock_result.add_error("Invalid file format")
        mock_validate.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file.flush()
            
            with open(temp_file.name, "rb") as f:
                response = api_client.post(
                    "/api/v1/validate",
                    files={"file": ("invalid.pdf", f, "application/pdf")},
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert "Invalid file format" in data["errors"]
        
        Path(temp_file.name).unlink()


class TestStatisticsEndpoints:
    """Test statistics and analytics endpoints."""
    
    @patch('src.api.routes.ContractRepository.get_statistics')
    @patch('src.api.routes.get_db_connection')
    def test_get_statistics(self, mock_get_db, mock_get_stats, api_client):
        """Test getting system statistics."""
        # Mock statistics
        mock_contract_stats = {
            "total_contracts": 10,
            "by_type": {"nda": 5, "employment_agreement": 3, "service_agreement": 2},
            "processing": {"avg_confidence": 0.91}
        }
        mock_get_stats.return_value = mock_contract_stats
        
        mock_db = Mock()
        mock_db.get_database_stats.return_value = {"contracts_count": 10}
        mock_get_db.return_value = mock_db
        
        response = api_client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "contracts" in data
        assert "database" in data
        assert "processing" in data
        assert data["contracts"]["total_contracts"] == 10


class TestMiddleware:
    """Test API middleware functionality."""
    
    def test_security_headers(self, api_client):
        """Test that security headers are added."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_cors_headers(self, api_client):
        """Test CORS headers in testing mode."""
        response = api_client.options("/health")
        
        # In testing mode, CORS should allow all origins
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_logging_headers(self, api_client):
        """Test that logging middleware adds correlation ID."""
        response = api_client.get("/health")
        
        assert "X-Correlation-ID" in response.headers
        assert "X-Process-Time" in response.headers
    
    def test_cache_control_headers(self, api_client):
        """Test cache control headers."""
        response = api_client.get("/health")
        
        # Health endpoint should have no-cache
        assert "Cache-Control" in response.headers


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_error_handling(self, api_client):
        """Test 404 error response format."""
        response = api_client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @patch('src.api.routes.ContractRepository.find_recent')
    def test_500_error_handling(self, mock_find, api_client):
        """Test 500 error response format."""
        # Mock an exception
        mock_find.side_effect = Exception("Database error")
        
        response = api_client.get("/api/v1/contracts")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 500
        assert data["error"]["type"] == "internal_error"
    
    def test_validation_error_handling(self, api_client):
        """Test validation error response format."""
        # Send invalid query parameter
        response = api_client.get("/api/v1/contracts?limit=invalid")
        
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data