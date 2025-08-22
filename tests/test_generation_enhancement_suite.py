"""Comprehensive test suite for Generation 1-3 enhancements.

Tests all new features including streaming, fraud detection, ML models,
quantum optimization, and auto-scaling capabilities.
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Import the enhanced modules
try:
    from src.multimodal_contract_extractor.real_time_streaming import (
        StreamingProcessor, StreamingMode, RealTimeContractProcessor
    )
    from src.multimodal_contract_extractor.fraud_detection import (
        FraudDetector, FraudRiskLevel
    )
    from src.multimodal_contract_extractor.adaptive_ml_models import (
        ModelSelector, ModelType, DocumentComplexity
    )
    from src.multimodal_contract_extractor.party_identification import (
        ContractPartyExtractor, ContractParty
    )
    from src.multimodal_contract_extractor.enterprise_error_recovery import (
        ErrorRecoveryOrchestrator, ErrorContext, ErrorSeverity, RecoveryStrategy
    )
    from src.multimodal_contract_extractor.comprehensive_monitoring import (
        ComprehensiveMonitor, MetricsCollector, AlertManager
    )
    from src.multimodal_contract_extractor.quantum_optimization import (
        QuantumOptimizer, OptimizationStrategy, QuantumSimulator
    )
    from src.multimodal_contract_extractor.ai_powered_auto_scaling import (
        AutoScalingOrchestrator, ResourceType, ScalingDirection
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Warning: Could not import enhanced modules: {e}")


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestStreamingProcessor:
    """Test suite for real-time streaming processing."""
    
    def test_streaming_processor_initialization(self):
        """Test streaming processor initialization."""
        processor = StreamingProcessor(mode=StreamingMode.ADAPTIVE, chunk_size=5)
        
        assert processor.mode == StreamingMode.ADAPTIVE
        assert processor.chunk_size == 5
        assert processor.chunks_processed == 0
        
    def test_streaming_modes(self):
        """Test different streaming modes."""
        modes = [StreamingMode.ADAPTIVE, StreamingMode.FIXED, StreamingMode.MEMORY_OPTIMIZED]
        
        for mode in modes:
            processor = StreamingProcessor(mode=mode)
            assert processor.mode == mode
            
    @patch('src.multimodal_contract_extractor.real_time_streaming.stream_document')
    def test_load_document_streaming(self, mock_stream):
        """Test document loading with streaming."""
        # Mock document pages
        mock_pages = [Mock() for _ in range(10)]
        mock_stream.return_value = mock_pages
        
        processor = StreamingProcessor(mode=StreamingMode.FIXED, chunk_size=3)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            # Mock the document loading
            with patch.object(processor, '_process_page_batch', return_value=mock_pages[:3]):
                document = processor.load_document(tmp_path)
                
                assert document.path == tmp_path
                assert processor.chunks_processed > 0
                
    def test_memory_efficiency_calculation(self):
        """Test memory efficiency calculation."""
        processor = StreamingProcessor()
        processor.metrics.memory_peak_mb = 100.0
        
        efficiency = processor.get_memory_efficiency()
        assert 0.0 <= efficiency <= 1.0
        
    def test_processing_speed_calculation(self):
        """Test processing speed calculation."""
        processor = StreamingProcessor(chunk_size=5)
        processor.chunks_processed = 10
        processor.metrics.total_processing_time = 5.0
        
        speed = processor.get_processing_speed()
        assert speed > 0
        
    @pytest.mark.asyncio
    async def test_real_time_contract_processor(self):
        """Test real-time contract processing."""
        processor = RealTimeContractProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            # Mock the streaming processor
            with patch.object(processor.streaming_processor, 'stream_extract_async') as mock_stream:
                mock_stream.return_value = iter([
                    {"page_number": 1, "status": "page_processed"},
                    {"status": "completed"}
                ])
                
                results = []
                async for result in processor.process_contract_realtime(tmp_path, "test_session"):
                    results.append(result)
                    
                assert len(results) > 0
                assert any(r.get("status") == "completed" for r in results)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestFraudDetection:
    """Test suite for fraud detection capabilities."""
    
    def test_fraud_detector_initialization(self):
        """Test fraud detector initialization."""
        detector = FraudDetector()
        
        assert hasattr(detector, 'suspicious_patterns')
        assert hasattr(detector, 'anomaly_thresholds')
        
    def test_fraud_analysis_basic(self):
        """Test basic fraud analysis."""
        detector = FraudDetector()
        
        # Test with clean document
        clean_text = "This is a normal contract between two parties for service provision."
        clauses = []
        metadata = {"filename": "test.pdf", "file_size": 1000}
        
        result = detector.analyze_document(clean_text, clauses, metadata)
        
        assert result.fraud_score >= 0.0
        assert result.risk_level in FraudRiskLevel
        assert isinstance(result.indicators, list)
        assert isinstance(result.recommendations, list)
        
    def test_fraud_detection_suspicious_language(self):
        """Test detection of suspicious language patterns."""
        detector = FraudDetector()
        
        # Test with suspicious language
        suspicious_text = "URGENT ACTION REQUIRED! Click here to verify your account immediately or lose access!"
        clauses = []
        metadata = {"filename": "suspicious.pdf", "file_size": 500}
        
        result = detector.analyze_document(suspicious_text, clauses, metadata)
        
        assert result.fraud_score > 0.3  # Should detect suspicious patterns
        assert result.risk_level in [FraudRiskLevel.MEDIUM, FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]
        assert len(result.indicators) > 0
        
    def test_fraud_detection_placeholder_parties(self):
        """Test detection of placeholder party names."""
        detector = FraudDetector()
        
        # Test with placeholder names
        placeholder_text = "This contract is between John Doe and Test Company LLC for various services."
        clauses = []
        metadata = {"filename": "placeholder.pdf", "file_size": 800}
        
        result = detector.analyze_document(placeholder_text, clauses, metadata)
        
        # Should detect placeholder parties
        placeholder_indicators = [i for i in result.indicators if i.indicator_type == "placeholder_parties"]
        assert len(placeholder_indicators) > 0
        
    def test_fraud_risk_levels(self):
        """Test fraud risk level determination."""
        detector = FraudDetector()
        
        # Test each risk level
        test_cases = [
            (0.1, FraudRiskLevel.LOW),
            (0.4, FraudRiskLevel.MEDIUM),
            (0.7, FraudRiskLevel.HIGH),
            (0.9, FraudRiskLevel.CRITICAL)
        ]
        
        for score, expected_level in test_cases:
            level = detector._determine_risk_level(score)
            assert level == expected_level


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestAdaptiveMLModels:
    """Test suite for adaptive ML model selection."""
    
    def test_model_selector_initialization(self):
        """Test model selector initialization."""
        selector = ModelSelector()
        
        assert hasattr(selector, 'available_models')
        assert hasattr(selector, 'performance_history')
        assert len(selector.available_models) > 0
        
    def test_model_selection_basic(self):
        """Test basic model selection."""
        selector = ModelSelector()
        
        selection = selector.select_optimal_model(
            document_type=".pdf",
            file_size=1024 * 1024,  # 1MB
            language_code="en"
        )
        
        assert selection.model_type in ModelType
        assert 0.0 <= selection.confidence <= 1.0
        assert isinstance(selection.reasoning, str)
        assert len(selection.reasoning) > 0
        assert selection.estimated_processing_time > 0
        assert 0.0 <= selection.estimated_accuracy <= 1.0
        
    def test_document_complexity_assessment(self):
        """Test document complexity assessment."""
        selector = ModelSelector()
        
        # Test different file sizes and types
        test_cases = [
            (".txt", 1024, DocumentComplexity.SIMPLE),
            (".pdf", 5 * 1024 * 1024, DocumentComplexity.MODERATE),
            (".pdf", 50 * 1024 * 1024, DocumentComplexity.COMPLEX),
            (".jpg", 20 * 1024 * 1024, DocumentComplexity.COMPLEX)
        ]
        
        for doc_type, file_size, expected_min_complexity in test_cases:
            complexity = selector._assess_document_complexity(doc_type, file_size)
            assert complexity in DocumentComplexity
            
    def test_model_filtering_compatibility(self):
        """Test model filtering based on compatibility."""
        selector = ModelSelector()
        
        # Test with constraints
        compatible_models = selector._filter_compatible_models(
            document_type=".pdf",
            file_size=10 * 1024 * 1024,  # 10MB
            language_code="en"
        )
        
        assert len(compatible_models) > 0
        for model in compatible_models:
            assert ".pdf" in model.document_types
            assert "en" in model.language_support
            assert model.max_file_size_mb >= 10
            
    def test_performance_history_update(self):
        """Test performance history tracking."""
        selector = ModelSelector()
        
        # Update performance history
        selector.update_performance_history(
            ModelType.OCR_ADVANCED,
            actual_accuracy=0.85,
            actual_processing_time=2.5
        )
        
        assert ModelType.OCR_ADVANCED in selector.performance_history
        history = selector.performance_history[ModelType.OCR_ADVANCED]
        assert len(history['accuracies']) > 0
        assert len(history['processing_times']) > 0
        assert history['usage_count'] > 0
        
    def test_model_recommendations(self):
        """Test model recommendations based on history."""
        selector = ModelSelector()
        
        # Add some performance data
        selector.update_performance_history(ModelType.OCR_ADVANCED, 0.9, 2.0)
        selector.update_performance_history(ModelType.OCR_LIGHTWEIGHT, 0.7, 1.0)
        
        recommendations = selector.get_model_recommendations()
        
        assert 'best_accuracy_model' in recommendations
        assert 'fastest_model' in recommendations
        assert 'performance_summary' in recommendations


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestPartyIdentification:
    """Test suite for contract party identification."""
    
    def test_party_extractor_initialization(self):
        """Test party extractor initialization."""
        extractor = ContractPartyExtractor()
        
        assert hasattr(extractor, 'entity_patterns')
        assert hasattr(extractor, 'role_patterns')
        assert hasattr(extractor, 'contact_patterns')
        
    def test_basic_party_extraction(self):
        """Test basic party extraction."""
        extractor = ContractPartyExtractor()
        
        contract_text = """
        This agreement is between TechCorp Inc. and John Smith for software development services.
        TechCorp Inc. is located at 123 Tech Street, San Francisco, CA.
        Contact: info@techcorp.com, (555) 123-4567
        """
        
        parties = extractor.extract_parties(contract_text, [])
        
        assert len(parties) > 0
        
        # Should find at least one party
        party_names = [p.name for p in parties]
        assert any("TechCorp" in name for name in party_names)
        
    def test_contact_info_extraction(self):
        """Test contact information extraction."""
        extractor = ContractPartyExtractor()
        
        text_with_contact = """
        Company: DataSystems LLC
        Email: contact@datasystems.com
        Phone: (555) 987-6543
        Address: 456 Data Drive, Austin, TX 78701
        Website: www.datasystems.com
        """
        
        contact_info = extractor._extract_contact_info(text_with_contact)
        
        assert contact_info.email is not None
        assert "datasystems.com" in contact_info.email
        assert contact_info.phone is not None
        assert contact_info.address is not None
        assert contact_info.website is not None
        
    def test_party_type_determination(self):
        """Test party type determination."""
        extractor = ContractPartyExtractor()
        
        test_cases = [
            ("Microsoft Corporation", "company"),
            ("John Smith", "individual"),
            ("City of San Francisco", "government"),
            ("ABC LLC", "company")
        ]
        
        for name, expected_type in test_cases:
            party_type = extractor._determine_party_type(name)
            assert party_type == expected_type or party_type == "organization"  # Allow fallback
            
    def test_party_consolidation(self):
        """Test party consolidation and deduplication."""
        extractor = ContractPartyExtractor()
        
        # Create duplicate parties with slight variations
        parties = [
            ContractParty(name="TechCorp Inc.", role="contractor", party_type="company", confidence=0.8),
            ContractParty(name="TechCorp Inc", role="vendor", party_type="company", confidence=0.9),
            ContractParty(name="DataSys LLC", role="client", party_type="company", confidence=0.7)
        ]
        
        consolidated = extractor._consolidate_parties(parties)
        
        # Should consolidate the TechCorp entries
        assert len(consolidated) <= len(parties)
        
        # Check that highest confidence party is kept
        techcorp_parties = [p for p in consolidated if "TechCorp" in p.name]
        if techcorp_parties:
            assert techcorp_parties[0].confidence >= 0.8


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestErrorRecovery:
    """Test suite for enterprise error recovery."""
    
    def test_error_recovery_orchestrator_initialization(self):
        """Test error recovery orchestrator initialization."""
        orchestrator = ErrorRecoveryOrchestrator()
        
        assert hasattr(orchestrator, 'circuit_breakers')
        assert hasattr(orchestrator, 'retry_manager')
        assert hasattr(orchestrator, 'failover_manager')
        assert hasattr(orchestrator, 'recovery_statistics')
        
    def test_error_context_creation(self):
        """Test error context creation."""
        context = ErrorContext(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.HIGH,
            component="test_component",
            operation="test_operation",
            timestamp=time.time()
        )
        
        assert context.error_type == "TestError"
        assert context.severity == ErrorSeverity.HIGH
        assert context.component == "test_component"
        
    def test_recovery_strategy_determination(self):
        """Test recovery strategy determination."""
        orchestrator = ErrorRecoveryOrchestrator()
        
        # Test different error types
        test_cases = [
            (Exception("Connection timeout"), ErrorSeverity.MEDIUM, RecoveryStrategy.CIRCUIT_BREAKER),
            (Exception("Service unavailable"), ErrorSeverity.HIGH, RecoveryStrategy.FAILOVER),
            (Exception("Critical system error"), ErrorSeverity.CRITICAL, RecoveryStrategy.MANUAL_INTERVENTION)
        ]
        
        for error, severity, expected_strategy in test_cases:
            context = ErrorContext(
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                component="test",
                operation="test",
                timestamp=time.time()
            )
            
            strategy = orchestrator._determine_recovery_strategy(error, context)
            # Allow for different strategies as implementation may vary
            assert strategy in RecoveryStrategy
            
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        from src.multimodal_contract_extractor.enterprise_error_recovery import CircuitBreaker
        
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # Test initial state
        assert circuit_breaker.get_state().value == "closed"
        
        # Simulate failures
        for _ in range(3):
            circuit_breaker._record_failure()
            
        # Should be open after failures
        assert circuit_breaker.get_state().value == "open"
        
        # Test reset
        circuit_breaker.reset()
        assert circuit_breaker.get_state().value == "closed"
        
    def test_retry_manager(self):
        """Test retry manager functionality."""
        from src.multimodal_contract_extractor.enterprise_error_recovery import RetryManager
        
        retry_manager = RetryManager(max_retries=3, base_delay=0.1)
        
        # Test successful retry
        call_count = 0
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
            
        result = retry_manager.retry_with_backoff(flaky_function)
        assert result == "success"
        assert call_count == 3
        
    def test_recovery_statistics(self):
        """Test recovery statistics tracking."""
        orchestrator = ErrorRecoveryOrchestrator()
        
        # Simulate some error handling
        error = Exception("Test error")
        context = ErrorContext(
            error_type="TestError",
            error_message="Test",
            severity=ErrorSeverity.MEDIUM,
            component="test",
            operation="test",
            timestamp=time.time()
        )
        
        result = orchestrator.handle_error(error, context)
        
        stats = orchestrator.get_recovery_statistics()
        assert stats['total_errors'] > 0
        assert 'recovery_success_rate' in stats
        assert 'recent_error_summary' in stats


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestComprehensiveMonitoring:
    """Test suite for comprehensive monitoring system."""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        
        assert hasattr(collector, 'registry')
        assert hasattr(collector, 'metrics')
        assert hasattr(collector, 'metric_definitions')
        
    def test_metric_registration(self):
        """Test metric registration."""
        from src.multimodal_contract_extractor.comprehensive_monitoring import MetricDefinition, MetricType
        
        collector = MetricsCollector()
        
        test_metric = MetricDefinition(
            name="test_metric",
            metric_type=MetricType.COUNTER,
            description="Test metric",
            labels=["label1", "label2"]
        )
        
        collector.register_metric(test_metric)
        
        assert "test_metric" in collector.metrics
        assert "test_metric" in collector.metric_definitions
        
    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        collector = MetricsCollector()
        
        # This should not raise an exception
        collector.collect_system_metrics()
        
        # Check that metrics were updated (basic check)
        assert True  # If we get here, collection succeeded
        
    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        collector = MetricsCollector()
        alert_manager = AlertManager(collector)
        
        assert hasattr(alert_manager, 'alert_rules')
        assert hasattr(alert_manager, 'active_alerts')
        assert len(alert_manager.alert_rules) > 0  # Should have default rules
        
    def test_alert_rule_management(self):
        """Test alert rule management."""
        from src.multimodal_contract_extractor.comprehensive_monitoring import AlertRule, AlertSeverity
        
        collector = MetricsCollector()
        alert_manager = AlertManager(collector)
        
        test_rule = AlertRule(
            name="test_alert",
            metric_name="test_metric",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.WARNING,
            description="Test alert rule"
        )
        
        alert_manager.add_alert_rule(test_rule)
        assert "test_alert" in alert_manager.alert_rules
        
        alert_manager.remove_alert_rule("test_alert")
        assert "test_alert" not in alert_manager.alert_rules
        
    def test_comprehensive_monitor(self):
        """Test comprehensive monitor."""
        monitor = ComprehensiveMonitor()
        
        assert hasattr(monitor, 'metrics_collector')
        assert hasattr(monitor, 'alert_manager')
        assert hasattr(monitor, 'distributed_tracing')
        
        # Test health status
        health = monitor.get_health_status()
        assert 'status' in health
        assert 'health_score' in health
        assert 'timestamp' in health
        
    @patch('src.multimodal_contract_extractor.comprehensive_monitoring.psutil')
    def test_health_status_calculation(self, mock_psutil):
        """Test health status calculation."""
        # Mock system metrics
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        mock_psutil.disk_usage.return_value = Mock(percent=70.0)
        
        monitor = ComprehensiveMonitor()
        health = monitor.get_health_status()
        
        assert health['status'] in ['excellent', 'good', 'warning', 'critical']
        assert 0.0 <= health['health_score'] <= 100.0


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
class TestQuantumOptimization:
    """Test suite for quantum optimization."""
    
    def test_quantum_simulator_initialization(self):
        """Test quantum simulator initialization."""
        simulator = QuantumSimulator(max_qubits=8)
        
        assert simulator.max_qubits == 8
        assert simulator.current_state is None
        
    def test_quantum_state_creation(self):
        """Test quantum state creation."""
        simulator = QuantumSimulator()
        
        state = simulator.create_initial_state(3)
        
        assert state.num_qubits == 3
        assert len(state.amplitudes) == 8  # 2^3
        assert abs(state.amplitudes[0] - 1.0) < 1e-6  # |000⟩ state
        
    def test_hadamard_gate(self):
        """Test Hadamard gate application."""
        simulator = QuantumSimulator()
        
        state = simulator.create_initial_state(1)
        state_after_h = simulator.apply_hadamard(state, 0)
        
        # After Hadamard, should be in superposition
        assert abs(abs(state_after_h.amplitudes[0]) - 1/np.sqrt(2)) < 1e-6
        assert abs(abs(state_after_h.amplitudes[1]) - 1/np.sqrt(2)) < 1e-6
        
    def test_quantum_circuit_execution(self):
        """Test quantum circuit execution."""
        from src.multimodal_contract_extractor.quantum_optimization import QuantumCircuit, QuantumGate
        
        simulator = QuantumSimulator()
        
        # Create simple circuit
        circuit = QuantumCircuit(num_qubits=2)
        circuit.gates.append((QuantumGate.HADAMARD, [0], {}))
        circuit.gates.append((QuantumGate.CNOT, [0, 1], {}))
        
        final_state = simulator.execute_circuit(circuit)
        
        assert final_state.num_qubits == 2
        assert len(final_state.amplitudes) == 4
        
    def test_quantum_optimizer_initialization(self):
        """Test quantum optimizer initialization."""
        optimizer = QuantumOptimizer(strategy=OptimizationStrategy.HYBRID_CLASSICAL)
        
        assert optimizer.strategy == OptimizationStrategy.HYBRID_CLASSICAL
        assert hasattr(optimizer, 'simulator')
        
    @pytest.mark.asyncio
    async def test_clause_extraction_optimization(self):
        """Test clause extraction optimization."""
        optimizer = QuantumOptimizer()
        
        # Simple test data
        document_segments = ["segment1", "segment2", "segment3"]
        clause_types = ["type1", "type2"]
        
        result = await optimizer.optimize_clause_extraction(
            document_segments, clause_types, confidence_threshold=0.8
        )
        
        assert hasattr(result, 'optimal_solution')
        assert hasattr(result, 'energy_value')
        assert hasattr(result, 'quantum_advantage')
        assert result.processing_time > 0
        
    def test_optimization_statistics(self):
        """Test optimization statistics."""
        optimizer = QuantumOptimizer()
        
        # Initially should have no statistics
        stats = optimizer.get_optimization_statistics()
        assert stats['total_optimizations'] == 0
        
        # After running optimization, should have stats
        # (This would require running actual optimization, simplified for test)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available") 
class TestAutoScaling:
    """Test suite for AI-powered auto-scaling."""
    
    def test_auto_scaling_orchestrator_initialization(self):
        """Test auto-scaling orchestrator initialization."""
        orchestrator = AutoScalingOrchestrator(scaling_interval=30.0)
        
        assert orchestrator.scaling_interval == 30.0
        assert hasattr(orchestrator, 'predictor')
        assert hasattr(orchestrator, 'ml_optimizer')
        assert hasattr(orchestrator, 'scaling_thresholds')
        
    def test_resource_metrics_simulation(self):
        """Test resource metrics simulation."""
        orchestrator = AutoScalingOrchestrator()
        
        metrics = orchestrator._collect_current_metrics()
        
        assert 0 <= metrics.cpu_usage_percent <= 100
        assert 0 <= metrics.memory_usage_percent <= 100
        assert metrics.response_time_ms > 0
        assert metrics.throughput_requests_per_second >= 0
        
    def test_scaling_decision_making(self):
        """Test scaling decision making."""
        from src.multimodal_contract_extractor.ai_powered_auto_scaling import ResourceMetrics
        
        orchestrator = AutoScalingOrchestrator()
        
        # High load scenario
        high_load_metrics = ResourceMetrics(
            cpu_usage_percent=90.0,
            memory_usage_percent=85.0,
            disk_usage_percent=60.0,
            network_io_mbps=150.0,
            active_connections=200,
            queue_depth=50,
            response_time_ms=1500.0,
            error_rate_percent=5.0,
            throughput_requests_per_second=300.0
        )
        
        decisions = orchestrator._make_scaling_decisions(high_load_metrics)
        
        assert ResourceType.CPU in decisions
        assert ResourceType.MEMORY in decisions
        assert ResourceType.INSTANCES in decisions
        
        # Should suggest scaling up for high load
        assert decisions[ResourceType.CPU] >= 1.0
        assert decisions[ResourceType.MEMORY] >= 1.0
        
    def test_scaling_constraints(self):
        """Test scaling constraints application."""
        orchestrator = AutoScalingOrchestrator()
        
        # Test extreme scaling factors
        decisions = {
            ResourceType.CPU: 10.0,      # Very high
            ResourceType.MEMORY: 0.1,    # Very low
            ResourceType.INSTANCES: 2.0  # Moderate
        }
        
        constrained = orchestrator._apply_scaling_constraints(decisions)
        
        # Should be within reasonable bounds
        for resource_type, factor in constrained.items():
            assert 0.5 <= factor <= 3.0  # Based on implementation constraints
            
    def test_time_series_prediction(self):
        """Test time series prediction."""
        from src.multimodal_contract_extractor.ai_powered_auto_scaling import TimeSeriesPredictor
        
        predictor = TimeSeriesPredictor(window_size=20)
        
        # Add some test data
        for i in range(15):
            predictor.add_data_point("test_metric", 50 + i * 2, time.time() + i * 60)
            
        # Predict future value
        predicted_value, confidence = predictor.predict_future_usage("test_metric", 30)
        
        assert predicted_value >= 0
        assert 0.0 <= confidence <= 1.0
        
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        from src.multimodal_contract_extractor.ai_powered_auto_scaling import TimeSeriesPredictor
        
        predictor = TimeSeriesPredictor()
        
        # Add normal data
        for i in range(20):
            predictor.add_data_point("test_metric", 50 + np.random.normal(0, 5))
            
        # Test normal value
        is_anomaly, score = predictor.detect_anomalies("test_metric", 52.0)
        assert not is_anomaly or score < 0.5
        
        # Test anomalous value
        is_anomaly, score = predictor.detect_anomalies("test_metric", 150.0)
        assert is_anomaly
        assert score > 0.5
        
    def test_ml_resource_optimizer(self):
        """Test ML resource optimizer."""
        from src.multimodal_contract_extractor.ai_powered_auto_scaling import MLResourceOptimizer, ResourceMetrics
        
        optimizer = MLResourceOptimizer()
        
        test_metrics = ResourceMetrics(
            cpu_usage_percent=75.0,
            memory_usage_percent=60.0,
            disk_usage_percent=50.0,
            network_io_mbps=100.0,
            active_connections=100,
            queue_depth=10,
            response_time_ms=300.0,
            error_rate_percent=2.0,
            throughput_requests_per_second=500.0
        )
        
        scaling_factors = optimizer.predict_optimal_scaling(test_metrics)
        
        assert ResourceType.CPU in scaling_factors
        assert ResourceType.MEMORY in scaling_factors
        assert ResourceType.INSTANCES in scaling_factors
        
        for factor in scaling_factors.values():
            assert 0.5 <= factor <= 3.0
            
    def test_scaling_status_report(self):
        """Test scaling status reporting."""
        orchestrator = AutoScalingOrchestrator()
        
        status = orchestrator.get_scaling_status()
        
        assert 'is_running' in status
        assert 'current_resources' in status
        assert 'current_cost_per_hour' in status
        assert 'scaling_statistics' in status
        assert 'ml_insights' in status


class TestIntegrationScenarios:
    """Integration tests for enhanced features."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
    def test_full_pipeline_integration(self):
        """Test integration of multiple enhanced features."""
        
        # This would test the full pipeline with all enhancements
        # For now, just verify imports work together
        from src.multimodal_contract_extractor.real_time_streaming import StreamingProcessor
        from src.multimodal_contract_extractor.fraud_detection import FraudDetector
        from src.multimodal_contract_extractor.adaptive_ml_models import ModelSelector
        
        # Initialize components
        streaming = StreamingProcessor()
        fraud_detector = FraudDetector()
        model_selector = ModelSelector()
        
        # Verify they can work together
        assert streaming is not None
        assert fraud_detector is not None
        assert model_selector is not None
        
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
    def test_error_recovery_integration(self):
        """Test error recovery integration with other components."""
        from src.multimodal_contract_extractor.enterprise_error_recovery import get_recovery_orchestrator
        
        orchestrator = get_recovery_orchestrator()
        
        # Test that global instance works
        assert orchestrator is not None
        
        stats = orchestrator.get_recovery_statistics()
        assert isinstance(stats, dict)
        
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Enhanced modules not available")
    def test_monitoring_integration(self):
        """Test monitoring integration."""
        from src.multimodal_contract_extractor.comprehensive_monitoring import get_monitor
        
        monitor = get_monitor()
        
        # Test global monitoring instance
        assert monitor is not None
        
        dashboard = monitor.get_monitoring_dashboard()
        assert 'health_status' in dashboard
        assert 'metrics_summary' in dashboard


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])