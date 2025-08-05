"""
Distributed processing architecture for Generation 3 scaling.

This module provides message queue integration, distributed task processing,
load balancing, and horizontal scaling capabilities for enterprise deployment.
"""

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task processing status."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    RETRY = auto()


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DistributedTask:
    """Distributed task representation."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "document_processing"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.name
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistributedTask':
        """Create task from dictionary."""
        task = cls()
        for key, value in data.items():
            if key == 'priority':
                task.priority = TaskPriority(value)
            elif key == 'status':
                task.status = TaskStatus[value]
            else:
                setattr(task, key, value)
        return task


@dataclass
class WorkerNode:
    """Distributed worker node information."""

    worker_id: str
    hostname: str
    port: int
    capabilities: Set[str] = field(default_factory=set)
    max_concurrent_tasks: int = 4
    current_tasks: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    status: str = "active"
    load_score: float = 0.0
    total_processed: int = 0
    total_failed: int = 0
    avg_processing_time: float = 0.0

    @property
    def is_available(self) -> bool:
        """Check if worker is available for new tasks."""
        return (
            self.status == "active" and
            self.current_tasks < self.max_concurrent_tasks and
            time.time() - self.last_heartbeat < 60  # 1 minute heartbeat timeout
        )

    @property
    def utilization(self) -> float:
        """Get worker utilization percentage."""
        return self.current_tasks / self.max_concurrent_tasks if self.max_concurrent_tasks > 0 else 0.0


class MessageQueue(ABC):
    """Abstract message queue interface."""

    @abstractmethod
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish message to queue."""
        pass

    @abstractmethod
    async def consume(self, queue_name: str, callback: Callable) -> None:
        """Consume messages from queue."""
        pass

    @abstractmethod
    async def ack_message(self, message_id: str) -> bool:
        """Acknowledge message processing."""
        pass

    @abstractmethod
    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge message."""
        pass


class InMemoryMessageQueue(MessageQueue):
    """In-memory message queue implementation for development/testing."""

    def __init__(self):
        self._queues: Dict[str, queue.Queue] = {}
        self._message_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._consumer_tasks: List[asyncio.Task] = []

    async def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish message to in-memory queue."""
        try:
            if queue_name not in self._queues:
                self._queues[queue_name] = queue.Queue()

            message_with_id = {
                'message_id': str(uuid.uuid4()),
                'timestamp': time.time(),
                'data': message
            }

            self._queues[queue_name].put(message_with_id)
            logger.debug(f"Published message to {queue_name}: {message_with_id['message_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            return False

    async def consume(self, queue_name: str, callback: Callable) -> None:
        """Start consuming messages from queue."""
        if queue_name not in self._queues:
            self._queues[queue_name] = queue.Queue()

        if queue_name not in self._message_callbacks:
            self._message_callbacks[queue_name] = []

        self._message_callbacks[queue_name].append(callback)

        # Start consumer task if not already running
        if not self._running:
            self._running = True
            task = asyncio.create_task(self._consumer_loop(queue_name))
            self._consumer_tasks.append(task)

    async def _consumer_loop(self, queue_name: str) -> None:
        """Consumer loop for processing messages."""
        while self._running:
            try:
                # Non-blocking get with timeout
                try:
                    message = self._queues[queue_name].get(timeout=1.0)
                except queue.Empty:
                    continue

                # Process message with all registered callbacks
                for callback in self._message_callbacks.get(queue_name, []):
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Callback failed for message {message.get('message_id')}: {e}")

            except Exception as e:
                logger.error(f"Consumer loop error for {queue_name}: {e}")
                await asyncio.sleep(1)

    async def ack_message(self, message_id: str) -> bool:
        """Acknowledge message (no-op for in-memory queue)."""
        logger.debug(f"ACK message: {message_id}")
        return True

    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge message (no-op for in-memory queue)."""
        logger.debug(f"NACK message: {message_id}, requeue: {requeue}")
        return True

    def shutdown(self) -> None:
        """Shutdown the message queue."""
        self._running = False
        for task in self._consumer_tasks:
            task.cancel()


class RedisMessageQueue(MessageQueue):
    """Redis-based message queue implementation."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self._initialize_redis()

    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis
            parsed_url = urlparse(self.redis_url)
            self.redis_client = redis.Redis(
                host=parsed_url.hostname or 'localhost',
                port=parsed_url.port or 6379,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except ImportError:
            logger.warning("Redis library not available, falling back to in-memory queue")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish message to Redis queue."""
        if not self.redis_client:
            return False

        try:
            message_with_id = {
                'message_id': str(uuid.uuid4()),
                'timestamp': time.time(),
                'data': message
            }

            # Use Redis list as queue
            self.redis_client.lpush(queue_name, json.dumps(message_with_id))
            logger.debug(f"Published message to Redis {queue_name}: {message_with_id['message_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message to Redis {queue_name}: {e}")
            return False

    async def consume(self, queue_name: str, callback: Callable) -> None:
        """Consume messages from Redis queue."""
        if not self.redis_client:
            return

        while True:
            try:
                # Blocking pop with timeout
                result = self.redis_client.brpop([queue_name], timeout=1)
                if result:
                    _, message_data = result
                    message = json.loads(message_data)
                    await callback(message)

            except Exception as e:
                logger.error(f"Redis consumer error for {queue_name}: {e}")
                await asyncio.sleep(1)

    async def ack_message(self, message_id: str) -> bool:
        """Acknowledge message (Redis lists don't need explicit ack)."""
        return True

    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge message."""
        # In Redis lists, we'd need to re-queue the message
        return True


class LoadBalancer:
    """Load balancer for distributing tasks across worker nodes."""

    def __init__(self):
        self.workers: Dict[str, WorkerNode] = {}
        self._lock = threading.RLock()

    def register_worker(self, worker: WorkerNode) -> None:
        """Register a new worker node."""
        with self._lock:
            self.workers[worker.worker_id] = worker
            logger.info(f"Registered worker {worker.worker_id} at {worker.hostname}:{worker.port}")

    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker node."""
        with self._lock:
            if worker_id in self.workers:
                del self.workers[worker_id]
                logger.info(f"Unregistered worker {worker_id}")

    def update_worker_heartbeat(self, worker_id: str) -> None:
        """Update worker heartbeat timestamp."""
        with self._lock:
            if worker_id in self.workers:
                self.workers[worker_id].last_heartbeat = time.time()

    def select_worker_round_robin(self) -> Optional[WorkerNode]:
        """Select worker using round-robin algorithm."""
        with self._lock:
            available_workers = [w for w in self.workers.values() if w.is_available]
            if not available_workers:
                return None

            # Simple round-robin based on total processed
            return min(available_workers, key=lambda w: w.total_processed)

    def select_worker_least_loaded(self) -> Optional[WorkerNode]:
        """Select worker with least load."""
        with self._lock:
            available_workers = [w for w in self.workers.values() if w.is_available]
            if not available_workers:
                return None

            # Select worker with lowest utilization
            return min(available_workers, key=lambda w: w.utilization)

    def select_worker_weighted(self, task: DistributedTask) -> Optional[WorkerNode]:
        """Select worker using weighted scoring based on task requirements."""
        with self._lock:
            available_workers = [w for w in self.workers.values() if w.is_available]
            if not available_workers:
                return None

            # Calculate scores based on multiple factors
            scored_workers = []
            for worker in available_workers:
                score = self._calculate_worker_score(worker, task)
                scored_workers.append((score, worker))

            # Select worker with highest score
            scored_workers.sort(key=lambda x: x[0], reverse=True)
            return scored_workers[0][1]

    def _calculate_worker_score(self, worker: WorkerNode, task: DistributedTask) -> float:
        """Calculate worker score for task assignment."""
        score = 0.0

        # Factor 1: Availability (0-1)
        availability_score = 1.0 - worker.utilization
        score += availability_score * 0.4

        # Factor 2: Performance history (0-1)
        if worker.total_processed > 0:
            success_rate = 1.0 - (worker.total_failed / worker.total_processed)
            score += success_rate * 0.3
        else:
            score += 0.5 * 0.3  # Neutral score for new workers

        # Factor 3: Processing speed (0-1)
        if worker.avg_processing_time > 0:
            # Invert time - lower is better
            speed_score = max(0, 1.0 - (worker.avg_processing_time / 300.0))  # 5 minutes max
            score += speed_score * 0.2
        else:
            score += 0.5 * 0.2  # Neutral score

        # Factor 4: Capability match (0-0.1)
        required_capabilities = set(task.metadata.get('required_capabilities', []))
        if required_capabilities.issubset(worker.capabilities):
            score += 0.1

        return score

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics."""
        with self._lock:
            active_workers = [w for w in self.workers.values() if w.status == "active"]
            available_workers = [w for w in active_workers if w.is_available]

            total_capacity = sum(w.max_concurrent_tasks for w in active_workers)
            current_load = sum(w.current_tasks for w in active_workers)

            return {
                'total_workers': len(self.workers),
                'active_workers': len(active_workers),
                'available_workers': len(available_workers),
                'total_capacity': total_capacity,
                'current_load': current_load,
                'utilization': current_load / total_capacity if total_capacity > 0 else 0.0,
                'average_processing_time': sum(w.avg_processing_time for w in active_workers) / len(active_workers) if active_workers else 0.0
            }


class TaskScheduler:
    """Task scheduling and distribution manager."""

    def __init__(self, message_queue: MessageQueue, load_balancer: LoadBalancer):
        self.message_queue = message_queue
        self.load_balancer = load_balancer
        self.pending_tasks: Dict[str, DistributedTask] = {}
        self.processing_tasks: Dict[str, DistributedTask] = {}
        self.completed_tasks: Dict[str, DistributedTask] = {}
        self._lock = threading.RLock()
        self._scheduler_running = False

    async def submit_task(self, task: DistributedTask) -> str:
        """Submit a task for distributed processing."""
        with self._lock:
            self.pending_tasks[task.task_id] = task

        # Publish task to message queue
        task_message = {
            'task_id': task.task_id,
            'task_data': task.to_dict()
        }

        queue_name = f"tasks_{task.priority.name.lower()}"
        success = await self.message_queue.publish(queue_name, task_message)

        if success:
            logger.info(f"Task {task.task_id} submitted to queue {queue_name}")
        else:
            logger.error(f"Failed to submit task {task.task_id}")

        return task.task_id

    async def start_scheduler(self) -> None:
        """Start the task scheduler."""
        if self._scheduler_running:
            return

        self._scheduler_running = True

        # Start consuming from priority queues
        priority_queues = [
            f"tasks_{priority.name.lower()}"
            for priority in TaskPriority
        ]

        for queue_name in priority_queues:
            await self.message_queue.consume(queue_name, self._handle_task_message)

        logger.info("Task scheduler started")

    async def _handle_task_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming task message."""
        try:
            task_id = message['data']['task_id']
            task_data = message['data']['task_data']

            # Reconstruct task
            task = DistributedTask.from_dict(task_data)

            # Select worker for task
            worker = self.load_balancer.select_worker_weighted(task)
            if not worker:
                logger.warning(f"No available workers for task {task_id}, requeueing")
                await self.message_queue.nack_message(message['message_id'], requeue=True)
                return

            # Assign task to worker
            await self._assign_task_to_worker(task, worker)
            await self.message_queue.ack_message(message['message_id'])

        except Exception as e:
            logger.error(f"Failed to handle task message: {e}")
            await self.message_queue.nack_message(message['message_id'], requeue=True)

    async def _assign_task_to_worker(self, task: DistributedTask, worker: WorkerNode) -> None:
        """Assign task to specific worker."""
        task.worker_id = worker.worker_id
        task.status = TaskStatus.PROCESSING
        task.started_at = time.time()

        with self._lock:
            # Move task from pending to processing
            if task.task_id in self.pending_tasks:
                del self.pending_tasks[task.task_id]
            self.processing_tasks[task.task_id] = task

        # Update worker state
        worker.current_tasks += 1

        # Send task to worker (this would be actual network communication)
        await self._send_task_to_worker(task, worker)

        logger.info(f"Assigned task {task.task_id} to worker {worker.worker_id}")

    async def _send_task_to_worker(self, task: DistributedTask, worker: WorkerNode) -> None:
        """Send task to worker node (placeholder for actual implementation)."""
        # This would be replaced with actual network communication
        # e.g., HTTP API call, gRPC, or message queue specific to the worker

        # For now, simulate task processing
        processing_time = 1.0  # Simulate 1 second processing
        await asyncio.sleep(processing_time)

        # Simulate task completion
        await self._handle_task_completion(task.task_id, {
            'success': True,
            'processing_time': processing_time,
            'result': f"Processed by worker {worker.worker_id}"
        })

    async def _handle_task_completion(self, task_id: str, result: Dict[str, Any]) -> None:
        """Handle task completion from worker."""
        with self._lock:
            if task_id not in self.processing_tasks:
                logger.warning(f"Received completion for unknown task {task_id}")
                return

            task = self.processing_tasks[task_id]
            task.completed_at = time.time()
            task.result = result

            if result.get('success', False):
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get('error', 'Unknown error')

            # Move task to completed
            del self.processing_tasks[task_id]
            self.completed_tasks[task_id] = task

            # Update worker state
            if task.worker_id:
                worker = self.load_balancer.workers.get(task.worker_id)
                if worker:
                    worker.current_tasks = max(0, worker.current_tasks - 1)
                    worker.total_processed += 1
                    if task.status == TaskStatus.FAILED:
                        worker.total_failed += 1

                    # Update average processing time
                    if task.started_at and task.completed_at:
                        processing_time = task.completed_at - task.started_at
                        if worker.avg_processing_time == 0:
                            worker.avg_processing_time = processing_time
                        else:
                            # Exponential moving average
                            worker.avg_processing_time = (
                                0.8 * worker.avg_processing_time + 0.2 * processing_time
                            )

        logger.info(f"Task {task_id} completed with status {task.status.name}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        with self._lock:
            task = None
            location = None

            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                location = "pending"
            elif task_id in self.processing_tasks:
                task = self.processing_tasks[task_id]
                location = "processing"
            elif task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                location = "completed"

            if task:
                return {
                    'task_id': task_id,
                    'status': task.status.name,
                    'location': location,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'worker_id': task.worker_id,
                    'retry_count': task.retry_count,
                    'result': task.result,
                    'error': task.error
                }

            return None

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        with self._lock:
            return {
                'pending_tasks': len(self.pending_tasks),
                'processing_tasks': len(self.processing_tasks),
                'completed_tasks': len(self.completed_tasks),
                'cluster_stats': self.load_balancer.get_cluster_stats()
            }


class DistributedProcessingManager:
    """Main manager for distributed processing system."""

    def __init__(self, message_queue_url: Optional[str] = None):
        # Initialize message queue
        if message_queue_url and message_queue_url.startswith('redis://'):
            self.message_queue = RedisMessageQueue(message_queue_url)
        else:
            self.message_queue = InMemoryMessageQueue()

        self.load_balancer = LoadBalancer()
        self.task_scheduler = TaskScheduler(self.message_queue, self.load_balancer)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the distributed processing system."""
        if self._initialized:
            return

        await self.task_scheduler.start_scheduler()
        self._initialized = True
        logger.info("Distributed processing system initialized")

    async def process_document_distributed(
        self,
        file_path: Path,
        priority: TaskPriority = TaskPriority.NORMAL,
        required_capabilities: Optional[List[str]] = None
    ) -> str:
        """Process document using distributed system."""
        if not self._initialized:
            await self.initialize()

        # Create distributed task
        task = DistributedTask(
            task_type="document_processing",
            payload={
                'file_path': str(file_path),
                'processing_options': {}
            },
            priority=priority,
            metadata={
                'required_capabilities': required_capabilities or [],
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }
        )

        # Submit task
        task_id = await self.task_scheduler.submit_task(task)
        return task_id

    async def wait_for_task(self, task_id: str, timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        """Wait for task completion."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.task_scheduler.get_task_status(task_id)
            if status and status['status'] in ['COMPLETED', 'FAILED']:
                return status

            await asyncio.sleep(1.0)

        return None  # Timeout

    def add_worker_node(self, hostname: str, port: int, capabilities: Optional[List[str]] = None) -> str:
        """Add a worker node to the cluster."""
        worker_id = f"{hostname}:{port}"
        worker = WorkerNode(
            worker_id=worker_id,
            hostname=hostname,
            port=port,
            capabilities=set(capabilities or [])
        )

        self.load_balancer.register_worker(worker)
        return worker_id

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'initialized': self._initialized,
            'scheduler_stats': self.task_scheduler.get_scheduler_stats(),
            'message_queue_type': type(self.message_queue).__name__,
            'timestamp': time.time()
        }


# Global distributed processing manager
_distributed_manager: Optional[DistributedProcessingManager] = None


def get_distributed_manager(message_queue_url: Optional[str] = None) -> DistributedProcessingManager:
    """Get global distributed processing manager."""
    global _distributed_manager

    if _distributed_manager is None:
        _distributed_manager = DistributedProcessingManager(message_queue_url)

    return _distributed_manager
