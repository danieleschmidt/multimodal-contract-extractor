"""Comprehensive tests for advanced monitoring and analytics system."""

import asyncio
import time
import pytest

from multimodal_contract_extractor.advanced_monitoring_analytics import (
    AdvancedMonitoringSystem,
    Alert,
    AlertSeverity,
    AnalyticsReport,
    AnalyticsScope,
    MetricPoint,
    MetricType,
    generate_daily_report,
    get_monitoring_system,
    record_accuracy_metric,
    record_business_metric,
    record_performance_metric,
)


class TestMetricPoint:
    """Test MetricPoint data class."""

    def test_metric_point_creation(self):
        """Test creating a metric point."""
        metric = MetricPoint(
            timestamp=time.time(),
            metric_name="test_accuracy",
            metric_type=MetricType.ACCURACY,
            value=0.85,
            tags={"model": "v1", "environment": "prod"},
            metadata={"source": "test"}
        )
        
        assert metric.metric_name == "test_accuracy"
        assert metric.metric_type == MetricType.ACCURACY
        assert metric.value == 0.85
        assert metric.tags["model"] == "v1"
        assert metric.metadata["source"] == "test"


class TestAlert:
    """Test Alert data class."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            id="alert_001",
            severity=AlertSeverity.HIGH,
            metric_name="response_latency",
            message="High response latency detected",
            threshold=2000.0,
            current_value=3500.0,
            timestamp=time.time(),
            tags={"service": "api"}
        )
        
        assert alert.id == "alert_001"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.metric_name == "response_latency"
        assert alert.threshold == 2000.0
        assert alert.current_value == 3500.0
        assert not alert.resolved


class TestAdvancedMonitoringSystem:
    """Test AdvancedMonitoringSystem class."""

    @pytest.fixture
    def monitoring_system(self):
        """Create a monitoring system for testing."""
        return AdvancedMonitoringSystem(retention_hours=1)  # Short retention for tests

    @pytest.mark.asyncio
    async def test_record_metric(self, monitoring_system):
        """Test recording a metric."""
        await monitoring_system.record_metric(
            metric_name="test_accuracy",
            metric_type=MetricType.ACCURACY,
            value=0.88,
            tags={"model": "test"},
            metadata={"source": "unittest"}
        )
        
        # Verify metric was recorded
        metrics = monitoring_system.get_metrics(metric_name="test_accuracy")
        assert len(metrics) == 1
        assert metrics[0].value == 0.88
        assert metrics[0].tags["model"] == "test"

    @pytest.mark.asyncio
    async def test_alert_triggering(self, monitoring_system):
        """Test automatic alert triggering."""
        # Record a metric that should trigger an alert
        await monitoring_system.record_metric(
            metric_name="model_accuracy",
            metric_type=MetricType.ACCURACY,
            value=0.70,  # Below threshold of 0.80
        )
        
        # Check if alert was created
        active_alerts = monitoring_system.get_active_alerts()
        assert len(active_alerts) > 0
        
        accuracy_alerts = [a for a in active_alerts if a.metric_name == "model_accuracy"]
        assert len(accuracy_alerts) > 0
        assert accuracy_alerts[0].severity == AlertSeverity.HIGH

    @pytest.mark.asyncio
    async def test_alert_resolution(self, monitoring_system):
        """Test alert resolution."""
        # Create an alert
        await monitoring_system.record_metric(
            metric_name="error_rate",
            metric_type=MetricType.ERROR_RATE,
            value=0.15,  # Above threshold
        )
        
        active_alerts = monitoring_system.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Resolve the alert
        alert_id = active_alerts[0].id
        success = await monitoring_system.resolve_alert(alert_id)
        assert success
        
        # Check that alert is no longer active
        active_alerts_after = monitoring_system.get_active_alerts()
        resolved_alert_ids = [a.id for a in active_alerts_after if a.resolved]
        assert alert_id not in [a.id for a in active_alerts_after if not a.resolved]

    def test_get_metrics_filtering(self, monitoring_system):
        """Test metric filtering functionality."""
        # Add multiple metrics with different properties
        metrics_data = [
            ("accuracy_v1", MetricType.ACCURACY, 0.85, {"model": "v1"}),
            ("accuracy_v2", MetricType.ACCURACY, 0.88, {"model": "v2"}),
            ("latency_api", MetricType.LATENCY, 150.0, {"service": "api"}),
            ("latency_ml", MetricType.LATENCY, 200.0, {"service": "ml"}),
        ]
        
        for name, metric_type, value, tags in metrics_data:
            monitoring_system.metrics_buffer.append(MetricPoint(
                timestamp=time.time(),
                metric_name=name,
                metric_type=metric_type,
                value=value,
                tags=tags
            ))
        
        # Test filtering by metric name
        accuracy_metrics = monitoring_system.get_metrics(metric_name="accuracy_v1")
        assert len(accuracy_metrics) == 1
        assert accuracy_metrics[0].metric_name == "accuracy_v1"
        
        # Test filtering by metric type
        latency_metrics = monitoring_system.get_metrics(metric_type=MetricType.LATENCY)
        assert len(latency_metrics) == 2
        assert all(m.metric_type == MetricType.LATENCY for m in latency_metrics)
        
        # Test filtering by tags
        v1_metrics = monitoring_system.get_metrics(tags={"model": "v1"})
        assert len(v1_metrics) == 1
        assert v1_metrics[0].tags["model"] == "v1"

    def test_metric_statistics(self, monitoring_system):
        """Test metric statistics calculation."""
        # Add sample metrics
        values = [0.85, 0.88, 0.90, 0.82, 0.87]
        metrics = []
        
        for value in values:
            metric = MetricPoint(
                timestamp=time.time(),
                metric_name="test_metric",
                metric_type=MetricType.ACCURACY,
                value=value
            )
            metrics.append(metric)
        
        stats = monitoring_system.calculate_metric_statistics(metrics)
        
        assert stats["count"] == 5
        assert abs(stats["mean"] - 0.864) < 0.001
        assert stats["min"] == 0.82
        assert stats["max"] == 0.90
        assert stats["median"] == 0.87
        assert stats["std"] > 0

    def test_anomaly_detection(self, monitoring_system):
        """Test anomaly detection functionality."""
        # Create metrics with one clear anomaly
        normal_values = [0.85, 0.86, 0.84, 0.87, 0.85, 0.86, 0.84, 0.87, 0.85, 0.86]
        anomaly_value = 0.50  # Clear anomaly
        
        metrics = []
        for value in normal_values + [anomaly_value]:
            metric = MetricPoint(
                timestamp=time.time(),
                metric_name="anomaly_test",
                metric_type=MetricType.ACCURACY,
                value=value
            )
            metrics.append(metric)
        
        anomalies = monitoring_system.detect_anomalies(metrics, sensitivity=2.0)
        
        assert len(anomalies) >= 1
        assert any(abs(a["value"] - anomaly_value) < 0.01 for a in anomalies)

    def test_trend_analysis(self, monitoring_system):
        """Test trend analysis functionality."""
        # Create increasing trend
        increasing_values = [0.70 + i * 0.02 for i in range(20)]
        metrics = []
        
        for value in increasing_values:
            metric = MetricPoint(
                timestamp=time.time(),
                metric_name="trend_test",
                metric_type=MetricType.ACCURACY,
                value=value
            )
            metrics.append(metric)
        
        trends = monitoring_system.analyze_trends(metrics)
        
        assert trends["trend"] in ["increasing", "strongly_increasing"]
        assert trends["correlation"] > 0.5

    def test_sla_compliance(self, monitoring_system):
        """Test SLA compliance checking."""
        # Add metrics for SLA testing
        accuracy_metrics = [
            MetricPoint(time.time(), "accuracy", MetricType.ACCURACY, 0.90),
            MetricPoint(time.time(), "accuracy", MetricType.ACCURACY, 0.88),
            MetricPoint(time.time(), "accuracy", MetricType.ACCURACY, 0.86),
            MetricPoint(time.time(), "accuracy", MetricType.ACCURACY, 0.84),  # Below SLA
        ]
        
        monitoring_system.metrics_buffer.extend(accuracy_metrics)
        
        start_time = time.time() - 3600
        end_time = time.time()
        
        compliance = monitoring_system.check_sla_compliance(start_time, end_time)
        
        assert "accuracy" in compliance
        assert 0 <= compliance["accuracy"] <= 1

    @pytest.mark.asyncio
    async def test_analytics_report_generation(self, monitoring_system):
        """Test analytics report generation."""
        # Add sample metrics
        current_time = time.time()
        sample_metrics = [
            MetricPoint(current_time - 3600, "accuracy", MetricType.ACCURACY, 0.85),
            MetricPoint(current_time - 1800, "accuracy", MetricType.ACCURACY, 0.87),
            MetricPoint(current_time - 900, "accuracy", MetricType.ACCURACY, 0.88),
            MetricPoint(current_time - 3600, "latency", MetricType.LATENCY, 150.0),
            MetricPoint(current_time - 1800, "latency", MetricType.LATENCY, 160.0),
            MetricPoint(current_time - 900, "latency", MetricType.LATENCY, 155.0),
        ]
        
        monitoring_system.metrics_buffer.extend(sample_metrics)
        
        # Generate report
        start_time = current_time - 3600
        end_time = current_time
        
        report = await monitoring_system.generate_analytics_report(
            AnalyticsScope.HOURLY, start_time, end_time
        )
        
        assert isinstance(report, AnalyticsReport)
        assert report.scope == AnalyticsScope.HOURLY
        assert report.start_time == start_time
        assert report.end_time == end_time
        assert "accuracy" in report.metrics_summary
        assert "latency" in report.metrics_summary
        assert isinstance(report.recommendations, list)

    def test_health_score_calculation(self, monitoring_system):
        """Test system health score calculation."""
        # Add recent metrics
        current_time = time.time()
        recent_metrics = [
            MetricPoint(current_time - 1800, "model_accuracy", MetricType.ACCURACY, 0.88),
            MetricPoint(current_time - 900, "response_latency", MetricType.LATENCY, 1500.0),
            MetricPoint(current_time - 600, "error_rate", MetricType.ERROR_RATE, 0.02),
        ]
        
        monitoring_system.metrics_buffer.extend(recent_metrics)
        
        health_score = monitoring_system.get_system_health_score()
        
        assert "health_score" in health_score
        assert "status" in health_score
        assert 0 <= health_score["health_score"] <= 1
        assert health_score["status"] in ["excellent", "good", "fair", "poor", "critical", "no_data"]


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_record_performance_metric(self):
        """Test high-level performance metric recording."""
        await record_performance_metric("api_latency", 125.0, {"endpoint": "/extract"})
        
        # Verify metric was recorded in global system
        system = get_monitoring_system()
        metrics = system.get_metrics(metric_name="api_latency")
        assert len(metrics) > 0
        assert metrics[-1].value == 125.0
        assert metrics[-1].metric_type == MetricType.PERFORMANCE

    @pytest.mark.asyncio
    async def test_record_accuracy_metric(self):
        """Test high-level accuracy metric recording."""
        await record_accuracy_metric("model_f1_score", 0.92, {"model": "legal_v2"})
        
        system = get_monitoring_system()
        metrics = system.get_metrics(metric_name="model_f1_score")
        assert len(metrics) > 0
        assert metrics[-1].value == 0.92
        assert metrics[-1].metric_type == MetricType.ACCURACY

    @pytest.mark.asyncio
    async def test_record_business_metric(self):
        """Test high-level business metric recording."""
        await record_business_metric("documents_processed", 1250.0, {"batch_id": "b001"})
        
        system = get_monitoring_system()
        metrics = system.get_metrics(metric_name="documents_processed")
        assert len(metrics) > 0
        assert metrics[-1].value == 1250.0
        assert metrics[-1].metric_type == MetricType.BUSINESS_IMPACT

    @pytest.mark.asyncio
    async def test_generate_daily_report(self):
        """Test daily report generation."""
        # Add some sample data
        await record_performance_metric("daily_test_metric", 100.0)
        
        report = await generate_daily_report()
        
        assert isinstance(report, AnalyticsReport)
        assert report.scope == AnalyticsScope.DAILY

    def test_get_monitoring_system(self):
        """Test getting the global monitoring system."""
        system = get_monitoring_system()
        assert isinstance(system, AdvancedMonitoringSystem)


class TestEnumerations:
    """Test enumeration values."""

    def test_metric_type_values(self):
        """Test metric type enum values."""
        assert MetricType.PERFORMANCE.value == "performance"
        assert MetricType.ACCURACY.value == "accuracy"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.RESOURCE_USAGE.value == "resource_usage"
        assert MetricType.BUSINESS_IMPACT.value == "business_impact"
        assert MetricType.MODEL_DRIFT.value == "model_drift"
        assert MetricType.DATA_QUALITY.value == "data_quality"

    def test_alert_severity_values(self):
        """Test alert severity enum values."""
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.INFO.value == "info"

    def test_analytics_scope_values(self):
        """Test analytics scope enum values."""
        assert AnalyticsScope.REAL_TIME.value == "real_time"
        assert AnalyticsScope.HOURLY.value == "hourly"
        assert AnalyticsScope.DAILY.value == "daily"
        assert AnalyticsScope.WEEKLY.value == "weekly"
        assert AnalyticsScope.MONTHLY.value == "monthly"
        assert AnalyticsScope.CUSTOM.value == "custom"


class TestIntegrationScenarios:
    """Test integration scenarios for monitoring and analytics."""

    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_workflow(self):
        """Test complete end-to-end monitoring workflow."""
        system = AdvancedMonitoringSystem(retention_hours=1)
        
        # Step 1: Record various metrics
        metrics_to_record = [
            ("model_accuracy", MetricType.ACCURACY, 0.89, {"model": "legal_v1"}),
            ("api_latency", MetricType.LATENCY, 180.0, {"endpoint": "/extract"}),
            ("error_rate", MetricType.ERROR_RATE, 0.03, {"service": "ml_pipeline"}),
            ("memory_usage", MetricType.RESOURCE_USAGE, 75.0, {"instance": "prod-01"}),
            ("documents_processed", MetricType.BUSINESS_IMPACT, 500.0, {"batch": "daily"})
        ]
        
        for name, metric_type, value, tags in metrics_to_record:
            await system.record_metric(name, metric_type, value, tags)
        
        # Step 2: Verify metrics were recorded
        all_metrics = system.get_metrics()
        assert len(all_metrics) == 5
        
        # Step 3: Check health score
        health_score = system.get_system_health_score()
        assert "health_score" in health_score
        
        # Step 4: Generate analytics report
        end_time = time.time()
        start_time = end_time - 3600
        
        report = await system.generate_analytics_report(
            AnalyticsScope.HOURLY, start_time, end_time
        )
        
        assert len(report.metrics_summary) > 0
        assert len(report.recommendations) >= 0

    @pytest.mark.asyncio
    async def test_alerting_and_monitoring_integration(self):
        """Test integration between alerting and monitoring systems."""
        system = AdvancedMonitoringSystem()
        
        # Record metrics that should trigger various alerts
        alert_scenarios = [
            ("model_accuracy", 0.70),  # Should trigger accuracy drop alert
            ("response_latency_p95", 6000.0),  # Should trigger high latency alert
            ("error_rate", 0.12),  # Should trigger error rate spike alert
            ("memory_usage_percent", 90.0),  # Should trigger memory usage alert
        ]
        
        for metric_name, value in alert_scenarios:
            await system.record_metric(metric_name, MetricType.PERFORMANCE, value)
        
        # Check that alerts were generated
        active_alerts = system.get_active_alerts()
        assert len(active_alerts) >= 3  # At least 3 alerts should be triggered
        
        # Check alert severities
        critical_alerts = system.get_active_alerts(AlertSeverity.CRITICAL)
        high_alerts = system.get_active_alerts(AlertSeverity.HIGH)
        
        assert len(critical_alerts) >= 1  # Error rate spike should be critical
        assert len(high_alerts) >= 1  # Accuracy drop should be high
        
        # Test alert resolution
        if active_alerts:
            alert_to_resolve = active_alerts[0]
            success = await system.resolve_alert(alert_to_resolve.id)
            assert success
            
            # Verify alert is resolved
            updated_alert = next(
                (a for a in system.alerts if a.id == alert_to_resolve.id), None
            )
            assert updated_alert is not None
            assert updated_alert.resolved

    @pytest.mark.asyncio
    async def test_multi_metric_analytics(self):
        """Test analytics with multiple related metrics."""
        system = AdvancedMonitoringSystem()
        
        # Simulate a day's worth of metrics with patterns
        current_time = time.time()
        
        # Simulate accuracy degradation over time
        for i in range(24):  # 24 hours
            timestamp = current_time - (24 - i) * 3600  # Hour by hour
            accuracy = 0.90 - (i * 0.01)  # Gradual degradation
            latency = 150 + (i * 10)  # Increasing latency
            error_rate = 0.02 + (i * 0.003)  # Increasing error rate
            
            # Add some noise
            accuracy += (random.random() - 0.5) * 0.02
            latency += (random.random() - 0.5) * 20
            error_rate += (random.random() - 0.5) * 0.01
            
            # Record metrics
            system.metrics_buffer.append(MetricPoint(
                timestamp, "model_accuracy", MetricType.ACCURACY, accuracy
            ))
            system.metrics_buffer.append(MetricPoint(
                timestamp, "response_latency", MetricType.LATENCY, latency
            ))
            system.metrics_buffer.append(MetricPoint(
                timestamp, "error_rate", MetricType.ERROR_RATE, max(0, error_rate)
            ))
        
        # Analyze trends
        accuracy_metrics = system.get_metrics(metric_name="model_accuracy")
        latency_metrics = system.get_metrics(metric_name="response_latency")
        error_metrics = system.get_metrics(metric_name="error_rate")
        
        accuracy_trend = system.analyze_trends(accuracy_metrics)
        latency_trend = system.analyze_trends(latency_metrics)
        error_trend = system.analyze_trends(error_metrics)
        
        # Verify trends match expectations
        assert accuracy_trend["trend"] in ["decreasing", "strongly_decreasing"]
        assert latency_trend["trend"] in ["increasing", "strongly_increasing"]
        assert error_trend["trend"] in ["increasing", "strongly_increasing"]
        
        # Generate comprehensive report
        start_time = current_time - 86400
        end_time = current_time
        
        report = await system.generate_analytics_report(
            AnalyticsScope.DAILY, start_time, end_time
        )
        
        # Verify report contains degradation warnings
        assert len(report.recommendations) > 0
        degradation_warnings = [
            rec for rec in report.recommendations 
            if "accuracy" in rec.lower() or "degradation" in rec.lower()
        ]
        assert len(degradation_warnings) > 0