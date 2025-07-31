# Advanced Health Check System

## Overview

This document extends the existing health check system with advanced monitoring and diagnostics for production deployments.

## Health Check Endpoints

### Basic Health Check
```python
# Already implemented in src/multimodal_contract_extractor/health.py
GET /health
{
    "status": "healthy",
    "timestamp": "2025-07-31T10:30:00Z",
    "version": "0.1.0",
    "dependencies": {
        "tesseract": "ok",
        "pdf2image": "ok", 
        "streamlit": "ok"
    }
}
```

### Detailed Health Check
```python
GET /health/detailed
{
    "status": "healthy",
    "timestamp": "2025-07-31T10:30:00Z",
    "version": "0.1.0",
    "system": {
        "cpu_percent": 15.2,
        "memory_percent": 45.8,
        "disk_usage_percent": 62.1,
        "load_average": [0.5, 0.7, 0.8]
    },
    "dependencies": {
        "tesseract": {
            "status": "ok",
            "version": "5.3.4",
            "response_time_ms": 12
        },
        "pdf2image": {
            "status": "ok", 
            "version": "1.17.0",
            "response_time_ms": 8
        }
    },
    "metrics": {
        "documents_processed_24h": 1247,
        "average_processing_time_ms": 2340,
        "error_rate_percent": 0.02,
        "cache_hit_rate_percent": 87.3
    }
}
```

### Readiness Check
```python
GET /health/ready
{
    "ready": true,
    "checks": {
        "database": "ok",
        "external_apis": "ok", 
        "file_system": "ok",
        "memory_available": "ok"
    }
}
```

### Liveness Check
```python
GET /health/live
{
    "alive": true,
    "uptime_seconds": 3600,
    "last_request_timestamp": "2025-07-31T10:29:45Z"
}
```

## Kubernetes Health Checks

### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-extractor
spec:
  template:
    spec:
      containers:
      - name: app
        image: contract-extractor:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30
```

## Monitoring Integration

### Prometheus Metrics
```python
# Extend existing metrics in src/multimodal_contract_extractor/metrics.py

# Health check metrics
health_check_duration = Histogram(
    'health_check_duration_seconds',
    'Time spent on health checks',
    ['check_type']
)

dependency_status = Gauge(
    'dependency_status',
    'Status of external dependencies (1=healthy, 0=unhealthy)',
    ['dependency_name']
)

system_resource_usage = Gauge(
    'system_resource_usage_percent',
    'System resource usage percentage',
    ['resource_type']
)
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Contract Extractor Health",
    "panels": [
      {
        "title": "Health Check Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"contract-extractor\"}"
          }
        ]
      },
      {
        "title": "Dependency Status",
        "type": "table",
        "targets": [
          {
            "expr": "dependency_status"
          }
        ]
      },
      {
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "system_resource_usage_percent"
          }
        ]
      }
    ]
  }
}
```

## Alert Rules

### Prometheus Alert Rules
```yaml
groups:
- name: contract-extractor-health
  rules:
  - alert: ServiceDown
    expr: up{job="contract-extractor"} == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "Contract Extractor service is down"
      
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      
  - alert: DependencyDown
    expr: dependency_status == 0
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "External dependency is down"
      
  - alert: HighResourceUsage
    expr: system_resource_usage_percent > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High resource usage detected"
```

## Load Balancer Health Checks

### AWS Application Load Balancer
```yaml
HealthCheckPath: /health
HealthCheckProtocol: HTTP
HealthCheckIntervalSeconds: 30
HealthCheckTimeoutSeconds: 5
HealthyThresholdCount: 2
UnhealthyThresholdCount: 3
```

### Google Cloud Load Balancer
```yaml
healthCheck:
  type: HTTP
  httpHealthCheck:
    requestPath: /health
    port: 8080
  checkIntervalSec: 30
  timeoutSec: 5
  healthyThreshold: 2
  unhealthyThreshold: 3
```

## Circuit Breaker Integration

### Implementation Example
```python
from circuit_breaker import CircuitBreaker

# Circuit breaker for external dependencies
ocr_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

@ocr_circuit_breaker
def perform_ocr(image_data):
    # OCR processing logic
    pass

# Health check integration
def check_ocr_health():
    if ocr_circuit_breaker.current_state == 'open':
        return {"status": "degraded", "reason": "circuit_breaker_open"}
    return {"status": "ok"}
```

## Custom Health Checks

### Business Logic Health
```python
def check_document_processing_pipeline():
    """Check if document processing pipeline is healthy"""
    try:
        # Test with a small sample document
        test_doc = create_test_document()
        result = process_document(test_doc, timeout=5)
        
        if result and result.get('clauses'):
            return {"status": "ok", "test_clauses_found": len(result['clauses'])}
        else:
            return {"status": "degraded", "reason": "no_clauses_extracted"}
            
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Database Health
```python
def check_database_health():
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        # Simple query to check connectivity
        connection.execute("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        
        if response_time < 100:
            return {"status": "ok", "response_time_ms": response_time}
        else:
            return {"status": "slow", "response_time_ms": response_time}
            
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Testing Health Checks

### Unit Tests
```python
def test_health_endpoint():
    """Test basic health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_with_dependency_failure():
    """Test health check behavior when dependencies fail"""
    with mock.patch('tesseract.is_available', return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"
```

### Integration Tests
```python
def test_kubernetes_health_checks():
    """Test that Kubernetes can successfully call health endpoints"""
    # Test liveness probe
    response = requests.get(f"{base_url}/health/live")
    assert response.status_code == 200
    
    # Test readiness probe  
    response = requests.get(f"{base_url}/health/ready")
    assert response.status_code == 200
```

## Best Practices

1. **Response Time**: Health checks should respond within 3-5 seconds
2. **Minimal Logic**: Keep health checks simple and fast
3. **Graceful Degradation**: Return appropriate status codes for different states
4. **Caching**: Cache expensive health check results for 30-60 seconds
5. **Logging**: Log health check failures for debugging
6. **Versioning**: Include API version in health check responses
7. **Security**: Don't expose sensitive information in health checks

## Conclusion

The existing health check system is already well-implemented. These advanced features provide additional monitoring capabilities for production environments with high availability requirements.