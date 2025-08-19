"""
Comprehensive Performance Testing and Validation Suite.

This module provides advanced performance testing, load testing, stress testing,
and validation capabilities to ensure the scalability and reliability of the
distributed contract extraction system under various load conditions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
import multiprocessing as mp

import numpy as np
import psutil

logger = logging.getLogger(__name__)

# Try to import testing and HTTP libraries
try:
    import aiohttp
    import aiofiles
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None
    aiofiles = None

try:
    import locust
    HAS_LOCUST = True
except ImportError:
    HAS_LOCUST = False
    locust = None


class TestType(Enum):
    """Types of performance tests."""
    LOAD_TEST = "load_test"
    STRESS_TEST = "stress_test"
    SPIKE_TEST = "spike_test"
    VOLUME_TEST = "volume_test"
    ENDURANCE_TEST = "endurance_test"
    SCALABILITY_TEST = "scalability_test"
    BASELINE_TEST = "baseline_test"
    REGRESSION_TEST = "regression_test"


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class LoadPattern(Enum):
    """Load generation patterns."""
    CONSTANT = "constant"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    WAVE = "wave"
    STEP = "step"
    RANDOM = "random"


class ResponseCategory(Enum):
    """Response time categories."""
    EXCELLENT = "excellent"  # < 100ms
    GOOD = "good"           # 100-500ms
    ACCEPTABLE = "acceptable"  # 500ms-2s
    SLOW = "slow"           # 2s-5s
    UNACCEPTABLE = "unacceptable"  # > 5s


@dataclass
class TestConfiguration:
    """Performance test configuration."""
    test_id: str
    test_type: TestType
    name: str
    description: str
    target_url: str
    duration_seconds: int
    concurrent_users: int
    requests_per_second: Optional[int] = None
    load_pattern: LoadPattern = LoadPattern.CONSTANT
    ramp_up_time: int = 60  # seconds
    ramp_down_time: int = 30  # seconds
    think_time: Tuple[float, float] = (1.0, 3.0)  # min, max seconds
    timeout_seconds: int = 30
    test_data: Dict[str, Any] = field(default_factory=dict)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class RequestResult:
    """Individual request result."""
    request_id: str
    timestamp: float
    method: str
    url: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestMetrics:
    """Aggregated test metrics."""
    test_id: str
    start_time: float
    end_time: float
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    response_times: Dict[str, float]  # min, max, mean, median, p95, p99
    response_time_distribution: Dict[ResponseCategory, int]
    error_rate: float
    throughput_mb_per_second: float
    concurrent_users_avg: float
    resource_utilization: Dict[str, float]
    errors_by_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""
    baseline_id: str
    test_type: TestType
    target_url: str
    baseline_metrics: TestMetrics
    acceptable_deviation: Dict[str, float]  # metric -> acceptable % deviation
    created_at: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)


@dataclass
class ValidationResult:
    """Test validation result."""
    validation_id: str
    test_id: str
    passed: bool
    assertion_results: List[Dict[str, Any]]
    performance_score: float  # 0-100
    baseline_comparison: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class LoadGenerator:
    """Advanced load generation engine."""
    
    def __init__(self, test_config: TestConfiguration):
        self.test_config = test_config
        self.is_running = False
        self.start_time = 0.0
        self.end_time = 0.0
        
        # Request tracking
        self.request_results: deque = deque(maxlen=100000)  # Keep last 100k requests
        self.active_requests: Dict[str, float] = {}  # request_id -> start_time
        
        # Load pattern state
        self.current_users = 0
        self.target_users = 0
        
        # Session management
        if HAS_AIOHTTP:
            self.session: Optional[aiohttp.ClientSession] = None
        else:
            self.session = None
        
        self.lock = threading.RLock()
    
    async def run_test(self) -> TestMetrics:
        """Run the performance test."""
        try:
            logger.info(f"Starting performance test: {self.test_config.name}")
            
            self.is_running = True
            self.start_time = time.time()
            
            # Initialize HTTP session
            if HAS_AIOHTTP:
                timeout = aiohttp.ClientTimeout(total=self.test_config.timeout_seconds)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Start load generation
            load_task = asyncio.create_task(self._generate_load())
            
            # Start monitoring
            monitoring_task = asyncio.create_task(self._monitor_resources())
            
            # Wait for test completion
            await asyncio.wait([load_task, monitoring_task], timeout=self.test_config.duration_seconds + 120)
            
            self.end_time = time.time()
            self.is_running = False
            
            # Clean up
            if self.session:
                await self.session.close()
            
            # Calculate metrics
            metrics = self._calculate_metrics()
            
            logger.info(f"Test completed: {metrics.successful_requests}/{metrics.total_requests} requests successful")
            return metrics
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.is_running = False
            if self.session:
                await self.session.close()
            raise
    
    async def _generate_load(self) -> None:
        """Generate load according to the specified pattern."""
        test_duration = self.test_config.duration_seconds
        ramp_up = self.test_config.ramp_up_time
        ramp_down = self.test_config.ramp_down_time
        steady_duration = test_duration - ramp_up - ramp_down
        
        start_time = time.time()
        
        # Track worker tasks
        worker_tasks = set()
        
        try:
            while self.is_running and (time.time() - start_time) < test_duration:
                current_time = time.time() - start_time
                
                # Calculate target users based on load pattern
                target_users = self._calculate_target_users(current_time, test_duration, ramp_up, ramp_down)
                
                # Adjust worker count
                current_workers = len(worker_tasks)
                
                if target_users > current_workers:
                    # Add workers
                    for _ in range(target_users - current_workers):
                        if self.is_running:
                            task = asyncio.create_task(self._worker_loop())
                            worker_tasks.add(task)
                
                elif target_users < current_workers:
                    # Remove workers (let some finish naturally)
                    workers_to_remove = current_workers - target_users
                    for _ in range(min(workers_to_remove, len(worker_tasks))):
                        if worker_tasks:
                            task = worker_tasks.pop()
                            task.cancel()
                
                # Clean up completed tasks
                completed_tasks = {task for task in worker_tasks if task.done()}
                worker_tasks -= completed_tasks
                
                self.current_users = len(worker_tasks)
                await asyncio.sleep(1.0)  # Check every second
                
        finally:
            # Cancel all remaining tasks
            for task in worker_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if worker_tasks:
                await asyncio.gather(*worker_tasks, return_exceptions=True)
    
    def _calculate_target_users(self, current_time: float, total_duration: float, 
                               ramp_up: float, ramp_down: float) -> int:
        """Calculate target number of users based on load pattern."""
        max_users = self.test_config.concurrent_users
        steady_duration = total_duration - ramp_up - ramp_down
        
        if self.test_config.load_pattern == LoadPattern.CONSTANT:
            return max_users
        
        elif self.test_config.load_pattern == LoadPattern.RAMP_UP:
            if current_time <= ramp_up:
                # Ramp up phase
                return int((current_time / ramp_up) * max_users)
            elif current_time <= ramp_up + steady_duration:
                # Steady phase
                return max_users
            else:
                # Ramp down phase
                remaining_time = total_duration - current_time
                return max(0, int((remaining_time / ramp_down) * max_users))
        
        elif self.test_config.load_pattern == LoadPattern.SPIKE:
            spike_time = total_duration * 0.5  # Spike at 50% of test duration
            spike_duration = min(60.0, total_duration * 0.1)  # 10% of test duration or 60s
            
            if abs(current_time - spike_time) <= spike_duration / 2:
                return max_users * 2  # Double the load during spike
            else:
                return max_users
        
        elif self.test_config.load_pattern == LoadPattern.WAVE:
            # Sinusoidal wave pattern
            wave_frequency = 2 * math.pi / (total_duration / 3)  # 3 cycles over test duration
            amplitude = max_users * 0.3  # 30% variation
            base_users = max_users * 0.7  # 70% base load
            return int(base_users + amplitude * math.sin(wave_frequency * current_time))
        
        elif self.test_config.load_pattern == LoadPattern.STEP:
            # Step pattern - increase load in steps
            step_duration = total_duration / 4
            step = int(current_time / step_duration)
            return min(max_users, (step + 1) * (max_users // 4))
        
        elif self.test_config.load_pattern == LoadPattern.RANDOM:
            # Random load between 50% and 150% of target
            variation = 0.5
            min_users = int(max_users * (1 - variation))
            max_random_users = int(max_users * (1 + variation))
            return random.randint(min_users, max_random_users)
        
        return max_users
    
    async def _worker_loop(self) -> None:
        """Individual worker loop."""
        try:
            while self.is_running:
                # Make request
                await self._make_request()
                
                # Think time
                think_time = random.uniform(*self.test_config.think_time)
                await asyncio.sleep(think_time)
                
        except asyncio.CancelledError:
            # Worker was cancelled, which is normal
            pass
        except Exception as e:
            logger.error(f"Worker error: {e}")
    
    async def _make_request(self) -> None:
        """Make a single HTTP request."""
        if not self.session or not HAS_AIOHTTP:
            # Simulate request without actual HTTP call
            await self._simulate_request()
            return
        
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            with self.lock:
                self.active_requests[request_id] = start_time
            
            # Prepare request
            method = self.test_config.test_data.get('method', 'GET')
            url = self.test_config.target_url
            headers = self.test_config.test_data.get('headers', {})
            data = self.test_config.test_data.get('data')
            
            # Make request
            async with self.session.request(method, url, headers=headers, json=data) as response:
                response_text = await response.text()
                end_time = time.time()
                
                # Create result
                result = RequestResult(
                    request_id=request_id,
                    timestamp=start_time,
                    method=method,
                    url=url,
                    status_code=response.status,
                    response_time_ms=(end_time - start_time) * 1000,
                    response_size_bytes=len(response_text.encode('utf-8')),
                    success=200 <= response.status < 400
                )
                
                if not result.success:
                    result.error_message = f"HTTP {response.status}"
                
        except asyncio.TimeoutError:
            end_time = time.time()
            result = RequestResult(
                request_id=request_id,
                timestamp=start_time,
                method=method,
                url=url,
                status_code=0,
                response_time_ms=(end_time - start_time) * 1000,
                response_size_bytes=0,
                success=False,
                error_message="Timeout"
            )
        except Exception as e:
            end_time = time.time()
            result = RequestResult(
                request_id=request_id,
                timestamp=start_time,
                method=method,
                url=url,
                status_code=0,
                response_time_ms=(end_time - start_time) * 1000,
                response_size_bytes=0,
                success=False,
                error_message=str(e)
            )
        
        finally:
            with self.lock:
                self.active_requests.pop(request_id, None)
                self.request_results.append(result)
    
    async def _simulate_request(self) -> None:
        """Simulate a request without actual HTTP call (for testing)."""
        request_id = f"sim_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Simulate processing time
        processing_time = random.uniform(0.05, 0.5)  # 50ms to 500ms
        await asyncio.sleep(processing_time)
        
        end_time = time.time()
        
        # Simulate occasional failures
        success = random.random() > 0.05  # 5% failure rate
        
        result = RequestResult(
            request_id=request_id,
            timestamp=start_time,
            method="GET",
            url=self.test_config.target_url,
            status_code=200 if success else 500,
            response_time_ms=(end_time - start_time) * 1000,
            response_size_bytes=random.randint(1000, 50000),  # 1KB to 50KB
            success=success,
            error_message=None if success else "Simulated error"
        )
        
        with self.lock:
            self.request_results.append(result)
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources during test."""
        resource_samples = []
        
        while self.is_running:
            try:
                sample = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'active_requests': len(self.active_requests),
                    'current_users': self.current_users
                }
                resource_samples.append(sample)
                
                await asyncio.sleep(5.0)  # Sample every 5 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
    
    def _calculate_metrics(self) -> TestMetrics:
        """Calculate aggregated test metrics."""
        with self.lock:
            results = list(self.request_results)
        
        if not results:
            # Return empty metrics
            return TestMetrics(
                test_id=self.test_config.test_id,
                start_time=self.start_time,
                end_time=self.end_time,
                duration_seconds=self.end_time - self.start_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                requests_per_second=0.0,
                response_times={},
                response_time_distribution={},
                error_rate=0.0,
                throughput_mb_per_second=0.0,
                concurrent_users_avg=0.0,
                resource_utilization={}
            )
        
        # Filter results to test duration
        test_results = [r for r in results if self.start_time <= r.timestamp <= self.end_time]
        
        # Basic counts
        total_requests = len(test_results)
        successful_requests = sum(1 for r in test_results if r.success)
        failed_requests = total_requests - successful_requests
        
        # Response times
        response_times_ms = [r.response_time_ms for r in test_results]
        
        if response_times_ms:
            response_times = {
                'min': min(response_times_ms),
                'max': max(response_times_ms),
                'mean': statistics.mean(response_times_ms),
                'median': statistics.median(response_times_ms),
                'p95': np.percentile(response_times_ms, 95),
                'p99': np.percentile(response_times_ms, 99)
            }
        else:
            response_times = {k: 0.0 for k in ['min', 'max', 'mean', 'median', 'p95', 'p99']}
        
        # Response time distribution
        distribution = {
            ResponseCategory.EXCELLENT: 0,
            ResponseCategory.GOOD: 0,
            ResponseCategory.ACCEPTABLE: 0,
            ResponseCategory.SLOW: 0,
            ResponseCategory.UNACCEPTABLE: 0
        }
        
        for rt in response_times_ms:
            if rt < 100:
                distribution[ResponseCategory.EXCELLENT] += 1
            elif rt < 500:
                distribution[ResponseCategory.GOOD] += 1
            elif rt < 2000:
                distribution[ResponseCategory.ACCEPTABLE] += 1
            elif rt < 5000:
                distribution[ResponseCategory.SLOW] += 1
            else:
                distribution[ResponseCategory.UNACCEPTABLE] += 1
        
        # Calculate rates
        duration = self.end_time - self.start_time
        requests_per_second = total_requests / max(duration, 1)
        error_rate = failed_requests / max(total_requests, 1) * 100
        
        # Calculate throughput
        total_bytes = sum(r.response_size_bytes for r in test_results)
        throughput_mb_per_second = (total_bytes / max(duration, 1)) / (1024 * 1024)
        
        # Error breakdown
        errors_by_type = {}
        for result in test_results:
            if not result.success and result.error_message:
                errors_by_type[result.error_message] = errors_by_type.get(result.error_message, 0) + 1
        
        return TestMetrics(
            test_id=self.test_config.test_id,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=requests_per_second,
            response_times=response_times,
            response_time_distribution=distribution,
            error_rate=error_rate,
            throughput_mb_per_second=throughput_mb_per_second,
            concurrent_users_avg=self.test_config.concurrent_users,
            resource_utilization={},  # Would be populated from monitoring data
            errors_by_type=errors_by_type
        )


class PerformanceValidator:
    """Performance test validation and analysis."""
    
    def __init__(self):
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.validation_rules: List[Callable] = [
            self._validate_response_times,
            self._validate_error_rate,
            self._validate_throughput,
            self._validate_resource_usage
        ]
    
    def add_baseline(self, baseline: PerformanceBaseline) -> None:
        """Add a performance baseline."""
        key = f"{baseline.test_type.value}:{baseline.target_url}"
        self.baselines[key] = baseline
    
    def validate_test_results(self, test_config: TestConfiguration, metrics: TestMetrics) -> ValidationResult:
        """Validate test results against expectations and baselines."""
        validation_id = f"validation_{uuid.uuid4().hex[:8]}"
        assertion_results = []
        passed = True
        recommendations = []
        
        try:
            # Run assertion checks
            for assertion in test_config.assertions:
                result = self._evaluate_assertion(assertion, metrics)
                assertion_results.append(result)
                if not result['passed']:
                    passed = False
            
            # Run validation rules
            for rule in self.validation_rules:
                try:
                    rule_result = rule(metrics)
                    if not rule_result['passed']:
                        passed = False
                    assertion_results.append(rule_result)
                    if 'recommendations' in rule_result:
                        recommendations.extend(rule_result['recommendations'])
                except Exception as e:
                    logger.error(f"Validation rule failed: {e}")
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(metrics)
            
            # Compare against baseline if available
            baseline_comparison = None
            baseline_key = f"{test_config.test_type.value}:{test_config.target_url}"
            if baseline_key in self.baselines:
                baseline_comparison = self._compare_against_baseline(
                    metrics, self.baselines[baseline_key]
                )
                if baseline_comparison['regression_detected']:
                    passed = False
                    recommendations.extend(baseline_comparison['recommendations'])
            
        except Exception as e:
            logger.error(f"Test validation failed: {e}")
            passed = False
            assertion_results.append({
                'assertion': 'validation_execution',
                'passed': False,
                'error': str(e)
            })
        
        return ValidationResult(
            validation_id=validation_id,
            test_id=test_config.test_id,
            passed=passed,
            assertion_results=assertion_results,
            performance_score=performance_score,
            baseline_comparison=baseline_comparison,
            recommendations=list(set(recommendations))  # Remove duplicates
        )
    
    def _evaluate_assertion(self, assertion: Dict[str, Any], metrics: TestMetrics) -> Dict[str, Any]:
        """Evaluate a single assertion."""
        try:
            metric_path = assertion['metric']
            operator = assertion['operator']
            expected_value = assertion['value']
            
            # Get actual value from metrics
            actual_value = self._get_metric_value(metrics, metric_path)
            
            # Evaluate assertion
            passed = self._apply_operator(actual_value, operator, expected_value)
            
            return {
                'assertion': assertion.get('name', metric_path),
                'metric': metric_path,
                'operator': operator,
                'expected': expected_value,
                'actual': actual_value,
                'passed': passed,
                'description': assertion.get('description', f"{metric_path} {operator} {expected_value}")
            }
            
        except Exception as e:
            return {
                'assertion': assertion.get('name', 'unknown'),
                'passed': False,
                'error': str(e)
            }
    
    def _get_metric_value(self, metrics: TestMetrics, metric_path: str) -> Any:
        """Get metric value by path (e.g., 'response_times.p95')."""
        obj = metrics
        for part in metric_path.split('.'):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                raise ValueError(f"Metric path '{metric_path}' not found")
        return obj
    
    def _apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Apply comparison operator."""
        operators = {
            'eq': lambda a, e: a == e,
            'ne': lambda a, e: a != e,
            'lt': lambda a, e: a < e,
            'le': lambda a, e: a <= e,
            'gt': lambda a, e: a > e,
            'ge': lambda a, e: a >= e,
            'contains': lambda a, e: e in a,
            'not_contains': lambda a, e: e not in a
        }
        
        if operator not in operators:
            raise ValueError(f"Unknown operator: {operator}")
        
        return operators[operator](actual, expected)
    
    def _validate_response_times(self, metrics: TestMetrics) -> Dict[str, Any]:
        """Validate response times are within acceptable ranges."""
        recommendations = []
        issues = []
        
        # Check if P95 response time is acceptable
        p95_threshold = 2000  # 2 seconds
        if metrics.response_times.get('p95', 0) > p95_threshold:
            issues.append(f"P95 response time ({metrics.response_times['p95']:.1f}ms) exceeds threshold ({p95_threshold}ms)")
            recommendations.append("Consider horizontal scaling to reduce response times")
            recommendations.append("Investigate potential bottlenecks in the application")
        
        # Check if mean response time is reasonable
        mean_threshold = 1000  # 1 second
        if metrics.response_times.get('mean', 0) > mean_threshold:
            issues.append(f"Mean response time ({metrics.response_times['mean']:.1f}ms) exceeds threshold ({mean_threshold}ms)")
            recommendations.append("Optimize application performance or increase resources")
        
        # Check response time distribution
        unacceptable_pct = (metrics.response_time_distribution.get(ResponseCategory.UNACCEPTABLE, 0) / 
                          max(metrics.total_requests, 1)) * 100
        
        if unacceptable_pct > 5:  # More than 5% unacceptable response times
            issues.append(f"{unacceptable_pct:.1f}% of requests had unacceptable response times (>5s)")
            recommendations.append("Investigate timeout issues and application performance")
        
        return {
            'rule': 'response_times',
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _validate_error_rate(self, metrics: TestMetrics) -> Dict[str, Any]:
        """Validate error rate is within acceptable limits."""
        recommendations = []
        issues = []
        
        error_rate_threshold = 1.0  # 1%
        
        if metrics.error_rate > error_rate_threshold:
            issues.append(f"Error rate ({metrics.error_rate:.2f}%) exceeds threshold ({error_rate_threshold}%)")
            recommendations.append("Investigate error causes and improve error handling")
            
            # Analyze error types
            if metrics.errors_by_type:
                most_common_error = max(metrics.errors_by_type.items(), key=lambda x: x[1])
                recommendations.append(f"Most common error: {most_common_error[0]} ({most_common_error[1]} occurrences)")
        
        return {
            'rule': 'error_rate',
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _validate_throughput(self, metrics: TestMetrics) -> Dict[str, Any]:
        """Validate throughput meets expectations."""
        recommendations = []
        issues = []
        
        # Basic throughput check - should handle reasonable load
        min_rps = 10  # Minimum 10 requests per second
        
        if metrics.requests_per_second < min_rps:
            issues.append(f"Throughput ({metrics.requests_per_second:.1f} RPS) is below minimum threshold ({min_rps} RPS)")
            recommendations.append("Consider performance optimizations or infrastructure scaling")
        
        return {
            'rule': 'throughput',
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _validate_resource_usage(self, metrics: TestMetrics) -> Dict[str, Any]:
        """Validate resource usage is reasonable."""
        recommendations = []
        issues = []
        
        # This would typically check CPU, memory, etc.
        # For now, just return success
        
        return {
            'rule': 'resource_usage',
            'passed': True,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _calculate_performance_score(self, metrics: TestMetrics) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0
        
        # Deduct points for high error rate
        if metrics.error_rate > 0:
            score -= min(50, metrics.error_rate * 10)  # Up to 50 points for errors
        
        # Deduct points for slow response times
        p95_penalty = max(0, (metrics.response_times.get('p95', 0) - 1000) / 100)  # Penalty after 1s
        score -= min(30, p95_penalty)  # Up to 30 points for slow response
        
        # Deduct points for poor response time distribution
        unacceptable_pct = (metrics.response_time_distribution.get(ResponseCategory.UNACCEPTABLE, 0) / 
                          max(metrics.total_requests, 1)) * 100
        score -= min(20, unacceptable_pct * 2)  # Up to 20 points for unacceptable responses
        
        return max(0.0, score)
    
    def _compare_against_baseline(self, current_metrics: TestMetrics, 
                                 baseline: PerformanceBaseline) -> Dict[str, Any]:
        """Compare current metrics against baseline."""
        comparison = {
            'baseline_id': baseline.baseline_id,
            'regression_detected': False,
            'improvements': [],
            'regressions': [],
            'recommendations': []
        }
        
        try:
            baseline_metrics = baseline.baseline_metrics
            
            # Compare key metrics
            metric_comparisons = [
                ('error_rate', current_metrics.error_rate, baseline_metrics.error_rate),
                ('p95_response_time', current_metrics.response_times.get('p95', 0), 
                 baseline_metrics.response_times.get('p95', 0)),
                ('requests_per_second', current_metrics.requests_per_second, baseline_metrics.requests_per_second),
                ('mean_response_time', current_metrics.response_times.get('mean', 0),
                 baseline_metrics.response_times.get('mean', 0))
            ]
            
            for metric_name, current_value, baseline_value in metric_comparisons:
                if baseline_value > 0:  # Avoid division by zero
                    change_pct = ((current_value - baseline_value) / baseline_value) * 100
                    acceptable_deviation = baseline.acceptable_deviation.get(metric_name, 10.0)  # Default 10%
                    
                    if abs(change_pct) > acceptable_deviation:
                        if change_pct > 0 and metric_name in ['error_rate', 'p95_response_time', 'mean_response_time']:
                            # Higher values are worse for these metrics
                            comparison['regressions'].append({
                                'metric': metric_name,
                                'change_pct': change_pct,
                                'current': current_value,
                                'baseline': baseline_value
                            })
                            comparison['regression_detected'] = True
                        elif change_pct < 0 and metric_name == 'requests_per_second':
                            # Lower throughput is worse
                            comparison['regressions'].append({
                                'metric': metric_name,
                                'change_pct': change_pct,
                                'current': current_value,
                                'baseline': baseline_value
                            })
                            comparison['regression_detected'] = True
                        else:
                            # Improvement
                            comparison['improvements'].append({
                                'metric': metric_name,
                                'change_pct': change_pct,
                                'current': current_value,
                                'baseline': baseline_value
                            })
            
            # Generate recommendations based on regressions
            if comparison['regression_detected']:
                comparison['recommendations'].append("Performance regression detected - investigate recent changes")
                if any(r['metric'] in ['p95_response_time', 'mean_response_time'] for r in comparison['regressions']):
                    comparison['recommendations'].append("Response time regression - check for resource constraints or code changes")
                if any(r['metric'] == 'error_rate' for r in comparison['regressions']):
                    comparison['recommendations'].append("Error rate regression - investigate error causes and stability")
                if any(r['metric'] == 'requests_per_second' for r in comparison['regressions']):
                    comparison['recommendations'].append("Throughput regression - check system capacity and bottlenecks")
        
        except Exception as e:
            logger.error(f"Baseline comparison failed: {e}")
            comparison['error'] = str(e)
        
        return comparison


class PerformanceTestSuite:
    """Comprehensive performance test suite manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.suite_id = f"suite_{uuid.uuid4().hex[:8]}"
        self.test_results: Dict[str, TestMetrics] = {}
        self.validation_results: Dict[str, ValidationResult] = {}
        
        self.validator = PerformanceValidator()
        
        # Test configurations
        self.test_configurations: Dict[str, TestConfiguration] = {}
        
        # Reporting
        self.reports_dir = Path(config.get('reports_dir', './performance_reports'))
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def add_test_configuration(self, test_config: TestConfiguration) -> None:
        """Add a test configuration to the suite."""
        self.test_configurations[test_config.test_id] = test_config
    
    def add_baseline(self, baseline: PerformanceBaseline) -> None:
        """Add a performance baseline."""
        self.validator.add_baseline(baseline)
    
    async def run_test(self, test_id: str) -> Tuple[TestMetrics, ValidationResult]:
        """Run a specific test."""
        if test_id not in self.test_configurations:
            raise ValueError(f"Test configuration '{test_id}' not found")
        
        test_config = self.test_configurations[test_id]
        
        logger.info(f"Running performance test: {test_config.name}")
        
        # Create load generator
        load_generator = LoadGenerator(test_config)
        
        # Run test
        metrics = await load_generator.run_test()
        self.test_results[test_id] = metrics
        
        # Validate results
        validation_result = self.validator.validate_test_results(test_config, metrics)
        self.validation_results[test_id] = validation_result
        
        # Generate report
        await self._generate_test_report(test_config, metrics, validation_result)
        
        return metrics, validation_result
    
    async def run_all_tests(self) -> Dict[str, Tuple[TestMetrics, ValidationResult]]:
        """Run all configured tests."""
        results = {}
        
        for test_id in self.test_configurations:
            try:
                metrics, validation = await self.run_test(test_id)
                results[test_id] = (metrics, validation)
            except Exception as e:
                logger.error(f"Test {test_id} failed: {e}")
                # Create dummy results for failed test
                results[test_id] = (None, ValidationResult(
                    validation_id=f"failed_{test_id}",
                    test_id=test_id,
                    passed=False,
                    assertion_results=[{'assertion': 'test_execution', 'passed': False, 'error': str(e)}],
                    performance_score=0.0
                ))
        
        # Generate suite report
        await self._generate_suite_report(results)
        
        return results
    
    async def _generate_test_report(self, test_config: TestConfiguration, 
                                  metrics: TestMetrics, validation: ValidationResult) -> None:
        """Generate individual test report."""
        try:
            report_data = {
                'test_configuration': {
                    'test_id': test_config.test_id,
                    'name': test_config.name,
                    'description': test_config.description,
                    'test_type': test_config.test_type.value,
                    'target_url': test_config.target_url,
                    'duration_seconds': test_config.duration_seconds,
                    'concurrent_users': test_config.concurrent_users,
                    'load_pattern': test_config.load_pattern.value,
                    'tags': list(test_config.tags)
                },
                'test_metrics': {
                    'start_time': metrics.start_time,
                    'end_time': metrics.end_time,
                    'duration_seconds': metrics.duration_seconds,
                    'total_requests': metrics.total_requests,
                    'successful_requests': metrics.successful_requests,
                    'failed_requests': metrics.failed_requests,
                    'requests_per_second': metrics.requests_per_second,
                    'response_times': metrics.response_times,
                    'response_time_distribution': {k.value: v for k, v in metrics.response_time_distribution.items()},
                    'error_rate': metrics.error_rate,
                    'throughput_mb_per_second': metrics.throughput_mb_per_second,
                    'errors_by_type': metrics.errors_by_type
                },
                'validation_result': {
                    'validation_id': validation.validation_id,
                    'passed': validation.passed,
                    'performance_score': validation.performance_score,
                    'assertion_results': validation.assertion_results,
                    'recommendations': validation.recommendations,
                    'baseline_comparison': validation.baseline_comparison
                },
                'generated_at': time.time()
            }
            
            # Write JSON report
            report_file = self.reports_dir / f"test_report_{test_config.test_id}_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Test report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")
    
    async def _generate_suite_report(self, results: Dict[str, Tuple[TestMetrics, ValidationResult]]) -> None:
        """Generate comprehensive suite report."""
        try:
            suite_summary = {
                'suite_id': self.suite_id,
                'generated_at': time.time(),
                'total_tests': len(results),
                'passed_tests': sum(1 for _, (_, v) in results.items() if v and v.passed),
                'failed_tests': sum(1 for _, (_, v) in results.items() if not v or not v.passed),
                'average_performance_score': statistics.mean([
                    v.performance_score for _, (_, v) in results.items() if v
                ]) if results else 0.0,
                'test_results': {}
            }
            
            # Add individual test summaries
            for test_id, (metrics, validation) in results.items():
                if metrics and validation:
                    suite_summary['test_results'][test_id] = {
                        'name': self.test_configurations[test_id].name,
                        'test_type': self.test_configurations[test_id].test_type.value,
                        'passed': validation.passed,
                        'performance_score': validation.performance_score,
                        'requests_per_second': metrics.requests_per_second,
                        'error_rate': metrics.error_rate,
                        'p95_response_time': metrics.response_times.get('p95', 0),
                        'recommendations_count': len(validation.recommendations)
                    }
                else:
                    suite_summary['test_results'][test_id] = {
                        'name': self.test_configurations.get(test_id, {}).name if self.test_configurations.get(test_id) else 'Unknown',
                        'test_type': 'unknown',
                        'passed': False,
                        'performance_score': 0.0,
                        'error': 'Test execution failed'
                    }
            
            # Write suite report
            suite_report_file = self.reports_dir / f"suite_report_{self.suite_id}_{int(time.time())}.json"
            with open(suite_report_file, 'w') as f:
                json.dump(suite_summary, f, indent=2)
            
            logger.info(f"Suite report generated: {suite_report_file}")
            
            # Log summary
            logger.info(f"Performance test suite completed: {suite_summary['passed_tests']}/{suite_summary['total_tests']} tests passed")
            logger.info(f"Average performance score: {suite_summary['average_performance_score']:.1f}/100")
            
        except Exception as e:
            logger.error(f"Failed to generate suite report: {e}")
    
    def create_baseline_from_test(self, test_id: str, acceptable_deviations: Optional[Dict[str, float]] = None) -> PerformanceBaseline:
        """Create a baseline from a successful test run."""
        if test_id not in self.test_results:
            raise ValueError(f"No test results found for test ID: {test_id}")
        
        if test_id not in self.validation_results or not self.validation_results[test_id].passed:
            raise ValueError(f"Cannot create baseline from failed test: {test_id}")
        
        test_config = self.test_configurations[test_id]
        metrics = self.test_results[test_id]
        
        baseline = PerformanceBaseline(
            baseline_id=f"baseline_{test_id}_{int(time.time())}",
            test_type=test_config.test_type,
            target_url=test_config.target_url,
            baseline_metrics=metrics,
            acceptable_deviation=acceptable_deviations or {
                'error_rate': 1.0,  # 1% increase acceptable
                'p95_response_time': 10.0,  # 10% increase acceptable
                'requests_per_second': 5.0,  # 5% decrease acceptable
                'mean_response_time': 15.0  # 15% increase acceptable
            },
            tags=test_config.tags
        )
        
        self.validator.add_baseline(baseline)
        logger.info(f"Created baseline {baseline.baseline_id} from test {test_id}")
        
        return baseline


# Global test suite instance
_test_suite: Optional[PerformanceTestSuite] = None


def get_performance_test_suite(config: Optional[Dict[str, Any]] = None) -> PerformanceTestSuite:
    """Get the global performance test suite instance."""
    global _test_suite
    if _test_suite is None:
        _test_suite = PerformanceTestSuite(config)
    return _test_suite


@asynccontextmanager
async def performance_test_context(test_config: TestConfiguration):
    """Context manager for performance testing."""
    suite = get_performance_test_suite()
    suite.add_test_configuration(test_config)
    
    try:
        metrics, validation = await suite.run_test(test_config.test_id)
        yield metrics, validation
    except Exception as e:
        logger.error(f"Performance test context error: {e}")
        raise
    finally:
        # Cleanup if needed
        pass