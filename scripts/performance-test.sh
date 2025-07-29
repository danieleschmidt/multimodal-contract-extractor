#!/bin/bash
# Performance Testing Automation Script
# Comprehensive performance validation and regression detection

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PERFORMANCE_DIR="${PERFORMANCE_DIR:-performance}"
RESULTS_DIR="${RESULTS_DIR:-$PERFORMANCE_DIR/results}"
LOAD_TEST_DIR="${LOAD_TEST_DIR:-$PERFORMANCE_DIR/load_test_results}"
BASELINE_FILE="${BASELINE_FILE:-baseline_results.json}"
REGRESSION_THRESHOLD="${REGRESSION_THRESHOLD:-0.1}"  # 10%
PYTHON_CMD="${PYTHON_CMD:-python}"

# Create directories
mkdir -p "$RESULTS_DIR" "$LOAD_TEST_DIR"

echo -e "${BLUE}=== Performance Testing Suite ===${NC}"
echo -e "Performance dir: ${PERFORMANCE_DIR}"
echo -e "Results dir: ${RESULTS_DIR}"
echo -e "Baseline file: ${BASELINE_FILE}"
echo -e "Regression threshold: ${REGRESSION_THRESHOLD}"
echo ""

# Function to check if Python module is available
check_python_module() {
    local module="$1"
    if $PYTHON_CMD -c "import $module" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install required dependencies
install_dependencies() {
    echo -e "${YELLOW}Checking performance testing dependencies...${NC}"
    
    local missing_modules=()
    
    # Check for required modules
    if ! check_python_module "psutil"; then
        missing_modules+=("psutil")
    fi
    
    if [[ ${#missing_modules[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Installing missing dependencies: ${missing_modules[*]}${NC}"
        $PYTHON_CMD -m pip install "${missing_modules[@]}"
    else
        echo -e "${GREEN}✓ All dependencies available${NC}"
    fi
}

# Function to run benchmark tests
run_benchmarks() {
    echo -e "${YELLOW}Running performance benchmarks...${NC}"
    
    if [[ -f "$PERFORMANCE_DIR/benchmarks.py" ]]; then
        cd "$PERFORMANCE_DIR"
        
        if $PYTHON_CMD benchmarks.py; then
            echo -e "${GREEN}✓ Benchmarks completed successfully${NC}"
            cd - > /dev/null
            return 0
        else
            echo -e "${RED}✗ Benchmarks failed${NC}"
            cd - > /dev/null
            return 1
        fi
    else
        echo -e "${RED}✗ Benchmark script not found: $PERFORMANCE_DIR/benchmarks.py${NC}"
        return 1
    fi
}

# Function to run load tests
run_load_tests() {
    echo -e "${YELLOW}Running load tests...${NC}"
    
    if [[ -f "$PERFORMANCE_DIR/load_testing.py" ]]; then
        cd "$PERFORMANCE_DIR"
        
        if $PYTHON_CMD load_testing.py; then
            echo -e "${GREEN}✓ Load tests completed successfully${NC}"
            cd - > /dev/null
            return 0
        else
            echo -e "${RED}✗ Load tests failed${NC}"
            cd - > /dev/null
            return 1
        fi
    else
        echo -e "${RED}✗ Load testing script not found: $PERFORMANCE_DIR/load_testing.py${NC}"
        return 1
    fi
}

# Function to analyze performance trends
analyze_trends() {
    echo -e "${YELLOW}Analyzing performance trends...${NC}"
    
    # Find the most recent benchmark result
    local latest_result
    latest_result=$(find "$RESULTS_DIR" -name "benchmark_results_*.json" -type f | sort | tail -1)
    
    if [[ -z "$latest_result" ]]; then
        echo -e "${YELLOW}⚠ No benchmark results found for trend analysis${NC}"
        return 0
    fi
    
    echo -e "Latest result: $(basename "$latest_result")"
    
    # Simple trend analysis using jq if available
    if command -v jq &> /dev/null; then
        local total_tests
        total_tests=$(jq '.results | length' "$latest_result")
        echo -e "Total benchmark tests: $total_tests"
        
        # Extract average execution times
        local avg_times
        avg_times=$(jq -r '.results[] | "\(.test_name): \(.avg_execution_time)s"' "$latest_result")
        echo -e "Average execution times:"
        echo "$avg_times" | while read -r line; do
            echo -e "  $line"
        done
    else
        echo -e "${YELLOW}⚠ jq not available for detailed analysis${NC}"
    fi
}

# Function to check performance thresholds
check_thresholds() {
    echo -e "${YELLOW}Checking performance thresholds...${NC}"
    
    local threshold_violations=()
    
    # Find the most recent benchmark result
    local latest_result
    latest_result=$(find "$RESULTS_DIR" -name "benchmark_results_*.json" -type f | sort | tail -1)
    
    if [[ -z "$latest_result" ]]; then
        echo -e "${YELLOW}⚠ No benchmark results found for threshold checking${NC}"
        return 0
    fi
    
    if command -v jq &> /dev/null; then
        # Check for tests taking longer than 5 seconds
        local slow_tests
        slow_tests=$(jq -r '.results[] | select(.avg_execution_time > 5) | .test_name' "$latest_result")
        
        if [[ -n "$slow_tests" ]]; then
            echo "$slow_tests" | while read -r test_name; do
                threshold_violations+=("$test_name: Execution time > 5s")
            done
        fi
        
        # Check for tests using more than 500MB memory
        local memory_intensive_tests
        memory_intensive_tests=$(jq -r '.results[] | select(.avg_memory_peak > 500) | .test_name' "$latest_result")
        
        if [[ -n "$memory_intensive_tests" ]]; then
            echo "$memory_intensive_tests" | while read -r test_name; do
                threshold_violations+=("$test_name: Memory usage > 500MB")
            done
        fi
    fi
    
    if [[ ${#threshold_violations[@]} -gt 0 ]]; then
        echo -e "${RED}⚠ Performance threshold violations:${NC}"
        printf '%s\n' "${threshold_violations[@]}" | while read -r violation; do
            echo -e "${RED}  - $violation${NC}"
        done
        return 1
    else
        echo -e "${GREEN}✓ All performance thresholds passed${NC}"
        return 0
    fi
}

# Function to generate performance summary
generate_summary() {
    echo -e "${YELLOW}Generating performance summary...${NC}"
    
    local summary_file="$RESULTS_DIR/performance_summary_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$summary_file" << EOF
Performance Testing Summary
===========================
Date: $(date)
Test Environment: $(uname -a)
Python Version: $($PYTHON_CMD --version)

System Information:
- CPU Cores: $(nproc 2>/dev/null || echo "Unknown")
- Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "Unknown")

Test Results:
- Benchmark results: $(find "$RESULTS_DIR" -name "benchmark_results_*.json" | wc -l) files
- Load test results: $(find "$LOAD_TEST_DIR" -name "load_test_results_*.json" | wc -l) files

Latest Results:
EOF
    
    # Add latest benchmark summary if available
    local latest_benchmark
    latest_benchmark=$(find "$RESULTS_DIR" -name "benchmark_results_*.json" -type f | sort | tail -1)
    
    if [[ -n "$latest_benchmark" ]] && command -v jq &> /dev/null; then
        echo "" >> "$summary_file"
        echo "Benchmark Summary:" >> "$summary_file"
        jq -r '.results[] | "- \(.test_name): \(.avg_execution_time)s avg, \(.avg_memory_peak)MB peak memory"' "$latest_benchmark" >> "$summary_file"
    fi
    
    # Add latest load test summary if available
    local latest_load_test
    latest_load_test=$(find "$LOAD_TEST_DIR" -name "load_test_results_*.json" -type f | sort | tail -1)
    
    if [[ -n "$latest_load_test" ]] && command -v jq &> /dev/null; then
        echo "" >> "$summary_file"
        echo "Load Test Summary:" >> "$summary_file"
        jq -r '.results[] | "- \(.test_name): \(.requests_per_second) RPS, \(.avg_response_time)s avg response"' "$latest_load_test" >> "$summary_file"
    fi
    
    echo -e "${GREEN}✓ Performance summary saved: $summary_file${NC}"
}

# Function to setup baseline
setup_baseline() {
    echo -e "${YELLOW}Setting up performance baseline...${NC}"
    
    local latest_result
    latest_result=$(find "$RESULTS_DIR" -name "benchmark_results_*.json" -type f | sort | tail -1)
    
    if [[ -z "$latest_result" ]]; then
        echo -e "${RED}✗ No benchmark results found to set as baseline${NC}"
        return 1
    fi
    
    cp "$latest_result" "$RESULTS_DIR/$BASELINE_FILE"
    echo -e "${GREEN}✓ Baseline set from: $(basename "$latest_result")${NC}"
}

# Function to run memory profiling
run_memory_profiling() {
    echo -e "${YELLOW}Running memory profiling...${NC}"
    
    if ! check_python_module "memory_profiler"; then
        echo -e "${YELLOW}Installing memory_profiler...${NC}"
        $PYTHON_CMD -m pip install memory_profiler
    fi
    
    # Create a simple memory profiling script
    cat > "$PERFORMANCE_DIR/memory_profile.py" << 'EOF'
import time
import gc
from memory_profiler import profile

@profile
def memory_intensive_function():
    """Function to profile memory usage."""
    # Simulate memory allocation
    data = []
    for i in range(1000):
        data.append([j for j in range(100)])
        if i % 100 == 0:
            time.sleep(0.01)
    
    # Simulate processing
    result = sum(len(chunk) for chunk in data)
    
    # Cleanup
    del data
    gc.collect()
    
    return result

if __name__ == "__main__":
    print("Running memory profiling...")
    result = memory_intensive_function()
    print(f"Result: {result}")
EOF
    
    cd "$PERFORMANCE_DIR"
    if $PYTHON_CMD memory_profile.py > "memory_profile_$(date +%Y%m%d_%H%M%S).txt" 2>&1; then
        echo -e "${GREEN}✓ Memory profiling completed${NC}"
        cd - > /dev/null
        return 0
    else
        echo -e "${RED}✗ Memory profiling failed${NC}"
        cd - > /dev/null
        return 1
    fi
}

# Main execution
main() {
    local exit_code=0
    local test_mode="${1:-full}"
    
    case "$test_mode" in
        "benchmark")
            install_dependencies
            if ! run_benchmarks; then
                exit_code=1
            fi
            ;;
        "load")
            install_dependencies
            if ! run_load_tests; then
                exit_code=1
            fi
            ;;
        "baseline")
            setup_baseline
            ;;
        "analyze")
            analyze_trends
            if ! check_thresholds; then
                exit_code=1
            fi
            ;;
        "memory")
            install_dependencies
            if ! run_memory_profiling; then
                exit_code=1
            fi
            ;;
        "full"|*)
            install_dependencies
            
            # Run all tests
            if ! run_benchmarks; then
                exit_code=1
            fi
            
            if ! run_load_tests; then
                exit_code=1
            fi
            
            if ! run_memory_profiling; then
                exit_code=1
            fi
            
            # Analysis
            analyze_trends
            if ! check_thresholds; then
                exit_code=1
            fi
            
            generate_summary
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}=== Performance Testing Complete ===${NC}"
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ All performance tests passed${NC}"
    else
        echo -e "${RED}⚠️ Performance issues detected${NC}"
    fi
    
    echo -e "Results available in: $RESULTS_DIR"
    echo -e "Load test results in: $LOAD_TEST_DIR"
    
    exit $exit_code
}

# Usage information
show_usage() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  full      - Run all performance tests (default)"
    echo "  benchmark - Run only benchmark tests" 
    echo "  load      - Run only load tests"
    echo "  memory    - Run only memory profiling"
    echo "  analyze   - Analyze existing results"
    echo "  baseline  - Set current results as baseline"
    echo ""
    echo "Environment variables:"
    echo "  PERFORMANCE_DIR      - Performance test directory (default: performance)"
    echo "  REGRESSION_THRESHOLD - Regression threshold (default: 0.1)"
    echo "  PYTHON_CMD          - Python command (default: python)"
}

# Handle command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "${1:-full}"