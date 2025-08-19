# Production Deployment Guide

**Multimodal Contract Extractor - Production Deployment**  
**Version**: 4.0 (Autonomous SDLC)  
**Status**: ✅ Production Ready  

## 🚀 Quick Start Production Deployment

### Prerequisites
- Docker 20.10+
- Kubernetes 1.20+
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum, 4 recommended

### 1-Command Production Deployment

```bash
# Clone and deploy
git clone <repository-url>
cd multimodal-contract-extractor
docker-compose -f docker-compose.production.yml up -d
```

The system will be available at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:9090 (Prometheus)
- **Dashboard**: http://localhost:3000 (Grafana)

## 🛠️ Detailed Production Setup

### Environment Configuration

Create production environment variables:

```bash
# Required Environment Variables
export MCE_HOST=0.0.0.0
export MCE_PORT=8000
export MCE_WORKERS=4
export MCE_DEBUG=false

# Security Configuration
export MCE_API_KEY=your-secure-api-key-here
export MCE_RATE_LIMIT_PER_MINUTE=100
export MCE_RATE_LIMIT_PER_HOUR=1000

# Performance Configuration  
export MCE_CACHE_SIZE=1000
export MCE_MAX_FILE_SIZE_MB=100
export MCE_WORKER_TIMEOUT=300

# Database Configuration (Optional)
export MCE_DATABASE_URL=postgresql://user:pass@localhost:5432/mce
export MCE_REDIS_URL=redis://localhost:6379/0
```

### Docker Production Deployment

```bash
# Build production image
docker build -f Dockerfile.production -t mce:production .

# Run with production settings
docker run -d \
  --name mce-production \
  -p 8000:8000 \
  -e MCE_WORKERS=4 \
  -e MCE_DEBUG=false \
  -v /path/to/config:/app/config \
  -v /path/to/logs:/app/logs \
  --restart unless-stopped \
  mce:production
```

### Kubernetes Production Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# Enable auto-scaling
kubectl apply -f k8s/autoscaling/hpa-vpa-configurations.yaml

# Deploy monitoring
kubectl apply -f k8s/monitoring/
```

## 📊 Production Monitoring

### Health Checks

The system provides comprehensive health endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health report
curl http://localhost:8000/health/detailed

# Metrics endpoint
curl http://localhost:8000/metrics
```

### Monitoring Stack

**Prometheus Configuration** (`monitoring/prometheus.yml`):
- System metrics collection
- Application performance monitoring
- Custom business metrics
- Alert rule evaluation

**Grafana Dashboards** (`monitoring/grafana/dashboards/`):
- System performance overview
- API request monitoring
- Error rate tracking
- Resource utilization

### Alert Configuration

Key alerts configured:
- **High Error Rate**: >5% error rate for 5 minutes
- **High Latency**: >2s average response time
- **Resource Usage**: >80% CPU or memory
- **Health Check Failures**: System health degraded

## 🔒 Production Security

### API Security

```yaml
# API Key Authentication
headers:
  Authorization: Bearer your-api-key
  
# Rate Limiting (configured per client)
rate_limits:
  per_minute: 100
  per_hour: 1000
  burst: 10
```

### File Upload Security

```python
# Secure file handling
max_file_size: 100MB
allowed_types: ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']
virus_scanning: enabled
path_traversal_protection: enabled
```

### Network Security

```yaml
# Ingress Security
ingress:
  tls:
    enabled: true
    cert_manager: true
  whitelist_ips:
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"
```

## ⚡ Performance Optimization

### Auto-Scaling Configuration

```yaml
# Horizontal Pod Autoscaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mce-hpa
spec:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Caching Configuration

```python
# Redis Cache Configuration
cache_config:
  backend: "redis"
  url: "redis://localhost:6379/0"
  ttl: 3600
  max_size: 1000
  
# Local Cache Fallback
local_cache:
  size: 500
  ttl: 1800
```

### Load Balancing

```yaml
# Nginx Load Balancer
upstream mce_backend {
    least_conn;
    server mce-1:8000 max_fails=3 fail_timeout=30s;
    server mce-2:8000 max_fails=3 fail_timeout=30s;
    server mce-3:8000 max_fails=3 fail_timeout=30s;
}
```

## 🌍 Multi-Region Deployment

### Region Configuration

```yaml
# us-west-2 deployment
regions:
  us_west_2:
    replicas: 3
    resources:
      cpu: "1000m"
      memory: "2Gi"
    
  us_east_1:
    replicas: 2
    resources:
      cpu: "500m"
      memory: "1Gi"
      
  eu_west_1:
    replicas: 2
    resources:
      cpu: "500m"  
      memory: "1Gi"
```

### Global Load Balancing

```yaml
# Route53 Configuration
dns:
  health_checks: enabled
  failover: automatic
  latency_routing: enabled
  geolocation_routing: enabled
```

## 🔧 Operational Procedures

### Deployment Process

1. **Pre-deployment Checks**
   ```bash
   # Run security scan
   trivy image mce:production
   
   # Validate configuration
   kubectl apply --dry-run=client -f k8s/
   
   # Run smoke tests
   pytest tests/smoke/
   ```

2. **Rolling Deployment**
   ```bash
   # Update image
   kubectl set image deployment/mce container=mce:new-version
   
   # Monitor rollout
   kubectl rollout status deployment/mce
   
   # Verify health
   kubectl get pods -l app=mce
   ```

3. **Post-deployment Validation**
   ```bash
   # Health checks
   curl -f http://mce.production/health
   
   # Functional tests
   pytest tests/integration/
   
   # Performance verification
   ab -n 100 -c 10 http://mce.production/
   ```

### Backup and Recovery

```bash
# Database backup
kubectl exec -it mce-db-0 -- pg_dump mce > backup.sql

# Configuration backup  
kubectl get configmap mce-config -o yaml > config-backup.yaml

# Volume snapshots (EBS/GCE)
kubectl create volumesnapshot mce-data-snapshot \
  --from-pvc=mce-data-pvc
```

### Disaster Recovery

```yaml
# Multi-region failover
failover:
  rto: 15_minutes  # Recovery Time Objective
  rpo: 5_minutes   # Recovery Point Objective
  
  procedures:
    - health_check_failure
    - dns_failover
    - traffic_rerouting
    - database_failover
```

## 📈 Scaling Guidelines

### Vertical Scaling

```yaml
# Increase resources
resources:
  requests:
    cpu: 2000m      # 2 CPUs
    memory: 4Gi     # 4GB RAM
  limits:
    cpu: 4000m      # 4 CPUs  
    memory: 8Gi     # 8GB RAM
```

### Horizontal Scaling

```bash
# Manual scaling
kubectl scale deployment mce --replicas=10

# Auto-scaling triggers
cpu_utilization: 70%
memory_utilization: 80%
custom_metrics: request_queue_length > 10
```

## 🚨 Troubleshooting

### Common Issues

**High Memory Usage**
```bash
# Check memory metrics
kubectl top pods
# Increase memory limits or enable swap
```

**API Timeouts**
```bash
# Check worker processes
kubectl logs deployment/mce
# Increase worker timeout or add replicas
```

**Database Connection Issues**
```bash
# Check database connectivity
kubectl exec -it mce-pod -- nc -zv db-host 5432
# Verify connection pool settings
```

### Log Analysis

```bash
# Application logs
kubectl logs -f deployment/mce --tail=100

# Structured log query
kubectl logs deployment/mce | jq '.level="ERROR"'

# Centralized logging (ELK/Loki)
grafana-cli dashboard list | grep mce
```

## 📞 Support and Maintenance

### Monitoring Checklist
- [ ] Health endpoints responding
- [ ] Error rates < 1%
- [ ] Response times < 500ms
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] Disk space > 20% free

### Maintenance Schedule
- **Daily**: Health check validation, log review
- **Weekly**: Performance analysis, capacity planning  
- **Monthly**: Security updates, dependency updates
- **Quarterly**: Full disaster recovery test

### Support Contacts
- **Operations**: ops@terragon.ai
- **Engineering**: engineering@terragon.ai  
- **Security**: security@terragon.ai
- **Emergency**: +1-555-MCE-HELP

---

## 🎯 Production Checklist

### Pre-Go-Live
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Health checks configured
- [ ] Monitoring dashboards ready
- [ ] Backup procedures tested
- [ ] Disaster recovery tested
- [ ] Documentation complete
- [ ] Team training complete

### Go-Live Day
- [ ] Deployment executed successfully
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Performance within SLA
- [ ] Security controls active
- [ ] Support team on standby

### Post-Go-Live
- [ ] 24-hour stability confirmed
- [ ] Performance SLA met
- [ ] No critical issues reported
- [ ] Monitoring data validates
- [ ] Team trained on operations
- [ ] Runbooks validated

**Status**: ✅ **PRODUCTION READY**

*This deployment guide ensures enterprise-grade production readiness with comprehensive operational procedures, monitoring, and support infrastructure.*