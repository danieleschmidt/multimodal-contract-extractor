"""
Load Balancing and Request Orchestration for Generation 3: Scale
Intelligent request distribution and resource management.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import queue
import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    CONSISTENT_HASHING = "consistent_hashing"
    ADAPTIVE = "adaptive"


class WorkerStatus(Enum):
    """Worker status states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class WorkerMetrics:
    """Metrics for a worker instance."""
    worker_id: str
    active_requests: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_response_time: float = 0.0
    last_response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    status: WorkerStatus = WorkerStatus.HEALTHY
    weight: float = 1.0
    last_health_check: float = field(default_factory=time.time)
    queue_size: int = 0

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return self.total_errors / max(1, self.total_requests)

    @property
    def load_score(self) -> float:
        """Calculate overall load score (0-1, lower is better)."""
        # Combine multiple factors
        connection_load = min(1.0, self.active_requests / 10.0)
        cpu_load = self.cpu_usage / 100.0
        memory_load = self.memory_usage / 100.0
        response_time_load = min(1.0, self.avg_response_time / 10.0)  # Normalize to 10s max
        error_load = min(1.0, self.error_rate * 10)  # Error rate penalty
        queue_load = min(1.0, self.queue_size / 100.0)

        return (connection_load + cpu_load + memory_load + response_time_load + error_load + queue_load) / 6.0


@dataclass
class Request:
    """Request object for load balancing."""
    request_id: str = field(default_factory=lambda: f"req_{int(time.time()*1000000)}")
    client_id: Optional[str] = None
    priority: int = 1  # 1 = low, 5 = high
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    assigned_worker: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def age(self) -> float:
        """Get request age in seconds."""
        return time.time() - self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if request has expired."""
        return self.age > self.timeout


class Worker(ABC):
    """Abstract worker interface."""

    def __init__(self, worker_id: str, weight: float = 1.0):
        self.worker_id = worker_id
        self.metrics = WorkerMetrics(worker_id=worker_id, weight=weight)
        self._active_requests: Set[str] = set()
        self._lock = threading.Lock()

    @abstractmethod
    async def process_request(self, request: Request) -> Any:
        """Process a request. Must be implemented by subclasses."""
        pass

    async def health_check(self) -> WorkerStatus:
        """Perform health check. Can be overridden by subclasses."""
        try:
            # Simple health check - can be overridden for more complex checks
            current_time = time.time()
            if current_time - self.metrics.last_health_check > 60:  # Check every minute
                self.metrics.last_health_check = current_time

                # Determine status based on load and error rate
                if self.metrics.error_rate > 0.1:  # More than 10% errors
                    self.metrics.status = WorkerStatus.UNHEALTHY
                elif self.metrics.load_score > 0.9:  # Very high load
                    self.metrics.status = WorkerStatus.OVERLOADED
                elif self.metrics.load_score > 0.7:  # High load
                    self.metrics.status = WorkerStatus.DEGRADED
                else:
                    self.metrics.status = WorkerStatus.HEALTHY

            return self.metrics.status

        except Exception as e:
            logger.error(f"Health check failed for worker {self.worker_id}: {e}")
            self.metrics.status = WorkerStatus.UNHEALTHY
            return WorkerStatus.UNHEALTHY

    async def execute_request(self, request: Request) -> Any:
        """Execute request with metrics tracking."""
        start_time = time.time()

        with self._lock:
            self._active_requests.add(request.request_id)
            self.metrics.active_requests = len(self._active_requests)
            self.metrics.total_requests += 1

        request.assigned_worker = self.worker_id
        request.started_at = start_time

        try:
            result = await self.process_request(request)
            request.completed_at = time.time()

            # Update metrics
            response_time = request.completed_at - start_time
            self.metrics.last_response_time = response_time

            # Update average response time (exponential moving average)
            alpha = 0.1  # Smoothing factor
            self.metrics.avg_response_time = (
                alpha * response_time +
                (1 - alpha) * self.metrics.avg_response_time
            )

            return result

        except Exception as e:
            self.metrics.total_errors += 1
            logger.error(f"Request {request.request_id} failed on worker {self.worker_id}: {e}")
            raise

        finally:
            with self._lock:
                self._active_requests.discard(request.request_id)
                self.metrics.active_requests = len(self._active_requests)


class ProcessingWorker(Worker):
    """Concrete worker implementation for document processing."""

    def __init__(self, worker_id: str, weight: float = 1.0, max_concurrent: int = 5):
        super().__init__(worker_id, weight)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_request(self, request: Request) -> Any:
        """Process document extraction request."""
        async with self.semaphore:
            # Simulate processing time based on request metadata
            file_size = request.metadata.get('file_size', 1000000)  # Default 1MB
            processing_time = min(10.0, file_size / 1000000)  # Max 10s

            # Add some realistic variance
            processing_time *= random.uniform(0.8, 1.2)

            await asyncio.sleep(processing_time)

            # Simulate potential errors
            if random.random() < 0.05:  # 5% error rate
                raise Exception("Simulated processing error")

            return {
                "request_id": request.request_id,
                "worker_id": self.worker_id,
                "processing_time": processing_time,
                "result": "Document processed successfully"
            }


class LoadBalancer:
    """Main load balancing orchestrator."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE):
        self.strategy = strategy
        self.workers: Dict[str, Worker] = {}
        self.request_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_requests: Dict[str, Request] = {}
        self._round_robin_index = 0
        self._lock = threading.RLock()
        self._health_check_interval = 30  # seconds
        self._last_health_check = 0

        # Consistent hashing ring for CONSISTENT_HASHING strategy
        self._hash_ring: List[Tuple[int, str]] = []
        self._ring_size = 256

    def add_worker(self, worker: Worker):
        """Add a worker to the load balancer."""
        with self._lock:
            self.workers[worker.worker_id] = worker
            if self.strategy == LoadBalancingStrategy.CONSISTENT_HASHING:
                self._rebuild_hash_ring()
        logger.info(f"Added worker {worker.worker_id}")

    def remove_worker(self, worker_id: str):
        """Remove a worker from the load balancer."""
        with self._lock:
            if worker_id in self.workers:
                del self.workers[worker_id]
                if self.strategy == LoadBalancingStrategy.CONSISTENT_HASHING:
                    self._rebuild_hash_ring()
        logger.info(f"Removed worker {worker_id}")

    def _rebuild_hash_ring(self):
        """Rebuild consistent hashing ring."""
        self._hash_ring.clear()

        for worker_id in self.workers:
            # Create multiple virtual nodes for better distribution
            virtual_nodes = max(1, int(self.workers[worker_id].metrics.weight * 10))

            for i in range(virtual_nodes):
                node_key = f"{worker_id}:{i}"
                hash_value = int(hashlib.md5(node_key.encode()).hexdigest(), 16) % (2**32)
                self._hash_ring.append((hash_value, worker_id))

        self._hash_ring.sort()

    async def _health_check_workers(self):
        """Perform health checks on all workers."""
        current_time = time.time()
        if current_time - self._last_health_check < self._health_check_interval:
            return

        self._last_health_check = current_time

        health_check_tasks = []
        for worker in self.workers.values():
            health_check_tasks.append(worker.health_check())

        await asyncio.gather(*health_check_tasks, return_exceptions=True)

    def _get_healthy_workers(self) -> List[Worker]:
        """Get list of healthy workers."""
        return [
            worker for worker in self.workers.values()
            if worker.metrics.status in [WorkerStatus.HEALTHY, WorkerStatus.DEGRADED]
        ]

    def _select_worker_round_robin(self) -> Optional[Worker]:
        """Select worker using round-robin strategy."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        with self._lock:
            worker = healthy_workers[self._round_robin_index % len(healthy_workers)]
            self._round_robin_index = (self._round_robin_index + 1) % len(healthy_workers)
            return worker

    def _select_worker_least_connections(self) -> Optional[Worker]:
        """Select worker with least active connections."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        return min(healthy_workers, key=lambda w: w.metrics.active_requests)

    def _select_worker_weighted_round_robin(self) -> Optional[Worker]:
        """Select worker using weighted round-robin."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        # Create weighted list
        weighted_workers = []
        for worker in healthy_workers:
            weight = max(1, int(worker.metrics.weight * 10))
            weighted_workers.extend([worker] * weight)

        if not weighted_workers:
            return None

        with self._lock:
            worker = weighted_workers[self._round_robin_index % len(weighted_workers)]
            self._round_robin_index = (self._round_robin_index + 1) % len(weighted_workers)
            return worker

    def _select_worker_least_response_time(self) -> Optional[Worker]:
        """Select worker with lowest average response time."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        return min(healthy_workers, key=lambda w: w.metrics.avg_response_time)

    def _select_worker_random(self) -> Optional[Worker]:
        """Select random healthy worker."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        return random.choice(healthy_workers)

    def _select_worker_consistent_hashing(self, request: Request) -> Optional[Worker]:
        """Select worker using consistent hashing."""
        if not self._hash_ring:
            return None

        # Generate hash for request (using client_id or request_id)
        hash_key = request.client_id or request.request_id
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16) % (2**32)

        # Find first worker in ring after hash value
        for ring_hash, worker_id in self._hash_ring:
            if ring_hash >= hash_value:
                worker = self.workers.get(worker_id)
                if worker and worker.metrics.status in [WorkerStatus.HEALTHY, WorkerStatus.DEGRADED]:
                    return worker

        # If no worker found after hash, use first worker in ring
        if self._hash_ring:
            worker_id = self._hash_ring[0][1]
            worker = self.workers.get(worker_id)
            if worker and worker.metrics.status in [WorkerStatus.HEALTHY, WorkerStatus.DEGRADED]:
                return worker

        return None

    def _select_worker_adaptive(self) -> Optional[Worker]:
        """Select worker using adaptive strategy based on current conditions."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            return None

        # Use load score to select best worker
        return min(healthy_workers, key=lambda w: w.metrics.load_score)

    def select_worker(self, request: Request) -> Optional[Worker]:
        """Select appropriate worker based on current strategy."""
        strategy_methods = {
            LoadBalancingStrategy.ROUND_ROBIN: self._select_worker_round_robin,
            LoadBalancingStrategy.LEAST_CONNECTIONS: self._select_worker_least_connections,
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: self._select_worker_weighted_round_robin,
            LoadBalancingStrategy.LEAST_RESPONSE_TIME: self._select_worker_least_response_time,
            LoadBalancingStrategy.RANDOM: self._select_worker_random,
            LoadBalancingStrategy.CONSISTENT_HASHING: lambda: self._select_worker_consistent_hashing(request),
            LoadBalancingStrategy.ADAPTIVE: self._select_worker_adaptive
        }

        method = strategy_methods.get(self.strategy)
        if method:
            return method()

        # Fallback to round-robin
        return self._select_worker_round_robin()

    async def process_request(self, request: Request) -> Any:
        """Process a request using load balancing."""
        await self._health_check_workers()

        # Check if request has expired
        if request.is_expired:
            raise Exception(f"Request {request.request_id} expired (age: {request.age:.1f}s)")

        # Select worker
        worker = self.select_worker(request)
        if not worker:
            raise Exception("No healthy workers available")

        # Track active request
        self.active_requests[request.request_id] = request

        try:
            result = await worker.execute_request(request)
            return result

        finally:
            # Clean up
            self.active_requests.pop(request.request_id, None)

    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get comprehensive load balancer statistics."""
        with self._lock:
            worker_stats = {}
            total_requests = 0
            total_errors = 0
            healthy_workers = 0

            for worker_id, worker in self.workers.items():
                metrics = worker.metrics
                worker_stats[worker_id] = {
                    "status": metrics.status.value,
                    "active_requests": metrics.active_requests,
                    "total_requests": metrics.total_requests,
                    "total_errors": metrics.total_errors,
                    "error_rate": metrics.error_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "load_score": metrics.load_score,
                    "weight": metrics.weight
                }

                total_requests += metrics.total_requests
                total_errors += metrics.total_errors

                if metrics.status in [WorkerStatus.HEALTHY, WorkerStatus.DEGRADED]:
                    healthy_workers += 1

            return {
                "strategy": self.strategy.value,
                "total_workers": len(self.workers),
                "healthy_workers": healthy_workers,
                "active_requests": len(self.active_requests),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_error_rate": total_errors / max(1, total_requests),
                "workers": worker_stats
            }


class RequestOrchestrator:
    """High-level request orchestrator with queue management."""

    def __init__(self, load_balancer: LoadBalancer, max_queue_size: int = 1000):
        self.load_balancer = load_balancer
        self.max_queue_size = max_queue_size
        self.request_queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._worker_tasks: List[asyncio.Task] = []
        self._stats_lock = threading.Lock()

    async def start_workers(self, num_workers: int = 5):
        """Start background worker tasks."""
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(f"orchestrator_worker_{i}"))
            self._worker_tasks.append(task)
        logger.info(f"Started {num_workers} orchestrator workers")

    async def stop_workers(self):
        """Stop background worker tasks."""
        self._shutdown_event.set()

        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()
        logger.info("Stopped orchestrator workers")

    async def _worker_loop(self, worker_name: str):
        """Background worker loop for processing requests."""
        logger.info(f"Started orchestrator worker: {worker_name}")

        while not self._shutdown_event.is_set():
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=1.0
                )

                # Process request
                try:
                    result = await self.load_balancer.process_request(request)
                    logger.debug(f"Request {request.request_id} processed successfully by {worker_name}")

                except Exception as e:
                    logger.error(f"Request {request.request_id} failed in {worker_name}: {e}")

                finally:
                    self.request_queue.task_done()

            except asyncio.TimeoutError:
                # No request available, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop

        logger.info(f"Stopped orchestrator worker: {worker_name}")

    async def submit_request(self, request: Request) -> bool:
        """Submit request to processing queue."""
        try:
            await self.request_queue.put(request)
            logger.debug(f"Request {request.request_id} queued for processing")
            return True
        except asyncio.QueueFull:
            logger.warning(f"Request queue full, rejecting request {request.request_id}")
            return False

    async def submit_and_wait(self, request: Request, timeout: float = 30.0) -> Any:
        """Submit request and wait for result."""
        # For immediate processing without queue
        return await self.load_balancer.process_request(request)

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "queue_size": self.request_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "active_workers": len([t for t in self._worker_tasks if not t.done()]),
            "load_balancer": self.load_balancer.get_load_balancer_stats()
        }


# Global orchestrator instance
_orchestrator: Optional[RequestOrchestrator] = None


async def get_orchestrator() -> RequestOrchestrator:
    """Get global request orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        # Initialize with default configuration
        load_balancer = LoadBalancer(strategy=LoadBalancingStrategy.ADAPTIVE)

        # Add some default workers
        for i in range(3):
            worker = ProcessingWorker(f"worker_{i}", weight=1.0)
            load_balancer.add_worker(worker)

        _orchestrator = RequestOrchestrator(load_balancer)
        await _orchestrator.start_workers(num_workers=3)

    return _orchestrator


async def process_request_optimized(request_data: Dict[str, Any], client_id: Optional[str] = None, priority: int = 1) -> Any:
    """High-level function for optimized request processing."""
    orchestrator = await get_orchestrator()

    request = Request(
        client_id=client_id,
        priority=priority,
        metadata=request_data
    )

    return await orchestrator.submit_and_wait(request)
