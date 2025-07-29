# Kubernetes Deployment Guide

This document provides comprehensive Kubernetes deployment configurations and best practices for the Multimodal Contract Extractor in production environments.

## Overview

The application is designed for cloud-native deployment with horizontal scaling, health monitoring, and enterprise security features.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.x (optional but recommended)
- Container registry access
- Monitoring stack (Prometheus/Grafana)

## Base Deployment

### Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: contract-extractor
  labels:
    app.kubernetes.io/name: multimodal-contract-extractor
    app.kubernetes.io/version: "0.1.0"
```

### ConfigMap for Application Configuration

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: contract-extractor-config
  namespace: contract-extractor
data:
  config.yml: |
    ocr:
      cache_size_limit: 200
      context_window_size: 150
    extraction:
      base_confidence_score: 0.8
      max_confidence_cap: 0.95
      file_size_threshold_mb: 50
    security:
      max_file_size_mb: 100
      request_id_length_limit: 64
    health:
      check_timeout_seconds: 5
```

### Deployment with Horizontal Pod Autoscaler

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-extractor
  namespace: contract-extractor
  labels:
    app.kubernetes.io/name: multimodal-contract-extractor
    app.kubernetes.io/version: "0.1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: multimodal-contract-extractor
  template:
    metadata:
      labels:
        app.kubernetes.io/name: multimodal-contract-extractor
        app.kubernetes.io/version: "0.1.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: contract-extractor
        image: multimodal-contract-extractor:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8501
          name: web
        - containerPort: 8080
          name: metrics
        env:
        - name: MCE_SECURITY_MAX_FILE_SIZE_MB
          value: "100"
        - name: MCE_EXTRACTION_BASE_CONFIDENCE_SCORE
          value: "0.8"
        volumeMounts:
        - name: config
          mountPath: /app/config.yml
          subPath: config.yml
        - name: tmp-storage
          mountPath: /tmp
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
      volumes:
      - name: config
        configMap:
          name: contract-extractor-config
      - name: tmp-storage
        emptyDir:
          sizeLimit: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: contract-extractor-service
  namespace: contract-extractor
  labels:
    app.kubernetes.io/name: multimodal-contract-extractor
spec:
  selector:
    app.kubernetes.io/name: multimodal-contract-extractor
  ports:
  - name: web
    port: 80
    targetPort: 8501
  - name: metrics
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: contract-extractor-hpa
  namespace: contract-extractor
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

## Production Ingress with TLS

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: contract-extractor-ingress
  namespace: contract-extractor
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/client-max-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - contract-extractor.your-domain.com
    secretName: contract-extractor-tls
  rules:
  - host: contract-extractor.your-domain.com
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

## Monitoring and Observability

### ServiceMonitor for Prometheus

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: contract-extractor-metrics
  namespace: contract-extractor
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: multimodal-contract-extractor
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboard ConfigMap

```yaml
# grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: contract-extractor-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Contract Extractor Metrics",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{job=\"contract-extractor\"}[5m])"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph", 
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"contract-extractor\"}[5m]))"
              }
            ]
          }
        ]
      }
    }
```

## Security Configuration

### Network Policies

```yaml
# networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: contract-extractor-netpol
  namespace: contract-extractor
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: multimodal-contract-extractor
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8501
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

### Pod Security Policy

```yaml
# podsecuritypolicy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: contract-extractor-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Deployment Commands

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy configuration
kubectl apply -f configmap.yaml

# Deploy application
kubectl apply -f deployment.yaml

# Deploy HPA
kubectl apply -f hpa.yaml

# Deploy ingress
kubectl apply -f ingress.yaml

# Deploy monitoring
kubectl apply -f servicemonitor.yaml
kubectl apply -f grafana-dashboard.yaml

# Deploy security policies
kubectl apply -f networkpolicy.yaml
kubectl apply -f podsecuritypolicy.yaml
```

## Verification

```bash
# Check deployment status
kubectl get pods -n contract-extractor

# Check HPA status
kubectl get hpa -n contract-extractor

# Check service endpoints
kubectl get endpoints -n contract-extractor

# View logs
kubectl logs -f deployment/contract-extractor -n contract-extractor

# Test health endpoint
kubectl port-forward svc/contract-extractor-service 8080:80 -n contract-extractor
curl http://localhost:8080/health
```

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   - Check resource limits
   - Review application logs
   - Verify configuration

2. **HPA not scaling**
   - Ensure metrics-server is running
   - Check resource requests are set
   - Verify CPU/memory usage

3. **Ingress 502 errors**
   - Check service endpoints
   - Verify pod readiness probes
   - Review ingress controller logs

For additional help, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)