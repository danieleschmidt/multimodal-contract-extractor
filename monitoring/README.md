# Monitoring & Observability

This directory contains the complete monitoring and observability stack for the Multimodal Contract Extractor. Our monitoring approach provides comprehensive insights into application performance, infrastructure health, business metrics, and security posture.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Quick Start](#quick-start)
- [Metrics](#metrics)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Health Monitoring](#health-monitoring)
- [Distributed Tracing](#distributed-tracing)
- [Log Aggregation](#log-aggregation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

Our monitoring stack implements the three pillars of observability:

1. **Metrics**: Time-series data collected via Prometheus
2. **Logs**: Structured logging with optional Loki aggregation
3. **Traces**: Distributed tracing with OpenTelemetry and Jaeger

### Key Features

- **Real-time Monitoring**: Sub-second metric collection and alerting
- **Comprehensive Health Checks**: Multi-layered health monitoring with automated recovery
- **Business Metrics**: Track clause detection accuracy, processing throughput, and data quality
- **Security Monitoring**: Detect suspicious activities and compliance violations
- **Performance Optimization**: Identify bottlenecks and optimization opportunities
- **Automated Alerting**: Multi-channel alerts with intelligent routing and suppression

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │Application  │────▶│ Prometheus   │────▶│   Grafana       │    │
│  │Metrics      │    │ (Metrics)    │    │ (Visualization) │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│         │                   │                      │           │
│         │            ┌──────────────┐              │           │
│         │            │ Alertmanager │              │           │
│         │            │ (Alerting)   │              │           │
│         │            └──────────────┘              │           │
│         │                   │                      │           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │Application  │────▶│    Loki      │────▶│     Grafana     │    │
│  │Logs         │    │  (Logs)      │    │   (Log View)    │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│         │                                        │           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │Application  │────▶│   Jaeger     │────▶│     Jaeger      │    │
│  │Traces       │    │ (Tracing)    │    │     UI          │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Core Components

1. **Prometheus**: Metrics collection and storage
2. **Grafana**: Visualization and dashboards
3. **Alertmanager**: Alert routing and management
4. **Node Exporter**: System metrics collection
5. **cAdvisor**: Container metrics collection

### Enhanced Monitoring

1. **Enhanced Health Monitor** (`health_monitor.py`): Advanced health checking
2. **Distributed Tracing** (`distributed_tracing.py`): OpenTelemetry integration
3. **SLA Monitoring** (`sla_monitoring.py`): Service level monitoring
4. **Error Tracking** (`error_tracking.py`): Centralized error management

### Optional Components

1. **Jaeger**: Distributed tracing (when enabled)
2. **Loki**: Log aggregation (when enabled)
3. **Promtail**: Log collection (when enabled)
4. **Blackbox Exporter**: Endpoint monitoring (when enabled)

## Quick Start

### Basic Monitoring Stack

```bash
# Start core monitoring components
docker-compose up -d app prometheus grafana alertmanager node-exporter cadvisor

# Wait for services to initialize
sleep 30

# Check service health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana
curl http://localhost:9093/-/healthy  # Alertmanager
```

### With Full Observability

```bash
# Start with all monitoring features
docker-compose --profile monitoring --profile logging --profile tracing up -d

# Verify all services
docker-compose ps
```

### Access Points

- **Application**: http://localhost:8501
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Alertmanager**: http://localhost:9093
- **Jaeger**: http://localhost:16686

## Metrics

### Application Metrics

Our application exposes metrics at `/metrics` endpoint:

#### Business Metrics
```
# Clause detection accuracy
mce_clause_detection_accuracy

# Document processing metrics
mce_document_processing_duration_seconds
mce_document_processing_queue_size
mce_documents_processed_total
mce_document_processing_failures_total

# Data quality metrics
mce_data_quality_score
mce_data_validation_failures_total
```

#### Performance Metrics
```
# HTTP request metrics
http_requests_total
http_request_duration_seconds
http_request_size_bytes
http_response_size_bytes

# Model inference metrics
mce_model_inference_duration_seconds
mce_model_inference_total
mce_model_inference_failures_total
mce_model_accuracy
```

#### System Metrics
```
# Health check metrics
mce_health_check_status
mce_health_check_duration_seconds
mce_health_check_failures_total

# Resource usage
mce_system_memory_usage_percent
mce_system_cpu_usage_percent
mce_system_disk_usage_percent
```

### Infrastructure Metrics

Collected via Node Exporter and cAdvisor:

- CPU, memory, disk, network utilization
- Container resource usage
- File system metrics
- System load and process counts

### Recording Rules

Pre-computed metrics for dashboard performance:

```yaml
# Application performance aggregations
app:http_request_rate_5m
app:http_error_rate_5m
app:document_processing_duration_p95_5m

# Business metric aggregations
business:clause_detection_accuracy_1h
business:contracts_processed_rate_1h

# SLA compliance metrics
sli:availability_5m
sli:latency_5m
sli:error_budget_consumption_5m
```

## Alerting

### Alert Rules

Our alerting system covers:

1. **Application Health**: Service availability, response times, error rates
2. **Infrastructure**: Resource utilization, disk space, network connectivity
3. **Business Metrics**: Accuracy thresholds, processing failures, data quality
4. **Security**: Unauthorized access, compliance violations, suspicious activities

### Alert Routing

Alerts are routed based on:

- **Severity**: Critical, Warning, Info
- **Category**: Application, Infrastructure, Security, Compliance
- **Team**: Application, Infrastructure, Security, Performance

### Notification Channels

- **Email**: Team-specific mailing lists
- **Slack**: Dedicated channels for different alert types
- **Webhooks**: Integration with external systems
- **PagerDuty**: Critical alerts for on-call rotation

### Example Alerts

```yaml
# Critical application down
- alert: ApplicationDown
  expr: up{job="multimodal-contract-extractor"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Application is down"
    description: "MCE application has been down for more than 1 minute"

# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
  for: 3m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

## Dashboards

### Main Dashboard: Multimodal Contract Extractor Overview

**Location**: `/monitoring/grafana/dashboards/multimodal-contract-extractor-overview.json`

**Panels**:
1. **System Health Overview**: Overall health scores
2. **Application Availability**: Uptime tracking
3. **Request Metrics**: Rate, errors, latency
4. **Document Processing**: Throughput, queue size, failures
5. **Business Metrics**: Accuracy, data quality
6. **Resource Usage**: CPU, memory, disk
7. **ML Model Performance**: Inference metrics
8. **SLA Compliance**: Availability, latency, quality targets

### Additional Dashboards

1. **Infrastructure Dashboard**: System and container metrics
2. **Business Metrics Dashboard**: Contract processing insights
3. **Security Dashboard**: Security events and compliance
4. **Performance Dashboard**: Detailed performance analysis

### Dashboard Features

- **Template Variables**: Filter by instance, time range
- **Annotations**: Deployment markers, incident tracking
- **Alerts Integration**: Visual alert status
- **Drill-down**: Links to detailed views

## Health Monitoring

### Enhanced Health Monitor

**Location**: `/monitoring/health_monitor.py`

**Features**:
- **Comprehensive Checks**: System, dependencies, filesystem, network, security
- **Configurable Thresholds**: Customizable warning and critical levels
- **Automated Recovery**: Self-healing capabilities where possible
- **Metrics Integration**: Prometheus metrics for all health checks
- **Alert Integration**: Automatic alerting for critical failures

### Health Check Categories

1. **System Resources**: CPU, memory, disk usage
2. **Dependencies**: External services, libraries, databases
3. **Filesystem**: File permissions, disk space, write tests
4. **Network**: Connectivity, DNS resolution, endpoint availability
5. **Security**: File permissions, user context, environment security
6. **Performance**: Benchmarks, latency tests, throughput validation
7. **Data Integrity**: Data validation, consistency checks

### Usage

```python
from monitoring.health_monitor import start_enhanced_monitoring, get_enhanced_health

# Start background monitoring
monitor = start_enhanced_monitoring()

# Get current health status
health = get_enhanced_health()
print(f"Status: {health['status']}")
```

```bash
# CLI usage
python monitoring/health_monitor.py --format json
python monitoring/health_monitor.py --start-monitoring
python monitoring/health_monitor.py --metrics
```

## Distributed Tracing

### OpenTelemetry Integration

**Location**: `/monitoring/distributed_tracing.py`

**Features**:
- **Automatic Instrumentation**: HTTP requests, database calls
- **Custom Spans**: Business logic tracing
- **Context Propagation**: Trace correlation across services
- **Sampling**: Configurable trace sampling rates
- **Multiple Exporters**: Jaeger, Zipkin, OTLP support

### Usage

```python
from monitoring.distributed_tracing import trace_function, trace_operation

@trace_function("document.processing")
def process_document(document_path):
    with trace_operation("ocr.extraction"):
        # OCR processing
        pass
    
    with trace_operation("clause.detection"):
        # ML inference
        pass
```

### Configuration

```bash
# Environment variables
export JAEGER_ENABLED=true
export JAEGER_ENDPOINT=http://localhost:14268/api/traces
export TRACE_SAMPLE_RATE=0.1
export SERVICE_NAME=multimodal-contract-extractor
```

## Log Aggregation

### Loki Integration

**Optional Component**: Enable with `--profile logging`

**Features**:
- **Structured Logging**: JSON log format
- **Label-based Indexing**: Efficient log queries
- **Grafana Integration**: Unified logs and metrics view
- **Log Retention**: Configurable retention policies

### Promtail Configuration

Collects logs from:
- Application logs: `/app/logs`
- System logs: `/var/log`
- Container logs: Docker logging driver

## Configuration

### Environment Variables

```bash
# Core monitoring
MCE_ENV=production
PROMETHEUS_ENABLED=true
MONITORING_ENABLED=true

# Health monitoring
HEALTH_CHECK_INTERVAL=30
HEALTH_ALERT_WEBHOOK=http://localhost:5001/alerts

# Tracing
JAEGER_ENABLED=false
TRACE_SAMPLE_RATE=1.0

# Alerting
ALERT_WEBHOOK_URL=https://hooks.slack.com/your/webhook
ALERT_EMAIL_RECIPIENTS=alerts@terragon.ai
```

### Docker Compose Profiles

```bash
# Basic monitoring
docker-compose up -d

# With extended monitoring
docker-compose --profile monitoring up -d

# With logging
docker-compose --profile logging up -d

# With tracing
docker-compose --profile tracing up -d

# Full observability stack
docker-compose --profile monitoring --profile logging --profile tracing up -d
```

### Prometheus Configuration

**File**: `/monitoring/prometheus.yml`

Key configurations:
- **Scrape Intervals**: 10s for application, 15s for infrastructure
- **Retention**: 30 days storage, 50GB limit
- **Alert Rules**: Comprehensive alerting coverage
- **Recording Rules**: Performance optimizations

## Troubleshooting

### Common Issues

1. **Metrics Not Appearing**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Verify application metrics endpoint
   curl http://localhost:8501/metrics
   ```

2. **Alerts Not Firing**
   ```bash
   # Check Alertmanager config
   curl http://localhost:9093/api/v1/status
   
   # Verify alert rules
   curl http://localhost:9090/api/v1/rules
   ```

3. **Grafana Dashboard Issues**
   ```bash
   # Check Grafana health
   curl http://localhost:3000/api/health
   
   # Verify datasource connection
   curl -u admin:admin http://localhost:3000/api/datasources
   ```

4. **Health Check Failures**
   ```bash
   # Run health check manually
   python monitoring/health_monitor.py --format json
   
   # Check specific health check
   python -c "from monitoring.health_monitor import get_enhanced_health; print(get_enhanced_health())"
   ```

### Performance Optimization

1. **Reduce Metric Cardinality**: Avoid high-cardinality labels
2. **Optimize Queries**: Use recording rules for complex queries
3. **Adjust Scrape Intervals**: Balance frequency vs. performance
4. **Configure Retention**: Set appropriate storage limits

### Debugging Tools

```bash
# Prometheus query CLI
promtool query instant 'up{job="multimodal-contract-extractor"}'

# Check configuration
promtool check config monitoring/prometheus.yml
promtool check rules monitoring/alert_rules.yml

# Grafana CLI
grafana-cli admin reset-admin-password newpassword
```

## Best Practices

### Metrics

1. **Use Appropriate Metric Types**:
   - Counters: Cumulative values (requests, errors)
   - Gauges: Point-in-time values (memory usage, queue size)
   - Histograms: Distribution measurements (response times)

2. **Label Guidelines**:
   - Keep cardinality low (< 1000 unique combinations)
   - Use meaningful, consistent label names
   - Avoid user-specific or timestamp labels

3. **Naming Conventions**:
   - Use snake_case for metric names
   - Include unit suffixes (`_seconds`, `_bytes`, `_total`)
   - Prefix with application name (`mce_`)

### Alerting

1. **Alert Design**:
   - Alert on symptoms, not causes
   - Make alerts actionable
   - Include relevant context in annotations

2. **Alert Fatigue Prevention**:
   - Use appropriate thresholds
   - Implement alert suppression
   - Group related alerts

3. **Runbooks**:
   - Document response procedures
   - Include diagnostic commands
   - Provide escalation paths

### Dashboards

1. **Dashboard Organization**:
   - Start with high-level overview
   - Provide drill-down capabilities
   - Use consistent colors and styles

2. **Performance**:
   - Use recording rules for complex queries
   - Limit time ranges appropriately
   - Avoid excessive auto-refresh

### Security

1. **Access Control**:
   - Implement authentication for Grafana
   - Restrict Prometheus access
   - Secure alert notification channels

2. **Data Privacy**:
   - Avoid logging sensitive data
   - Implement log scrubbing
   - Configure appropriate retention

### Maintenance

1. **Regular Tasks**:
   - Monitor storage usage
   - Review and update alert thresholds
   - Test alert notification channels
   - Update dashboard templates

2. **Capacity Planning**:
   - Monitor ingestion rates
   - Plan for growth
   - Implement data lifecycle policies

For additional support or questions about the monitoring setup, please refer to the main project documentation or open an issue in the repository.