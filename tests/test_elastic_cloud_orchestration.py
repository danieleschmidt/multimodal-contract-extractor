"""Comprehensive tests for elastic cloud orchestration framework."""

import asyncio
import time
import pytest

from multimodal_contract_extractor.elastic_cloud_orchestration import (
    CloudProvider,
    CloudResource,
    CloudResourceManager,
    ElasticCloudOrchestrator,
    InstanceType,
    PredictiveScaler,
    ScalingPolicy,
    ScalingTrigger,
    WorkloadForecast,
    WorkloadPattern,
    enable_predictive_scaling,
    get_cloud_orchestrator,
    record_system_metrics,
)


class TestCloudResource:
    """Test CloudResource data class."""

    def test_cloud_resource_creation(self):
        """Test creating a cloud resource."""
        resource = CloudResource(
            instance_id="test-instance-123",
            instance_type=InstanceType.GENERAL_PURPOSE,
            provider=CloudProvider.AWS,
            region="us-east-1",
            availability_zone="us-east-1a",
            cpu_cores=4,
            memory_gb=16.0,
            gpu_count=0,
            storage_gb=100.0,
            hourly_cost=0.40,
            status="running",
            tags={"environment": "test", "project": "legal-ai"}
        )
        
        assert resource.instance_id == "test-instance-123"
        assert resource.instance_type == InstanceType.GENERAL_PURPOSE
        assert resource.provider == CloudProvider.AWS
        assert resource.cpu_cores == 4
        assert resource.memory_gb == 16.0
        assert resource.hourly_cost == 0.40
        assert resource.tags["environment"] == "test"


class TestScalingPolicy:
    """Test ScalingPolicy data class."""

    def test_scaling_policy_creation(self):
        """Test creating a scaling policy."""
        policy = ScalingPolicy(
            name="cpu_scaling",
            trigger=ScalingTrigger.CPU_UTILIZATION,
            scale_up_threshold=75.0,
            scale_down_threshold=25.0,
            scale_up_adjustment=2,
            scale_down_adjustment=1,
            cooldown_period=300.0,
            min_instances=1,
            max_instances=20,
            target_instance_type=InstanceType.GENERAL_PURPOSE,
            evaluation_periods=3
        )
        
        assert policy.name == "cpu_scaling"
        assert policy.trigger == ScalingTrigger.CPU_UTILIZATION
        assert policy.scale_up_threshold == 75.0
        assert policy.scale_down_threshold == 25.0
        assert policy.enabled is True
        assert policy.evaluation_periods == 3


class TestPredictiveScaler:
    """Test PredictiveScaler implementation."""

    @pytest.fixture
    def predictive_scaler(self):
        """Create a predictive scaler for testing."""
        return PredictiveScaler()

    def test_record_metrics(self, predictive_scaler):
        """Test recording metrics for pattern analysis."""
        current_time = time.time()
        
        predictive_scaler.record_metrics(
            timestamp=current_time,
            cpu_usage=65.0,
            memory_usage=70.0,
            request_rate=150.0,
            tags={"service": "contract_processor"}
        )
        
        assert len(predictive_scaler.historical_metrics) == 1
        metric = predictive_scaler.historical_metrics[0]
        assert metric["cpu_usage"] == 65.0
        assert metric["memory_usage"] == 70.0
        assert metric["request_rate"] == 150.0
        assert metric["tags"]["service"] == "contract_processor"

    def test_detect_steady_state_pattern(self, predictive_scaler):
        """Test detection of steady state workload pattern."""
        current_time = time.time()
        
        # Add steady state metrics (low variance)
        for i in range(100):
            predictive_scaler.record_metrics(
                timestamp=current_time + i,
                cpu_usage=50.0 + (i % 3) * 0.5,  # Very low variance
                memory_usage=60.0,
                request_rate=100.0
            )
        
        pattern = predictive_scaler.detect_workload_pattern()
        assert pattern == WorkloadPattern.STEADY_STATE

    def test_detect_spiky_pattern(self, predictive_scaler):
        """Test detection of spiky workload pattern."""
        current_time = time.time()
        
        # Add spiky metrics (high variance, no clear pattern)
        for i in range(100):
            if i % 10 == 0:
                cpu_usage = 90.0  # Spikes
            else:
                cpu_usage = 20.0  # Low baseline
            
            predictive_scaler.record_metrics(
                timestamp=current_time + i,
                cpu_usage=cpu_usage,
                memory_usage=60.0,
                request_rate=100.0
            )
        
        pattern = predictive_scaler.detect_workload_pattern()
        assert pattern in [WorkloadPattern.SPIKY, WorkloadPattern.PERIODIC]

    def test_generate_forecast_insufficient_data(self, predictive_scaler):
        """Test forecast generation with insufficient data."""
        # Add minimal data
        for i in range(10):
            predictive_scaler.record_metrics(
                timestamp=time.time() + i,
                cpu_usage=50.0,
                memory_usage=60.0,
                request_rate=100.0
            )
        
        forecast = predictive_scaler.generate_forecast(forecast_horizon_hours=12)
        
        assert isinstance(forecast, WorkloadForecast)
        assert forecast.forecast_horizon_hours == 12
        assert len(forecast.predicted_cpu_usage) == 12
        assert forecast.pattern == WorkloadPattern.UNPREDICTABLE
        assert forecast.confidence_interval[0] < forecast.confidence_interval[1]

    def test_generate_forecast_sufficient_data(self, predictive_scaler):
        """Test forecast generation with sufficient data."""
        current_time = time.time()
        
        # Add sufficient historical data
        for i in range(300):
            predictive_scaler.record_metrics(
                timestamp=current_time + i,
                cpu_usage=50.0 + i * 0.1,  # Growing pattern
                memory_usage=60.0,
                request_rate=100.0
            )
        
        forecast = predictive_scaler.generate_forecast(forecast_horizon_hours=24)
        
        assert isinstance(forecast, WorkloadForecast)
        assert forecast.forecast_horizon_hours == 24
        assert len(forecast.predicted_cpu_usage) == 24
        assert len(forecast.predicted_memory_usage) == 24
        assert len(forecast.predicted_request_rate) == 24
        assert forecast.recommended_instances >= 1


class TestCloudResourceManager:
    """Test CloudResourceManager implementation."""

    @pytest.fixture
    def resource_manager(self):
        """Create a cloud resource manager for testing."""
        return CloudResourceManager()

    @pytest.mark.asyncio
    async def test_provision_instance(self, resource_manager):
        """Test provisioning a new cloud instance."""
        resource = await resource_manager.provision_instance(
            instance_type=InstanceType.CPU_OPTIMIZED,
            provider=CloudProvider.AWS,
            region="us-west-2",
            tags={"environment": "production"}
        )
        
        assert isinstance(resource, CloudResource)
        assert resource.instance_type == InstanceType.CPU_OPTIMIZED
        assert resource.provider == CloudProvider.AWS
        assert resource.region == "us-west-2"
        assert resource.status == "running"
        assert resource.tags["environment"] == "production"
        
        # Verify resource is tracked
        assert resource.instance_id in resource_manager.active_resources
        assert len(resource_manager.resource_pools[CloudProvider.AWS]) == 1

    @pytest.mark.asyncio
    async def test_terminate_instance(self, resource_manager):
        """Test terminating a cloud instance."""
        # First provision an instance
        resource = await resource_manager.provision_instance(
            InstanceType.GENERAL_PURPOSE, CloudProvider.AWS, "us-east-1"
        )
        
        instance_id = resource.instance_id
        
        # Terminate the instance
        success = await resource_manager.terminate_instance(instance_id)
        
        assert success is True
        assert instance_id not in resource_manager.active_resources
        assert instance_id in resource_manager.cost_tracking
        assert resource_manager.cost_tracking[instance_id] > 0

    @pytest.mark.asyncio
    async def test_terminate_nonexistent_instance(self, resource_manager):
        """Test terminating a non-existent instance."""
        success = await resource_manager.terminate_instance("nonexistent-instance")
        assert success is False

    @pytest.mark.asyncio
    async def test_instance_specifications(self, resource_manager):
        """Test different instance type specifications."""
        # Test GPU instance
        gpu_resource = await resource_manager.provision_instance(
            InstanceType.GPU_ACCELERATED, CloudProvider.AWS, "us-east-1"
        )
        assert gpu_resource.gpu_count > 0
        assert gpu_resource.hourly_cost > 1.0  # Should be expensive
        
        # Test memory optimized
        memory_resource = await resource_manager.provision_instance(
            InstanceType.MEMORY_OPTIMIZED, CloudProvider.AWS, "us-east-1"
        )
        assert memory_resource.memory_gb >= 32.0
        
        # Test burstable (cheapest)
        burstable_resource = await resource_manager.provision_instance(
            InstanceType.BURSTABLE, CloudProvider.AWS, "us-east-1"
        )
        assert burstable_resource.hourly_cost < 0.5

    def test_get_total_cost(self, resource_manager):
        """Test total cost calculation."""
        # Initially should be zero
        assert resource_manager.get_total_cost() == 0.0
        
        # Add some cost tracking
        resource_manager.cost_tracking["terminated-1"] = 10.50
        resource_manager.cost_tracking["terminated-2"] = 5.75
        
        total_cost = resource_manager.get_total_cost()
        assert total_cost == 16.25

    @pytest.mark.asyncio
    async def test_resource_utilization_summary(self, resource_manager):
        """Test resource utilization summary."""
        # Initially empty
        utilization = resource_manager.get_resource_utilization()
        assert utilization["total_instances"] == 0
        
        # Add some resources
        await resource_manager.provision_instance(
            InstanceType.CPU_OPTIMIZED, CloudProvider.AWS, "us-east-1"
        )
        await resource_manager.provision_instance(
            InstanceType.MEMORY_OPTIMIZED, CloudProvider.GCP, "us-central1"
        )
        
        utilization = resource_manager.get_resource_utilization()
        
        assert utilization["total_instances"] == 2
        assert utilization["total_cpu_cores"] > 0
        assert utilization["total_memory_gb"] > 0
        assert "cpu_optimized" in utilization["by_instance_type"]
        assert "memory_optimized" in utilization["by_instance_type"]
        assert "aws" in utilization["by_provider"]
        assert "gcp" in utilization["by_provider"]


class TestElasticCloudOrchestrator:
    """Test ElasticCloudOrchestrator implementation."""

    @pytest.fixture
    def orchestrator(self):
        """Create an elastic cloud orchestrator for testing."""
        return ElasticCloudOrchestrator()

    @pytest.mark.asyncio
    async def test_record_metrics(self, orchestrator):
        """Test recording system metrics."""
        await orchestrator.record_metrics(
            cpu_usage=65.0,
            memory_usage=70.0,
            response_time=250.0,
            request_rate=150.0,
            error_rate=0.02,
            tags={"service": "contract_extraction"}
        )
        
        assert len(orchestrator.metrics_buffer) == 1
        
        metric = orchestrator.metrics_buffer[0]
        assert metric["cpu_usage"] == 65.0
        assert metric["memory_usage"] == 70.0
        assert metric["response_time"] == 250.0
        assert metric["request_rate"] == 150.0
        assert metric["error_rate"] == 0.02

    @pytest.mark.asyncio
    async def test_default_scaling_policies(self, orchestrator):
        """Test default scaling policies setup."""
        assert "cpu_scaling" in orchestrator.scaling_policies
        assert "memory_scaling" in orchestrator.scaling_policies
        assert "latency_scaling" in orchestrator.scaling_policies
        
        cpu_policy = orchestrator.scaling_policies["cpu_scaling"]
        assert cpu_policy.trigger == ScalingTrigger.CPU_UTILIZATION
        assert cpu_policy.scale_up_threshold == 75.0
        assert cpu_policy.enabled is True

    @pytest.mark.asyncio
    async def test_scale_up_trigger(self, orchestrator):
        """Test scale up triggering."""
        # Record high CPU usage metrics to trigger scaling
        for _ in range(5):  # Need multiple evaluation periods
            await orchestrator.record_metrics(
                cpu_usage=85.0,  # Above 75% threshold
                memory_usage=60.0,
                response_time=200.0,
                request_rate=100.0
            )
            await asyncio.sleep(0.001)
        
        # Wait a bit for evaluation
        await asyncio.sleep(0.01)
        
        # Check if scaling occurred
        assert len(orchestrator.scaling_history) > 0
        
        # Check if instances were provisioned
        assert len(orchestrator.resource_manager.active_resources) > 0

    @pytest.mark.asyncio
    async def test_scale_down_trigger(self, orchestrator):
        """Test scale down triggering."""
        # First provision some instances
        await orchestrator.resource_manager.provision_instance(
            InstanceType.GENERAL_PURPOSE, CloudProvider.AWS, "us-east-1"
        )
        await orchestrator.resource_manager.provision_instance(
            InstanceType.GENERAL_PURPOSE, CloudProvider.AWS, "us-east-1"
        )
        
        initial_instances = len(orchestrator.resource_manager.active_resources)
        
        # Wait for cooldown to pass
        await asyncio.sleep(0.01)
        
        # Record low CPU usage to trigger scale down
        for _ in range(5):
            await orchestrator.record_metrics(
                cpu_usage=15.0,  # Below 25% threshold
                memory_usage=30.0,
                response_time=100.0,
                request_rate=50.0
            )
            await asyncio.sleep(0.001)
        
        # Wait for evaluation
        await asyncio.sleep(0.01)
        
        # Should have scaled down
        final_instances = len(orchestrator.resource_manager.active_resources)
        assert final_instances < initial_instances

    @pytest.mark.asyncio
    async def test_custom_scaling_policy(self, orchestrator):
        """Test creating custom scaling policy."""
        orchestrator.create_scaling_policy(
            name="custom_error_scaling",
            trigger=ScalingTrigger.ERROR_RATE,
            scale_up_threshold=0.05,  # 5% error rate
            scale_down_threshold=0.01,  # 1% error rate
            scale_up_adjustment=3,
            scale_down_adjustment=1,
            min_instances=2,
            max_instances=25,
            target_instance_type=InstanceType.CPU_OPTIMIZED,
            cooldown_period=120.0
        )
        
        assert "custom_error_scaling" in orchestrator.scaling_policies
        
        custom_policy = orchestrator.scaling_policies["custom_error_scaling"]
        assert custom_policy.trigger == ScalingTrigger.ERROR_RATE
        assert custom_policy.scale_up_threshold == 0.05
        assert custom_policy.min_instances == 2
        assert custom_policy.max_instances == 25

    @pytest.mark.asyncio
    async def test_predictive_scaling(self, orchestrator):
        """Test predictive scaling functionality."""
        # Add historical data for better predictions
        current_time = time.time()
        for i in range(300):
            orchestrator.predictive_scaler.record_metrics(
                timestamp=current_time + i,
                cpu_usage=40.0 + i * 0.1,  # Growing pattern
                memory_usage=50.0,
                request_rate=100.0
            )
        
        initial_instances = len(orchestrator.resource_manager.active_resources)
        
        # Enable predictive scaling
        await orchestrator.enable_predictive_scaling(forecast_horizon_hours=6)
        
        # Should have provisioned instances based on forecast
        final_instances = len(orchestrator.resource_manager.active_resources)
        assert final_instances >= initial_instances
        
        # Check scaling history
        predictive_events = [
            event for event in orchestrator.scaling_history
            if event.get("policy_name") == "predictive_scaling"
        ]
        assert len(predictive_events) > 0

    def test_orchestration_status(self, orchestrator):
        """Test orchestration status reporting."""
        status = orchestrator.get_orchestration_status()
        
        assert "resource_utilization" in status
        assert "recent_scaling_events" in status
        assert "workload_pattern" in status
        assert "active_policies" in status
        assert "policy_status" in status
        assert "total_scaling_events" in status
        
        assert isinstance(status["active_policies"], int)
        assert isinstance(status["total_scaling_events"], int)


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_record_system_metrics(self):
        """Test high-level system metrics recording."""
        await record_system_metrics(
            cpu_usage=75.0,
            memory_usage=80.0,
            response_time=300.0,
            request_rate=200.0,
            error_rate=0.03,
            tags={"service": "legal_ai", "version": "v2.1"}
        )
        
        # Verify metrics were recorded in global orchestrator
        orchestrator = get_cloud_orchestrator()
        assert len(orchestrator.metrics_buffer) > 0
        
        latest_metric = orchestrator.metrics_buffer[-1]
        assert latest_metric["cpu_usage"] == 75.0
        assert latest_metric["memory_usage"] == 80.0
        assert latest_metric["tags"]["service"] == "legal_ai"

    @pytest.mark.asyncio
    async def test_enable_predictive_scaling(self):
        """Test high-level predictive scaling enablement."""
        # Add some historical data first
        orchestrator = get_cloud_orchestrator()
        current_time = time.time()
        
        for i in range(250):
            orchestrator.predictive_scaler.record_metrics(
                timestamp=current_time + i,
                cpu_usage=30.0 + i * 0.2,
                memory_usage=40.0,
                request_rate=80.0
            )
        
        initial_instances = len(orchestrator.resource_manager.active_resources)
        
        await enable_predictive_scaling(forecast_horizon_hours=8)
        
        # Should have potentially scaled based on prediction
        final_instances = len(orchestrator.resource_manager.active_resources)
        # Note: May or may not scale depending on forecast, but shouldn't error

    def test_get_cloud_orchestrator(self):
        """Test getting the global cloud orchestrator."""
        orchestrator = get_cloud_orchestrator()
        assert isinstance(orchestrator, ElasticCloudOrchestrator)


class TestEnumerations:
    """Test enumeration values."""

    def test_cloud_provider_values(self):
        """Test cloud provider enum values."""
        assert CloudProvider.AWS.value == "aws"
        assert CloudProvider.AZURE.value == "azure"
        assert CloudProvider.GCP.value == "gcp"
        assert CloudProvider.KUBERNETES.value == "kubernetes"
        assert CloudProvider.ON_PREMISE.value == "on_premise"
        assert CloudProvider.HYBRID.value == "hybrid"

    def test_instance_type_values(self):
        """Test instance type enum values."""
        assert InstanceType.CPU_OPTIMIZED.value == "cpu_optimized"
        assert InstanceType.MEMORY_OPTIMIZED.value == "memory_optimized"
        assert InstanceType.GPU_ACCELERATED.value == "gpu_accelerated"
        assert InstanceType.GENERAL_PURPOSE.value == "general_purpose"
        assert InstanceType.BURSTABLE.value == "burstable"
        assert InstanceType.SPOT_INSTANCE.value == "spot_instance"

    def test_scaling_trigger_values(self):
        """Test scaling trigger enum values."""
        assert ScalingTrigger.CPU_UTILIZATION.value == "cpu_utilization"
        assert ScalingTrigger.MEMORY_UTILIZATION.value == "memory_utilization"
        assert ScalingTrigger.REQUEST_QUEUE_LENGTH.value == "request_queue_length"
        assert ScalingTrigger.RESPONSE_TIME.value == "response_time"
        assert ScalingTrigger.ERROR_RATE.value == "error_rate"
        assert ScalingTrigger.CUSTOM_METRIC.value == "custom_metric"
        assert ScalingTrigger.PREDICTIVE.value == "predictive"
        assert ScalingTrigger.SCHEDULE_BASED.value == "schedule_based"

    def test_workload_pattern_values(self):
        """Test workload pattern enum values."""
        assert WorkloadPattern.STEADY_STATE.value == "steady_state"
        assert WorkloadPattern.SPIKY.value == "spiky"
        assert WorkloadPattern.PERIODIC.value == "periodic"
        assert WorkloadPattern.GROWING.value == "growing"
        assert WorkloadPattern.DECLINING.value == "declining"
        assert WorkloadPattern.UNPREDICTABLE.value == "unpredictable"


class TestIntegrationScenarios:
    """Test integration scenarios for cloud orchestration."""

    @pytest.mark.asyncio
    async def test_complete_auto_scaling_workflow(self):
        """Test complete auto-scaling workflow from metrics to scaling."""
        orchestrator = ElasticCloudOrchestrator()
        
        # Step 1: Normal load - should not trigger scaling
        for _ in range(3):
            await orchestrator.record_metrics(
                cpu_usage=50.0,
                memory_usage=55.0,
                response_time=200.0,
                request_rate=100.0,
                error_rate=0.01
            )
            await asyncio.sleep(0.001)
        
        initial_scaling_events = len(orchestrator.scaling_history)
        
        # Step 2: High load - should trigger scale up
        for _ in range(5):
            await orchestrator.record_metrics(
                cpu_usage=85.0,  # High CPU
                memory_usage=90.0,  # High memory
                response_time=3000.0,  # High latency
                request_rate=500.0,
                error_rate=0.08  # High error rate
            )
            await asyncio.sleep(0.001)
        
        await asyncio.sleep(0.01)  # Wait for evaluation
        
        # Should have triggered multiple scaling policies
        assert len(orchestrator.scaling_history) > initial_scaling_events
        assert len(orchestrator.resource_manager.active_resources) > 0
        
        # Step 3: Low load - should trigger scale down after cooldown
        await asyncio.sleep(0.02)  # Wait for cooldown
        
        for _ in range(5):
            await orchestrator.record_metrics(
                cpu_usage=15.0,
                memory_usage=20.0,
                response_time=100.0,
                request_rate=20.0,
                error_rate=0.001
            )
            await asyncio.sleep(0.001)
        
        await asyncio.sleep(0.01)
        
        # Should have triggered scale down
        scale_down_events = [
            event for event in orchestrator.scaling_history
            if "scale_down" in event.get("action", "")
        ]
        assert len(scale_down_events) > 0

    @pytest.mark.asyncio
    async def test_multi_provider_deployment(self):
        """Test deployment across multiple cloud providers."""
        resource_manager = CloudResourceManager()
        
        # Deploy across different providers
        aws_resource = await resource_manager.provision_instance(
            InstanceType.GENERAL_PURPOSE, CloudProvider.AWS, "us-east-1"
        )
        
        azure_resource = await resource_manager.provision_instance(
            InstanceType.MEMORY_OPTIMIZED, CloudProvider.AZURE, "eastus"
        )
        
        gcp_resource = await resource_manager.provision_instance(
            InstanceType.CPU_OPTIMIZED, CloudProvider.GCP, "us-central1"
        )
        
        # Verify deployment across providers
        utilization = resource_manager.get_resource_utilization()
        
        assert utilization["total_instances"] == 3
        assert "aws" in utilization["by_provider"]
        assert "azure" in utilization["by_provider"]
        assert "gcp" in utilization["by_provider"]
        
        # Each provider should have 1 instance
        assert utilization["by_provider"]["aws"] == 1
        assert utilization["by_provider"]["azure"] == 1
        assert utilization["by_provider"]["gcp"] == 1

    @pytest.mark.asyncio
    async def test_cost_optimization_workflow(self):
        """Test cost optimization through instance type selection."""
        resource_manager = CloudResourceManager()
        
        # Provision different instance types
        instances = []
        
        # Expensive GPU instance
        gpu_instance = await resource_manager.provision_instance(
            InstanceType.GPU_ACCELERATED, CloudProvider.AWS, "us-east-1"
        )
        instances.append(gpu_instance)
        
        # Cheap burstable instance
        burstable_instance = await resource_manager.provision_instance(
            InstanceType.BURSTABLE, CloudProvider.AWS, "us-east-1"
        )
        instances.append(burstable_instance)
        
        # Spot instance (cheapest)
        spot_instance = await resource_manager.provision_instance(
            InstanceType.SPOT_INSTANCE, CloudProvider.AWS, "us-east-1"
        )
        instances.append(spot_instance)
        
        # Verify cost differences
        assert gpu_instance.hourly_cost > burstable_instance.hourly_cost
        assert burstable_instance.hourly_cost > spot_instance.hourly_cost
        
        # Simulate some runtime
        await asyncio.sleep(0.01)
        
        # Terminate instances and check costs
        for instance in instances:
            await resource_manager.terminate_instance(instance.instance_id)
        
        # GPU should be most expensive
        gpu_cost = resource_manager.cost_tracking[gpu_instance.instance_id]
        spot_cost = resource_manager.cost_tracking[spot_instance.instance_id]
        
        assert gpu_cost > spot_cost

    @pytest.mark.asyncio
    async def test_predictive_scaling_with_patterns(self):
        """Test predictive scaling with different workload patterns."""
        orchestrator = ElasticCloudOrchestrator()
        predictive_scaler = orchestrator.predictive_scaler
        
        current_time = time.time()
        
        # Simulate periodic workload (daily pattern)
        for hour in range(168):  # One week of hourly data
            # Simulate daily pattern: low at night, high during day
            hour_of_day = hour % 24
            if 9 <= hour_of_day <= 17:  # Business hours
                base_cpu = 70.0
            elif 6 <= hour_of_day <= 8 or 18 <= hour_of_day <= 20:  # Peak hours
                base_cpu = 85.0
            else:  # Off hours
                base_cpu = 30.0
            
            # Add some noise
            cpu_usage = base_cpu + (hash(str(hour)) % 20 - 10)
            cpu_usage = max(10, min(95, cpu_usage))  # Clamp to realistic range
            
            predictive_scaler.record_metrics(
                timestamp=current_time + hour * 3600,
                cpu_usage=cpu_usage,
                memory_usage=60.0,
                request_rate=100.0
            )
        
        # Detect pattern
        pattern = predictive_scaler.detect_workload_pattern()
        assert pattern in [WorkloadPattern.PERIODIC, WorkloadPattern.STEADY_STATE]
        
        # Generate forecast
        forecast = predictive_scaler.generate_forecast(forecast_horizon_hours=24)
        
        assert forecast.pattern != WorkloadPattern.UNPREDICTABLE
        assert forecast.confidence_interval[1] > forecast.confidence_interval[0]
        assert forecast.recommended_instances >= 1
        
        # Enable predictive scaling
        initial_instances = len(orchestrator.resource_manager.active_resources)
        await orchestrator.enable_predictive_scaling(forecast_horizon_hours=12)
        
        # Should have made scaling decision based on forecast
        final_instances = len(orchestrator.resource_manager.active_resources)
        
        # Check that predictive scaling event was recorded
        predictive_events = [
            event for event in orchestrator.scaling_history
            if event.get("policy_name") == "predictive_scaling"
        ]
        
        # May or may not scale depending on forecast, but should record event if it does
        if final_instances != initial_instances:
            assert len(predictive_events) > 0