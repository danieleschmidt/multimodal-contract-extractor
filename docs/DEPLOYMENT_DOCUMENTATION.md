# Deployment Documentation
## Advanced Multimodal Contract Extractor System

**Version**: 4.0.0  
**Last Updated**: 2025-01-24  
**Target Audience**: DevOps Engineers, System Administrators, Cloud Architects  

---

## 📋 Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Production Deployment Guide](#production-deployment-guide)
3. [Scaling Guide](#scaling-guide)
4. [Monitoring Setup](#monitoring-setup)
5. [Security Hardening](#security-hardening)
6. [Multi-Cloud Deployment](#multi-cloud-deployment)
7. [Container Orchestration](#container-orchestration)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start Guide

### Prerequisites Checklist

- [ ] **Docker**: Version 20.10+ installed
- [ ] **Docker Compose**: Version 2.0+ installed
- [ ] **Python**: Version 3.9+ (for local development)
- [ ] **Git**: Latest version for code checkout
- [ ] **Minimum Resources**: 8GB RAM, 4 CPU cores, 50GB storage

### 15-Minute Quick Setup

#### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/multimodal-contract-extractor.git
cd multimodal-contract-extractor

# Create environment file
cp config.example.yml config.yml

# Quick configuration for local testing
cat > .env << EOF
ENVIRONMENT=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@postgres:5432/mce_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$(openssl rand -base64 32)
EOF
```

#### Step 2: Launch with Docker Compose

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check service logs
docker-compose logs -f app
```

#### Step 3: Verify Installation

```bash
# Test API health endpoint
curl http://localhost:8000/api/v1/health

# Test document extraction
curl -X POST -F "file=@test_contract.pdf" \
     http://localhost:8000/api/v1/extract

# Access web interface
open http://localhost:8080
```

### Quick Test with Sample Documents

```bash
# Download sample contracts
mkdir -p test_documents
curl -o test_documents/sample_nda.pdf \
     https://example.com/sample_contracts/nda.pdf

# Test extraction
python extract.py --file test_documents/sample_nda.pdf \
                  --output results.json \
                  --enable-gnn \
                  --enable-advanced-attention

# View results
cat results.json | jq '.results.clauses[] | {type: .type, confidence: .confidence}'
```

---

## 🏭 Production Deployment Guide

### Infrastructure Requirements

#### Hardware Specifications

| Component | Minimum | Recommended | High-Performance |
|-----------|---------|-------------|------------------|
| **CPU** | 8 cores (3.0GHz) | 16 cores (3.5GHz) | 32 cores (4.0GHz) |
| **RAM** | 16 GB | 32 GB | 64 GB |
| **Storage** | 500 GB SSD | 1 TB NVMe | 2 TB NVMe |
| **GPU** | - | 8 GB VRAM | 24 GB VRAM |
| **Network** | 1 Gbps | 10 Gbps | 25 Gbps |

#### Cloud Instance Recommendations

**AWS:**
- Development: `m5.2xlarge` (8 vCPU, 32 GB RAM)
- Production: `c5.4xlarge` (16 vCPU, 32 GB RAM)
- GPU-enabled: `p3.2xlarge` (8 vCPU, 61 GB RAM, V100)

**Google Cloud:**
- Development: `n1-standard-8` (8 vCPU, 30 GB RAM)
- Production: `c2-standard-16` (16 vCPU, 64 GB RAM)
- GPU-enabled: `n1-standard-8` + `nvidia-tesla-v100`

**Azure:**
- Development: `Standard_D8s_v3` (8 vCPU, 32 GB RAM)
- Production: `Standard_F16s_v2` (16 vCPU, 32 GB RAM)
- GPU-enabled: `Standard_NC6s_v3` (6 vCPU, 112 GB RAM, V100)

### Environment Setup

#### Production Configuration

```yaml
# config.production.yml
system:
  name: "multimodal-contract-extractor"
  version: "4.0.0"
  environment: "production"
  debug: false
  
# High-performance processing settings
processing:
  batch_size: 64
  max_concurrent_requests: 500
  timeout_seconds: 600
  memory_limit_mb: 8192
  
# Enable all research algorithms for maximum capability
research:
  gnn:
    enabled: true
    model_type: "legal_gat_large"
    hidden_dimensions: 512
    num_layers: 6
    attention_heads: 16
    
  transformer_attention:
    enabled: true
    model_size: "xlarge"
    max_sequence_length: 4096
    num_attention_heads: 24
    
  federated_learning:
    enabled: true  # Enable for multi-org deployments
    privacy_budget: 5.0
    differential_privacy: true
    secure_aggregation: true
    
  causal_inference:
    enabled: true
    confidence_threshold: 0.8
    max_causal_depth: 10
    
  multimodal_fusion:
    enabled: true
    text_weight: 0.6
    visual_weight: 0.4

# Enterprise-grade reliability
enterprise:
  error_handling:
    circuit_breaker:
      enabled: true
      failure_threshold: 3
      recovery_timeout: 60
      half_open_max_calls: 10
    retry:
      max_attempts: 5
      backoff_multiplier: 2.0
      max_delay: 300
      
  monitoring:
    prometheus:
      enabled: true
      port: 9090
      scrape_interval: 15
    jaeger:
      enabled: true
      sampling_rate: 0.1
    metrics_collection_interval: 15
    health_check_interval: 30
    performance_monitoring: true
    
  security:
    encryption_enabled: true
    tls_enabled: true
    audit_logging: true
    access_control: "rbac"
    rate_limiting: true
    
  logging:
    level: "INFO"
    structured: true
    json_format: true
    retention_days: 90
    compression: true

# Maximum optimization settings
optimization:
  gpu:
    enabled: true  # Enable for GPU instances
    memory_optimization: true
    mixed_precision: true
    tensor_parallelism: true
    
  distributed_computing:
    enabled: true
    max_workers: 50
    load_balancing: "intelligent"
    fault_tolerance: true
    
  caching:
    multi_level: true
    l1_size_mb: 2048
    l2_enabled: true
    l2_size_mb: 8192
    l3_enabled: true
    cache_warming: true
    
  auto_scaling:
    enabled: true
    predictive: true
    min_replicas: 3
    max_replicas: 100
    scale_up_threshold: 70
    scale_down_threshold: 30
    
  performance_monitoring:
    real_time: true
    bottleneck_detection: true
    analytics: true
    profiling: true
```

#### Database Setup

```sql
-- Production PostgreSQL setup
-- Create optimized database for contract processing

CREATE DATABASE mce_production;

\c mce_production;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA contracts;
CREATE SCHEMA research;
CREATE SCHEMA monitoring;
CREATE SCHEMA audit;

-- Contracts schema tables
CREATE TABLE contracts.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    content_hash CHAR(64) UNIQUE NOT NULL,
    document_type VARCHAR(50),
    file_size_bytes BIGINT,
    page_count INTEGER,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    processing_duration_ms INTEGER,
    confidence_score DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    search_vector tsvector
);

CREATE TABLE contracts.clauses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES contracts.documents(id) ON DELETE CASCADE,
    clause_type VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    confidence DECIMAL(4,3),
    position JSONB,
    page_number INTEGER,
    legal_analysis JSONB,
    risk_factors TEXT[],
    recommendations TEXT[],
    jurisdiction VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    search_vector tsvector
);

CREATE TABLE contracts.entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES contracts.documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    role VARCHAR(100),
    confidence DECIMAL(4,3),
    normalized_name VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contracts.relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES contracts.documents(id) ON DELETE CASCADE,
    source_id UUID,
    target_id UUID,
    relationship_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(4,3),
    strength DECIMAL(4,3),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Research schema tables
CREATE TABLE research.gnn_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES contracts.documents(id),
    graph_statistics JSONB,
    temporal_analysis JSONB,
    relationship_strength JSONB,
    novel_insights JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE research.federated_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    federation_id VARCHAR(100),
    round_number INTEGER,
    participating_clients TEXT[],
    aggregation_strategy VARCHAR(50),
    privacy_budget_used DECIMAL(10,6),
    convergence_metrics JSONB,
    byzantine_detections TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX CONCURRENTLY idx_documents_status ON contracts.documents(processing_status);
CREATE INDEX CONCURRENTLY idx_documents_hash ON contracts.documents(content_hash);
CREATE INDEX CONCURRENTLY idx_documents_created ON contracts.documents(created_at);
CREATE INDEX CONCURRENTLY idx_documents_search ON contracts.documents USING GIN(search_vector);

CREATE INDEX CONCURRENTLY idx_clauses_document ON contracts.clauses(document_id);
CREATE INDEX CONCURRENTLY idx_clauses_type ON contracts.clauses(clause_type);
CREATE INDEX CONCURRENTLY idx_clauses_confidence ON contracts.clauses(confidence);
CREATE INDEX CONCURRENTLY idx_clauses_search ON contracts.clauses USING GIN(search_vector);
CREATE INDEX CONCURRENTLY idx_clauses_text_gin ON contracts.clauses USING GIN(text gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_entities_document ON contracts.entities(document_id);
CREATE INDEX CONCURRENTLY idx_entities_type ON contracts.entities(entity_type);
CREATE INDEX CONCURRENTLY idx_entities_name ON contracts.entities USING GIN(name gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_relationships_document ON contracts.relationships(document_id);
CREATE INDEX CONCURRENTLY idx_relationships_type ON contracts.relationships(relationship_type);

-- Partitioning for large deployments
CREATE TABLE contracts.documents_y2025 PARTITION OF contracts.documents
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Update search vectors trigger
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'documents' THEN
        NEW.search_vector := 
            setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.document_type, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.metadata::text, '')), 'C');
    ELSIF TG_TABLE_NAME = 'clauses' THEN
        NEW.search_vector := 
            setweight(to_tsvector('english', COALESCE(NEW.clause_type, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.text, '')), 'B');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_search_vector
    BEFORE INSERT OR UPDATE ON contracts.documents
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

CREATE TRIGGER update_clauses_search_vector
    BEFORE INSERT OR UPDATE ON contracts.clauses
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

#### Redis Configuration

```conf
# redis.production.conf
# Production Redis configuration

# Network
bind 0.0.0.0
port 6379
protected-mode yes
requirepass your_secure_redis_password

# Memory management
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Clients
maxclients 10000

# Modules for advanced features
loadmodule /usr/lib/redis/modules/rejson.so
loadmodule /usr/lib/redis/modules/redisearch.so
```

### Container Deployment

#### Production Dockerfile

```dockerfile
# Dockerfile.production
# Multi-stage production build

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-gpu.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production-cpu
# CPU-optimized production image

COPY . .
RUN pip install -e .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.prod.py", "src.api.app:app"]

FROM base AS production-gpu
# GPU-optimized production image

RUN pip install --no-cache-dir -r requirements-gpu.txt

COPY . .
RUN pip install -e .

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.prod.py", "src.api.app:app"]
```

#### Gunicorn Production Configuration

```python
# gunicorn.prod.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 300
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "multimodal-contract-extractor"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload application
preload_app = True

def on_starting(server):
    server.log.info("Starting Multimodal Contract Extractor")

def on_reload(server):
    server.log.info("Reloading Multimodal Contract Extractor")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
```

#### Docker Compose Production

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  app:
    image: ghcr.io/your-org/mce-app:v4.0.0-cpu
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://mce_user:${DB_PASSWORD}@postgres:5432/mce_production
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./config.production.yml:/app/config.yml:ro
      - ./logs:/app/logs
      - model_cache:/app/models
    networks:
      - internal
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  app-gpu:
    image: ghcr.io/your-org/mce-app:v4.0.0-gpu
    restart: unless-stopped
    depends_on:
      - postgres
      - redis
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://mce_user:${DB_PASSWORD}@postgres:5432/mce_production
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./config.production.yml:/app/config.yml:ro
      - ./logs:/app/logs
      - model_cache:/app/models
    networks:
      - internal
    deploy:
      replicas: 2
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  nginx:
    image: nginx:1.21-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.production.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - internal
      - external

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=mce_production
      - POSTGRES_USER=mce_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 2G

  prometheus:
    image: prom/prometheus:v2.40.0
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=90d'
    networks:
      - internal

  grafana:
    image: grafana/grafana:9.2.0
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - internal

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  model_cache:

networks:
  internal:
    driver: bridge
  external:
    driver: bridge
```

---

## 📈 Scaling Guide

### Horizontal Scaling Strategies

#### Load Balancing Configuration

```nginx
# nginx.production.conf
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    upstream app_servers {
        least_conn;
        server app_1:8000 weight=1 max_fails=3 fail_timeout=30s;
        server app_2:8000 weight=1 max_fails=3 fail_timeout=30s;
        server app_3:8000 weight=1 max_fails=3 fail_timeout=30s;
        server app_4:8000 weight=2 max_fails=3 fail_timeout=30s;  # GPU server
        server app_5:8000 weight=2 max_fails=3 fail_timeout=30s;  # GPU server
        keepalive 32;
    }

    upstream research_servers {
        # Dedicated servers for research-intensive operations
        server research_1:8000 weight=3;
        server research_2:8000 weight=3;
        keepalive 16;
    }

    server {
        listen 80;
        server_name your-domain.com;

        client_max_body_size 100M;
        client_body_timeout 300s;
        client_header_timeout 60s;
        keepalive_timeout 65s;

        # Standard extraction requests
        location /api/v1/extract {
            proxy_pass http://app_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        # Research-intensive requests
        location /api/v1/research/ {
            proxy_pass http://research_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 120s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
        }

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Health checks
        location /health {
            access_log off;
            proxy_pass http://app_servers;
        }
    }
}
```

#### Auto-Scaling with Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mce-app
  namespace: multimodal-contract-extractor
  labels:
    app: mce-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mce-app
  template:
    metadata:
      labels:
        app: mce-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/api/v1/metrics"
    spec:
      containers:
      - name: mce-app
        image: ghcr.io/your-org/mce-app:v4.0.0-cpu
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mce-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mce-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        volumeMounts:
        - name: config
          mountPath: /app/config.yml
          subPath: config.yml
        - name: model-cache
          mountPath: /app/models
      volumes:
      - name: config
        configMap:
          name: mce-config
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: mce-app-service
  namespace: multimodal-contract-extractor
spec:
  selector:
    app: mce-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mce-app-hpa
  namespace: multimodal-contract-extractor
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mce-app
  minReplicas: 3
  maxReplicas: 50
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### GPU Scaling Configuration

```yaml
# k8s/gpu-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mce-app-gpu
  namespace: multimodal-contract-extractor
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mce-app-gpu
  template:
    metadata:
      labels:
        app: mce-app-gpu
    spec:
      nodeSelector:
        accelerator: nvidia-tesla-v100
      containers:
      - name: mce-app-gpu
        image: ghcr.io/your-org/mce-app:v4.0.0-gpu
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "8Gi"
            cpu: "4000m"
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "8000m"
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: "all"
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
```

### Vertical Scaling Guidelines

#### Performance Tuning by Workload

**Document Processing Heavy:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "12Gi"
    cpu: "6000m"
```

**Research Algorithm Heavy:**
```yaml
resources:
  requests:
    memory: "8Gi"
    cpu: "4000m"
  limits:
    memory: "24Gi"
    cpu: "12000m"
```

**Mixed Workload:**
```yaml
resources:
  requests:
    memory: "6Gi"
    cpu: "3000m"
  limits:
    memory: "16Gi"
    cpu: "8000m"
```

### Database Scaling

#### Read Replicas Configuration

```yaml
# PostgreSQL read replica setup
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "2GB"
      effective_cache_size: "6GB"
      work_mem: "64MB"
      maintenance_work_mem: "512MB"
      
  bootstrap:
    initdb:
      database: mce_production
      owner: mce_user
      
  storage:
    size: 1Ti
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
```

#### Redis Clustering

```yaml
# Redis Cluster for high availability
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: redis-cluster
spec:
  clusterSize: 6
  redisLeader:
    replicas: 3
  redisFollower:
    replicas: 3
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"
  - "recording_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mce-app'
    static_configs:
      - targets: ['app:8000', 'app-gpu:8000']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 30s
    
  - job_name: 'mce-research'
    static_configs:
      - targets: ['research-server:8000']
    metrics_path: '/api/v1/research/metrics'
    scrape_interval: 60s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
- name: mce_alerts
  rules:
  # High error rate
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

  # High response time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High response time"
      description: "95th percentile response time is {{ $value }}s"

  # GPU memory usage
  - alert: HighGPUMemoryUsage
    expr: nvidia_ml_py_memory_used_bytes / nvidia_ml_py_memory_total_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High GPU memory usage"
      description: "GPU memory usage is {{ $value | humanizePercentage }}"

  # Processing queue backlog
  - alert: ProcessingQueueBacklog
    expr: processing_queue_size > 1000
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Processing queue backlog"
      description: "Processing queue has {{ $value }} pending items"

  # Research algorithm performance
  - alert: GNNProcessingSlowdown
    expr: avg_over_time(gnn_processing_duration_seconds[10m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "GNN processing slowdown"
      description: "Average GNN processing time is {{ $value }}s"

  # Federated learning issues
  - alert: FederatedLearningFailure
    expr: federated_round_failures_total > 3
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Federated learning failures"
      description: "{{ $value }} federated learning failures detected"

  # Database performance
  - alert: DatabaseSlowQueries
    expr: pg_stat_database_tup_returned / pg_stat_database_tup_fetched > 100
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Database slow queries"
      description: "Database query efficiency has degraded"
```

### Grafana Dashboards

#### Main System Dashboard

```json
{
  "dashboard": {
    "title": "Multimodal Contract Extractor - System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Active Processing Jobs",
        "type": "graph",
        "targets": [
          {
            "expr": "processing_active_jobs",
            "legendFormat": "Active Jobs"
          }
        ]
      }
    ]
  }
}
```

#### Research Algorithms Dashboard

```json
{
  "dashboard": {
    "title": "Research Algorithms Performance",
    "panels": [
      {
        "title": "GNN Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "gnn_processing_duration_seconds",
            "legendFormat": "GNN Processing Time"
          }
        ]
      },
      {
        "title": "Transformer Attention Accuracy",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(transformer_attention_accuracy_score)",
            "legendFormat": "Accuracy"
          }
        ]
      },
      {
        "title": "Federated Learning Rounds",
        "type": "graph",
        "targets": [
          {
            "expr": "federated_learning_rounds_completed_total",
            "legendFormat": "Completed Rounds"
          }
        ]
      },
      {
        "title": "Causal Inference Results",
        "type": "table",
        "targets": [
          {
            "expr": "causal_inference_relationships_detected",
            "legendFormat": "Relationships Detected"
          }
        ]
      }
    ]
  }
}
```

### Custom Metrics Collection

```python
# Custom metrics for research algorithms
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Create custom registry
registry = CollectorRegistry()

# Document processing metrics
documents_processed = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['document_type', 'processing_mode'],
    registry=registry
)

processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Time spent processing documents',
    ['document_type', 'size_category'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300],
    registry=registry
)

# Research algorithm metrics
gnn_processing_time = Histogram(
    'gnn_processing_duration_seconds',
    'GNN processing time',
    buckets=[0.5, 1, 2, 5, 10, 20, 50],
    registry=registry
)

transformer_accuracy = Gauge(
    'transformer_attention_accuracy_score',
    'Transformer attention accuracy score',
    registry=registry
)

federated_rounds = Counter(
    'federated_learning_rounds_completed_total',
    'Total federated learning rounds completed',
    ['federation_id'],
    registry=registry
)

# GPU utilization
gpu_memory_usage = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage in bytes',
    ['gpu_id'],
    registry=registry
)

# Cache performance
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_level'],
    registry=registry
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_level'],
    registry=registry
)

# Usage in application
@documents_processed.count_exceptions()
@processing_duration.time()
async def process_document(document):
    documents_processed.labels(
        document_type=document.type,
        processing_mode='full'
    ).inc()
    
    # Processing logic here
    result = await extract_clauses(document)
    
    return result
```

---

## 🔐 Security Hardening

### TLS/SSL Configuration

#### SSL Certificate Setup

```bash
# Generate production SSL certificates
# Option 1: Let's Encrypt (Free)
certbot certonly --webroot \
  --webroot-path=/var/www/html \
  --email admin@your-domain.com \
  --agree-tos \
  --no-eff-email \
  --domains your-domain.com,api.your-domain.com

# Option 2: Self-signed for testing
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/ssl/private/mce.key \
  -out /etc/ssl/certs/mce.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Option 3: Corporate CA
# Use your organization's certificate authority
```

#### Nginx SSL Configuration

```nginx
# nginx-ssl.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Authentication & Authorization

#### JWT Authentication Setup

```python
# Authentication middleware
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.token_expiry
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, 
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token"
            )

# Dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    return payload

# Role-based access control
def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in endpoints
@app.post("/api/v1/admin/config")
async def update_config(
    config_data: dict,
    current_user: dict = Depends(require_role("admin"))
):
    # Admin-only endpoint
    pass

@app.post("/api/v1/extract")
async def extract_document(
    document: UploadFile,
    current_user: dict = Depends(get_current_user)
):
    # Authenticated endpoint
    pass
```

### Network Security

#### Firewall Rules

```bash
#!/bin/bash
# firewall-setup.sh
# Configure iptables for production

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# SSH access (restrict to management networks)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Application ports (internal only)
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/8 -j ACCEPT

# Monitoring ports (internal only)
iptables -A INPUT -p tcp --dport 9090 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -s 10.0.0.0/8 -j ACCEPT

# Rate limiting for HTTP
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Drop everything else
iptables -A INPUT -j LOG --log-prefix "Dropped: "
iptables -A INPUT -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Data Encryption

#### Application-Level Encryption

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, password: str):
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.urandom(16),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

# Usage for sensitive document content
encryption = DataEncryption(os.environ['ENCRYPTION_KEY'])

# Encrypt before storing
encrypted_content = encryption.encrypt_data(document_content)
await database.store_document(doc_id, encrypted_content)

# Decrypt when retrieving
encrypted_content = await database.get_document(doc_id)
document_content = encryption.decrypt_data(encrypted_content)
```

### Compliance & Auditing

#### GDPR Compliance Implementation

```python
class GDPRCompliance:
    """GDPR compliance implementation for legal document processing."""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.data_retention = DataRetentionManager()
    
    async def process_with_consent(self, document_data: bytes, 
                                 user_consent: dict) -> dict:
        """Process document with GDPR consent tracking."""
        
        # Verify consent
        if not self._verify_consent(user_consent):
            raise HTTPException(
                status_code=400,
                detail="Valid consent required for processing"
            )
        
        # Log processing activity
        await self.audit_logger.log_processing_activity(
            user_id=user_consent['user_id'],
            document_type=user_consent['document_type'],
            processing_purpose=user_consent['purpose'],
            consent_timestamp=user_consent['timestamp']
        )
        
        # Process with data minimization
        results = await self._process_with_minimization(
            document_data, 
            user_consent['processing_scope']
        )
        
        # Schedule data deletion if temporary processing
        if user_consent.get('temporary_processing', False):
            await self.data_retention.schedule_deletion(
                results['processing_id'],
                retention_days=30
            )
        
        return results
    
    def _verify_consent(self, consent: dict) -> bool:
        """Verify GDPR consent requirements."""
        required_fields = [
            'user_id', 'timestamp', 'purpose', 
            'processing_scope', 'explicit_consent'
        ]
        
        return (
            all(field in consent for field in required_fields) and
            consent['explicit_consent'] is True and
            self._consent_not_expired(consent['timestamp'])
        )
    
    async def handle_data_subject_request(self, request_type: str, 
                                        user_id: str) -> dict:
        """Handle GDPR data subject requests."""
        
        if request_type == "access":
            return await self._export_user_data(user_id)
        elif request_type == "delete":
            return await self._delete_user_data(user_id)
        elif request_type == "rectification":
            return await self._update_user_data(user_id)
        elif request_type == "portability":
            return await self._export_portable_data(user_id)
        else:
            raise ValueError(f"Unknown request type: {request_type}")

# Integration with main application
@app.post("/api/v1/extract-gdpr")
async def extract_with_gdpr_compliance(
    document: UploadFile,
    consent: GDPRConsent,
    gdpr: GDPRCompliance = Depends(get_gdpr_compliance)
):
    document_data = await document.read()
    
    results = await gdpr.process_with_consent(
        document_data=document_data,
        user_consent=consent.dict()
    )
    
    return results
```

This deployment documentation provides comprehensive guidance for deploying the advanced multimodal contract extractor system from quick start to enterprise-scale production deployment with security hardening.