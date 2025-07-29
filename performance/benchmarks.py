"""
Performance benchmarking suite for multimodal contract extractor.
Automated performance testing and regression detection.
"""

import time
import json
import statistics
import tracemalloc
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import psutil
import gc

# Import application modules for testing
try:
    from multimodal_contract_extractor.extraction import DocumentProcessor
    from multimodal_contract_extractor.config import Config
except ImportError:
    # Fallback for testing without full installation
    DocumentProcessor = None
    Config = None


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    test_name: str
    execution_time: float
    memory_peak: float
    memory_current: float
    cpu_percent: float
    iterations: int
    timestamp: str
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class BenchmarkResult:
    """Complete benchmark result with statistics."""
    test_name: str
    metrics: List[PerformanceMetrics]
    avg_execution_time: float
    std_execution_time: float
    min_execution_time: float
    max_execution_time: float
    avg_memory_peak: float
    throughput: float  # operations per second
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            'metrics': [m.to_dict() for m in self.metrics]
        }


class PerformanceBenchmark:
    """Performance benchmarking framework."""
    
    def __init__(self, output_dir: str = "performance/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        
    def measure_performance(
        self,
        func: Callable,
        test_name: str,
        iterations: int = 10,
        warmup_iterations: int = 2,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """
        Measure performance of a function with comprehensive metrics.
        
        Args:
            func: Function to benchmark
            test_name: Name of the test
            iterations: Number of iterations to run
            warmup_iterations: Number of warmup iterations
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            BenchmarkResult with comprehensive metrics
        """
        print(f"Running benchmark: {test_name}")
        
        # Warmup runs
        for _ in range(warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Warmup failed: {e}")
                
        # Collect garbage before benchmarking
        gc.collect()
        
        metrics: List[PerformanceMetrics] = []
        
        for i in range(iterations):
            # Start memory tracking
            tracemalloc.start()
            process = psutil.Process()
            cpu_before = process.cpu_percent()
            
            # Measure execution time
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(f"Benchmark iteration {i+1} failed: {e}")
                continue
                
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # Memory metrics
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # CPU metrics
            cpu_after = process.cpu_percent()
            cpu_percent = max(cpu_after - cpu_before, 0)
            
            # Create metrics record
            metric = PerformanceMetrics(
                test_name=test_name,
                execution_time=execution_time,
                memory_peak=peak / 1024 / 1024,  # Convert to MB
                memory_current=current / 1024 / 1024,  # Convert to MB
                cpu_percent=cpu_percent,
                iterations=iterations,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            metrics.append(metric)
            print(f"  Iteration {i+1}: {execution_time:.4f}s, {peak/1024/1024:.2f}MB peak")
            
            # Brief pause between iterations
            time.sleep(0.1)
        
        if not metrics:
            raise RuntimeError(f"All benchmark iterations failed for {test_name}")
        
        # Calculate statistics
        execution_times = [m.execution_time for m in metrics]
        memory_peaks = [m.memory_peak for m in metrics]
        
        benchmark_result = BenchmarkResult(
            test_name=test_name,
            metrics=metrics,
            avg_execution_time=statistics.mean(execution_times),
            std_execution_time=statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            min_execution_time=min(execution_times),
            max_execution_time=max(execution_times),
            avg_memory_peak=statistics.mean(memory_peaks),
            throughput=iterations / sum(execution_times),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        self.results.append(benchmark_result)
        return benchmark_result
    
    def save_results(self, filename: Optional[str] = None) -> Path:
        """Save benchmark results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
            
        output_path = self.output_dir / filename
        
        results_data = {
            'benchmark_run_timestamp': datetime.now(timezone.utc).isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                'python_version': str(psutil.version_info if hasattr(psutil, 'version_info') else 'unknown')
            },
            'results': [result.to_dict() for result in self.results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
            
        print(f"Benchmark results saved to: {output_path}")
        return output_path
    
    def load_baseline(self, baseline_file: str) -> Dict[str, BenchmarkResult]:
        """Load baseline results for comparison."""
        baseline_path = self.output_dir / baseline_file
        
        if not baseline_path.exists():
            print(f"Baseline file not found: {baseline_path}")
            return {}
            
        with open(baseline_path, 'r') as f:
            data = json.load(f)
            
        baseline_results = {}
        for result_data in data.get('results', []):
            metrics = [
                PerformanceMetrics(**m) for m in result_data.get('metrics', [])
            ]
            # Reconstruct BenchmarkResult (excluding metrics in constructor)
            result_dict = result_data.copy()
            result_dict.pop('metrics', None)
            result = BenchmarkResult(metrics=metrics, **result_dict)
            baseline_results[result.test_name] = result
            
        return baseline_results
    
    def compare_with_baseline(
        self,
        baseline_file: str,
        regression_threshold: float = 0.1  # 10% regression threshold
    ) -> Dict[str, Dict[str, Any]]:
        """Compare current results with baseline and detect regressions."""
        baseline_results = self.load_baseline(baseline_file)
        
        if not baseline_results:
            print("No baseline results available for comparison")
            return {}
            
        comparison = {}
        
        for current_result in self.results:
            test_name = current_result.test_name
            
            if test_name not in baseline_results:
                comparison[test_name] = {
                    'status': 'new_test',
                    'message': 'No baseline data available'
                }
                continue
                
            baseline = baseline_results[test_name]
            
            # Calculate performance change
            time_change = (
                (current_result.avg_execution_time - baseline.avg_execution_time)
                / baseline.avg_execution_time
            )
            
            memory_change = (
                (current_result.avg_memory_peak - baseline.avg_memory_peak)
                / baseline.avg_memory_peak
            )
            
            # Determine status
            if time_change > regression_threshold:
                status = 'regression'
                message = f"Performance regression detected: {time_change:.1%} slower"
            elif time_change < -regression_threshold:
                status = 'improvement'
                message = f"Performance improvement: {abs(time_change):.1%} faster"
            else:
                status = 'stable'
                message = f"Performance stable: {time_change:.1%} change"
                
            comparison[test_name] = {
                'status': status,
                'message': message,
                'time_change_percent': time_change * 100,
                'memory_change_percent': memory_change * 100,
                'current_avg_time': current_result.avg_execution_time,
                'baseline_avg_time': baseline.avg_execution_time,
                'current_avg_memory': current_result.avg_memory_peak,
                'baseline_avg_memory': baseline.avg_memory_peak
            }
            
        return comparison


# Sample benchmark functions for common operations
def benchmark_dummy_extraction(iterations: int = 100) -> None:
    """Benchmark dummy extraction operation for testing."""
    # Simulate document processing work
    import time
    import random
    
    # Simulate variable processing time
    processing_time = random.uniform(0.001, 0.01)
    time.sleep(processing_time)
    
    # Simulate memory allocation
    dummy_data = [i for i in range(random.randint(100, 1000))]
    
    # Simulate some computation
    result = sum(x * x for x in dummy_data)
    return result


def benchmark_config_loading() -> None:
    """Benchmark configuration loading."""
    # If Config class is available, use it
    if Config:
        config = Config()
        return config
    else:
        # Fallback dummy config loading
        import yaml
        dummy_config = {
            'processing': {'batch_size': 10},
            'ocr': {'engine': 'tesseract'},
            'output': {'format': 'json'}
        }
        return dummy_config


def main():
    """Run the performance benchmark suite."""
    print("Starting Performance Benchmark Suite")
    print("=" * 50)
    
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    try:
        # Benchmark 1: Document extraction (dummy)
        benchmark.measure_performance(
            benchmark_dummy_extraction,
            "dummy_document_extraction",
            iterations=20,
            warmup_iterations=3
        )
        
        # Benchmark 2: Configuration loading
        benchmark.measure_performance(
            benchmark_config_loading,
            "config_loading",
            iterations=50,
            warmup_iterations=5
        )
        
        # Benchmark 3: Memory intensive operation
        def memory_intensive_operation():
            # Simulate processing large amount of data
            data = [[i * j for j in range(100)] for i in range(100)]
            return sum(sum(row) for row in data)
            
        benchmark.measure_performance(
            memory_intensive_operation,
            "memory_intensive_processing",
            iterations=10,
            warmup_iterations=2
        )
        
    except Exception as e:
        print(f"Benchmark execution failed: {e}")
        return 1
    
    # Save results
    results_file = benchmark.save_results()
    
    # Try to compare with baseline (if exists)
    try:
        comparison = benchmark.compare_with_baseline("baseline_results.json")
        
        if comparison:
            print("\nPerformance Comparison with Baseline:")
            print("-" * 40)
            
            regression_found = False
            for test_name, comp in comparison.items():
                status_symbol = {
                    'regression': '❌',
                    'improvement': '✅', 
                    'stable': '➖',
                    'new_test': '🆕'
                }.get(comp['status'], '❓')
                
                print(f"{status_symbol} {test_name}: {comp['message']}")
                
                if comp['status'] == 'regression':
                    regression_found = True
                    
            if regression_found:
                print("\n⚠️  Performance regressions detected!")
                return 1
            else:
                print("\n✅ All performance tests passed!")
                
    except Exception as e:
        print(f"Baseline comparison failed: {e}")
    
    print(f"\nBenchmark complete. Results saved to: {results_file}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())