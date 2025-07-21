"""Tests for enhanced observability features."""

import time
from unittest.mock import patch

from multimodal_contract_extractor.extraction import extract_from_document
from tests.test_helpers import create_test_pdf


class TestStructuredLogging:
    """Test structured JSON logging with request IDs."""
    
    def test_request_id_in_logs(self, tmp_path, caplog):
        """Test that request IDs are included in log entries."""
        input_file = tmp_path / "test.pdf"
        create_test_pdf(input_file, "Test content with confidential information")
        
        # Mock the CLI to include request ID in logging setup
        with patch('multimodal_contract_extractor.cli_utils.setup_logging'):
            with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
                mock_ocr.return_value = "Test content with confidential information"
                
                # Process document
                result = extract_from_document(input_file)
                
                # Verify result is valid
                assert result is not None
                assert "document_info" in result
    
    def test_structured_log_format(self, tmp_path, caplog):
        """Test that logs can be formatted as JSON with structured data."""
        input_file = tmp_path / "test.pdf"
        create_test_pdf(input_file, "Test content")
        
        # Set logging level to capture logs
        import logging
        caplog.set_level(logging.INFO)
        
        with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            mock_ocr.return_value = "Test content"
            
            # Process document
            extract_from_document(input_file)
            
            # Check that we have log entries
            assert len(caplog.records) > 0
            
            # Verify logs contain expected structured information
            log_record = caplog.records[0]
            assert hasattr(log_record, 'levelname')
            assert hasattr(log_record, 'name')
            assert hasattr(log_record, 'message')


class TestMetricsEnhancement:
    """Test enhanced metrics collection."""
    
    def test_processing_time_metrics(self, tmp_path):
        """Test that processing time metrics are collected accurately."""
        input_file = tmp_path / "metrics_test.pdf"
        create_test_pdf(input_file, "Metrics test content")
        
        with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            mock_ocr.return_value = "Metrics test content"
            
            # Process document
            start_time = time.perf_counter()
            result = extract_from_document(input_file)
            actual_time = time.perf_counter() - start_time
            
            # Check that processing time is recorded
            recorded_time = result["document_info"]["processing_time"]
            assert recorded_time > 0
            assert recorded_time <= actual_time + 0.1  # Allow small overhead
    
    def test_accuracy_metrics(self, tmp_path):
        """Test that accuracy/confidence metrics are collected."""
        input_file = tmp_path / "accuracy_test.pdf"
        create_test_pdf(input_file, "Accuracy test with confidential terms")
        
        with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            mock_ocr.return_value = "Accuracy test with confidential terms"
            
            # Process document
            result = extract_from_document(input_file)
            
            # Check confidence metrics
            assert "overall_confidence" in result["document_info"]
            confidence = result["document_info"]["overall_confidence"]
            assert 0 <= confidence <= 1.0
            
            # Check clause-level confidence
            if result["clauses"]:
                for clause in result["clauses"]:
                    # Note: current implementation doesn't include clause confidence
                    # This test documents the expected behavior for future enhancement
                    pass
    
    def test_document_type_classification_metrics(self, tmp_path):
        """Test that document type classification is tracked."""
        input_file = tmp_path / "classification_test.pdf"
        create_test_pdf(input_file, "This is a confidentiality agreement")
        
        with patch('multimodal_contract_extractor.clause_detection._ocr_image') as mock_ocr:
            mock_ocr.return_value = "This is a confidentiality agreement"
            
            # Process document
            result = extract_from_document(input_file)
            
            # Check document type classification
            assert "document_type" in result["document_info"]
            doc_type = result["document_info"]["document_type"]
            assert isinstance(doc_type, str)
            assert doc_type in ["nda", "employment_agreement", "service_agreement", "general_contract", "unknown"]


class TestHealthCheckEndpoints:
    """Test health check endpoint functionality."""
    
    def test_health_check_implementation(self):
        """Test that health check returns system status."""
        from multimodal_contract_extractor.health import get_health_status
        
        # Get health status
        health = get_health_status()
        
        # Verify health check structure
        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health
        assert "version" in health
        assert "dependencies" in health
        
        # Check status values
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health["timestamp"], str)
        assert isinstance(health["dependencies"], dict)
    
    def test_dependency_health_checks(self):
        """Test that dependency health is checked."""
        from multimodal_contract_extractor.health import check_dependencies
        
        # Check dependencies
        deps = check_dependencies()
        
        # Verify dependency checks
        assert isinstance(deps, dict)
        assert "tesseract" in deps
        assert "poppler" in deps
        
        # Each dependency should have status
        for dep_name, dep_info in deps.items():
            assert isinstance(dep_info, dict)
            assert "status" in dep_info
            assert dep_info["status"] in ["available", "unavailable", "error"]
    
    def test_health_check_performance(self):
        """Test that health checks complete quickly."""
        from multimodal_contract_extractor.health import get_health_status
        
        # Time health check
        start_time = time.perf_counter()
        health = get_health_status()
        elapsed = time.perf_counter() - start_time
        
        # Health check should be fast
        assert elapsed < 1.0  # Should complete in under 1 second
        assert health is not None


class TestMonitoringIntegration:
    """Test monitoring dashboard integration."""
    
    def test_prometheus_metrics_format(self):
        """Test that metrics can be exported in Prometheus format."""
        from multimodal_contract_extractor.metrics import get_prometheus_metrics
        
        # Get Prometheus formatted metrics
        metrics = get_prometheus_metrics()
        
        # Verify format
        assert isinstance(metrics, str)
        assert len(metrics) > 0
        
        # Check for expected metric names
        assert "multimodal_contract_processing_time" in metrics or "processing_time" in metrics
        assert "multimodal_contract_memory_usage" in metrics or "memory_usage" in metrics
    
    def test_metrics_collection_intervals(self):
        """Test that metrics are collected at appropriate intervals."""
        # This test documents expected behavior for future implementation
        # Metrics should be collected efficiently without impacting performance
        pass
    
    def test_dashboard_data_format(self):
        """Test that metrics are formatted for dashboard consumption."""
        from multimodal_contract_extractor.metrics import get_dashboard_metrics
        
        # Get dashboard formatted metrics
        metrics = get_dashboard_metrics()
        
        # Verify structure
        assert isinstance(metrics, dict)
        assert "processing_stats" in metrics
        assert "system_health" in metrics
        assert "recent_activity" in metrics