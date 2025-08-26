#!/usr/bin/env python3
"""
Comprehensive Test Suite for Autonomous SDLC v6.0
Advanced testing framework with quantum-enhanced validation, 
performance benchmarking, and enterprise-grade quality assurance.
"""

import asyncio
import pytest
import time
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all components to test
from multimodal_contract_extractor.autonomous_sdlc_v6_orchestrator import (
    AutonomousSDLCOrchestrator,
    SDLCGeneration,
    QualityGate,
    ResearchOpportunity
)
from multimodal_contract_extractor.enterprise_resilience_v2 import (
    EnterpriseResilienceOrchestrator,
    AdvancedCircuitBreaker,
    IntelligentRetryPolicy
)
from multimodal_contract_extractor.comprehensive_validation_v2 import (
    ComprehensiveValidator,
    ValidationLevel,
    ValidationResult
)
from multimodal_contract_extractor.enterprise_error_recovery_v2 import (
    EnterpriseErrorRecoverySystem,
    ErrorSeverity,
    RecoveryStrategy
)
from multimodal_contract_extractor.enterprise_security_framework_v2 import (
    EnterpriseSecurityOrchestrator,
    ThreatLevel,
    SecurityLevel
)
from multimodal_contract_extractor.comprehensive_logging_system_v2 import (
    ComprehensiveLogger,
    LogLevel,
    LoggingConfig
)
from multimodal_contract_extractor.advanced_monitoring_health_v2 import (
    AdvancedMonitoringOrchestrator,
    HealthStatus,
    MetricType
)
from multimodal_contract_extractor.quantum_performance_optimizer_v3 import (
    GlobalPerformanceOptimizer,
    OptimizationStrategy,
    CacheStrategy
)
from multimodal_contract_extractor.horizontal_scaling_orchestrator_v3 import (
    HorizontalScalingOrchestrator,
    TaskPriority,
    ScalingMode
)


class TestConfiguration:
    """Test configuration and utilities"""
    
    def __init__(self):
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="sdlc_test_"))
        self.test_start_time = datetime.utcnow()
        self.performance_benchmarks = {
            'max_response_time_ms': 5000,
            'min_throughput_ops_sec': 100,
            'max_memory_usage_mb': 1024,
            'min_cache_hit_rate': 0.8
        }
    
    def cleanup(self):
        """Clean up test resources"""
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)


@pytest.fixture
def test_config():
    """Test configuration fixture"""
    config = TestConfiguration()
    yield config
    config.cleanup()


@pytest.fixture
def sample_requirements():
    """Sample SDLC requirements for testing"""
    return [
        "Implement advanced document processing with 99.9% accuracy",
        "Add real-time fraud detection with sub-second response times",
        "Integrate quantum-enhanced security framework",
        "Ensure enterprise-grade scalability and resilience",
        "Implement comprehensive monitoring and observability"
    ]


class TestAutonomousSDLCOrchestrator:
    """Test the main SDLC orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, test_config):
        """Test orchestrator initialization"""
        orchestrator = AutonomousSDLCOrchestrator()
        
        assert orchestrator is not None
        assert orchestrator.current_generation == SDLCGeneration.GENERATION_1
        assert len(orchestrator.quality_gates) > 0
        assert orchestrator.research_mode is False
    
    @pytest.mark.asyncio
    async def test_full_lifecycle_execution(self, test_config, sample_requirements):
        """Test complete SDLC lifecycle execution"""
        orchestrator = AutonomousSDLCOrchestrator()
        
        start_time = time.time()
        
        try:
            result = await orchestrator.execute_full_lifecycle(
                requirements=sample_requirements,
                target_quality_score=0.85
            )
            
            execution_time = time.time() - start_time
            
            # Validate results
            assert result is not None
            assert 'lifecycle_status' in result
            assert result['lifecycle_status'] == 'completed'
            assert 'quality_score' in result
            assert result['quality_score'] >= 0.85
            assert 'generations_completed' in result
            assert result['generations_completed'] >= 3
            
            # Performance benchmark
            assert execution_time < test_config.performance_benchmarks['max_response_time_ms'] / 1000
            
        except Exception as e:
            pytest.fail(f"Full lifecycle execution failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_generation_progression(self, test_config, sample_requirements):
        """Test progression through SDLC generations"""
        orchestrator = AutonomousSDLCOrchestrator()
        
        # Test Generation 1: MAKE IT WORK
        gen1_result = await orchestrator._execute_generation_1(sample_requirements)
        assert gen1_result is not None
        assert len(gen1_result['implementations']) > 0
        
        # Test Generation 2: MAKE IT ROBUST
        gen2_result = await orchestrator._execute_generation_2(gen1_result)
        assert gen2_result is not None
        assert 'resilience_components' in gen2_result
        
        # Test Generation 3: MAKE IT SCALE
        gen3_result = await orchestrator._execute_generation_3(gen2_result)
        assert gen3_result is not None
        assert 'scaling_components' in gen3_result
    
    @pytest.mark.asyncio
    async def test_quality_gates_validation(self, test_config):
        """Test quality gates validation"""
        orchestrator = AutonomousSDLCOrchestrator()
        
        # Mock implementation results
        mock_results = {
            'test_coverage': 0.95,
            'code_quality_score': 0.88,
            'security_scan_score': 0.92,
            'performance_benchmarks': {'latency_ms': 150, 'throughput': 500}
        }
        
        quality_result = await orchestrator._validate_quality_gates(mock_results)
        
        assert quality_result is not None
        assert 'overall_score' in quality_result
        assert 'gate_results' in quality_result
        assert quality_result['overall_score'] > 0.85
    
    @pytest.mark.asyncio
    async def test_research_mode_execution(self, test_config):
        """Test research mode execution"""
        orchestrator = AutonomousSDLCOrchestrator()
        orchestrator.research_mode = True
        
        research_opportunities = [
            ResearchOpportunity(
                opportunity_id="quantum_ml",
                title="Quantum Machine Learning Integration",
                description="Investigate quantum-enhanced ML algorithms",
                priority=0.9,
                estimated_impact=0.8,
                research_domains=["quantum_computing", "machine_learning"],
                success_criteria={"accuracy_improvement": 0.15}
            )
        ]
        
        research_result = await orchestrator._execute_research_opportunities(research_opportunities)
        
        assert research_result is not None
        assert 'research_results' in research_result
        assert len(research_result['research_results']) > 0


class TestEnterpriseResilience:
    """Test enterprise resilience framework"""
    
    @pytest.mark.asyncio
    async def test_resilience_orchestrator_initialization(self, test_config):
        """Test resilience orchestrator initialization"""
        orchestrator = EnterpriseResilienceOrchestrator()
        
        assert orchestrator is not None
        assert len(orchestrator.circuit_breakers) == 0  # Initially empty
        assert len(orchestrator.retry_policies) == 0  # Initially empty
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, test_config):
        """Test circuit breaker functionality"""
        orchestrator = EnterpriseResilienceOrchestrator()
        
        # Create circuit breaker
        cb = orchestrator.get_circuit_breaker(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=5,
            expected_exception=Exception
        )
        
        assert cb is not None
        assert cb.state == "CLOSED"
        
        # Simulate failures
        failing_function = Mock(side_effect=Exception("Service failure"))
        
        # Test failures until circuit opens
        for i in range(4):
            try:
                result = await cb.call(failing_function)
            except Exception:
                pass
        
        assert cb.state == "OPEN"
        
        # Test that calls are rejected when open
        with pytest.raises(Exception):
            await cb.call(failing_function)
    
    @pytest.mark.asyncio
    async def test_retry_policy_functionality(self, test_config):
        """Test intelligent retry policy"""
        orchestrator = EnterpriseResilienceOrchestrator()
        
        retry_policy = orchestrator.get_retry_policy(
            name="test_retry",
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            backoff_multiplier=2.0
        )
        
        assert retry_policy is not None
        
        # Test successful retry after failure
        call_count = 0
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await retry_policy.execute(failing_then_success)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_self_healing_mechanisms(self, test_config):
        """Test self-healing mechanisms"""
        orchestrator = EnterpriseResilienceOrchestrator()
        
        # Enable self-healing
        await orchestrator.enable_self_healing()
        
        # Simulate system degradation
        degradation_event = {
            'component': 'database',
            'issue': 'high_latency',
            'severity': 'medium',
            'metrics': {'avg_response_time': 5000}
        }
        
        healing_result = await orchestrator._attempt_self_healing(degradation_event)
        
        assert healing_result is not None
        assert 'healing_actions' in healing_result
        assert len(healing_result['healing_actions']) > 0


class TestComprehensiveValidation:
    """Test comprehensive validation system"""
    
    def test_validator_initialization(self, test_config):
        """Test validator initialization"""
        validator = ComprehensiveValidator()
        
        assert validator is not None
        assert len(validator.validation_rules) > 0
        assert validator.ml_validator is not None
    
    @pytest.mark.asyncio
    async def test_multi_layer_validation(self, test_config):
        """Test multi-layer validation process"""
        validator = ComprehensiveValidator()
        
        test_data = {
            'code': 'def test_function(): return "Hello World"',
            'documentation': 'A simple test function',
            'tests': ['test_basic_functionality()'],
            'performance_metrics': {'execution_time': 0.001},
            'security_scan': {'vulnerabilities': []}
        }
        
        result = await validator.validate(test_data, ValidationLevel.COMPREHENSIVE)
        
        assert result is not None
        assert isinstance(result, ValidationResult)
        assert result.overall_score > 0
        assert len(result.validation_details) > 0
        assert result.passed is not None
    
    def test_semantic_validation(self, test_config):
        """Test semantic validation capabilities"""
        validator = ComprehensiveValidator()
        
        # Test code semantic validation
        code_data = {
            'code': '''
            def process_document(document):
                if document is None:
                    raise ValueError("Document cannot be None")
                return document.upper()
            ''',
            'function_name': 'process_document',
            'expected_behavior': 'converts document to uppercase'
        }
        
        semantic_result = validator._validate_semantic_correctness(code_data)
        
        assert semantic_result['is_valid'] is True
        assert semantic_result['confidence'] > 0.7
    
    def test_cross_reference_validation(self, test_config):
        """Test cross-reference validation"""
        validator = ComprehensiveValidator()
        
        reference_data = {
            'api_definition': {'endpoint': '/process', 'method': 'POST'},
            'implementation': {'function_name': 'process_request'},
            'documentation': 'POST /process - processes incoming requests',
            'tests': ['test_process_endpoint()']
        }
        
        cross_ref_result = validator._validate_cross_references(reference_data)
        
        assert cross_ref_result['consistency_score'] > 0.5
        assert 'inconsistencies' in cross_ref_result


class TestErrorRecoverySystem:
    """Test enterprise error recovery system"""
    
    @pytest.mark.asyncio
    async def test_error_recovery_initialization(self, test_config):
        """Test error recovery system initialization"""
        recovery_system = EnterpriseErrorRecoverySystem()
        
        assert recovery_system is not None
        assert len(recovery_system.recovery_strategies) > 0
        assert recovery_system.error_classifier is not None
    
    @pytest.mark.asyncio
    async def test_error_classification(self, test_config):
        """Test intelligent error classification"""
        recovery_system = EnterpriseErrorRecoverySystem()
        
        test_exceptions = [
            Exception("Connection timeout"),
            ValueError("Invalid input format"),
            MemoryError("Out of memory"),
            KeyError("Missing configuration key")
        ]
        
        for exception in test_exceptions:
            classification = await recovery_system._classify_error(exception)
            
            assert 'error_type' in classification
            assert 'severity' in classification
            assert 'recovery_strategy' in classification
            assert classification['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_automated_rollback(self, test_config):
        """Test automated rollback functionality"""
        recovery_system = EnterpriseErrorRecoverySystem()
        
        # Mock system state
        original_state = {
            'database_version': '1.0',
            'config_version': '2.0',
            'deployed_services': ['service_a', 'service_b']
        }
        
        # Save checkpoint
        checkpoint_id = await recovery_system.save_checkpoint(original_state)
        assert checkpoint_id is not None
        
        # Simulate system changes
        modified_state = original_state.copy()
        modified_state['database_version'] = '1.1'
        modified_state['deployed_services'].append('service_c')
        
        # Test rollback
        rollback_result = await recovery_system.rollback_to_checkpoint(checkpoint_id)
        
        assert rollback_result['success'] is True
        assert 'rollback_actions' in rollback_result
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_execution(self, test_config):
        """Test recovery strategy execution"""
        recovery_system = EnterpriseErrorRecoverySystem()
        
        error_context = {
            'error_type': 'network_timeout',
            'component': 'api_client',
            'severity': ErrorSeverity.MEDIUM,
            'retry_count': 0
        }
        
        # Test different recovery strategies
        strategies = [
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.CIRCUIT_BREAKER,
            RecoveryStrategy.FAILOVER,
            RecoveryStrategy.GRACEFUL_DEGRADATION
        ]
        
        for strategy in strategies:
            recovery_result = await recovery_system._execute_recovery_strategy(
                strategy, error_context
            )
            
            assert recovery_result is not None
            assert 'strategy_applied' in recovery_result
            assert recovery_result['strategy_applied'] == strategy.name


class TestSecurityFramework:
    """Test enterprise security framework"""
    
    @pytest.mark.asyncio
    async def test_security_orchestrator_initialization(self, test_config):
        """Test security orchestrator initialization"""
        security_orchestrator = EnterpriseSecurityOrchestrator()
        
        assert security_orchestrator is not None
        assert security_orchestrator.input_sanitizer is not None
        assert security_orchestrator.threat_detector is not None
        assert security_orchestrator.zero_trust is not None
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, test_config):
        """Test input sanitization functionality"""
        security_orchestrator = EnterpriseSecurityOrchestrator()
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "$(rm -rf /)",
            "javascript:alert('test')"
        ]
        
        for malicious_input in malicious_inputs:
            request_data = {'user_input': malicious_input}
            user_context = {'user_id': 'test_user', 'auth_method': 'jwt_token'}
            
            security_result = await security_orchestrator.secure_request(
                request_data, user_context
            )
            
            assert security_result is not None
            assert 'sanitized_data' in security_result
            assert len(security_result['threats_detected']) > 0
            
            # Verify malicious content is neutralized
            sanitized_input = security_result['sanitized_data'].get('user_input', '')
            assert malicious_input not in sanitized_input
    
    @pytest.mark.asyncio
    async def test_threat_detection(self, test_config):
        """Test threat detection engine"""
        security_orchestrator = EnterpriseSecurityOrchestrator()
        
        suspicious_requests = [
            {
                'source_ip': '192.168.1.100',
                'headers': {'user-agent': ''},
                'payload': {'sql_query': "SELECT * FROM users WHERE id = '1' OR '1'='1'"}
            },
            {
                'source_ip': '10.0.0.1',
                'headers': {'user-agent': 'sqlmap/1.0'},
                'payload': {'file_path': '../../../etc/passwd'}
            }
        ]
        
        for request in suspicious_requests:
            threat_level, risk_score, threats = security_orchestrator.threat_detector.analyze_request(request)
            
            assert threat_level is not None
            assert risk_score >= 0
            assert len(threats) > 0
            assert threat_level.value >= ThreatLevel.MEDIUM.value
    
    @pytest.mark.asyncio
    async def test_zero_trust_verification(self, test_config):
        """Test zero trust framework"""
        security_orchestrator = EnterpriseSecurityOrchestrator()
        
        # Test legitimate user
        legitimate_context = {
            'user_id': 'admin_user',
            'auth_method': 'multi_factor',
            'device_info': {'device_id': 'known_device', 'is_managed': True},
            'network_info': {'type': 'corporate', 'is_vpn': True}
        }
        
        access_granted, reason, result = security_orchestrator.zero_trust.verify_access(
            'admin_user', '/api/sensitive', 'read', legitimate_context
        )
        
        assert access_granted is True
        assert result['risk_score'] < 0.5
        
        # Test suspicious user
        suspicious_context = {
            'user_id': 'unknown_user',
            'auth_method': 'api_key',
            'device_info': {'device_id': 'unknown_device', 'is_managed': False},
            'network_info': {'type': 'public', 'is_vpn': False}
        }
        
        access_granted, reason, result = security_orchestrator.zero_trust.verify_access(
            'unknown_user', '/api/sensitive', 'write', suspicious_context
        )
        
        assert access_granted is False
        assert result['risk_score'] > 0.5


class TestLoggingSystem:
    """Test comprehensive logging system"""
    
    def test_logger_initialization(self, test_config):
        """Test logger initialization"""
        config = LoggingConfig(
            log_directory=str(test_config.test_data_dir),
            enable_async_logging=False  # Disable for testing
        )
        
        logger = ComprehensiveLogger("test_logger", config)
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.writers) > 0
    
    def test_structured_logging(self, test_config):
        """Test structured logging functionality"""
        config = LoggingConfig(
            log_directory=str(test_config.test_data_dir),
            enable_structured_logging=True,
            enable_async_logging=False
        )
        
        logger = ComprehensiveLogger("test_logger", config)
        
        # Test different log levels
        logger.info("Test info message", user_id="test_user")
        logger.warning("Test warning", request_id="req_123")
        logger.error("Test error", exception=Exception("Test exception"))
        logger.security("Security event", metadata={"threat_level": "high"})
        logger.business("Business event", contract_id="contract_123")
        
        # Test performance logging
        with logger.timer("test_operation"):
            time.sleep(0.1)
        
        # Verify log statistics
        stats = logger.get_statistics()
        assert stats['total_logs'] > 0
        assert 'log_counts' in stats
    
    def test_log_aggregation(self, test_config):
        """Test log aggregation functionality"""
        config = LoggingConfig(
            log_directory=str(test_config.test_data_dir),
            enable_async_logging=False
        )
        
        logger = ComprehensiveLogger("test_logger", config)
        
        # Generate various log entries
        for i in range(10):
            logger.info(f"Info message {i}")
            if i % 3 == 0:
                logger.error(f"Error message {i}")
            if i % 5 == 0:
                logger.performance(f"Performance metric {i}", i * 10.0)
        
        stats = logger.get_statistics()
        
        assert stats['total_logs'] >= 10
        assert stats['error_count'] > 0
        assert len(stats['performance_metrics']) > 0


class TestMonitoringSystem:
    """Test advanced monitoring system"""
    
    @pytest.mark.asyncio
    async def test_monitoring_initialization(self, test_config):
        """Test monitoring system initialization"""
        monitor = AdvancedMonitoringOrchestrator()
        
        assert monitor is not None
        assert monitor.metrics_collector is not None
        assert monitor.health_checker is not None
        assert monitor.alert_manager is not None
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, test_config):
        """Test metrics collection functionality"""
        monitor = AdvancedMonitoringOrchestrator()
        
        # Start monitoring briefly
        await monitor.start_monitoring()
        await asyncio.sleep(2)
        
        # Check that metrics are being collected
        metrics = monitor.metrics_collector.get_all_metrics()
        assert len(metrics) > 0
        
        # Verify system metrics are present
        metric_names = [m['name'] for m in metrics if m]
        system_metrics = [name for name in metric_names if name.startswith('system.')]
        assert len(system_metrics) > 0
        
        monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_health_checks(self, test_config):
        """Test health check functionality"""
        monitor = AdvancedMonitoringOrchestrator()
        
        await monitor.start_monitoring()
        await asyncio.sleep(3)
        
        overall_health, health_details = monitor.health_checker.get_overall_health()
        
        assert overall_health is not None
        assert health_details is not None
        assert 'checks' in health_details
        assert len(health_details['checks']) > 0
        
        monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_alerting_system(self, test_config):
        """Test alerting system"""
        monitor = AdvancedMonitoringOrchestrator()
        
        # Add test alert callback
        alerts_received = []
        
        def test_alert_handler(alert):
            alerts_received.append(alert)
        
        monitor.alert_manager.add_notification_channel(test_alert_handler)
        
        # Start monitoring and let it run
        await monitor.start_monitoring()
        await asyncio.sleep(3)
        
        # Force high CPU usage metric to trigger alert
        monitor.metrics_collector.record_metric("system.cpu.usage_percent", 95.0)
        
        # Evaluate alerts
        await monitor.alert_manager.evaluate_alerts()
        
        alert_summary = monitor.alert_manager.get_alert_summary()
        
        # Verify alerting is working (may or may not trigger based on thresholds)
        assert 'active_alerts' in alert_summary
        assert 'alert_counts' in alert_summary
        
        monitor.stop_monitoring()


class TestPerformanceOptimization:
    """Test quantum performance optimization"""
    
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self, test_config):
        """Test performance optimizer initialization"""
        optimizer = GlobalPerformanceOptimizer()
        
        assert optimizer is not None
        assert optimizer.quantum_optimizer is not None
        assert optimizer.cache_system is not None
        assert optimizer.scaling_engine is not None
    
    @pytest.mark.asyncio
    async def test_cache_system(self, test_config):
        """Test adaptive cache system"""
        optimizer = GlobalPerformanceOptimizer()
        
        # Test cache operations
        test_data = {'key1': 'value1', 'key2': 'value2'}
        
        for key, value in test_data.items():
            optimizer.cache_system.put(key, value, compute_cost=0.5)
        
        # Test retrieval
        for key, expected_value in test_data.items():
            cached_value = optimizer.cache_system.get(key)
            assert cached_value == expected_value
        
        # Test cache statistics
        stats = optimizer.cache_system.get_cache_statistics()
        assert stats['hit_rate'] > 0
        assert stats['total_entries'] == len(test_data)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, test_config):
        """Test performance monitoring"""
        optimizer = GlobalPerformanceOptimizer()
        
        # Start optimization
        await optimizer.start_optimization()
        await asyncio.sleep(2)
        
        # Check optimization status
        status = optimizer.get_optimization_status()
        
        assert status is not None
        assert 'optimization_active' in status
        assert 'performance_metrics' in status
        assert 'optimization_score' in status
        
        optimizer.stop_optimization()
    
    def test_quantum_cache_decorator(self, test_config):
        """Test quantum cache decorator"""
        from multimodal_contract_extractor.quantum_performance_optimizer_v3 import quantum_cache
        
        call_count = 0
        
        @quantum_cache(max_size=100)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment


class TestHorizontalScaling:
    """Test horizontal scaling orchestrator"""
    
    @pytest.mark.asyncio
    async def test_scaling_orchestrator_initialization(self, test_config):
        """Test scaling orchestrator initialization"""
        orchestrator = HorizontalScalingOrchestrator(max_nodes=10)
        
        assert orchestrator is not None
        assert orchestrator.task_queue is not None
        assert orchestrator.load_balancer is not None
        assert orchestrator.auto_scaler is not None
    
    @pytest.mark.asyncio
    async def test_task_submission_and_processing(self, test_config):
        """Test task submission and processing"""
        orchestrator = HorizontalScalingOrchestrator(max_nodes=5)
        
        # Start processing
        await orchestrator.start_processing()
        
        # Submit test tasks
        task_ids = []
        for i in range(5):
            task_id = orchestrator.submit_task(
                task_type="document_processing",
                payload={"document_id": f"doc_{i}"},
                priority=TaskPriority.MEDIUM
            )
            task_ids.append(task_id)
        
        # Let tasks process
        await asyncio.sleep(3)
        
        # Check task results
        completed_tasks = 0
        for task_id in task_ids:
            result = orchestrator.get_task_result(task_id)
            if result:
                completed_tasks += 1
        
        assert completed_tasks > 0
        
        # Check system status
        status = orchestrator.get_comprehensive_status()
        assert status is not None
        assert 'system_health' in status
        assert status['system_health']['healthy_nodes'] > 0
        
        orchestrator.stop_processing()
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, test_config):
        """Test load balancing functionality"""
        orchestrator = HorizontalScalingOrchestrator(max_nodes=3)
        
        # Get load balancer stats
        lb_stats = orchestrator.load_balancer.get_load_balancing_stats()
        
        assert lb_stats is not None
        assert 'total_nodes' in lb_stats
        assert 'healthy_nodes' in lb_stats
        assert lb_stats['total_nodes'] >= 2  # Initial nodes
    
    @pytest.mark.asyncio
    async def test_auto_scaling(self, test_config):
        """Test auto-scaling functionality"""
        orchestrator = HorizontalScalingOrchestrator(max_nodes=5)
        
        await orchestrator.start_processing()
        
        # Simulate high load to trigger scaling
        for i in range(20):  # Submit many tasks
            orchestrator.submit_task(
                task_type="ml_inference",
                payload={"model_input": f"test_data_{i}"},
                priority=TaskPriority.HIGH
            )
        
        # Let auto-scaler evaluate
        await asyncio.sleep(3)
        
        scaling_status = orchestrator.auto_scaler.get_scaling_status()
        
        assert scaling_status is not None
        assert 'recent_scaling_events' in scaling_status
        assert 'policy_status' in scaling_status
        
        orchestrator.stop_processing()


class TestIntegrationScenarios:
    """Test integration scenarios across all components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing_pipeline(self, test_config, sample_requirements):
        """Test complete end-to-end processing pipeline"""
        # Initialize all components
        orchestrator = AutonomousSDLCOrchestrator()
        performance_optimizer = GlobalPerformanceOptimizer()
        scaling_orchestrator = HorizontalScalingOrchestrator(max_nodes=5)
        security_orchestrator = EnterpriseSecurityOrchestrator()
        
        try:
            # Start all systems
            await performance_optimizer.start_optimization()
            await scaling_orchestrator.start_processing()
            
            # Process a complete workflow
            start_time = time.time()
            
            # Security check
            request_data = {'requirements': sample_requirements}
            user_context = {'user_id': 'system', 'auth_method': 'certificate'}
            
            security_result = await security_orchestrator.secure_request(
                request_data, user_context
            )
            assert security_result['allowed'] is True
            
            # Submit scaling task
            task_id = scaling_orchestrator.submit_task(
                task_type="sdlc_execution",
                payload={'requirements': sample_requirements},
                priority=TaskPriority.HIGH
            )
            
            # Execute SDLC lifecycle
            lifecycle_result = await orchestrator.execute_full_lifecycle(
                requirements=sample_requirements,
                target_quality_score=0.80
            )
            
            total_time = time.time() - start_time
            
            # Validate integration results
            assert lifecycle_result is not None
            assert lifecycle_result['lifecycle_status'] == 'completed'
            assert security_result['allowed'] is True
            assert task_id is not None
            
            # Performance validation
            assert total_time < 30  # Should complete within 30 seconds
            
            # Get comprehensive status from all systems
            perf_status = performance_optimizer.get_optimization_status()
            scaling_status = scaling_orchestrator.get_comprehensive_status()
            security_metrics = security_orchestrator.get_security_metrics()
            
            assert perf_status['optimization_active'] is True
            assert scaling_status['processing_active'] is True
            assert security_metrics['total_security_events'] > 0
            
        finally:
            # Cleanup
            performance_optimizer.stop_optimization()
            scaling_orchestrator.stop_processing()
    
    @pytest.mark.asyncio
    async def test_failure_recovery_integration(self, test_config):
        """Test failure recovery across integrated systems"""
        resilience_orchestrator = EnterpriseResilienceOrchestrator()
        error_recovery = EnterpriseErrorRecoverySystem()
        
        # Enable self-healing
        await resilience_orchestrator.enable_self_healing()
        
        # Simulate system failure
        failure_context = {
            'component': 'scaling_orchestrator',
            'error_type': 'resource_exhaustion',
            'severity': 'high',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Test error recovery
        recovery_result = await error_recovery.handle_error(
            Exception("Resource exhaustion"),
            failure_context
        )
        
        assert recovery_result is not None
        assert 'recovery_actions' in recovery_result
        assert recovery_result['recovery_success'] is True
        
        # Test resilience mechanisms
        healing_result = await resilience_orchestrator._attempt_self_healing(failure_context)
        
        assert healing_result is not None
        assert 'healing_actions' in healing_result
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, test_config):
        """Test system performance under high load"""
        scaling_orchestrator = HorizontalScalingOrchestrator(max_nodes=10)
        performance_optimizer = GlobalPerformanceOptimizer()
        
        await scaling_orchestrator.start_processing()
        await performance_optimizer.start_optimization()
        
        # Submit high volume of tasks
        task_ids = []
        for i in range(100):
            task_id = scaling_orchestrator.submit_task(
                task_type="load_test",
                payload={"iteration": i},
                priority=TaskPriority.MEDIUM
            )
            task_ids.append(task_id)
        
        # Monitor performance
        start_time = time.time()
        completed_tasks = 0
        
        while completed_tasks < 50 and (time.time() - start_time) < 30:  # 30 second timeout
            completed_tasks = sum(
                1 for task_id in task_ids 
                if scaling_orchestrator.get_task_result(task_id) is not None
            )
            await asyncio.sleep(1)
        
        processing_time = time.time() - start_time
        throughput = completed_tasks / processing_time
        
        # Performance assertions
        assert completed_tasks >= 30  # At least 30% completion
        assert throughput >= test_config.performance_benchmarks['min_throughput_ops_sec'] / 10  # Adjusted for test
        
        # Check system health under load
        status = scaling_orchestrator.get_comprehensive_status()
        assert status['system_health']['healthy_nodes'] > 0
        
        perf_status = performance_optimizer.get_optimization_status()
        assert perf_status['optimization_score'] > 0.5
        
        scaling_orchestrator.stop_processing()
        performance_optimizer.stop_optimization()


# Performance benchmarking utilities
class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    @staticmethod
    def measure_execution_time(func):
        """Decorator to measure function execution time"""
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Log performance metric
            logging.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            
            return result, execution_time
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Log performance metric
            logging.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            
            return result, execution_time
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


# Main test execution
if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",  # Verbose output
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--durations=10"  # Show 10 slowest tests
    ])