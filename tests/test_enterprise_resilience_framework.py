"""Comprehensive tests for enterprise resilience framework."""

import asyncio
import random
import time
import pytest

from multimodal_contract_extractor.enterprise_resilience_framework import (
    CircuitBreaker,
    EnterpriseResilienceFramework,
    FailureMode,
    FailureScenario,
    FallbackModelManager,
    RecoveryStrategy,
    ResilienceEvent,
    ResilienceLevel,
    RetryHandler,
    configure_resilience_level,
    execute_resilient_operation,
    get_resilience_framework,
)


class TestFailureScenario:
    """Test FailureScenario data class."""

    def test_failure_scenario_creation(self):
        """Test creating a failure scenario."""
        scenario = FailureScenario(
            id="test_scenario",
            failure_mode=FailureMode.MODEL_DEGRADATION,
            description="Test model degradation scenario",
            probability=0.15,
            impact_severity=3,
            detection_time=30.0,
            recovery_strategy=RecoveryStrategy.FALLBACK_MODEL,
            recovery_time_target=120.0,
            data_loss_target=0.0,
            dependencies=["model_service", "database"]
        )
        
        assert scenario.id == "test_scenario"
        assert scenario.failure_mode == FailureMode.MODEL_DEGRADATION
        assert scenario.probability == 0.15
        assert scenario.impact_severity == 3
        assert scenario.recovery_strategy == RecoveryStrategy.FALLBACK_MODEL
        assert scenario.automated_recovery is True
        assert "model_service" in scenario.dependencies


class TestResilienceEvent:
    """Test ResilienceEvent data class."""

    def test_resilience_event_creation(self):
        """Test creating a resilience event."""
        event = ResilienceEvent(
            timestamp=time.time(),
            event_type="failure",
            failure_mode=FailureMode.NETWORK_PARTITION,
            scenario_id="network_test",
            duration=45.0,
            recovery_strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
            success=False,
            details={"error_message": "Network timeout", "retry_count": 3}
        )
        
        assert event.event_type == "failure"
        assert event.failure_mode == FailureMode.NETWORK_PARTITION
        assert event.scenario_id == "network_test"
        assert event.duration == 45.0
        assert event.recovery_strategy_used == RecoveryStrategy.RETRY_WITH_BACKOFF
        assert not event.success
        assert event.details["retry_count"] == 3


class TestCircuitBreaker:
    """Test CircuitBreaker implementation."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing."""
        return CircuitBreaker(failure_threshold=3, timeout=1.0)

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state."""
        async def successful_operation():
            return "success"
        
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self, circuit_breaker):
        """Test circuit breaker opening after failures."""
        async def failing_operation():
            raise Exception("Test failure")
        
        # Trigger failures to open circuit breaker
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.state == "open"
        
        # Should immediately fail without calling function
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await circuit_breaker.call(failing_operation)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self, circuit_breaker):
        """Test circuit breaker half-open state."""
        async def failing_operation():
            raise Exception("Test failure")
        
        async def successful_operation():
            return "success"
        
        # Open the circuit breaker
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.state == "open"
        
        # Wait for timeout to allow half-open state
        await asyncio.sleep(1.1)
        
        # Should transition to half-open and allow one call
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.state == "closed"


class TestRetryHandler:
    """Test RetryHandler implementation."""

    @pytest.fixture
    def retry_handler(self):
        """Create a retry handler for testing."""
        return RetryHandler(max_retries=3, base_delay=0.1, max_delay=1.0)

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self, retry_handler):
        """Test successful execution on first attempt."""
        async def successful_operation():
            return "success"
        
        result = await retry_handler.execute(successful_operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, retry_handler):
        """Test successful execution after some failures."""
        call_count = 0
        
        async def eventually_successful_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return f"success on attempt {call_count}"
        
        result = await retry_handler.execute(eventually_successful_operation)
        assert result == "success on attempt 3"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, retry_handler):
        """Test retry exhaustion."""
        async def always_failing_operation():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await retry_handler.execute(always_failing_operation)

    @pytest.mark.asyncio
    async def test_retry_delay_calculation(self):
        """Test retry delay calculation with backoff."""
        retry_handler = RetryHandler(
            max_retries=3, base_delay=0.1, backoff_factor=2.0, jitter=False
        )
        
        call_times = []
        
        async def failing_operation():
            call_times.append(time.time())
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            await retry_handler.execute(failing_operation)
        
        # Verify exponential backoff (allowing some tolerance for execution time)
        assert len(call_times) == 4  # Initial + 3 retries
        
        if len(call_times) >= 2:
            first_delay = call_times[1] - call_times[0]
            assert 0.08 <= first_delay <= 0.15  # ~0.1s base delay
        
        if len(call_times) >= 3:
            second_delay = call_times[2] - call_times[1]
            assert 0.18 <= second_delay <= 0.25  # ~0.2s with backoff


class TestFallbackModelManager:
    """Test FallbackModelManager implementation."""

    @pytest.fixture
    def fallback_manager(self):
        """Create a fallback model manager for testing."""
        return FallbackModelManager()

    def test_register_fallback_model(self, fallback_manager):
        """Test registering fallback models."""
        model_instance = {"type": "simple_model", "accuracy": 0.8}
        
        fallback_manager.register_fallback_model(
            "simple_model", model_instance, priority=1
        )
        
        assert "simple_model" in fallback_manager.fallback_models
        assert fallback_manager.model_priorities["simple_model"] == 1
        assert fallback_manager.model_health["simple_model"] is True

    def test_get_best_available_model(self, fallback_manager):
        """Test getting the best available model."""
        # Register multiple models with different priorities
        models = [
            ("basic_model", {"type": "basic"}, 1),
            ("advanced_model", {"type": "advanced"}, 3),
            ("premium_model", {"type": "premium"}, 2),
        ]
        
        for name, instance, priority in models:
            fallback_manager.register_fallback_model(name, instance, priority)
        
        # Should get highest priority model
        best_model = fallback_manager.get_best_available_model()
        assert best_model is not None
        assert best_model[0] == "advanced_model"  # Highest priority

    def test_model_health_management(self, fallback_manager):
        """Test model health management."""
        fallback_manager.register_fallback_model(
            "test_model", {"type": "test"}, priority=1
        )
        
        # Initially healthy
        assert fallback_manager.model_health["test_model"] is True
        
        # Mark as unhealthy
        fallback_manager.mark_model_unhealthy("test_model")
        assert fallback_manager.model_health["test_model"] is False
        
        # Should not be returned as best available
        best_model = fallback_manager.get_best_available_model()
        assert best_model is None
        
        # Mark as healthy again
        fallback_manager.mark_model_healthy("test_model")
        assert fallback_manager.model_health["test_model"] is True
        
        best_model = fallback_manager.get_best_available_model()
        assert best_model is not None
        assert best_model[0] == "test_model"

    def test_exclude_models(self, fallback_manager):
        """Test excluding models from selection."""
        models = [
            ("model_a", {"type": "a"}, 1),
            ("model_b", {"type": "b"}, 2),
            ("model_c", {"type": "c"}, 3),
        ]
        
        for name, instance, priority in models:
            fallback_manager.register_fallback_model(name, instance, priority)
        
        # Exclude highest priority model
        best_model = fallback_manager.get_best_available_model(exclude_models=["model_c"])
        assert best_model is not None
        assert best_model[0] == "model_b"  # Second highest priority


class TestEnterpriseResilienceFramework:
    """Test EnterpriseResilienceFramework implementation."""

    @pytest.fixture
    def resilience_framework(self):
        """Create a resilience framework for testing."""
        return EnterpriseResilienceFramework(ResilienceLevel.STANDARD)

    def test_framework_initialization(self, resilience_framework):
        """Test framework initialization."""
        assert resilience_framework.resilience_level == ResilienceLevel.STANDARD
        assert len(resilience_framework.retry_handlers) > 0
        assert len(resilience_framework.circuit_breakers) > 0
        assert isinstance(resilience_framework.fallback_manager, FallbackModelManager)

    def test_resilience_level_configuration(self):
        """Test different resilience level configurations."""
        levels = [
            ResilienceLevel.BASIC,
            ResilienceLevel.STANDARD,
            ResilienceLevel.HIGH,
            ResilienceLevel.MISSION_CRITICAL
        ]
        
        for level in levels:
            framework = EnterpriseResilienceFramework(level)
            assert framework.resilience_level == level
            
            # Higher levels should have more components
            if level == ResilienceLevel.MISSION_CRITICAL:
                assert len(framework.failure_scenarios) > 0
                assert "mission_critical" in framework.retry_handlers

    @pytest.mark.asyncio
    async def test_execute_with_resilience_success(self, resilience_framework):
        """Test successful execution with resilience."""
        async def successful_operation(value):
            return f"processed: {value}"
        
        result = await resilience_framework.execute_with_resilience(
            "test_operation", successful_operation, "test_data"
        )
        
        assert result == "processed: test_data"
        
        # Check that success event was recorded
        events = list(resilience_framework.resilience_events)
        success_events = [e for e in events if e.event_type == "success"]
        assert len(success_events) > 0

    @pytest.mark.asyncio
    async def test_execute_with_resilience_fallback(self, resilience_framework):
        """Test fallback execution on failure."""
        async def failing_operation(value):
            raise Exception("Primary operation failed")
        
        async def fallback_operation(value):
            return f"fallback: {value}"
        
        result = await resilience_framework.execute_with_resilience(
            "test_operation",
            failing_operation,
            "test_data",
            fallback_func=fallback_operation
        )
        
        assert result == "fallback: test_data"
        
        # Check that fallback success event was recorded
        events = list(resilience_framework.resilience_events)
        fallback_events = [e for e in events if e.event_type == "fallback_success"]
        assert len(fallback_events) > 0

    def test_health_check_registration(self, resilience_framework):
        """Test health check registration."""
        def test_health_check():
            return True
        
        resilience_framework.register_health_check("test_component", test_health_check)
        
        assert "test_component" in resilience_framework.health_checks
        assert resilience_framework.health_checks["test_component"] == test_health_check

    @pytest.mark.asyncio
    async def test_run_health_checks(self, resilience_framework):
        """Test running health checks."""
        def healthy_component():
            return True
        
        async def unhealthy_component():
            return False
        
        def failing_component():
            raise Exception("Health check failed")
        
        # Register health checks
        resilience_framework.register_health_check("healthy", healthy_component)
        resilience_framework.register_health_check("unhealthy", unhealthy_component)
        resilience_framework.register_health_check("failing", failing_component)
        
        # Run health checks
        health_status = await resilience_framework.run_health_checks()
        
        assert health_status["healthy"] is True
        assert health_status["unhealthy"] is False
        assert health_status["failing"] is False

    def test_disaster_recovery_plan_creation(self, resilience_framework):
        """Test disaster recovery plan creation."""
        recovery_steps = [
            {"name": "stop_services", "duration": 30.0},
            {"name": "backup_data", "duration": 120.0},
            {"name": "restore_from_backup", "duration": 300.0},
            {"name": "restart_services", "duration": 60.0}
        ]
        
        resilience_framework.create_disaster_recovery_plan(
            "data_center_outage", recovery_steps
        )
        
        assert "data_center_outage" in resilience_framework.disaster_recovery_plans
        plan = resilience_framework.disaster_recovery_plans["data_center_outage"]
        assert len(plan["steps"]) == 4
        assert plan["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_disaster_recovery_execution(self, resilience_framework):
        """Test disaster recovery plan execution."""
        recovery_steps = [
            {"name": "step1", "duration": 0.1},
            {"name": "step2", "duration": 0.1},
            {"name": "step3", "duration": 0.1}
        ]
        
        resilience_framework.create_disaster_recovery_plan(
            "test_recovery", recovery_steps
        )
        
        # Execute disaster recovery
        success = await resilience_framework.execute_disaster_recovery("test_recovery")
        assert success is True

    def test_resilience_metrics_calculation(self, resilience_framework):
        """Test resilience metrics calculation."""
        # Add some mock events
        current_time = time.time()
        events = [
            ResilienceEvent(
                timestamp=current_time - 3600,
                event_type="success",
                failure_mode=None,
                scenario_id="test_1",
                duration=1.0,
                recovery_strategy_used=None,
                success=True
            ),
            ResilienceEvent(
                timestamp=current_time - 1800,
                event_type="failure",
                failure_mode=FailureMode.MODEL_DEGRADATION,
                scenario_id="test_2",
                duration=30.0,
                recovery_strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
                success=False
            ),
            ResilienceEvent(
                timestamp=current_time - 900,
                event_type="recovery",
                failure_mode=None,
                scenario_id="test_3",
                duration=15.0,
                recovery_strategy_used=RecoveryStrategy.FALLBACK_MODEL,
                success=True
            )
        ]
        
        resilience_framework.resilience_events.extend(events)
        
        metrics = resilience_framework.get_resilience_metrics()
        
        assert "success_rate" in metrics
        assert "total_events" in metrics
        assert "mtbf_seconds" in metrics
        assert "mttr_seconds" in metrics
        assert "availability" in metrics
        
        assert metrics["total_events"] == 3
        assert 0 <= metrics["success_rate"] <= 1
        assert 0 <= metrics["availability"] <= 1


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_execute_resilient_operation(self):
        """Test high-level resilient operation execution."""
        async def test_operation(value):
            return f"result: {value}"
        
        result = await execute_resilient_operation(
            "api_test", test_operation, "input_data"
        )
        
        assert result == "result: input_data"

    @pytest.mark.asyncio
    async def test_execute_resilient_operation_with_fallback(self):
        """Test resilient operation with fallback."""
        async def failing_operation(value):
            raise Exception("Primary failed")
        
        async def fallback_operation(value):
            return f"fallback: {value}"
        
        result = await execute_resilient_operation(
            "fallback_test",
            failing_operation,
            "test_input",
            fallback_func=fallback_operation
        )
        
        assert result == "fallback: test_input"

    def test_get_resilience_framework(self):
        """Test getting the global resilience framework."""
        framework = get_resilience_framework()
        assert isinstance(framework, EnterpriseResilienceFramework)

    def test_configure_resilience_level(self):
        """Test configuring resilience level."""
        configure_resilience_level(ResilienceLevel.HIGH)
        
        framework = get_resilience_framework()
        assert framework.resilience_level == ResilienceLevel.HIGH


class TestEnumerations:
    """Test enumeration values."""

    def test_failure_mode_values(self):
        """Test failure mode enum values."""
        assert FailureMode.MODEL_DEGRADATION.value == "model_degradation"
        assert FailureMode.DATA_CORRUPTION.value == "data_corruption"
        assert FailureMode.NETWORK_PARTITION.value == "network_partition"
        assert FailureMode.RESOURCE_EXHAUSTION.value == "resource_exhaustion"
        assert FailureMode.DEPENDENCY_FAILURE.value == "dependency_failure"
        assert FailureMode.SECURITY_BREACH.value == "security_breach"
        assert FailureMode.CONFIGURATION_ERROR.value == "configuration_error"
        assert FailureMode.HARDWARE_FAILURE.value == "hardware_failure"

    def test_recovery_strategy_values(self):
        """Test recovery strategy enum values."""
        assert RecoveryStrategy.RETRY_WITH_BACKOFF.value == "retry_with_backoff"
        assert RecoveryStrategy.CIRCUIT_BREAKER.value == "circuit_breaker"
        assert RecoveryStrategy.FALLBACK_MODEL.value == "fallback_model"
        assert RecoveryStrategy.GRACEFUL_DEGRADATION.value == "graceful_degradation"
        assert RecoveryStrategy.FAILOVER_CLUSTER.value == "failover_cluster"
        assert RecoveryStrategy.DATA_RECOVERY.value == "data_recovery"
        assert RecoveryStrategy.ROLLBACK_DEPLOYMENT.value == "rollback_deployment"
        assert RecoveryStrategy.MANUAL_INTERVENTION.value == "manual_intervention"

    def test_resilience_level_values(self):
        """Test resilience level enum values."""
        assert ResilienceLevel.BASIC.value == "basic"
        assert ResilienceLevel.STANDARD.value == "standard"
        assert ResilienceLevel.HIGH.value == "high"
        assert ResilienceLevel.MISSION_CRITICAL.value == "mission_critical"


class TestIntegrationScenarios:
    """Test integration scenarios for resilience framework."""

    @pytest.mark.asyncio
    async def test_comprehensive_resilience_scenario(self):
        """Test comprehensive resilience scenario."""
        framework = EnterpriseResilienceFramework(ResilienceLevel.HIGH)
        
        # Register fallback models
        framework.fallback_manager.register_fallback_model(
            "simple_model", {"type": "simple", "accuracy": 0.8}, priority=1
        )
        framework.fallback_manager.register_fallback_model(
            "advanced_model", {"type": "advanced", "accuracy": 0.9}, priority=2
        )
        
        # Register health checks
        def healthy_database():
            return True
        
        framework.register_health_check("database", healthy_database)
        
        # Test operation with multiple failure modes
        call_count = 0
        
        async def unreliable_operation(data):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise Exception("Network timeout")
            elif call_count == 2:
                raise Exception("Service unavailable")
            else:
                return f"processed: {data}"
        
        # Execute with resilience
        result = await framework.execute_with_resilience(
            "api_calls", unreliable_operation, "test_data"
        )
        
        assert result == "processed: test_data"
        assert call_count == 3  # Should retry twice before succeeding
        
        # Check events were recorded
        events = list(framework.resilience_events)
        assert len(events) > 0
        
        # Run health checks
        health_status = await framework.run_health_checks()
        assert health_status["database"] is True
        
        # Get resilience metrics
        metrics = framework.get_resilience_metrics()
        assert metrics["success_rate"] > 0

    @pytest.mark.asyncio
    async def test_mission_critical_resilience(self):
        """Test mission-critical resilience configuration."""
        framework = EnterpriseResilienceFramework(ResilienceLevel.MISSION_CRITICAL)
        
        # Should have comprehensive failure scenarios
        assert len(framework.failure_scenarios) > 0
        
        # Should have mission-critical retry handler
        assert "mission_critical" in framework.retry_handlers
        
        # Create and execute disaster recovery plan
        recovery_steps = [
            {"name": "isolate_failure", "duration": 0.1},
            {"name": "activate_backup", "duration": 0.1},
            {"name": "verify_integrity", "duration": 0.1}
        ]
        
        framework.create_disaster_recovery_plan("critical_failure", recovery_steps)
        
        success = await framework.execute_disaster_recovery("critical_failure")
        assert success is True
        
        # Test high-resilience operation execution
        failure_count = 0
        
        async def mission_critical_operation():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:  # Fail first 5 times
                raise Exception("Critical system failure")
            return "mission accomplished"
        
        # Should retry up to 10 times for mission-critical operations
        result = await framework.execute_with_resilience(
            "mission_critical", mission_critical_operation
        )
        
        assert result == "mission accomplished"
        assert failure_count == 6  # Failed 5 times, succeeded on 6th

    @pytest.mark.asyncio
    async def test_cascading_failure_handling(self):
        """Test handling of cascading failures."""
        framework = EnterpriseResilienceFramework(ResilienceLevel.HIGH)
        
        # Simulate cascading failures across multiple components
        component_states = {
            "database": True,
            "cache": True,
            "ml_service": True,
            "api_gateway": True
        }
        
        async def database_operation():
            if not component_states["database"]:
                raise Exception("Database connection failed")
            return "database_result"
        
        async def cache_operation():
            if not component_states["cache"]:
                raise Exception("Cache service unavailable")
            return "cache_result"
        
        async def ml_inference():
            if not component_states["ml_service"]:
                raise Exception("ML service degraded")
            return "ml_result"
        
        # Register health checks for components
        framework.register_health_check("database", lambda: component_states["database"])
        framework.register_health_check("cache", lambda: component_states["cache"])
        framework.register_health_check("ml_service", lambda: component_states["ml_service"])
        
        # Initially all healthy
        health_status = await framework.run_health_checks()
        assert all(health_status.values())
        
        # Simulate cascading failure
        component_states["database"] = False
        component_states["cache"] = False
        
        # Test operations with failures
        with pytest.raises(Exception):
            await framework.execute_with_resilience("database", database_operation)
        
        with pytest.raises(Exception):
            await framework.execute_with_resilience("cache", cache_operation)
        
        # ML service should still work
        result = await framework.execute_with_resilience("ml_service", ml_inference)
        assert result == "ml_result"
        
        # Check health status reflects failures
        health_status = await framework.run_health_checks()
        assert not health_status["database"]
        assert not health_status["cache"]
        assert health_status["ml_service"]
        
        # Recovery simulation
        component_states["database"] = True
        component_states["cache"] = True
        
        health_status = await framework.run_health_checks()
        assert all(health_status.values())
        
        # Operations should work again
        result = await framework.execute_with_resilience("database", database_operation)
        assert result == "database_result"