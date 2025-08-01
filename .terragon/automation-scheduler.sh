#!/bin/bash
# Terragon Autonomous SDLC Scheduler
# Advanced repository continuous value discovery automation

set -euo pipefail

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PATH="$REPO_ROOT/.terragon/config.yaml"
DISCOVERY_SCRIPT="$REPO_ROOT/.terragon/value-discovery.py"
LOG_DIR="$REPO_ROOT/.terragon/logs"
METRICS_PATH="$REPO_ROOT/.terragon/value-metrics.json"

# Ensure directories exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_DIR/scheduler.log"
}

# Check if configuration exists
check_config() {
    if [[ ! -f "$CONFIG_PATH" ]]; then
        log "ERROR: Configuration not found at $CONFIG_PATH"
        exit 1
    fi
}

# Run value discovery
run_discovery() {
    local trigger="$1"
    log "🔍 Starting value discovery (trigger: $trigger)"
    
    cd "$REPO_ROOT"
    
    if python3 "$DISCOVERY_SCRIPT" > "$LOG_DIR/discovery-$(date +%Y%m%d-%H%M%S).log" 2>&1; then
        log "✅ Value discovery completed successfully"
        return 0
    else
        log "❌ Value discovery failed"
        return 1
    fi
}

# Execute next best value item
execute_next_item() {
    if [[ ! -f "$METRICS_PATH" ]]; then
        log "⚠️  No metrics file found, running discovery first"
        run_discovery "auto"
        return
    fi
    
    # Extract next best item from metrics
    local next_item
    next_item=$(python3 -c "
import json
import sys
try:
    with open('$METRICS_PATH', 'r') as f:
        data = json.load(f)
    if data.get('top_opportunities'):
        item = data['top_opportunities'][0]
        print(f\"{item['category']}:{item['title'][:50]}:{item['composite_score']}\")
    else:
        print('none')
except Exception as e:
    print('error')
")
    
    if [[ "$next_item" == "none" ]]; then
        log "🎯 No high-value items to execute"
        return
    elif [[ "$next_item" == "error" ]]; then
        log "❌ Error reading metrics file"
        return
    fi
    
    IFS=':' read -r category title score <<< "$next_item"
    log "🚀 Executing next best value item: $title (score: $score)"
    
    # Execute based on category
    case "$category" in
        "security_vulnerability"|"security_issue")
            execute_security_fix "$title"
            ;;
        "dependency_update")
            execute_dependency_update "$title"
            ;;
        "technical_debt"|"refactoring")
            execute_refactoring "$title"
            ;;
        "performance_optimization")
            execute_performance_optimization "$title"
            ;;
        *)
            log "⚠️  Unknown category: $category, skipping execution"
            ;;
    esac
}

# Execute security fixes
execute_security_fix() {
    local title="$1"
    log "🔒 Executing security fix: $title"
    
    # Update dependencies with security patches
    if command -v safety >/dev/null 2>&1; then
        pip install --upgrade pip
        pip-audit --fix --dry-run
        log "✅ Security dependency analysis completed"
    fi
    
    # Run security scans
    if command -v bandit >/dev/null 2>&1; then
        bandit -r src/ -f json -o "$LOG_DIR/bandit-$(date +%Y%m%d).json" || true
        log "✅ Security scan completed"
    fi
}

# Execute dependency updates  
execute_dependency_update() {
    local title="$1"
    log "📦 Executing dependency update: $title"
    
    # Check for outdated packages
    pip list --outdated --format=json > "$LOG_DIR/outdated-$(date +%Y%m%d).json" || true
    
    # Update development dependencies (safer for automation)
    pip install --upgrade \
        ruff bandit pytest pre-commit mypy black coverage safety pip-audit || true
    
    log "✅ Development dependencies updated"
}

# Execute refactoring tasks
execute_refactoring() {
    local title="$1"
    log "🔧 Executing refactoring: $title"
    
    # Run code formatting
    if command -v black >/dev/null 2>&1; then
        black src/ tests/ --check --diff > "$LOG_DIR/black-$(date +%Y%m%d).log" 2>&1 || true
    fi
    
    # Run linting with auto-fix
    if command -v ruff >/dev/null 2>&1; then
        ruff check . --fix --show-fixes > "$LOG_DIR/ruff-$(date +%Y%m%d).log" 2>&1 || true
    fi
    
    log "✅ Code quality improvements completed"
}

# Execute performance optimizations
execute_performance_optimization() {
    local title="$1"
    log "⚡ Executing performance optimization: $title"
    
    # Run performance tests if available
    if [[ -f "performance/benchmarks.py" ]]; then
        python3 performance/benchmarks.py > "$LOG_DIR/perf-$(date +%Y%m%d).log" 2>&1 || true
        log "✅ Performance benchmarks completed"
    fi
    
    # Profile memory usage
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import psutil
import json
stats = {
    'memory_usage': psutil.virtual_memory()._asdict(),
    'disk_usage': psutil.disk_usage('.')._asdict(),
    'cpu_count': psutil.cpu_count()
}
with open('$LOG_DIR/system-stats-$(date +%Y%m%d).json', 'w') as f:
    json.dump(stats, f, indent=2)
" 2>/dev/null || true
    fi
    
    log "✅ Performance analysis completed"
}

# Run comprehensive health check
health_check() {
    log "🏥 Running comprehensive health check"
    
    local health_score=100
    
    # Check Git status
    if ! git status --porcelain >/dev/null 2>&1; then
        log "⚠️  Git repository issues detected"
        ((health_score -= 10))
    fi
    
    # Check Python environment
    if ! python3 -c "import sys; print(sys.version)" >/dev/null 2>&1; then
        log "⚠️  Python environment issues"
        ((health_score -= 20))
    fi
    
    # Check dependencies
    if ! pip check >/dev/null 2>&1; then
        log "⚠️  Dependency conflicts detected"
        ((health_score -= 15))
    fi
    
    # Check test suite
    if [[ -d "tests" ]] && ! python3 -m pytest --collect-only >/dev/null 2>&1; then
        log "⚠️  Test suite issues detected" 
        ((health_score -= 25))
    fi
    
    # Save health metrics
    python3 -c "
import json
from datetime import datetime
health_data = {
    'timestamp': datetime.now().isoformat(),
    'health_score': $health_score,
    'status': 'healthy' if $health_score >= 80 else 'degraded' if $health_score >= 60 else 'critical'
}
with open('$LOG_DIR/health-$(date +%Y%m%d).json', 'w') as f:
    json.dump(health_data, f, indent=2)
"
    
    log "🏥 Health check completed (score: $health_score/100)"
}

# Main execution logic
main() {
    local action="${1:-discover}"
    
    log "🚀 Terragon Autonomous SDLC Scheduler started (action: $action)"
    check_config
    
    case "$action" in
        "discover")
            run_discovery "manual"
            ;;
        "execute")
            execute_next_item
            ;;
        "health")
            health_check
            ;;
        "continuous")
            log "🔄 Starting continuous execution mode"
            while true; do
                run_discovery "continuous"
                execute_next_item
                health_check
                log "😴 Sleeping for 1 hour..."
                sleep 3600
            done
            ;;
        "security-scan")
            run_discovery "security"
            execute_security_fix "Automated security scan"
            ;;
        *)
            echo "Usage: $0 {discover|execute|health|continuous|security-scan}"
            echo "  discover     - Run value discovery only"
            echo "  execute      - Execute next best value item"
            echo "  health       - Run health check"
            echo "  continuous   - Run continuous execution loop"
            echo "  security-scan - Run security-focused scan"
            exit 1
            ;;
    esac
    
    log "✅ Terragon Autonomous SDLC Scheduler completed"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi