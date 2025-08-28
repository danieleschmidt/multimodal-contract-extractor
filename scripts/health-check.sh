#!/bin/bash
# Health check script for Progressive Quality Gates Autonomous SDLC
# Comprehensive health validation for production deployment

set -euo pipefail

# Configuration
HEALTH_ENDPOINT="http://localhost:8081/health"
READY_ENDPOINT="http://localhost:8081/ready"
METRICS_ENDPOINT="http://localhost:8080/metrics"
TIMEOUT=10
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check HTTP endpoint
check_endpoint() {
    local endpoint=$1
    local name=$2
    local expected_status=${3:-200}
    
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
                   --max-time $TIMEOUT \
                   --connect-timeout 5 \
                   "$endpoint" 2>/dev/null || echo "HTTPSTATUS:000")
    
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [[ "$status_code" == "$expected_status" ]]; then
        log "✅ ${name}: OK (${status_code})"
        return 0
    else
        log "❌ ${name}: FAILED (${status_code})"
        return 1
    fi
}

# Check process health
check_process_health() {
    log "🔍 Checking process health..."
    
    # Check if Python process is running
    if pgrep -f "python.*autonomous" > /dev/null; then
        log "✅ Python process: RUNNING"
    else
        log "❌ Python process: NOT RUNNING"
        return 1
    fi
    
    # Check memory usage
    local memory_usage
    memory_usage=$(ps -o pid,ppid,cmd,%mem --sort=-%mem | head -n 5)
    log "📊 Memory usage (top 5 processes):"
    echo "$memory_usage"
    
    # Check if memory usage is too high (> 90%)
    local mem_percent
    mem_percent=$(free | grep '^Mem:' | awk '{printf "%.0f", ($3/$2) * 100.0}')
    
    if [[ $mem_percent -gt 90 ]]; then
        log "⚠️  High memory usage: ${mem_percent}%"
        return 1
    else
        log "✅ Memory usage: ${mem_percent}% (OK)"
    fi
    
    return 0
}

# Check file system health
check_filesystem_health() {
    log "🔍 Checking filesystem health..."
    
    # Check disk space
    local disk_usage
    disk_usage=$(df -h /app /tmp 2>/dev/null | grep -v "Filesystem" || true)
    
    if [[ -n "$disk_usage" ]]; then
        log "💾 Disk usage:"
        echo "$disk_usage"
        
        # Check if any partition is > 95% full
        local high_usage
        high_usage=$(echo "$disk_usage" | awk '$5 ~ /^[0-9]+%$/ && int($5) > 95')
        
        if [[ -n "$high_usage" ]]; then
            log "❌ High disk usage detected"
            return 1
        fi
    fi
    
    # Check if required directories exist and are writable
    local dirs=("/app/logs" "/app/reports" "/app/temp")
    
    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" && -w "$dir" ]]; then
            log "✅ Directory ${dir}: OK"
        else
            log "❌ Directory ${dir}: FAILED"
            return 1
        fi
    done
    
    return 0
}

# Check application health
check_application_health() {
    log "🔍 Checking application health..."
    
    local retry_count=0
    local success=false
    
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        if check_endpoint "$HEALTH_ENDPOINT" "Health endpoint"; then
            success=true
            break
        fi
        
        retry_count=$((retry_count + 1))
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            log "⏳ Retrying health check in 2 seconds... (${retry_count}/${MAX_RETRIES})"
            sleep 2
        fi
    done
    
    if [[ "$success" != "true" ]]; then
        log "❌ Health check failed after ${MAX_RETRIES} retries"
        return 1
    fi
    
    return 0
}

# Check readiness
check_readiness() {
    log "🔍 Checking application readiness..."
    
    if check_endpoint "$READY_ENDPOINT" "Readiness endpoint"; then
        return 0
    else
        log "❌ Application not ready"
        return 1
    fi
}

# Check metrics endpoint
check_metrics() {
    log "🔍 Checking metrics endpoint..."
    
    local response
    response=$(curl -s --max-time $TIMEOUT "$METRICS_ENDPOINT" 2>/dev/null || echo "")
    
    if [[ -n "$response" ]] && echo "$response" | grep -q "quality_gates"; then
        log "✅ Metrics endpoint: OK"
        return 0
    else
        log "⚠️  Metrics endpoint: LIMITED (non-critical)"
        return 0  # Non-critical failure
    fi
}

# Check quality gates status
check_quality_gates_status() {
    log "🔍 Checking quality gates status..."
    
    # Check if quality gates reports exist and are recent
    local reports_dir="/app/reports"
    local recent_report
    
    if [[ -d "$reports_dir" ]]; then
        recent_report=$(find "$reports_dir" -name "*quality_report.json" -mmin -60 2>/dev/null | head -1)
        
        if [[ -n "$recent_report" ]]; then
            log "✅ Recent quality gates report found: $(basename "$recent_report")"
        else
            log "⚠️  No recent quality gates reports (non-critical)"
        fi
    else
        log "⚠️  Reports directory not found (non-critical)"
    fi
    
    return 0
}

# Main health check function
main() {
    local exit_code=0
    local start_time
    start_time=$(date +%s)
    
    log "🚀 Starting Progressive Quality Gates Health Check"
    log "================================================"
    
    # Run all health checks
    if ! check_process_health; then
        exit_code=1
    fi
    
    if ! check_filesystem_health; then
        exit_code=1
    fi
    
    if ! check_application_health; then
        exit_code=1
    fi
    
    if ! check_readiness; then
        exit_code=1
    fi
    
    # Non-critical checks
    check_metrics || true
    check_quality_gates_status || true
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "================================================"
    
    if [[ $exit_code -eq 0 ]]; then
        log "🎉 Health check PASSED (${duration}s)"
        echo -e "${GREEN}✅ HEALTHY${NC}"
    else
        log "💥 Health check FAILED (${duration}s)"
        echo -e "${RED}❌ UNHEALTHY${NC}"
    fi
    
    exit $exit_code
}

# Handle signals
trap 'log "🛑 Health check interrupted"; exit 1' INT TERM

# Run main function
main "$@"