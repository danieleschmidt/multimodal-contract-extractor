# Multimodal Contract Extractor - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Multimodal Contract Extractor system in production environments. The system has been enhanced through three generations of development:

- **Generation 1**: Core functionality with multi-language support and advanced classification
- **Generation 2**: Production-ready robustness with security, validation, and monitoring
- **Generation 3**: Enterprise-scale performance optimization and distributed processing

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Python**: 3.9 or higher (3.12 recommended)
- **Memory**: Minimum 8GB RAM (16GB+ recommended for production)
- **Storage**: 50GB+ available space for caches and logs
- **CPU**: Multi-core processor (8+ cores recommended for high throughput)

### Dependencies

```bash
# Core dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip python3-venv
sudo apt-get install -y tesseract-ocr tesseract-ocr-dev
sudo apt-get install -y libtesseract-dev libleptonica-dev
sudo apt-get install -y pkg-config libmagic1

# Optional: Redis for L2 caching
sudo apt-get install -y redis-server

# Optional: GPU support
sudo apt-get install -y nvidia-cuda-toolkit  # if using GPU acceleration
```

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd multimodal-contract-extractor

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-gpu.txt  # Optional: for GPU support
```

### 2. Configuration

Create production configuration file:

```bash
cp config.yml.example config.yml
```

Edit `config.yml` for production settings:

```yaml
# Production Configuration
debug: false
environment: "production"

# Security Settings
security:
  virus_scanning_enabled: true
  rate_limiting_enabled: true
  file_size_limit_mb: 100
  allowed_file_types: ["pdf", "png", "jpg", "jpeg", "tiff"]

# Performance Settings
performance:
  max_concurrent_requests: 50
  request_timeout_seconds: 300
  cache_ttl_seconds: 3600

# Monitoring
monitoring:
  structured_logging_enabled: true
  metrics_enabled: true
  health_checks_enabled: true
  log_level: "INFO"

# Infrastructure
infrastructure:
  caching_enabled: true
  backup_enabled: true
  connection_pooling_enabled: true
  
# Generation 3 Scaling
scaling:
  multi_level_caching:
    l1_memory_mb: 512
    l2_redis_enabled: true
    l3_persistent_enabled: true
  
  distributed_processing:
    enabled: true
    message_queue_url: "redis://localhost:6379"
    max_workers: 10
  
  gpu_acceleration:
    enabled: false  # Set to true if GPU available
    cuda_device: 0
```

### 3. Environment Variables

Set production environment variables:

```bash
export MCE_ENVIRONMENT=production
export MCE_LOG_LEVEL=INFO
export MCE_REDIS_URL=redis://localhost:6379
export MCE_SECRET_KEY=your-secure-secret-key-here
export MCE_MAX_FILE_SIZE=104857600  # 100MB
```

## Deployment Options

### Option 1: Docker Deployment (Recommended)

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-dev \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.multimodal_contract_extractor.health import get_health_status; import sys; sys.exit(0 if get_health_status()['status'] == 'healthy' else 1)"

# Start application
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t multimodal-contract-extractor .
docker run -d \
  --name mce-app \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  -e MCE_ENVIRONMENT=production \
  multimodal-contract-extractor
```

### Option 2: Docker Compose (Full Stack)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCE_ENVIRONMENT=production
      - MCE_REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
```

### Option 3: Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multimodal-contract-extractor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mce
  template:
    metadata:
      labels:
        app: mce
    spec:
      containers:
      - name: mce
        image: multimodal-contract-extractor:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCE_ENVIRONMENT
          value: "production"
        - name: MCE_REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mce-service
spec:
  selector:
    app: mce
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Security Configuration

### 1. SSL/TLS Setup

Configure nginx for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Authentication & Authorization

Enable enterprise SSO integration:

```python
# In your configuration
enterprise_integration = {
    "sso": {
        "providers": [
            {
                "type": "oauth2",
                "provider_url": "https://your-oauth-provider.com",
                "client_id": "your-client-id",
                "client_secret": "your-client-secret",
                "redirect_uri": "https://your-domain.com/auth/callback"
            }
        ]
    },
    "api_gateway": {
        "features": ["authentication", "rate_limiting", "logging"],
        "rate_limits": [
            {
                "path_pattern": "/api/*",
                "requests_per_minute": 100
            }
        ]
    }
}
```

## Monitoring & Observability

### 1. Health Checks

The system provides comprehensive health endpoints:

- `GET /health` - Overall system health
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

### 2. Logging Configuration

Configure structured logging:

```yaml
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    structured:
      format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "correlation_id": "%(correlation_id)s"}'
  handlers:
    file:
      class: logging.handlers.RotatingFileHandler
      filename: logs/application.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
      formatter: structured
  root:
    level: INFO
    handlers: [file]
```

### 3. Metrics Collection

Integrate with Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'multimodal-contract-extractor'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Performance Optimization

### 1. Caching Strategy

Configure multi-level caching:

```python
# L1: In-memory cache (fast access)
l1_config = {
    "max_size_mb": 512,
    "max_entries": 10000,
    "eviction_policy": "adaptive"
}

# L2: Redis cache (shared across instances)
l2_config = {
    "redis_url": "redis://localhost:6379",
    "prefix": "mce_l2"
}

# L3: Persistent cache (long-term storage)
l3_config = {
    "cache_dir": "./cache/l3",
    "max_size_mb": 2048
}
```

### 2. Distributed Processing

Enable distributed processing for high throughput:

```python
# Configure distributed processing
distributed_config = {
    "message_queue_url": "redis://localhost:6379",
    "worker_nodes": [
        {"hostname": "worker1", "port": 8001, "capabilities": ["ocr", "classification"]},
        {"hostname": "worker2", "port": 8002, "capabilities": ["ocr", "classification"]},
        {"hostname": "worker3", "port": 8003, "capabilities": ["gpu_processing"]}
    ]
}
```

### 3. GPU Acceleration

Enable GPU processing for better performance:

```python
# GPU configuration
gpu_config = {
    "enabled": True,
    "cuda_device": 0,
    "memory_limit_gb": 8,
    "batch_size": 32
}
```

## Backup & Recovery

### 1. Automated Backups

Configure automated backups:

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mce_$DATE"

# Create backup using built-in functionality
python -c "
from src.multimodal_contract_extractor.generation2_integration import create_system_backup
result = create_system_backup('automated_backup_$DATE')
print(f'Backup completed: {result}')
"

# Compress and store
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

# Upload to cloud storage (optional)
# aws s3 cp "$BACKUP_DIR.tar.gz" s3://your-backup-bucket/
```

Add to crontab:
```bash
# Run backup every 6 hours
0 */6 * * * /path/to/backup.sh
```

### 2. Recovery Procedures

```bash
# Extract backup
tar -xzf mce_backup_20241201_120000.tar.gz

# Restore data
cp -r mce_backup_20241201_120000/data ./data/
cp -r mce_backup_20241201_120000/logs ./logs/
cp mce_backup_20241201_120000/config.yml ./config.yml

# Restart services
docker-compose restart
# or
kubectl rollout restart deployment/multimodal-contract-extractor
```

## Load Balancing & Scaling

### 1. Horizontal Scaling

Configure auto-scaling in Kubernetes:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mce-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: multimodal-contract-extractor
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Load Balancer Configuration

Configure nginx load balancing:

```nginx
upstream mce_backend {
    least_conn;
    server mce-app-1:8000 max_fails=3 fail_timeout=30s;
    server mce-app-2:8000 max_fails=3 fail_timeout=30s;
    server mce-app-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    location / {
        proxy_pass http://mce_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce L1 cache size: `l1_config.max_size_mb = 256`
   - Enable cache eviction: `eviction_policy = "lru"`
   - Monitor with: `GET /metrics`

2. **Slow Processing**
   - Enable GPU acceleration if available
   - Increase worker count: `max_workers = 20`
   - Check distributed processing: `GET /status/distributed`

3. **Authentication Failures**
   - Verify SSO configuration
   - Check JWT secret key
   - Monitor logs: `tail -f logs/security.log`

### Log Analysis

Monitor key log files:
```bash
# Application logs
tail -f logs/application.log

# Security logs
tail -f logs/security.log

# Performance logs  
tail -f logs/performance.log

# Error aggregation
grep -E "(ERROR|CRITICAL)" logs/application.log | tail -20
```

### Health Monitoring

Set up monitoring alerts:
```bash
# Check system health every minute
*/1 * * * * curl -f http://localhost:8000/health || echo "Health check failed" | mail -s "MCE Health Alert" admin@yourcompany.com
```

## API Usage Examples

### Basic Document Processing

```python
import requests

# Upload and process document
with open('contract.pdf', 'rb') as f:
    response = requests.post(
        'http://your-domain.com/api/extract',
        files={'file': f},
        headers={'Authorization': 'Bearer your-token'}
    )

result = response.json()
print(f"Clauses found: {len(result['clauses'])}")
```

### Batch Processing

```python
# Submit batch job
batch_files = ['contract1.pdf', 'contract2.pdf', 'contract3.pdf']
job_response = requests.post(
    'http://your-domain.com/api/batch',
    json={'files': batch_files},
    headers={'Authorization': 'Bearer your-token'}
)

job_id = job_response.json()['job_id']

# Check status
status_response = requests.get(
    f'http://your-domain.com/api/batch/{job_id}/status',
    headers={'Authorization': 'Bearer your-token'}
)
```

## Performance Benchmarks

Expected performance metrics for the production system:

- **Single Document**: 2-5 seconds for typical PDF (10-50 pages)
- **Throughput**: 100-500 documents/hour (depending on hardware)
- **Memory Usage**: 2-8GB per instance
- **Cache Hit Rate**: 60-85% with proper configuration
- **API Response Time**: <200ms for cached results, <5s for new documents

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review error logs
   - Check system metrics
   - Verify backup integrity

2. **Monthly**:
   - Update dependencies
   - Review security configurations
   - Analyze performance trends

3. **Quarterly**:
   - Security audit
   - Performance optimization review
   - Disaster recovery testing

### Monitoring Dashboards

Create Grafana dashboards to monitor:
- Request rate and response times
- Error rates and types
- Cache hit rates and efficiency
- Resource utilization (CPU, memory, disk)
- Queue depths and processing times

For additional support, refer to the project documentation or contact the development team.