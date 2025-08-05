"""
Load testing suite for multimodal contract extractor.
Simulates concurrent usage patterns and measures system behavior under load.
"""

import json
import queue
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class LoadTestMetrics:
    """Load test metrics data structure."""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors_per_second: float
    peak_memory_mb: float
    avg_cpu_percent: float
    duration_seconds: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class RequestResult:
    """Individual request result."""
    success: bool
    response_time: float
    error_message: Optional[str] = None
    timestamp: float = 0.0


class LoadTester:
    """Load testing framework for performance validation."""

    def __init__(self, output_dir: str = "performance/load_test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[LoadTestMetrics] = []

    def simulate_user_request(self, user_id: int, request_func: Callable) -> RequestResult:
        """Simulate a single user request."""
        start_time = time.perf_counter()

        try:
            # Execute the request function
            result = request_func(user_id)
            end_time = time.perf_counter()

            return RequestResult(
                success=True,
                response_time=end_time - start_time,
                timestamp=start_time
            )

        except Exception as e:
            end_time = time.perf_counter()
            return RequestResult(
                success=False,
                response_time=end_time - start_time,
                error_message=str(e),
                timestamp=start_time
            )

    def run_load_test(
        self,
        test_name: str,
        request_func: Callable,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: float = 1.0,
        test_duration: Optional[float] = None
    ) -> LoadTestMetrics:
        """
        Run a load test with specified parameters.
        
        Args:
            test_name: Name of the load test
            request_func: Function to execute for each request
            concurrent_users: Number of concurrent users to simulate
            requests_per_user: Number of requests each user should make
            ramp_up_time: Time to ramp up all users (seconds)
            test_duration: Optional fixed test duration (seconds)
            
        Returns:
            LoadTestMetrics with comprehensive results
        """
        print(f"Starting load test: {test_name}")
        print(f"  Concurrent users: {concurrent_users}")
        print(f"  Requests per user: {requests_per_user}")
        print(f"  Ramp-up time: {ramp_up_time}s")

        results_queue = queue.Queue()
        start_time = time.perf_counter()

        # System monitoring setup
        process = psutil.Process()
        memory_samples = []
        cpu_samples = []

        def monitor_system():
            """Monitor system resources during test."""
            while not getattr(monitor_system, 'stop', False):
                try:
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                    cpu_samples.append(process.cpu_percent())
                    time.sleep(0.5)
                except:
                    break

        # Start system monitoring
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()

        def user_simulation(user_id: int, start_delay: float):
            """Simulate user behavior."""
            # Ramp-up delay
            time.sleep(start_delay)

            user_results = []
            for request_num in range(requests_per_user):
                if test_duration and (time.perf_counter() - start_time) > test_duration:
                    break

                result = self.simulate_user_request(user_id, request_func)
                user_results.append(result)
                results_queue.put(result)

                # Small delay between requests from same user
                time.sleep(0.1)

            return user_results

        # Calculate ramp-up delays
        ramp_up_delay = ramp_up_time / concurrent_users if concurrent_users > 1 else 0

        # Execute load test with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            for user_id in range(concurrent_users):
                delay = user_id * ramp_up_delay
                future = executor.submit(user_simulation, user_id, delay)
                futures.append(future)

            # Wait for all users to complete
            all_results = []
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    print(f"User simulation failed: {e}")

        # Stop system monitoring
        monitor_system.stop = True
        monitor_thread.join(timeout=1)

        end_time = time.perf_counter()
        test_duration_actual = end_time - start_time

        # Collect all results from queue
        queue_results = []
        while not results_queue.empty():
            try:
                queue_results.append(results_queue.get_nowait())
            except queue.Empty:
                break

        # Use queue results if available, otherwise use thread results
        final_results = queue_results if queue_results else all_results

        if not final_results:
            raise RuntimeError(f"No results collected for load test: {test_name}")

        # Calculate metrics
        successful_requests = sum(1 for r in final_results if r.success)
        failed_requests = len(final_results) - successful_requests

        response_times = [r.response_time for r in final_results if r.success]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p95_response_time = p99_response_time = 0.0

        # Calculate throughput
        requests_per_second = len(final_results) / test_duration_actual if test_duration_actual > 0 else 0
        errors_per_second = failed_requests / test_duration_actual if test_duration_actual > 0 else 0

        # System resource metrics
        peak_memory_mb = max(memory_samples) if memory_samples else 0
        avg_cpu_percent = statistics.mean(cpu_samples) if cpu_samples else 0

        metrics = LoadTestMetrics(
            test_name=test_name,
            concurrent_users=concurrent_users,
            total_requests=len(final_results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            errors_per_second=errors_per_second,
            peak_memory_mb=peak_memory_mb,
            avg_cpu_percent=avg_cpu_percent,
            duration_seconds=test_duration_actual,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        self.results.append(metrics)

        # Print summary
        print(f"Load test completed: {test_name}")
        print(f"  Duration: {test_duration_actual:.2f}s")
        print(f"  Total requests: {len(final_results)}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  RPS: {requests_per_second:.2f}")
        print(f"  Avg response time: {avg_response_time:.4f}s")
        print(f"  P95 response time: {p95_response_time:.4f}s")

        return metrics

    def save_results(self, filename: Optional[str] = None) -> Path:
        """Save load test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"

        output_path = self.output_dir / filename

        results_data = {
            'load_test_run_timestamp': datetime.now(timezone.utc).isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'platform': psutil.platform if hasattr(psutil, 'platform') else 'unknown',
            },
            'results': [result.to_dict() for result in self.results]
        }

        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"Load test results saved to: {output_path}")
        return output_path

    def generate_load_test_report(self) -> Path:
        """Generate an HTML report for load test results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"load_test_report_{timestamp}.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Load Test Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>System: {psutil.cpu_count()} CPUs, {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB RAM</p>
    </div>
    
    <div class="section">
        <h2>Test Summary</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Concurrent Users</th>
                <th>Total Requests</th>
                <th>Success Rate</th>
                <th>Avg Response Time</th>
                <th>P95 Response Time</th>
                <th>RPS</th>
                <th>Peak Memory (MB)</th>
            </tr>
"""

        for result in self.results:
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            success_class = 'success' if success_rate >= 95 else 'warning' if success_rate >= 80 else 'error'

            html_content += f"""
            <tr>
                <td>{result.test_name}</td>
                <td>{result.concurrent_users}</td>
                <td>{result.total_requests}</td>
                <td class="{success_class}">{success_rate:.1f}%</td>
                <td>{result.avg_response_time:.4f}s</td>
                <td>{result.p95_response_time:.4f}s</td>
                <td>{result.requests_per_second:.2f}</td>
                <td>{result.peak_memory_mb:.1f}</td>
            </tr>
"""

        html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>Performance Thresholds</h2>
        <ul>
            <li><strong>Success Rate:</strong> ≥95% (Good), ≥80% (Acceptable), &lt;80% (Poor)</li>
            <li><strong>Response Time:</strong> &lt;1s (Good), &lt;3s (Acceptable), ≥3s (Poor)</li>
            <li><strong>Error Rate:</strong> &lt;1% (Good), &lt;5% (Acceptable), ≥5% (Poor)</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            <li>Monitor response times under increasing load</li>
            <li>Set up automated load testing in CI/CD pipeline</li>
            <li>Establish SLA/SLO targets based on these results</li>
            <li>Consider horizontal scaling if concurrent user limits reached</li>
            <li>Implement caching for frequently accessed data</li>
        </ul>
    </div>
</body>
</html>
"""

        with open(report_path, 'w') as f:
            f.write(html_content)

        print(f"Load test report generated: {report_path}")
        return report_path


# Sample load test functions
def sample_document_processing_request(user_id: int) -> Dict[str, Any]:
    """Sample document processing request for load testing."""
    import random
    import time

    # Simulate variable processing load
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)

    # Simulate memory usage
    dummy_data = [f"user_{user_id}_data_{i}" for i in range(random.randint(100, 500))]

    # Simulate occasional errors (5% failure rate)
    if random.random() < 0.05:
        raise Exception(f"Simulated processing error for user {user_id}")

    return {
        'user_id': user_id,
        'processed_items': len(dummy_data),
        'processing_time': processing_time,
        'status': 'success'
    }


def sample_config_request(user_id: int) -> Dict[str, Any]:
    """Sample configuration request for load testing."""
    import random
    import time

    # Simulate fast configuration lookup
    time.sleep(random.uniform(0.001, 0.01))

    return {
        'user_id': user_id,
        'config': {
            'batch_size': 10,
            'timeout': 30,
            'retries': 3
        }
    }


def main():
    """Run the load testing suite."""
    print("Starting Load Testing Suite")
    print("=" * 50)

    load_tester = LoadTester()

    try:
        # Test 1: Light load - config requests
        load_tester.run_load_test(
            test_name="config_light_load",
            request_func=sample_config_request,
            concurrent_users=5,
            requests_per_user=20,
            ramp_up_time=2.0
        )

        # Test 2: Medium load - document processing
        load_tester.run_load_test(
            test_name="document_processing_medium_load",
            request_func=sample_document_processing_request,
            concurrent_users=10,
            requests_per_user=10,
            ramp_up_time=5.0
        )

        # Test 3: High load - stress test
        load_tester.run_load_test(
            test_name="document_processing_high_load",
            request_func=sample_document_processing_request,
            concurrent_users=20,
            requests_per_user=5,
            ramp_up_time=3.0
        )

        # Test 4: Sustained load test
        load_tester.run_load_test(
            test_name="sustained_load_test",
            request_func=sample_document_processing_request,
            concurrent_users=15,
            requests_per_user=50,  # More requests per user
            ramp_up_time=10.0,
            test_duration=60.0  # Fixed 60-second test
        )

    except Exception as e:
        print(f"Load test execution failed: {e}")
        return 1

    # Save results and generate report
    results_file = load_tester.save_results()
    report_file = load_tester.generate_load_test_report()

    # Check for performance issues
    performance_issues = []
    for result in load_tester.results:
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0

        if success_rate < 95:
            performance_issues.append(f"{result.test_name}: Low success rate ({success_rate:.1f}%)")

        if result.avg_response_time > 1.0:
            performance_issues.append(f"{result.test_name}: High response time ({result.avg_response_time:.3f}s)")

        if result.errors_per_second > 0.1:
            performance_issues.append(f"{result.test_name}: High error rate ({result.errors_per_second:.2f} errors/s)")

    if performance_issues:
        print("\n⚠️  Performance issues detected:")
        for issue in performance_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("\n✅ All load tests passed!")

    print("\nLoad testing complete.")
    print(f"Results: {results_file}")
    print(f"Report: {report_file}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
