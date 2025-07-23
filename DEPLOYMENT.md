# Deployment Guide

This guide covers deployment options for the Multimodal Contract Extractor across different environments.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+
- **Python**: 3.8+ (3.12 recommended)
- **Memory**: 4GB RAM minimum, 8GB+ recommended for large documents
- **Storage**: 2GB free space for dependencies, additional space for document processing
- **CPU**: Multi-core processor recommended for batch processing

### Required System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y tesseract-ocr poppler-utils python3-pip python3-venv

# CentOS/RHEL
sudo yum install -y tesseract poppler-utils python3-pip

# macOS (using Homebrew)
brew install tesseract poppler python3

# Windows (using Chocolatey)
choco install tesseract poppler python3
```

### OCR Language Support

```bash
# Install additional language packs (optional)
sudo apt install -y tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa

# Verify installation
tesseract --list-langs
```

## Local Development

### Quick Setup

```bash
# Clone repository
git clone <repository-url>
cd multimodal-contract-extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
python extract.py --version
pytest tests/ -v
```

### Development Environment

```bash
# Enable development mode
pip install -e .

# Set up pre-commit hooks
pre-commit install

# Run development server
streamlit run web_app.py --server.port 8501
```

### Configuration for Development

Create `config.dev.yml`:

```yaml
# Development Configuration
ocr:
  cache_size_limit: 50  # Smaller cache for development
  context_window_size: 50

extraction:
  base_confidence_score: 0.7  # Lower threshold for testing
  file_size_threshold_mb: 5   # Stream smaller files in dev

security:
  max_file_size_mb: 50  # Smaller files for development

health:
  check_timeout_seconds: 2  # Faster health checks
```

Set environment variables:
```bash
export MCE_CONFIG_PATH=config.dev.yml
export MCE_LOG_LEVEL=DEBUG
```

## Production Deployment

### Docker Deployment

#### Single Container

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
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
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "from multimodal_contract_extractor.health import health_check; health_check()"

# Run application
CMD ["streamlit", "run", "web_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
# Build image
docker build -t contract-extractor:latest .

# Run container
docker run -d \
  --name contract-extractor \
  -p 8501:8501 \
  -v $(pwd)/config.yml:/app/config.yml:ro \
  -v $(pwd)/data:/app/data \
  contract-extractor:latest
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  contract-extractor:
    build: .
    ports:
      - "8501:8501"
    environment:
      - MCE_SECURITY_MAX_FILE_SIZE_MB=100
      - MCE_OCR_CACHE_SIZE_LIMIT=200
    volumes:
      - ./config.yml:/app/config.yml:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from multimodal_contract_extractor.health import health_check; health_check()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - contract-extractor
    restart: unless-stopped
```

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream contract_extractor {
        server contract-extractor:8501;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        client_max_body_size 100M;

        location / {
            proxy_pass http://contract_extractor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
```

Deploy:
```bash
docker-compose up -d
```

### Kubernetes Deployment

#### Basic Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-extractor
  labels:
    app: contract-extractor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contract-extractor
  template:
    metadata:
      labels:
        app: contract-extractor
    spec:
      containers:
      - name: contract-extractor
        image: contract-extractor:latest
        ports:
        - containerPort: 8501
        env:
        - name: MCE_SECURITY_MAX_FILE_SIZE_MB
          value: "100"
        - name: MCE_OCR_CACHE_SIZE_LIMIT
          value: "200"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: config
          mountPath: /app/config.yml
          subPath: config.yml
          readOnly: true
        - name: data
          mountPath: /app/data
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from multimodal_contract_extractor.health import health_check; health_check()"
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8501
          initialDelaySeconds: 15
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: contract-extractor-config
      - name: data
        persistentVolumeClaim:
          claimName: contract-extractor-data

---
apiVersion: v1
kind: Service
metadata:
  name: contract-extractor-service
spec:
  selector:
    app: contract-extractor
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: contract-extractor-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: contract-extractor-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: contract-extractor-service
            port:
              number: 80
```

Create ConfigMap:
```bash
kubectl create configmap contract-extractor-config --from-file=config.yml
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

### Cloud Platforms

#### AWS ECS Deployment

Create `task-definition.json`:

```json
{
  "family": "contract-extractor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "contract-extractor",
      "image": "your-account.dkr.ecr.region.amazonaws.com/contract-extractor:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MCE_SECURITY_MAX_FILE_SIZE_MB",
          "value": "100"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/contract-extractor",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "python -c 'from multimodal_contract_extractor.health import health_check; health_check()'"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Deploy:
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster contract-extractor-cluster \
  --service-name contract-extractor-service \
  --task-definition contract-extractor:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### Google Cloud Run

Create `cloudbuild.yaml`:

```yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/contract-extractor:$COMMIT_SHA', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/contract-extractor:$COMMIT_SHA']
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
  - 'run'
  - 'deploy'
  - 'contract-extractor'
  - '--image=gcr.io/$PROJECT_ID/contract-extractor:$COMMIT_SHA'
  - '--region=us-central1'
  - '--platform=managed'
  - '--allow-unauthenticated'
  - '--memory=2Gi'
  - '--cpu=1000m'
  - '--max-instances=10'
  - '--set-env-vars=MCE_SECURITY_MAX_FILE_SIZE_MB=100'
```

Deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

#### Azure Container Instances

Create deployment:
```bash
az container create \
  --resource-group contract-extractor-rg \
  --name contract-extractor \
  --image contract-extractor:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8501 \
  --environment-variables MCE_SECURITY_MAX_FILE_SIZE_MB=100 \
  --dns-name-label contract-extractor
```

## High Availability Setup

### Load Balancer Configuration

#### HAProxy Configuration

```haproxy
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend contract_extractor_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/contract-extractor.pem
    redirect scheme https if !{ ssl_fc }
    default_backend contract_extractor_backend

backend contract_extractor_backend
    balance roundrobin
    option httpchk GET /
    server app1 app1:8501 check
    server app2 app2:8501 check
    server app3 app3:8501 check
```

### Database Setup (Optional)

For session storage and result caching:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: contract_extractor
      POSTGRES_USER: ce_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

## Performance Optimization

### Production Configuration

Create `config.prod.yml`:

```yaml
# Production Configuration
ocr:
  cache_size_limit: 500
  context_window_size: 200

extraction:
  base_confidence_score: 0.8
  max_confidence_cap: 0.98
  file_size_threshold_mb: 20
  streaming_chunk_size: 10

security:
  max_file_size_mb: 200
  request_id_length_limit: 64

health:
  check_timeout_seconds: 10

document:
  default_streaming_chunk_size: 15
```

### Resource Monitoring

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'contract-extractor'
    static_configs:
      - targets: ['contract-extractor:8501']
```

#### Grafana Dashboard

Import dashboard configuration for monitoring:
- Processing times
- Memory usage
- Cache hit rates
- Error rates
- Document throughput

### Auto-scaling

#### Kubernetes HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: contract-extractor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: contract-extractor
  minReplicas: 2
  maxReplicas: 10
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

## Security Considerations

### SSL/TLS Configuration

Generate certificates:
```bash
# Self-signed certificate for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Let's Encrypt for production
certbot certonly --standalone -d your-domain.com
```

### Environment Variables Security

```bash
# Use secrets management
export MCE_SECRET_KEY=$(openssl rand -base64 32)
export MCE_DATABASE_URL="postgresql://user:$(cat /secrets/db_password)@db:5432/contract_extractor"
```

### Network Security

- Configure firewall rules
- Use VPC/private networks
- Implement rate limiting
- Enable request logging
- Regular security audits

## Backup and Recovery

### Data Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup configuration
cp config.yml $BACKUP_DIR/config_$DATE.yml

# Backup processed data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/
```

### Disaster Recovery

1. Document all configuration files
2. Automate deployment with Infrastructure as Code
3. Regular backup testing
4. Recovery time objectives (RTO) planning
5. Data replication strategies

## Maintenance Tasks

### Regular Maintenance

```bash
#!/bin/bash
# maintenance.sh

# Clean old temporary files
find /tmp -name "ce_*" -mtime +1 -delete

# Rotate logs
logrotate /etc/logrotate.d/contract-extractor

# Health check
python -c "from multimodal_contract_extractor.health import health_check; health_check()"

# Update dependencies (scheduled maintenance window)
pip install --upgrade -r requirements.txt
```

### Monitoring and Alerts

Set up alerts for:
- High memory usage (>80%)
- High CPU usage (>80%)
- Processing failures (>5% error rate)
- Long processing times (>60s average)
- Disk space usage (>90%)

### Updates and Patches

1. Test updates in staging environment
2. Schedule maintenance windows
3. Use blue-green deployments for zero-downtime updates
4. Rollback procedures for failed updates
5. Version pinning for reproducible deployments

## Environment-Specific Notes

### Development
- Use file-based configuration
- Local database for testing
- Verbose logging enabled
- Smaller resource limits

### Staging
- Production-like configuration
- Separate database instance
- Load testing environment
- Automated deployment testing

### Production
- Optimized configuration
- High availability setup
- Production database cluster
- Comprehensive monitoring
- Security hardening
- Backup and recovery procedures