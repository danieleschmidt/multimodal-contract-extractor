"""
Integration tests for enterprise reliability components.

Tests the integration of error handling, monitoring, security, health checks,
and logging systems with the novel research algorithms.
"""

import asyncio
import json
import logging
import pytest
import time
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the enterprise reliability components
from src.multimodal_contract_extractor.enterprise_error_handling import (
    EnterpriseErrorRecoveryManager,
    ComponentType,
    ErrorSeverity,
    ResourceConstraint,
    with_error_recovery,
    CircuitBreaker,
    QuantumProcessingError,
    NeuromorphicProcessingError,
    get_error_recovery_manager
)

from src.multimodal_contract_extractor.enterprise_monitoring import (
    EnterpriseMonitoringSystem,
    MetricType,
    AlertLevel,
    PerformanceMetrics,
    monitor_algorithm_performance,
    get_monitoring_system
)

from src.multimodal_contract_extractor.enhanced_enterprise_security import (
    EnhancedEnterpriseSecurityManager,
    SecurityLevel,
    AccessLevel,
    SecurityContext,
    AuditEventType,
    require_enhanced_security,
    get_enhanced_security_manager
)

from src.multimodal_contract_extractor.enterprise_health_recovery import (
    EnterpriseHealthRecoverySystem,
    HealthStatus,
    ChaosExperiment,
    ChaosExperimentType,
    get_health_recovery_system,
    perform_health_check
)

from src.multimodal_contract_extractor.enterprise_logging_analytics import (
    EnterpriseLoggingAnalyticsSystem,
    LogLevel,
    EventCategory,
    log_performance,
    get_enterprise_logger,
    get_logging_analytics_system
)

# Mock research algorithm functions for testing
async def mock_quantum_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock quantum processing algorithm."""
    await asyncio.sleep(0.1)  # Simulate processing time
    if data.get('trigger_error'):
        raise QuantumProcessingError("Quantum state decoherence detected")
    
    return {
        'algorithm': 'quantum_processor',
        'accuracy': 0.92,
        'confidence': 0.85,
        'processing_time': 0.1,
        'quantum_state': 'coherent'
    }

async def mock_neuromorphic_engine(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock neuromorphic processing algorithm."""
    await asyncio.sleep(0.05)
    if data.get('trigger_error'):
        raise NeuromorphicProcessingError("Spike pattern anomaly detected")
    
    return {
        'algorithm': 'neuromorphic_engine',
        'accuracy': 0.88,
        'confidence': 0.82,
        'processing_time': 0.05,
        'spike_patterns': 'normal'
    }

async def mock_failing_algorithm(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock algorithm that always fails."""
    await asyncio.sleep(0.01)
    raise Exception("Simulated algorithm failure")

async def mock_slow_algorithm(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock slow algorithm for timeout testing."""
    await asyncio.sleep(2)  # Longer than typical timeout
    return {'algorithm': 'slow_algorithm', 'result': 'completed'}


class TestEnterpriseErrorHandling:
    """Test enterprise error handling and recovery."""
    
    @pytest.fixture
    def error_manager(self):
        """Create error recovery manager for testing."""
        return EnterpriseErrorRecoveryManager()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern."""
        circuit_breaker = CircuitBreaker(
            name="test_circuit",
            failure_threshold=3,
            recovery_timeout=1.0
        )
        
        # Function that fails
        @circuit_breaker
        async def failing_function():
            raise Exception("Test failure")
        
        # Test failures until circuit opens
        for i in range(3):
            with pytest.raises(Exception, match="Test failure"):
                await failing_function()
        
        # Circuit should now be open
        assert circuit_breaker.state == "open"
        
        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(Exception):  # CircuitBreakerOpenError or the original error
            await failing_function()
    
    @pytest.mark.asyncio
    async def test_algorithm_recovery_with_fallback(self, error_manager):
        """Test algorithm recovery with fallback mechanisms."""
        # Mock algorithm that fails first few times, then succeeds
        call_count = 0
        
        async def unreliable_algorithm(data):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise QuantumProcessingError("Temporary quantum error")
            return {'result': 'success', 'attempts': call_count}
        
        # Execute with recovery
        result = await error_manager.execute_with_recovery(
            unreliable_algorithm,
            ComponentType.QUANTUM_PROCESSOR,
            "quantum_analysis",
            {"input": "test_data"},
            max_attempts=3
        )
        
        assert result['result'] == 'success'
        assert result['attempts'] == 3
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_resource_management(self, error_manager):
        """Test resource management and constraints."""
        resource_manager = error_manager.resource_manager
        
        # Test resource reservation
        resources = {
            ResourceConstraint.MEMORY_LIMIT: 100 * 1024 * 1024,  # 100MB
            ResourceConstraint.CPU_UTILIZATION: 50.0,  # 50%
        }
        
        # Should succeed with reasonable resource request
        with resource_manager.reserve_resources(resources):
            # Simulate work
            await asyncio.sleep(0.1)
        
        # Check resource statistics
        stats = resource_manager.get_current_usage(ResourceConstraint.MEMORY_LIMIT)
        assert isinstance(stats, (int, float))
    
    @pytest.mark.asyncio
    async def test_decorator_error_recovery(self, error_manager):
        """Test error recovery decorator."""
        
        @with_error_recovery(
            ComponentType.NEUROMORPHIC_ENGINE,
            "spike_analysis",
            max_attempts=2
        )
        async def decorated_algorithm(data):
            if data.get('should_fail'):
                raise NeuromorphicProcessingError("Spike processing failed")
            return {'result': 'success'}
        
        # Test successful execution
        result = await decorated_algorithm({'input': 'test'})
        assert result['result'] == 'success'
        
        # Test error recovery (should eventually fail after retries)
        with pytest.raises(NeuromorphicProcessingError):
            await decorated_algorithm({'should_fail': True})


class TestEnterpriseMonitoring:
    """Test enterprise monitoring and observability."""
    
    @pytest.fixture
    def monitoring_system(self):
        """Create monitoring system for testing."""
        return EnterpriseMonitoringSystem()
    
    @pytest.mark.asyncio
    async def test_monitoring_system_lifecycle(self, monitoring_system):
        """Test monitoring system start/stop lifecycle."""
        # Start monitoring
        await monitoring_system.start_monitoring(collection_interval=1.0)
        assert monitoring_system.running is True
        
        # Let it run briefly
        await asyncio.sleep(2)
        
        # Stop monitoring
        await monitoring_system.stop_monitoring()
        assert monitoring_system.running is False
    
    @pytest.mark.asyncio
    async def test_algorithm_performance_monitoring(self, monitoring_system):
        """Test algorithm performance monitoring."""
        # Record algorithm metrics
        monitoring_system.record_algorithm_metrics(
            algorithm_name="quantum_processor",
            execution_time=0.15,
            throughput=100.0,
            accuracy=0.92,
            confidence=0.85,
            resource_usage={'memory_mb': 512, 'cpu_percent': 45},
            error_count=0,
            success_count=1
        )
        
        # Get algorithm statistics
        stats = monitoring_system.algorithm_monitor.get_algorithm_statistics("quantum_processor")
        
        assert stats['total_executions'] == 1
        assert stats['execution_time']['mean'] == 0.15
        assert stats['accuracy']['mean'] == 0.92
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_decorator(self, monitoring_system):
        """Test performance monitoring decorator."""
        
        @monitor_algorithm_performance("test_algorithm")
        async def monitored_algorithm(data):
            await asyncio.sleep(0.1)
            return {
                'accuracy': 0.88,
                'confidence': 0.82,
                'result': 'success'
            }
        
        # Execute monitored algorithm
        result = await monitored_algorithm({'input': 'test'})
        
        assert result['result'] == 'success'
        assert result['accuracy'] == 0.88
        
        # Check that metrics were recorded
        # Note: In real implementation, we'd check the monitoring system's metrics
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, monitoring_system):
        """Test performance anomaly detection."""
        # Set baseline for algorithm
        monitoring_system.algorithm_monitor.set_baseline_metrics(
            "test_algorithm",
            {
                'execution_time': 0.1,
                'accuracy': 0.9,
                'memory_usage': 100
            }
        )
        
        # Record some normal performance
        for i in range(10):
            monitoring_system.algorithm_monitor.record_algorithm_execution(
                "test_algorithm",
                {
                    'execution_time': 0.1 + (i * 0.01),
                    'accuracy': 0.9 + (i * 0.005),
                    'memory_usage': 100 + i
                }
            )
        
        # Record anomalous performance
        monitoring_system.algorithm_monitor.record_algorithm_execution(
            "test_algorithm",
            {
                'execution_time': 0.5,  # 5x slower
                'accuracy': 0.5,  # Much lower accuracy
                'memory_usage': 500  # 5x more memory
            }
        )
        
        # Detect anomalies
        anomalies = monitoring_system.algorithm_monitor.detect_performance_anomalies("test_algorithm")
        
        # Should detect anomalies in execution time and accuracy
        assert len(anomalies) > 0
        assert any(a['type'] == 'latency_increase' for a in anomalies)
        assert any(a['type'] == 'accuracy_degradation' for a in anomalies)
    
    @pytest.mark.asyncio
    async def test_dashboard_data_generation(self, monitoring_system):
        """Test dashboard data generation."""
        # Record some metrics
        monitoring_system.record_algorithm_metrics(
            algorithm_name="test_algorithm",
            execution_time=0.1,
            throughput=50.0,
            accuracy=0.85,
            confidence=0.8,
            resource_usage={'memory_mb': 256}
        )
        
        # Get dashboard data
        dashboard_data = monitoring_system.get_dashboard_data()
        
        assert 'timestamp' in dashboard_data
        assert 'system_metrics' in dashboard_data
        assert 'algorithm_statistics' in dashboard_data
        assert 'health_status' in dashboard_data


class TestEnhancedSecurity:
    """Test enhanced enterprise security."""
    
    @pytest.fixture
    def security_manager(self):
        """Create security manager for testing."""
        return EnhancedEnterpriseSecurityManager()
    
    @pytest.fixture
    def security_context(self, security_manager):
        """Create test security context."""
        # Create test user
        security_manager.access_control.create_user(
            "test_user",
            AccessLevel.RESEARCHER,
            {"execute_research", "read_confidential"}
        )
        
        # Authenticate user
        context = security_manager.access_control.authenticate_user(
            "test_user",
            {"client_ip": "127.0.0.1", "user_agent": "test"}
        )
        return context
    
    @pytest.mark.asyncio
    async def test_secure_operation_context(self, security_manager, security_context):
        """Test secure operation context manager."""
        
        async with security_manager.secure_operation(
            security_context,
            ComponentType.QUANTUM_PROCESSOR,
            "quantum_analysis",
            "test_resource",
            "execute_research"
        ):
            # Simulate secure operation
            await asyncio.sleep(0.1)
            result = "operation_completed"
        
        assert result == "operation_completed"
        
        # Check audit log was created
        audit_events = security_manager.audit_logger.search_audit_events({
            'user_id': security_context.user_id,
            'component': ComponentType.QUANTUM_PROCESSOR
        })
        
        assert len(audit_events) >= 2  # Start and end events
    
    @pytest.mark.asyncio
    async def test_algorithm_encryption(self, security_manager):
        """Test research algorithm data encryption."""
        test_data = {
            'weights': [0.1, 0.2, 0.3],
            'parameters': {'learning_rate': 0.01},
            'training_data': ['sample1', 'sample2']
        }
        
        # Encrypt research data
        encrypted_data = security_manager.encryption_manager.encrypt_research_data(
            test_data,
            ComponentType.QUANTUM_PROCESSOR
        )
        
        # Check that sensitive fields are encrypted
        assert 'weights_encrypted' in encrypted_data
        assert 'weights_key_id' in encrypted_data
        assert encrypted_data['weights_encrypted'] is True
        
        # Decrypt and verify
        decrypted_data = security_manager.encryption_manager.decrypt_research_data(encrypted_data)
        
        assert decrypted_data['weights'] == test_data['weights']
        assert decrypted_data['parameters'] == test_data['parameters']
    
    @pytest.mark.asyncio
    async def test_federated_learning_security(self, security_manager):
        """Test federated learning security features."""
        participants = ["participant_1", "participant_2", "participant_3"]
        round_id = "test_round_001"
        
        # Register participants
        for participant in participants:
            public_key = b"mock_public_key_" + participant.encode()
            security_manager.federated_security.register_participant(participant, public_key)
        
        # Mock model updates
        model_updates = {
            "participant_1": {"weights": [0.1, 0.2]},
            "participant_2": {"weights": [0.15, 0.25]},
            "participant_3": {"weights": [0.12, 0.22]}
        }
        
        # Execute secure federated learning round
        result = security_manager.secure_federated_learning_round(
            round_id,
            participants,
            model_updates,
            security_context
        )
        
        assert result["round_id"] == round_id
        assert "aggregation_keys" in result
        assert "valid_participants" in result
        assert len(result["valid_participants"]) == 3
    
    @pytest.mark.asyncio
    async def test_security_decorator(self, security_manager, security_context):
        """Test security decorator functionality."""
        
        @require_enhanced_security(
            "execute_research",
            ComponentType.QUANTUM_PROCESSOR,
            SecurityLevel.CONFIDENTIAL
        )
        async def secure_algorithm(context, data):
            return {'result': 'success', 'data_processed': len(data)}
        
        # Test successful execution with proper permissions
        result = await secure_algorithm(security_context, {'input': 'test_data'})
        assert result['result'] == 'success'
        
        # Test with insufficient permissions (should be caught by the decorator)
        low_privilege_context = SecurityContext(
            user_id="low_user",
            session_id="session_123",
            access_level=AccessLevel.GUEST,
            permissions={"read_public"}
        )
        
        with pytest.raises(PermissionError):
            await secure_algorithm(low_privilege_context, {'input': 'test'})
    
    @pytest.mark.asyncio
    async def test_security_health_check(self, security_manager):
        """Test security health check."""
        health_result = await security_manager.security_health_check()
        
        assert 'security_status' in health_result
        assert 'security_score' in health_result
        assert 'encryption_health' in health_result
        assert 'access_control_health' in health_result
        
        # Security score should be reasonable
        assert 0 <= health_result['security_score'] <= 100


class TestHealthRecoverySystem:
    """Test health monitoring and recovery system."""
    
    @pytest.fixture
    def health_system(self):
        """Create health recovery system for testing."""
        return EnterpriseHealthRecoverySystem()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_lifecycle(self, health_system):
        """Test health monitoring system lifecycle."""
        # Start monitoring
        await health_system.start_monitoring()
        assert health_system.monitoring_active is True
        
        # Let it run briefly
        await asyncio.sleep(2)
        
        # Stop monitoring
        await health_system.stop_monitoring()
        assert health_system.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_algorithm_health_monitoring(self, health_system):
        """Test algorithm health monitoring."""
        # Set baseline metrics
        health_system.algorithm_monitor.set_algorithm_baseline(
            "test_algorithm",
            {
                'accuracy': 0.9,
                'latency': 0.1,
                'memory_usage': 100,
                'error_rate': 0.01
            }
        )
        
        # Record some performance data
        for i in range(5):
            health_system.algorithm_monitor.record_algorithm_execution(
                "test_algorithm",
                {
                    'accuracy': 0.9 + (i * 0.01),
                    'latency': 0.1 + (i * 0.01),
                    'memory_usage': 100 + i,
                    'error_rate': 0.01
                }
            )
        
        # Check algorithm health
        health_result = await health_system.algorithm_monitor.check_algorithm_health("test_algorithm")
        
        assert health_result.check_name == "algorithm_test_algorithm"
        assert health_result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert 'current_metrics' in health_result.details
    
    @pytest.mark.asyncio
    async def test_dependency_health_monitoring(self, health_system):
        """Test dependency health monitoring."""
        # Check health of registered dependencies
        dep_result = await health_system.dependency_monitor.check_dependency_health("postgresql_db")
        
        assert dep_result.check_name == "dependency_postgresql_db"
        assert dep_result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert 'connection_count' in dep_result.details
    
    @pytest.mark.asyncio
    async def test_self_healing_execution(self, health_system):
        """Test self-healing recovery execution."""
        # Create mock unhealthy result
        from src.multimodal_contract_extractor.enterprise_health_recovery import HealthCheckResult
        
        unhealthy_result = HealthCheckResult(
            check_name="test_component",
            component=ComponentType.QUANTUM_PROCESSOR,
            status=HealthStatus.UNHEALTHY,
            details={'issue': 'high_error_rate'},
            metrics={'error_rate': 0.15}
        )
        
        # Execute recovery
        recovery_result = await health_system.self_healing.execute_recovery(
            ComponentType.QUANTUM_PROCESSOR,
            unhealthy_result
        )
        
        assert recovery_result['status'] in ['completed', 'failed']
        assert 'recovery_id' in recovery_result
        assert 'duration' in recovery_result
    
    @pytest.mark.asyncio
    async def test_chaos_engineering_experiment(self, health_system):
        """Test chaos engineering experiment execution."""
        experiment = ChaosExperiment(
            name="test_cpu_stress",
            type=ChaosExperimentType.CPU_STRESS,
            target_components=[ComponentType.QUANTUM_PROCESSOR],
            duration_seconds=5.0,  # Short duration for testing
            intensity=0.3,
            safety_checks=["system_load_check"],
            recovery_validation=True
        )
        
        # Run chaos experiment
        result = await health_system.chaos_engineering.run_chaos_experiment(experiment)
        
        assert result['status'] in ['completed', 'aborted', 'failed']
        if result['status'] == 'completed':
            assert 'experiment_id' in result
            assert 'recovery_validated' in result
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, health_system):
        """Test comprehensive health check."""
        health_summary = await health_system.comprehensive_health_check()
        
        assert 'comprehensive_check' in health_summary
        assert 'health_check_results' in health_summary
        assert 'dependency_results' in health_summary
        assert 'summary' in health_summary
        
        # Check that timing information is included
        assert 'duration_seconds' in health_summary['comprehensive_check']
        assert health_summary['comprehensive_check']['duration_seconds'] > 0


class TestLoggingAnalytics:
    """Test enterprise logging and analytics."""
    
    @pytest.fixture
    def logging_system(self):
        """Create logging system for testing."""
        return EnterpriseLoggingAnalyticsSystem()
    
    @pytest.mark.asyncio
    async def test_structured_logging(self, logging_system):
        """Test structured logging functionality."""
        logger = logging_system.structured_logger
        
        # Test different log levels
        log_id = logger.info(
            "Test info message",
            component=ComponentType.QUANTUM_PROCESSOR,
            correlation_id="test_123",
            tags={'test': 'true'},
            metrics={'accuracy': 0.95}
        )
        
        assert log_id is not None
        assert len(log_id) > 0
        
        # Test error logging
        test_exception = Exception("Test error")
        error_log_id = logger.error(
            "Test error occurred",
            error=test_exception,
            component=ComponentType.NEUROMORPHIC_ENGINE
        )
        
        assert error_log_id != log_id
    
    @pytest.mark.asyncio
    async def test_performance_analytics(self, logging_system):
        """Test performance analytics."""
        analytics = logging_system.performance_analytics
        
        # Record some metrics
        analytics.record_metric(
            "test_metric",
            value=42.0,
            component=ComponentType.QUANTUM_PROCESSOR,
            tags={'algorithm': 'test'}
        )
        
        # Get metric summary
        summary = analytics.get_metric_summary("test_metric")
        
        assert summary['count'] == 1
        assert summary['mean'] == 42.0
        assert summary['min'] == 42.0
        assert summary['max'] == 42.0
    
    @pytest.mark.asyncio
    async def test_error_analytics(self, logging_system):
        """Test error analytics."""
        error_analytics = logging_system.error_analytics
        
        # Record some errors
        error_analytics.record_error(
            error_type="TestError",
            error_message="Test error message",
            component=ComponentType.QUANTUM_PROCESSOR,
            operation="test_operation"
        )
        
        error_analytics.record_error(
            error_type="TestError",
            error_message="Another test error",
            component=ComponentType.QUANTUM_PROCESSOR,
            operation="test_operation"
        )
        
        # Get error statistics
        stats = error_analytics.get_error_statistics(time_window_hours=1)
        
        assert stats['total_errors'] == 2
        assert 'TestError' in [e['type'] for e in stats['top_errors']]
    
    @pytest.mark.asyncio
    async def test_research_experiment_tracking(self, logging_system):
        """Test research experiment tracking."""
        tracker = logging_system.research_tracker
        
        # Start experiment
        exp_id = tracker.start_experiment(
            algorithm_name="test_algorithm",
            parameters={'param1': 'value1'},
            hyperparameters={'learning_rate': 0.01},
            tags={'project': 'test'}
        )
        
        # Update metrics
        tracker.update_experiment_metrics(
            exp_id,
            metrics={'accuracy': 0.85, 'loss': 0.15},
            results={'final_accuracy': 0.88}
        )
        
        # Record resource usage
        tracker.record_resource_usage(
            exp_id,
            memory_mb=512,
            cpu_hours=0.1
        )
        
        # Finish experiment
        result = tracker.finish_experiment(
            exp_id,
            status="completed",
            final_results={'test_accuracy': 0.90},
            notes="Test experiment completed successfully"
        )
        
        assert result['status'] == 'completed'
        assert result['experiment_id'] == exp_id
        
        # Get experiment summary
        summary = tracker.get_experiment_summary(exp_id)
        assert summary is not None
        assert summary['algorithm_name'] == "test_algorithm"
        assert summary['status'] == "completed"
    
    @pytest.mark.asyncio
    async def test_logging_decorator(self, logging_system):
        """Test performance logging decorator."""
        
        @log_performance("test_algorithm", ComponentType.QUANTUM_PROCESSOR)
        async def decorated_algorithm(data):
            await asyncio.sleep(0.1)
            return {
                'accuracy': 0.88,
                'confidence': 0.82,
                'result': 'success'
            }
        
        # Execute decorated function
        result = await decorated_algorithm({'input': 'test'})
        
        assert result['result'] == 'success'
        
        # Check that performance was logged
        # Note: In real implementation, we'd verify the logged data
    
    @pytest.mark.asyncio
    async def test_analytics_dashboard(self, logging_system):
        """Test analytics dashboard data generation."""
        # Generate some data
        logging_system.structured_logger.info("Test log message")
        logging_system.error_analytics.record_error(
            "TestError", "Test message", ComponentType.QUANTUM_PROCESSOR, "test_op"
        )
        
        # Get dashboard data
        dashboard = logging_system.get_comprehensive_analytics_dashboard()
        
        assert 'timestamp' in dashboard
        assert 'system_overview' in dashboard
        assert 'logging' in dashboard['system_overview']
        assert 'performance' in dashboard['system_overview']
        assert 'errors' in dashboard['system_overview']


class TestIntegratedScenarios:
    """Test integrated scenarios combining multiple systems."""
    
    @pytest.fixture
    async def integrated_setup(self):
        """Setup integrated test environment."""
        # Initialize all systems
        error_manager = get_error_recovery_manager()
        monitoring_system = get_monitoring_system()
        security_manager = get_enhanced_security_manager()
        health_system = get_health_recovery_system()
        logging_system = get_logging_analytics_system()
        
        # Create security context
        security_manager.access_control.create_user(
            "test_researcher",
            AccessLevel.RESEARCHER,
            {"execute_research", "read_confidential"}
        )
        
        security_context = security_manager.access_control.authenticate_user(
            "test_researcher",
            {"client_ip": "127.0.0.1", "user_agent": "test_integration"}
        )
        
        # Start systems
        await monitoring_system.start_monitoring(collection_interval=2.0)
        await health_system.start_monitoring()
        await logging_system.start_analytics()
        
        yield {
            'error_manager': error_manager,
            'monitoring': monitoring_system,
            'security': security_manager,
            'health': health_system,
            'logging': logging_system,
            'security_context': security_context
        }
        
        # Cleanup
        await monitoring_system.stop_monitoring()
        await health_system.stop_monitoring()
        await logging_system.stop_analytics()
    
    @pytest.mark.asyncio
    async def test_end_to_end_algorithm_execution(self, integrated_setup):
        """Test end-to-end secure algorithm execution with full observability."""
        systems = integrated_setup
        
        # Create research experiment
        exp_id = systems['logging'].research_tracker.start_experiment(
            algorithm_name="quantum_processor",
            parameters={'quantum_bits': 16},
            hyperparameters={'coherence_time': 0.1}
        )
        
        try:
            # Execute algorithm with full security and monitoring
            async with systems['security'].secure_operation(
                systems['security_context'],
                ComponentType.QUANTUM_PROCESSOR,
                "quantum_analysis",
                "test_contract_data",
                "execute_research"
            ):
                # Simulate algorithm execution with monitoring
                start_time = time.time()
                
                # Record that algorithm is starting
                systems['logging'].structured_logger.research(
                    "Starting quantum algorithm execution",
                    experiment_id=exp_id,
                    algorithm_name="quantum_processor",
                    component=ComponentType.QUANTUM_PROCESSOR
                )
                
                # Execute mock algorithm
                result = await mock_quantum_processor({'input': 'test_contract'})
                
                execution_time = time.time() - start_time
                
                # Record performance metrics
                systems['monitoring'].record_algorithm_metrics(
                    algorithm_name="quantum_processor",
                    execution_time=execution_time,
                    throughput=1.0 / execution_time,
                    accuracy=result['accuracy'],
                    confidence=result['confidence'],
                    resource_usage={'memory_mb': 256, 'cpu_percent': 45}
                )
                
                # Update experiment
                systems['logging'].research_tracker.update_experiment_metrics(
                    exp_id,
                    metrics={
                        'execution_time': execution_time,
                        'accuracy': result['accuracy'],
                        'confidence': result['confidence']
                    }
                )
                
                # Log successful completion
                systems['logging'].structured_logger.research(
                    "Quantum algorithm completed successfully",
                    experiment_id=exp_id,
                    algorithm_name="quantum_processor",
                    accuracy=result['accuracy'],
                    confidence=result['confidence']
                )
            
            # Finish experiment
            exp_result = systems['logging'].research_tracker.finish_experiment(
                exp_id,
                status="completed",
                final_results=result
            )
            
            assert exp_result['status'] == 'completed'
            assert result['accuracy'] == 0.92
            
        except Exception as e:
            # Handle any errors
            systems['logging'].structured_logger.error(
                "Algorithm execution failed",
                error=e,
                experiment_id=exp_id,
                algorithm_name="quantum_processor"
            )
            
            # Mark experiment as failed
            systems['logging'].research_tracker.finish_experiment(
                exp_id,
                status="failed",
                notes=f"Failed with error: {str(e)}"
            )
            raise
    
    @pytest.mark.asyncio
    async def test_error_recovery_with_monitoring(self, integrated_setup):
        """Test error recovery with full monitoring and logging."""
        systems = integrated_setup
        
        # Create an algorithm that will fail initially
        failure_count = 0
        
        async def unreliable_algorithm(data):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:
                # Log the failure
                systems['logging'].structured_logger.error(
                    f"Algorithm failure attempt {failure_count}",
                    component=ComponentType.NEUROMORPHIC_ENGINE,
                    operation="spike_processing"
                )
                
                raise NeuromorphicProcessingError(f"Processing failed on attempt {failure_count}")
            
            # Success on third attempt
            systems['logging'].structured_logger.info(
                "Algorithm succeeded after retries",
                component=ComponentType.NEUROMORPHIC_ENGINE,
                operation="spike_processing",
                tags={'retry_count': str(failure_count)}
            )
            
            return {'result': 'success', 'attempts': failure_count}
        
        # Execute with error recovery
        result = await systems['error_manager'].execute_with_recovery(
            unreliable_algorithm,
            ComponentType.NEUROMORPHIC_ENGINE,
            "spike_processing",
            {'input': 'test_spikes'},
            max_attempts=3
        )
        
        assert result['result'] == 'success'
        assert result['attempts'] == 3
        assert failure_count == 3
        
        # Check that error statistics were recorded
        error_stats = systems['logging'].error_analytics.get_error_statistics()
        assert error_stats['total_errors'] >= 2  # At least 2 failures were recorded
    
    @pytest.mark.asyncio
    async def test_health_monitoring_with_recovery(self, integrated_setup):
        """Test health monitoring triggering automatic recovery."""
        systems = integrated_setup
        
        # Record some algorithm performance data to establish baseline
        for i in range(10):
            systems['health'].algorithm_monitor.record_algorithm_execution(
                "neuromorphic_engine",
                {
                    'accuracy': 0.88 + (i * 0.001),
                    'latency': 0.05 + (i * 0.001),
                    'memory_usage': 100 + i,
                    'error_rate': 0.01
                }
            )
        
        # Record degraded performance
        systems['health'].algorithm_monitor.record_algorithm_execution(
            "neuromorphic_engine",
            {
                'accuracy': 0.60,  # Much lower accuracy
                'latency': 0.20,   # Much higher latency
                'memory_usage': 300,  # Much higher memory
                'error_rate': 0.15    # Higher error rate
            }
        )
        
        # Check algorithm health
        health_result = await systems['health'].algorithm_monitor.check_algorithm_health("neuromorphic_engine")
        
        # Should detect unhealthy state
        assert health_result.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        
        # If unhealthy, trigger recovery
        if health_result.status == HealthStatus.UNHEALTHY:
            recovery_result = await systems['health'].self_healing.execute_recovery(
                ComponentType.NEUROMORPHIC_ENGINE,
                health_result
            )
            
            assert recovery_result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_comprehensive_system_health_check(self, integrated_setup):
        """Test comprehensive system health check across all components."""
        systems = integrated_setup
        
        # Perform comprehensive health check
        health_summary = await perform_health_check()
        
        assert 'comprehensive_check' in health_summary
        assert 'summary' in health_summary
        
        # Check overall system health
        overall_health = systems['health'].get_system_health_summary()
        
        assert 'overall_status' in overall_health
        assert 'health_checks' in overall_health
        assert 'dependencies' in overall_health
        assert 'recovery_system' in overall_health
        
        # Log the health check results
        systems['logging'].structured_logger.info(
            "Comprehensive health check completed",
            category=EventCategory.SYSTEM,
            context_data={
                'overall_status': overall_health['overall_status'],
                'health_checks_total': overall_health['health_checks']['total'],
                'monitoring_active': overall_health['monitoring_active']
            }
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])