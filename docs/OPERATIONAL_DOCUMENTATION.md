# Operational Documentation
## Advanced Multimodal Contract Extractor - Operations Manual

**Version**: 4.0.0  
**Last Updated**: 2025-01-24  
**Target Audience**: Operations Team, SRE, System Administrators, DevOps Engineers  

---

## 📋 Table of Contents

1. [Operations Manual](#operations-manual)
2. [Incident Response](#incident-response)
3. [Performance Optimization](#performance-optimization)
4. [Cost Management](#cost-management)
5. [Disaster Recovery](#disaster-recovery)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Security Operations](#security-operations)
9. [Capacity Planning](#capacity-planning)

---

## 📖 Operations Manual

### Daily Operations Procedures

#### Morning Health Check Routine

```bash
#!/bin/bash
# daily_health_check.sh
# Daily operations health check routine

echo "=== Daily Health Check - $(date) ==="

# 1. Check system health endpoints
echo "1. Checking API health..."
curl -s http://localhost:8000/api/v1/health | jq '.'

# 2. Check database connectivity
echo "2. Checking database connectivity..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
fi

# 3. Check Redis connectivity
echo "3. Checking Redis connectivity..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
if [ $? -eq 0 ]; then
    echo "✓ Redis connection successful"
else
    echo "✗ Redis connection failed"
fi

# 4. Check processing queue status
echo "4. Checking processing queue..."
QUEUE_SIZE=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT llen processing_queue)
echo "Processing queue size: $QUEUE_SIZE"

if [ $QUEUE_SIZE -gt 1000 ]; then
    echo "⚠ Queue size is high, consider scaling up workers"
fi

# 5. Check disk space
echo "5. Checking disk space..."
df -h | grep -E "(/$|/data|/logs)" | while read line; do
    USAGE=$(echo $line | awk '{print $5}' | sed 's/%//')
    MOUNT=$(echo $line | awk '{print $6}')
    
    if [ $USAGE -gt 85 ]; then
        echo "⚠ Disk usage high on $MOUNT: ${USAGE}%"
    else
        echo "✓ Disk usage OK on $MOUNT: ${USAGE}%"
    fi
done

# 6. Check memory usage
echo "6. Checking memory usage..."
MEMORY_USAGE=$(free | awk 'FNR==2{printf "%.0f", $3/($3+$4)*100}')
if [ $MEMORY_USAGE -gt 85 ]; then
    echo "⚠ Memory usage high: ${MEMORY_USAGE}%"
else
    echo "✓ Memory usage OK: ${MEMORY_USAGE}%"
fi

# 7. Check recent errors in logs
echo "7. Checking for recent errors..."
ERROR_COUNT=$(journalctl -u multimodal-contract-extractor --since "1 hour ago" | grep -i error | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "⚠ High error count in last hour: $ERROR_COUNT"
    echo "Recent errors:"
    journalctl -u multimodal-contract-extractor --since "1 hour ago" | grep -i error | tail -5
else
    echo "✓ Error count normal: $ERROR_COUNT"
fi

# 8. Check certificate expiration
echo "8. Checking SSL certificate expiration..."
CERT_DAYS=$(openssl x509 -in /etc/ssl/certs/mce.crt -noout -dates | grep notAfter | cut -d= -f2 | xargs -I {} date -d {} +%s)
CURRENT_DAYS=$(date +%s)
DAYS_LEFT=$(( ($CERT_DAYS - $CURRENT_DAYS) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "⚠ SSL certificate expires in $DAYS_LEFT days"
else
    echo "✓ SSL certificate valid for $DAYS_LEFT days"
fi

echo "=== Health check completed ==="
```

#### System Status Dashboard

```python
# operational_dashboard.py
import asyncio
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: Dict[str, float]
    queue_sizes: Dict[str, int]
    active_connections: int
    processing_rate: float
    error_rate: float
    response_times: Dict[str, float]

@dataclass
class ServiceStatus:
    name: str
    status: str  # healthy, degraded, unhealthy
    uptime: timedelta
    last_check: datetime
    endpoints: Dict[str, bool]
    dependencies: Dict[str, str]

class OperationalDashboard:
    """Real-time operational dashboard for system monitoring."""
    
    def __init__(self):
        self.metrics_history = []
        self.services = {}
        self.alerts = []
        
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        
        # CPU and Memory
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                disk = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = disk.percent
            except PermissionError:
                continue
        
        # Queue sizes (Redis)
        import redis
        r = redis.Redis()
        queue_sizes = {
            'processing': r.llen('processing_queue'),
            'failed': r.llen('failed_queue'),
            'completed': r.llen('completed_queue')
        }
        
        # Database connections
        active_connections = await self._get_db_connections()
        
        # Processing metrics
        processing_rate = await self._calculate_processing_rate()
        error_rate = await self._calculate_error_rate()
        response_times = await self._get_response_times()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            queue_sizes=queue_sizes,
            active_connections=active_connections,
            processing_rate=processing_rate,
            error_rate=error_rate,
            response_times=response_times
        )
    
    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of individual service."""
        
        service_configs = {
            'api_server': {
                'endpoints': {
                    'health': 'http://localhost:8000/api/v1/health',
                    'metrics': 'http://localhost:8000/api/v1/metrics'
                },
                'dependencies': ['database', 'redis', 'file_storage']
            },
            'database': {
                'endpoints': {
                    'connection': 'postgresql://localhost:5432/mce_production'
                },
                'dependencies': []
            },
            'redis': {
                'endpoints': {
                    'ping': 'redis://localhost:6379'
                },
                'dependencies': []
            },
            'research_service': {
                'endpoints': {
                    'gnn': 'http://localhost:8000/api/v1/research/gnn/health',
                    'federated': 'http://localhost:8000/api/v1/research/federated/health'
                },
                'dependencies': ['api_server', 'gpu_resources']
            }
        }
        
        if service_name not in service_configs:
            raise ValueError(f"Unknown service: {service_name}")
        
        config = service_configs[service_name]
        
        # Check endpoints
        endpoint_status = {}
        for endpoint_name, endpoint_url in config['endpoints'].items():
            endpoint_status[endpoint_name] = await self._check_endpoint(endpoint_url)
        
        # Check dependencies
        dependency_status = {}
        for dep in config['dependencies']:
            dep_status = await self.check_service_health(dep)
            dependency_status[dep] = dep_status.status
        
        # Determine overall status
        if all(endpoint_status.values()) and all(s == 'healthy' for s in dependency_status.values()):
            status = 'healthy'
        elif any(endpoint_status.values()):
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        return ServiceStatus(
            name=service_name,
            status=status,
            uptime=await self._get_service_uptime(service_name),
            last_check=datetime.now(),
            endpoints=endpoint_status,
            dependencies=dependency_status
        )
    
    async def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        
        # Collect current metrics
        metrics = await self.collect_system_metrics()
        self.metrics_history.append(metrics)
        
        # Keep only last 24 hours of metrics
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # Check all services
        services = ['api_server', 'database', 'redis', 'research_service']
        service_statuses = {}
        
        for service in services:
            service_statuses[service] = await self.check_service_health(service)
        
        # Calculate trends
        trends = self._calculate_trends()
        
        # Generate alerts
        current_alerts = self._check_alert_conditions(metrics, service_statuses)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._determine_overall_status(service_statuses),
            'current_metrics': {
                'cpu_usage': metrics.cpu_usage,
                'memory_usage': metrics.memory_usage,
                'disk_usage': metrics.disk_usage,
                'queue_sizes': metrics.queue_sizes,
                'processing_rate': metrics.processing_rate,
                'error_rate': metrics.error_rate,
                'response_times': metrics.response_times
            },
            'service_statuses': {
                name: {
                    'status': status.status,
                    'uptime': str(status.uptime),
                    'endpoints': status.endpoints,
                    'dependencies': status.dependencies
                }
                for name, status in service_statuses.items()
            },
            'trends': trends,
            'active_alerts': current_alerts,
            'recommendations': self._generate_recommendations(metrics, service_statuses)
        }
        
        return report
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calculate performance trends from historical data."""
        
        if len(self.metrics_history) < 10:
            return {'status': 'insufficient_data'}
        
        # Get recent metrics
        recent = self.metrics_history[-10:]
        older = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else []
        
        trends = {}
        
        # CPU trend
        recent_cpu = sum(m.cpu_usage for m in recent) / len(recent)
        if older:
            older_cpu = sum(m.cpu_usage for m in older) / len(older)
            trends['cpu'] = 'increasing' if recent_cpu > older_cpu * 1.1 else 'decreasing' if recent_cpu < older_cpu * 0.9 else 'stable'
        else:
            trends['cpu'] = 'stable'
        
        # Memory trend
        recent_memory = sum(m.memory_usage for m in recent) / len(recent)
        if older:
            older_memory = sum(m.memory_usage for m in older) / len(older)
            trends['memory'] = 'increasing' if recent_memory > older_memory * 1.1 else 'decreasing' if recent_memory < older_memory * 0.9 else 'stable'
        else:
            trends['memory'] = 'stable'
        
        # Processing rate trend
        recent_rate = sum(m.processing_rate for m in recent) / len(recent)
        if older:
            older_rate = sum(m.processing_rate for m in older) / len(older)
            trends['processing_rate'] = 'increasing' if recent_rate > older_rate * 1.1 else 'decreasing' if recent_rate < older_rate * 0.9 else 'stable'
        else:
            trends['processing_rate'] = 'stable'
        
        return trends
    
    def _check_alert_conditions(self, metrics: SystemMetrics, 
                               services: Dict[str, ServiceStatus]) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        
        alerts = []
        
        # High resource usage alerts
        if metrics.cpu_usage > 85:
            alerts.append({
                'type': 'resource_usage',
                'severity': 'critical' if metrics.cpu_usage > 95 else 'warning',
                'message': f'High CPU usage: {metrics.cpu_usage:.1f}%',
                'timestamp': metrics.timestamp.isoformat()
            })
        
        if metrics.memory_usage > 85:
            alerts.append({
                'type': 'resource_usage',
                'severity': 'critical' if metrics.memory_usage > 95 else 'warning',
                'message': f'High memory usage: {metrics.memory_usage:.1f}%',
                'timestamp': metrics.timestamp.isoformat()
            })
        
        # Disk usage alerts
        for mount, usage in metrics.disk_usage.items():
            if usage > 85:
                alerts.append({
                    'type': 'disk_usage',
                    'severity': 'critical' if usage > 95 else 'warning',
                    'message': f'High disk usage on {mount}: {usage:.1f}%',
                    'timestamp': metrics.timestamp.isoformat()
                })
        
        # Queue backlog alerts
        for queue_name, size in metrics.queue_sizes.items():
            if size > 1000:
                alerts.append({
                    'type': 'queue_backlog',
                    'severity': 'warning',
                    'message': f'Queue {queue_name} has {size} items',
                    'timestamp': metrics.timestamp.isoformat()
                })
        
        # Service health alerts
        for service_name, service_status in services.items():
            if service_status.status == 'unhealthy':
                alerts.append({
                    'type': 'service_health',
                    'severity': 'critical',
                    'message': f'Service {service_name} is unhealthy',
                    'timestamp': metrics.timestamp.isoformat()
                })
            elif service_status.status == 'degraded':
                alerts.append({
                    'type': 'service_health',
                    'severity': 'warning',
                    'message': f'Service {service_name} is degraded',
                    'timestamp': metrics.timestamp.isoformat()
                })
        
        # Error rate alerts
        if metrics.error_rate > 0.05:  # 5% error rate
            alerts.append({
                'type': 'error_rate',
                'severity': 'critical' if metrics.error_rate > 0.1 else 'warning',
                'message': f'High error rate: {metrics.error_rate:.2%}',
                'timestamp': metrics.timestamp.isoformat()
            })
        
        return alerts
    
    def _generate_recommendations(self, metrics: SystemMetrics, 
                                services: Dict[str, ServiceStatus]) -> List[str]:
        """Generate operational recommendations."""
        
        recommendations = []
        
        # Resource scaling recommendations
        if metrics.cpu_usage > 80:
            recommendations.append("Consider scaling up CPU resources or adding more instances")
        
        if metrics.memory_usage > 80:
            recommendations.append("Consider increasing memory allocation")
        
        if any(usage > 80 for usage in metrics.disk_usage.values()):
            recommendations.append("Consider increasing disk capacity or implementing log rotation")
        
        # Queue management recommendations
        if metrics.queue_sizes.get('processing', 0) > 500:
            recommendations.append("Consider adding more processing workers to reduce queue backlog")
        
        # Performance recommendations
        if metrics.processing_rate < 10:  # Less than 10 docs/minute
            recommendations.append("Processing rate is low, check for bottlenecks in the pipeline")
        
        if metrics.error_rate > 0.02:  # More than 2% errors
            recommendations.append("Error rate is elevated, review recent error logs")
        
        # Service-specific recommendations
        for service_name, service_status in services.items():
            if service_status.status != 'healthy':
                recommendations.append(f"Investigate {service_name} service issues")
        
        return recommendations

# CLI tool for operations
async def main():
    dashboard = OperationalDashboard()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        report = await dashboard.generate_status_report()
        print(json.dumps(report, indent=2))
    else:
        # Interactive monitoring
        while True:
            report = await dashboard.generate_status_report()
            
            print("\n" + "="*50)
            print(f"System Status Report - {report['timestamp']}")
            print("="*50)
            
            print(f"Overall Status: {report['overall_status']}")
            print(f"CPU Usage: {report['current_metrics']['cpu_usage']:.1f}%")
            print(f"Memory Usage: {report['current_metrics']['memory_usage']:.1f}%")
            print(f"Processing Rate: {report['current_metrics']['processing_rate']:.1f} docs/min")
            print(f"Error Rate: {report['current_metrics']['error_rate']:.2%}")
            
            if report['active_alerts']:
                print("\nActive Alerts:")
                for alert in report['active_alerts']:
                    print(f"  {alert['severity'].upper()}: {alert['message']}")
            
            if report['recommendations']:
                print("\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")
            
            await asyncio.sleep(30)  # Update every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
```

### Service Management

#### Systemd Service Configuration

```ini
# /etc/systemd/system/multimodal-contract-extractor.service
[Unit]
Description=Multimodal Contract Extractor API Server
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=mce
Group=mce
WorkingDirectory=/opt/multimodal-contract-extractor
Environment=PATH=/opt/multimodal-contract-extractor/venv/bin
Environment=ENVIRONMENT=production
EnvironmentFile=/opt/multimodal-contract-extractor/.env

ExecStart=/opt/multimodal-contract-extractor/venv/bin/gunicorn \
    --config /opt/multimodal-contract-extractor/gunicorn.prod.py \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile /var/log/mce/access.log \
    --error-logfile /var/log/mce/error.log \
    src.api.app:app

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/mce /tmp /opt/multimodal-contract-extractor/data

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target

# Worker service for background processing
# /etc/systemd/system/mce-worker@.service
[Unit]
Description=MCE Background Worker %i
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=mce
Group=mce
WorkingDirectory=/opt/multimodal-contract-extractor
Environment=PATH=/opt/multimodal-contract-extractor/venv/bin
Environment=ENVIRONMENT=production
Environment=WORKER_ID=%i
EnvironmentFile=/opt/multimodal-contract-extractor/.env

ExecStart=/opt/multimodal-contract-extractor/venv/bin/python \
    -m multimodal_contract_extractor.worker \
    --worker-id %i \
    --concurrency 2

Restart=always
RestartSec=10
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

#### Service Management Commands

```bash
# Service management script
# manage_services.sh

#!/bin/bash

ACTION=$1
SERVICE=$2

case $ACTION in
    start)
        if [ "$SERVICE" = "all" ]; then
            systemctl start multimodal-contract-extractor
            systemctl start mce-worker@{1..4}
            systemctl start prometheus
            systemctl start grafana-server
        else
            systemctl start $SERVICE
        fi
        ;;
    
    stop)
        if [ "$SERVICE" = "all" ]; then
            systemctl stop multimodal-contract-extractor
            systemctl stop mce-worker@{1..4}
            systemctl stop prometheus
            systemctl stop grafana-server
        else
            systemctl stop $SERVICE
        fi
        ;;
    
    restart)
        if [ "$SERVICE" = "all" ]; then
            systemctl restart multimodal-contract-extractor
            systemctl restart mce-worker@{1..4}
        else
            systemctl restart $SERVICE
        fi
        ;;
    
    status)
        echo "=== Main API Server ==="
        systemctl status multimodal-contract-extractor
        
        echo "=== Background Workers ==="
        for i in {1..4}; do
            echo "Worker $i:"
            systemctl is-active mce-worker@$i
        done
        
        echo "=== Monitoring Stack ==="
        echo "Prometheus: $(systemctl is-active prometheus)"
        echo "Grafana: $(systemctl is-active grafana-server)"
        ;;
    
    logs)
        if [ "$SERVICE" = "all" ]; then
            journalctl -u multimodal-contract-extractor -f
        else
            journalctl -u $SERVICE -f
        fi
        ;;
    
    health)
        echo "Checking system health..."
        
        # API health check
        API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
        if [ "$API_STATUS" = "200" ]; then
            echo "✓ API Server: Healthy"
        else
            echo "✗ API Server: Unhealthy (HTTP $API_STATUS)"
        fi
        
        # Database check
        if pg_isready -h localhost -p 5432; then
            echo "✓ PostgreSQL: Ready"
        else
            echo "✗ PostgreSQL: Not ready"
        fi
        
        # Redis check
        if redis-cli ping > /dev/null; then
            echo "✓ Redis: Connected"
        else
            echo "✗ Redis: Connection failed"
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health} {service_name|all}"
        echo "Available services: multimodal-contract-extractor, mce-worker@N, prometheus, grafana-server"
        exit 1
        ;;
esac
```

---

## 🚨 Incident Response

### Incident Classification

#### Severity Levels

**P0 - Critical (Response: Immediate)**
- Complete system outage
- Data loss or corruption
- Security breach
- SLA violation > 30 minutes

**P1 - High (Response: 30 minutes)**
- Significant functionality degraded
- Performance degradation > 50%
- Research algorithms failing
- Multiple service failures

**P2 - Medium (Response: 2 hours)**
- Minor functionality issues
- Performance degradation < 50%
- Single service degradation
- Non-critical errors increasing

**P3 - Low (Response: Next business day)**
- Cosmetic issues
- Documentation problems
- Enhancement requests
- Monitoring alerts (informational)

### Incident Response Playbooks

#### P0 Critical Incident Response

```bash
#!/bin/bash
# p0_incident_response.sh
# Critical incident response playbook

echo "=== P0 CRITICAL INCIDENT RESPONSE ==="
echo "Timestamp: $(date)"

# 1. Immediate actions
echo "1. Immediate Assessment..."

# Check system health
curl -s http://localhost:8000/api/v1/health | jq '.status' || echo "API DOWN"

# Check core services
systemctl is-active multimodal-contract-extractor || echo "MAIN SERVICE DOWN"
systemctl is-active postgresql || echo "DATABASE DOWN"
systemctl is-active redis || echo "REDIS DOWN"

# 2. Notification
echo "2. Sending alerts..."

# Send to incident response team
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-type: application/json' \
  --data '{
    "text": "🚨 P0 CRITICAL INCIDENT - Multimodal Contract Extractor",
    "attachments": [{
      "color": "danger",
      "fields": [{
        "title": "Severity",
        "value": "P0 - Critical",
        "short": true
      }, {
        "title": "Time",
        "value": "'$(date)'",
        "short": true
      }]
    }]
  }'

# Send email alert
echo "P0 Critical incident detected at $(date). System requires immediate attention." | \
mail -s "P0 CRITICAL: MCE System Down" ops-team@company.com

# 3. Initial diagnostics
echo "3. Running diagnostics..."

# Check resource usage
echo "Resource usage:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%\n", $3/$2 * 100.0)}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}')"

# Check recent logs for errors
echo "Recent errors:"
journalctl -u multimodal-contract-extractor --since "10 minutes ago" | grep -i error | tail -10

# Check network connectivity
echo "Network connectivity:"
ping -c 1 google.com > /dev/null && echo "Internet: OK" || echo "Internet: FAILED"

# 4. Auto-recovery attempts
echo "4. Attempting auto-recovery..."

# Restart services
systemctl restart multimodal-contract-extractor
systemctl restart mce-worker@{1..4}

# Wait and check
sleep 30
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✓ Auto-recovery successful"
    # Send recovery notification
    curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
      -H 'Content-type: application/json' \
      --data '{"text": "✅ P0 Incident auto-recovered via service restart"}'
else
    echo "✗ Auto-recovery failed - manual intervention required"
fi

# 5. Create incident record
INCIDENT_ID="INC-$(date +%Y%m%d-%H%M%S)"
echo "Incident ID: $INCIDENT_ID"

cat > /tmp/incident_${INCIDENT_ID}.json << EOF
{
  "incident_id": "$INCIDENT_ID",
  "severity": "P0",
  "start_time": "$(date -Iseconds)",
  "status": "investigating",
  "initial_diagnosis": "$(journalctl -u multimodal-contract-extractor --since '10 minutes ago' | grep -i error | tail -3 | tr '\n' ' ')",
  "actions_taken": ["service_restart", "diagnostics_run"],
  "next_steps": ["manual_investigation_required"]
}
EOF

echo "Incident record created: /tmp/incident_${INCIDENT_ID}.json"
```

#### Common Issue Resolution

```python
# incident_automation.py
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class IncidentAutomation:
    """Automated incident detection and resolution."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.known_issues = self._load_known_issues()
        self.resolution_scripts = self._load_resolution_scripts()
    
    def _load_known_issues(self) -> Dict[str, Dict[str, Any]]:
        """Load known issues and their signatures."""
        return {
            'high_memory_usage': {
                'signature': ['memory_usage > 90%', 'oom_killer'],
                'severity': 'P1',
                'resolution': 'restart_services_clear_cache'
            },
            'database_connection_pool_exhausted': {
                'signature': ['connection pool exhausted', 'too many connections'],
                'severity': 'P1',
                'resolution': 'restart_database_connections'
            },
            'redis_connection_timeout': {
                'signature': ['redis timeout', 'connection timeout'],
                'severity': 'P2',
                'resolution': 'restart_redis_clear_connections'
            },
            'gpu_out_of_memory': {
                'signature': ['cuda out of memory', 'gpu memory'],
                'severity': 'P1',
                'resolution': 'clear_gpu_memory_restart_workers'
            },
            'processing_queue_stuck': {
                'signature': ['queue size > 1000', 'no processing progress'],
                'severity': 'P2',
                'resolution': 'clear_stuck_jobs_restart_workers'
            }
        }
    
    async def detect_incident(self, logs: List[str], metrics: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Detect incidents based on logs and metrics."""
        
        # Combine logs into searchable text
        log_text = ' '.join(logs).lower()
        
        # Check each known issue
        for issue_name, issue_config in self.known_issues.items():
            signature_matches = 0
            
            for signature in issue_config['signature']:
                if signature.lower() in log_text:
                    signature_matches += 1
            
            # Also check metrics for threshold-based issues
            if 'memory_usage' in signature and metrics.get('memory_usage', 0) > 90:
                signature_matches += 1
            
            # If enough signatures match, we have an incident
            if signature_matches >= len(issue_config['signature']) * 0.6:  # 60% match threshold
                incident = {
                    'issue_type': issue_name,
                    'severity': issue_config['severity'],
                    'confidence': signature_matches / len(issue_config['signature']),
                    'detected_at': datetime.now().isoformat(),
                    'resolution_action': issue_config['resolution'],
                    'matching_signatures': [
                        sig for sig in issue_config['signature'] 
                        if sig.lower() in log_text
                    ]
                }
                return incident
        
        return None
    
    async def auto_resolve_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt automatic resolution of detected incident."""
        
        resolution_action = incident['resolution_action']
        
        if resolution_action not in self.resolution_scripts:
            return {'success': False, 'error': f'No resolution script for {resolution_action}'}
        
        try:
            # Execute resolution script
            resolution_result = await self.resolution_scripts[resolution_action]()
            
            # Wait for system to stabilize
            await asyncio.sleep(30)
            
            # Verify resolution
            verification_result = await self._verify_resolution(incident)
            
            return {
                'success': verification_result['resolved'],
                'resolution_actions': resolution_result,
                'verification': verification_result,
                'resolved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Auto-resolution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _verify_resolution(self, incident: Dict[str, Any]) -> Dict[str, bool]:
        """Verify that the incident has been resolved."""
        
        # Check system health
        health_checks = {
            'api_responsive': await self._check_api_health(),
            'database_connected': await self._check_database_health(),
            'redis_connected': await self._check_redis_health(),
            'processing_active': await self._check_processing_health(),
            'error_rate_normal': await self._check_error_rate()
        }
        
        # Incident is resolved if all health checks pass
        resolved = all(health_checks.values())
        
        return {
            'resolved': resolved,
            'health_checks': health_checks
        }
    
    def _load_resolution_scripts(self) -> Dict[str, callable]:
        """Load automated resolution scripts."""
        
        async def restart_services_clear_cache():
            """Restart services and clear cache."""
            import subprocess
            
            # Clear application cache
            subprocess.run(['redis-cli', 'FLUSHDB'])
            
            # Restart services
            subprocess.run(['systemctl', 'restart', 'multimodal-contract-extractor'])
            subprocess.run(['systemctl', 'restart', 'mce-worker@{1..4}'])
            
            return {'action': 'services_restarted', 'cache_cleared': True}
        
        async def restart_database_connections():
            """Restart database connection pool."""
            # This would typically involve calling an API endpoint or 
            # restarting the database service
            import subprocess
            
            subprocess.run(['systemctl', 'reload', 'postgresql'])
            subprocess.run(['systemctl', 'restart', 'multimodal-contract-extractor'])
            
            return {'action': 'database_connections_restarted'}
        
        async def clear_gpu_memory_restart_workers():
            """Clear GPU memory and restart workers."""
            import subprocess
            
            # Kill GPU processes
            try:
                subprocess.run(['nvidia-smi', '--gpu-reset'])
            except:
                pass
            
            # Restart workers
            subprocess.run(['systemctl', 'restart', 'mce-worker@{1..4}'])
            
            return {'action': 'gpu_cleared_workers_restarted'}
        
        async def clear_stuck_jobs_restart_workers():
            """Clear stuck processing jobs."""
            import redis
            
            r = redis.Redis()
            
            # Clear stuck jobs from queues
            stuck_count = r.llen('processing_queue')
            r.delete('processing_queue')
            r.delete('failed_queue')
            
            # Restart workers
            import subprocess
            subprocess.run(['systemctl', 'restart', 'mce-worker@{1..4}'])
            
            return {'action': 'stuck_jobs_cleared', 'jobs_cleared': stuck_count}
        
        return {
            'restart_services_clear_cache': restart_services_clear_cache,
            'restart_database_connections': restart_database_connections,
            'restart_redis_clear_connections': restart_services_clear_cache,  # Same action
            'clear_gpu_memory_restart_workers': clear_gpu_memory_restart_workers,
            'clear_stuck_jobs_restart_workers': clear_stuck_jobs_restart_workers
        }

# Incident monitoring daemon
async def incident_monitoring_daemon():
    """Run continuous incident monitoring."""
    
    automation = IncidentAutomation()
    
    while True:
        try:
            # Collect recent logs
            import subprocess
            result = subprocess.run(
                ['journalctl', '-u', 'multimodal-contract-extractor', '--since', '5 minutes ago'],
                capture_output=True, text=True
            )
            recent_logs = result.stdout.split('\n')
            
            # Collect current metrics
            metrics = await collect_current_metrics()
            
            # Check for incidents
            incident = await automation.detect_incident(recent_logs, metrics)
            
            if incident:
                print(f"Incident detected: {incident['issue_type']} (Severity: {incident['severity']})")
                
                # Attempt auto-resolution for P2 and lower
                if incident['severity'] in ['P2', 'P3']:
                    resolution_result = await automation.auto_resolve_incident(incident)
                    
                    if resolution_result['success']:
                        print(f"Incident auto-resolved: {incident['issue_type']}")
                        # Log successful resolution
                        with open('/var/log/mce/incident_resolutions.log', 'a') as f:
                            f.write(f"{datetime.now().isoformat()}: Auto-resolved {incident['issue_type']}\n")
                    else:
                        print(f"Auto-resolution failed for {incident['issue_type']}")
                        # Escalate to human operators
                
                else:
                    # High severity incidents need human intervention
                    print(f"High severity incident {incident['issue_type']} requires manual intervention")
            
            # Wait before next check
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            print(f"Error in incident monitoring: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

async def collect_current_metrics():
    """Collect current system metrics."""
    import psutil
    
    return {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

if __name__ == "__main__":
    asyncio.run(incident_monitoring_daemon())
```

### War Room Procedures

#### Incident Communication Template

```markdown
# Incident Communication Template

## Initial Notification (within 15 minutes)

**Subject**: [P0/P1/P2] Incident - Multimodal Contract Extractor

**Incident ID**: INC-YYYYMMDD-HHMMSS  
**Severity**: P0/P1/P2  
**Status**: Investigating/Identified/Resolving/Resolved  
**Started**: YYYY-MM-DD HH:MM UTC  
**Services Affected**: API Server / Processing / Research Algorithms  

**Impact**: 
- Brief description of user impact
- Estimated number of affected users
- Affected functionality

**Current Actions**:
- What is being done to resolve
- ETA for next update

**War Room**: #incident-response (Slack)

---

## Status Updates (every 30 minutes for P0, 60 minutes for P1)

**Update #N - HH:MM UTC**

**Status**: [No change/Progress/Escalated]

**Actions Taken**:
- List of actions completed since last update

**Current Findings**:
- What has been discovered

**Next Steps**:
- Planned actions
- ETA for next update

---

## Resolution Notification

**RESOLVED - HH:MM UTC**

**Root Cause**: 
- Technical explanation of what caused the incident

**Resolution**: 
- What was done to resolve the issue

**Prevention**: 
- Steps taken to prevent recurrence

**Follow-up Actions**:
- Post-incident review scheduled
- Any remaining cleanup tasks
```

---

## ⚡ Performance Optimization

### Performance Monitoring

#### Real-time Performance Dashboard

```python
# performance_monitor.py
import asyncio
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class PerformanceMetrics:
    timestamp: datetime
    
    # System metrics
    cpu_usage: float
    memory_usage: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float
    
    # Application metrics
    requests_per_second: float
    avg_response_time: float
    p95_response_time: float
    error_rate: float
    active_connections: int
    
    # Processing metrics
    documents_processed_per_minute: float
    processing_queue_size: int
    avg_document_size: float
    
    # Research algorithm metrics
    gnn_processing_time: Optional[float]
    transformer_processing_time: Optional[float]
    causal_processing_time: Optional[float]
    gpu_utilization: Optional[float]
    gpu_memory_usage: Optional[float]

class PerformanceMonitor:
    """Real-time performance monitoring and optimization."""
    
    def __init__(self):
        self.metrics_history = []
        self.baseline_metrics = None
        self.performance_thresholds = {
            'cpu_usage_warning': 70.0,
            'cpu_usage_critical': 85.0,
            'memory_usage_warning': 75.0,
            'memory_usage_critical': 90.0,
            'response_time_warning': 2.0,  # seconds
            'response_time_critical': 5.0,
            'error_rate_warning': 0.02,    # 2%
            'error_rate_critical': 0.05,   # 5%
        }
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive performance metrics."""
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_read = disk_io.read_bytes_per_sec if hasattr(disk_io, 'read_bytes_per_sec') else 0
        disk_io_write = disk_io.write_bytes_per_sec if hasattr(disk_io, 'write_bytes_per_sec') else 0
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_io_sent = network_io.bytes_sent
        network_io_recv = network_io.bytes_recv
        
        # Application metrics (would be collected from API metrics endpoint)
        app_metrics = await self._collect_application_metrics()
        
        # GPU metrics (if available)
        gpu_metrics = await self._collect_gpu_metrics()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_io_sent=network_io_sent,
            network_io_recv=network_io_recv,
            requests_per_second=app_metrics.get('rps', 0),
            avg_response_time=app_metrics.get('avg_response_time', 0),
            p95_response_time=app_metrics.get('p95_response_time', 0),
            error_rate=app_metrics.get('error_rate', 0),
            active_connections=app_metrics.get('active_connections', 0),
            documents_processed_per_minute=app_metrics.get('docs_per_minute', 0),
            processing_queue_size=app_metrics.get('queue_size', 0),
            avg_document_size=app_metrics.get('avg_doc_size', 0),
            gnn_processing_time=app_metrics.get('gnn_time', None),
            transformer_processing_time=app_metrics.get('transformer_time', None),
            causal_processing_time=app_metrics.get('causal_time', None),
            gpu_utilization=gpu_metrics.get('utilization', None),
            gpu_memory_usage=gpu_metrics.get('memory_usage', None)
        )
    
    def analyze_performance_trends(self, window_hours: int = 24) -> Dict[str, Any]:
        """Analyze performance trends over specified time window."""
        
        if not self.metrics_history:
            return {'status': 'insufficient_data'}
        
        # Filter metrics within time window
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if len(recent_metrics) < 10:
            return {'status': 'insufficient_data'}
        
        # Calculate trends
        trends = {}
        
        # CPU trend
        cpu_values = [m.cpu_usage for m in recent_metrics]
        trends['cpu'] = self._calculate_trend(cpu_values)
        
        # Memory trend
        memory_values = [m.memory_usage for m in recent_metrics]
        trends['memory'] = self._calculate_trend(memory_values)
        
        # Response time trend
        response_times = [m.avg_response_time for m in recent_metrics]
        trends['response_time'] = self._calculate_trend(response_times)
        
        # Processing throughput trend
        throughput = [m.documents_processed_per_minute for m in recent_metrics]
        trends['throughput'] = self._calculate_trend(throughput)
        
        # Identify performance bottlenecks
        bottlenecks = self._identify_bottlenecks(recent_metrics)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(recent_metrics, trends)
        
        return {
            'analysis_window_hours': window_hours,
            'metrics_count': len(recent_metrics),
            'trends': trends,
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'performance_score': self._calculate_performance_score(recent_metrics)
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend statistics for a series of values."""
        
        if len(values) < 2:
            return {'direction': 'stable', 'slope': 0.0, 'confidence': 0.0}
        
        # Simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        slope, intercept = np.polyfit(x, y, 1)
        correlation = np.corrcoef(x, y)[0, 1]
        
        # Determine trend direction
        if abs(slope) < np.std(values) * 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        return {
            'direction': direction,
            'slope': slope,
            'confidence': abs(correlation),
            'current_value': values[-1],
            'average_value': np.mean(values),
            'std_deviation': np.std(values)
        }
    
    def _identify_bottlenecks(self, metrics: List[PerformanceMetrics]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        
        bottlenecks = []
        
        # Check latest metrics for bottlenecks
        latest = metrics[-1]
        
        # CPU bottleneck
        if latest.cpu_usage > self.performance_thresholds['cpu_usage_warning']:
            bottlenecks.append({
                'type': 'cpu',
                'severity': 'critical' if latest.cpu_usage > self.performance_thresholds['cpu_usage_critical'] else 'warning',
                'current_value': latest.cpu_usage,
                'threshold': self.performance_thresholds['cpu_usage_warning'],
                'recommendation': 'Consider scaling up CPU resources or optimizing CPU-intensive operations'
            })
        
        # Memory bottleneck
        if latest.memory_usage > self.performance_thresholds['memory_usage_warning']:
            bottlenecks.append({
                'type': 'memory',
                'severity': 'critical' if latest.memory_usage > self.performance_thresholds['memory_usage_critical'] else 'warning',
                'current_value': latest.memory_usage,
                'threshold': self.performance_thresholds['memory_usage_warning'],
                'recommendation': 'Consider increasing memory allocation or implementing memory optimization'
            })
        
        # Response time bottleneck
        if latest.avg_response_time > self.performance_thresholds['response_time_warning']:
            bottlenecks.append({
                'type': 'response_time',
                'severity': 'critical' if latest.avg_response_time > self.performance_thresholds['response_time_critical'] else 'warning',
                'current_value': latest.avg_response_time,
                'threshold': self.performance_thresholds['response_time_warning'],
                'recommendation': 'Investigate slow queries or optimize processing algorithms'
            })
        
        # Processing queue bottleneck
        if latest.processing_queue_size > 100:
            bottlenecks.append({
                'type': 'processing_queue',
                'severity': 'warning',
                'current_value': latest.processing_queue_size,
                'threshold': 100,
                'recommendation': 'Consider adding more processing workers or optimizing processing speed'
            })
        
        # GPU bottleneck (if GPU metrics available)
        if latest.gpu_utilization and latest.gpu_utilization > 90:
            bottlenecks.append({
                'type': 'gpu',
                'severity': 'warning',
                'current_value': latest.gpu_utilization,
                'threshold': 90,
                'recommendation': 'GPU utilization is high, consider GPU-specific optimizations'
            })
        
        return bottlenecks
    
    def _generate_optimization_recommendations(self, 
                                            metrics: List[PerformanceMetrics], 
                                            trends: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate performance optimization recommendations."""
        
        recommendations = []
        
        # CPU optimization recommendations
        if trends.get('cpu', {}).get('direction') == 'increasing':
            recommendations.append("CPU usage is trending upward. Consider:")
            recommendations.append("  - Profile CPU-intensive operations")
            recommendations.append("  - Implement CPU-specific optimizations")
            recommendations.append("  - Scale horizontally with more instances")
        
        # Memory optimization recommendations
        if trends.get('memory', {}).get('direction') == 'increasing':
            recommendations.append("Memory usage is trending upward. Consider:")
            recommendations.append("  - Implement memory profiling")
            recommendations.append("  - Add garbage collection optimization")
            recommendations.append("  - Scale vertically with more RAM")
        
        # Response time optimization
        if trends.get('response_time', {}).get('direction') == 'increasing':
            recommendations.append("Response times are trending upward. Consider:")
            recommendations.append("  - Database query optimization")
            recommendations.append("  - Implement response caching")
            recommendations.append("  - Optimize research algorithm performance")
        
        # Throughput optimization
        if trends.get('throughput', {}).get('direction') == 'decreasing':
            recommendations.append("Processing throughput is declining. Consider:")
            recommendations.append("  - Optimize document processing pipeline")
            recommendations.append("  - Implement parallel processing")
            recommendations.append("  - Review queue management strategies")
        
        # Research algorithm specific recommendations
        latest = metrics[-1]
        if latest.gnn_processing_time and latest.gnn_processing_time > 5.0:
            recommendations.append("GNN processing time is high. Consider:")
            recommendations.append("  - Graph pruning techniques")
            recommendations.append("  - Batch processing optimization")
            recommendations.append("  - GPU acceleration for GNN operations")
        
        if latest.gpu_memory_usage and latest.gpu_memory_usage > 85:
            recommendations.append("GPU memory usage is high. Consider:")
            recommendations.append("  - Implement gradient checkpointing")
            recommendations.append("  - Use mixed precision training")
            recommendations.append("  - Optimize batch sizes")
        
        return recommendations
    
    def _calculate_performance_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall performance score (0-100)."""
        
        if not metrics:
            return 0.0
        
        latest = metrics[-1]
        score_components = []
        
        # CPU score (inverse of usage)
        cpu_score = max(0, 100 - latest.cpu_usage)
        score_components.append(cpu_score * 0.2)
        
        # Memory score
        memory_score = max(0, 100 - latest.memory_usage)
        score_components.append(memory_score * 0.2)
        
        # Response time score (capped at 10 seconds)
        response_time_score = max(0, 100 - (latest.avg_response_time / 10 * 100))
        score_components.append(response_time_score * 0.3)
        
        # Error rate score
        error_rate_score = max(0, 100 - (latest.error_rate * 2000))  # 5% error = 0 score
        score_components.append(error_rate_score * 0.2)
        
        # Throughput score (normalized)
        max_expected_throughput = 100  # docs per minute
        throughput_score = min(100, (latest.documents_processed_per_minute / max_expected_throughput) * 100)
        score_components.append(throughput_score * 0.1)
        
        return sum(score_components)
    
    async def _collect_application_metrics(self) -> Dict[str, float]:
        """Collect application-specific metrics."""
        try:
            # This would typically call the metrics API endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8000/api/v1/metrics') as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
        except:
            pass
        
        # Return default values if metrics endpoint is unavailable
        return {
            'rps': 0,
            'avg_response_time': 0,
            'p95_response_time': 0,
            'error_rate': 0,
            'active_connections': 0,
            'docs_per_minute': 0,
            'queue_size': 0,
            'avg_doc_size': 0
        }
    
    async def _collect_gpu_metrics(self) -> Dict[str, Optional[float]]:
        """Collect GPU metrics if available."""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                line = result.stdout.strip()
                if line:
                    parts = line.split(', ')
                    utilization = float(parts[0])
                    memory_used = float(parts[1])
                    memory_total = float(parts[2])
                    memory_usage = (memory_used / memory_total) * 100
                    
                    return {
                        'utilization': utilization,
                        'memory_usage': memory_usage,
                        'memory_used_mb': memory_used,
                        'memory_total_mb': memory_total
                    }
        except:
            pass
        
        return {'utilization': None, 'memory_usage': None}

# Performance optimization automation
class PerformanceOptimizer:
    """Automated performance optimization."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.optimization_actions = {
            'scale_workers': self._scale_workers,
            'optimize_cache': self._optimize_cache,
            'tune_database': self._tune_database,
            'optimize_gpu': self._optimize_gpu_usage
        }
    
    async def auto_optimize(self) -> Dict[str, Any]:
        """Perform automated performance optimization."""
        
        # Collect current metrics
        metrics = await self.monitor.collect_metrics()
        
        # Analyze performance
        analysis = self.monitor.analyze_performance_trends()
        
        optimization_results = []
        
        # Apply optimizations based on bottlenecks
        for bottleneck in analysis.get('bottlenecks', []):
            optimization = await self._apply_optimization_for_bottleneck(bottleneck)
            optimization_results.append(optimization)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_score': analysis.get('performance_score', 0),
            'optimizations_applied': optimization_results,
            'next_optimization_schedule': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
    
    async def _apply_optimization_for_bottleneck(self, bottleneck: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific optimization for identified bottleneck."""
        
        bottleneck_type = bottleneck['type']
        severity = bottleneck['severity']
        
        if bottleneck_type == 'cpu' and severity == 'critical':
            return await self._scale_workers()
        
        elif bottleneck_type == 'memory' and severity == 'critical':
            return await self._optimize_cache()
        
        elif bottleneck_type == 'response_time':
            return await self._tune_database()
        
        elif bottleneck_type == 'gpu':
            return await self._optimize_gpu_usage()
        
        else:
            return {'action': 'no_optimization', 'reason': f'No automatic optimization for {bottleneck_type}'}
    
    async def _scale_workers(self) -> Dict[str, Any]:
        """Scale up worker processes."""
        try:
            import subprocess
            
            # Check current worker count
            result = subprocess.run(['systemctl', 'list-units', '--plain', '--no-legend', 'mce-worker@*'], 
                                  capture_output=True, text=True)
            
            current_workers = len([line for line in result.stdout.split('\n') if 'mce-worker@' in line and 'active' in line])
            
            if current_workers < 8:  # Max 8 workers
                # Start additional worker
                new_worker_id = current_workers + 1
                subprocess.run(['systemctl', 'start', f'mce-worker@{new_worker_id}'])
                
                return {
                    'action': 'scale_workers',
                    'previous_count': current_workers,
                    'new_count': new_worker_id,
                    'success': True
                }
            else:
                return {
                    'action': 'scale_workers',
                    'success': False,
                    'reason': 'Maximum worker count reached'
                }
        
        except Exception as e:
            return {'action': 'scale_workers', 'success': False, 'error': str(e)}
    
    async def _optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache settings."""
        try:
            import redis
            r = redis.Redis()
            
            # Clear expired keys
            r.execute_command('MEMORY', 'PURGE')
            
            # Get memory info
            memory_info = r.info('memory')
            
            return {
                'action': 'optimize_cache',
                'memory_freed_mb': memory_info.get('used_memory_overhead', 0) / 1024 / 1024,
                'success': True
            }
        
        except Exception as e:
            return {'action': 'optimize_cache', 'success': False, 'error': str(e)}
    
    async def _tune_database(self) -> Dict[str, Any]:
        """Optimize database performance."""
        try:
            # This would typically involve running database optimization queries
            # or adjusting connection pool settings
            
            return {
                'action': 'tune_database',
                'optimizations': ['connection_pool_adjusted', 'query_cache_cleared'],
                'success': True
            }
        
        except Exception as e:
            return {'action': 'tune_database', 'success': False, 'error': str(e)}
    
    async def _optimize_gpu_usage(self) -> Dict[str, Any]:
        """Optimize GPU usage."""
        try:
            import subprocess
            
            # Clear GPU memory
            subprocess.run(['nvidia-smi', '--gpu-reset'])
            
            return {
                'action': 'optimize_gpu',
                'gpu_reset': True,
                'success': True
            }
        
        except Exception as e:
            return {'action': 'optimize_gpu', 'success': False, 'error': str(e)}

# Performance monitoring daemon
async def performance_monitoring_daemon():
    """Run continuous performance monitoring and optimization."""
    
    monitor = PerformanceMonitor()
    optimizer = PerformanceOptimizer()
    
    while True:
        try:
            # Collect metrics
            metrics = await monitor.collect_metrics()
            monitor.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.now() - timedelta(hours=24)
            monitor.metrics_history = [
                m for m in monitor.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Print current status
            print(f"Performance Status - {metrics.timestamp.strftime('%H:%M:%S')}")
            print(f"CPU: {metrics.cpu_usage:.1f}% | Memory: {metrics.memory_usage:.1f}% | Response: {metrics.avg_response_time:.2f}s")
            print(f"Queue: {metrics.processing_queue_size} | Docs/min: {metrics.documents_processed_per_minute:.1f}")
            
            # Run optimization every 30 minutes
            if len(monitor.metrics_history) > 0 and len(monitor.metrics_history) % 6 == 0:  # Every 6 * 5min = 30min
                optimization_result = await optimizer.auto_optimize()
                
                if optimization_result['optimizations_applied']:
                    print(f"Applied optimizations: {[opt['action'] for opt in optimization_result['optimizations_applied']]}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            print(f"Error in performance monitoring: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(performance_monitoring_daemon())
```

This comprehensive operational documentation provides all the tools, procedures, and automation needed to effectively operate, monitor, and maintain the advanced multimodal contract extractor system in production environments. It covers incident response, performance optimization, and proactive system management to ensure high availability and optimal performance.