"""Distributed Computing Engine for Large-Scale Contract Processing.

This module implements distributed computing capabilities including
cluster management, load balancing, fault tolerance, and horizontal
scaling for processing large volumes of contract documents.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Node roles in distributed cluster."""

    COORDINATOR = "coordinator"
    WORKER = "worker"
    HYBRID = "hybrid"


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class NodeStatus(Enum):
    """Node health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class Task:
    """Distributed task representation."""

    task_id: str
    task_type: str
    data: Dict[str, Any]
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_node: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Get task execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def is_expired(self, timeout: float = 3600.0) -> bool:
        """Check if task has expired."""
        return time.time() - self.created_at > timeout


@dataclass
class ClusterNode:
    """Cluster node information."""

    node_id: str
    role: NodeRole
    host: str
    port: int
    capabilities: Set[str] = field(default_factory=set)
    max_concurrent_tasks: int = 4
    current_tasks: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    status: NodeStatus = NodeStatus.HEALTHY
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0

    @property
    def utilization(self) -> float:
        """Get node utilization percentage."""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return self.current_tasks / self.max_concurrent_tasks

    @property
    def is_available(self) -> bool:
        """Check if node is available for new tasks."""
        return (self.status == NodeStatus.HEALTHY and
                self.current_tasks < self.max_concurrent_tasks)

    @property
    def is_alive(self, heartbeat_timeout: float = 30.0) -> bool:
        """Check if node is alive based on heartbeat."""
        return time.time() - self.last_heartbeat < heartbeat_timeout


class LoadBalancer:
    """Load balancer for distributing tasks across cluster nodes."""

    def __init__(self):
        self.strategies = {
            "round_robin": self._round_robin,
            "least_loaded": self._least_loaded,
            "weighted": self._weighted_selection,
            "capability_aware": self._capability_aware
        }
        self.current_strategy = "least_loaded"
        self._round_robin_index = 0

    def select_node(
        self,
        nodes: List[ClusterNode],
        task: Task,
        strategy: Optional[str] = None
    ) -> Optional[ClusterNode]:
        """Select optimal node for task execution."""
        # Filter available nodes
        available_nodes = [node for node in nodes if node.is_available]

        if not available_nodes:
            return None

        # Filter by capabilities if task has requirements
        if hasattr(task, 'required_capabilities') and task.required_capabilities:
            capable_nodes = [
                node for node in available_nodes
                if task.required_capabilities.issubset(node.capabilities)
            ]
            if capable_nodes:
                available_nodes = capable_nodes

        # Apply load balancing strategy
        strategy_name = strategy or self.current_strategy
        if strategy_name in self.strategies:
            return self.strategies[strategy_name](available_nodes, task)
        else:
            return self._least_loaded(available_nodes, task)

    def _round_robin(self, nodes: List[ClusterNode], task: Task) -> ClusterNode:
        """Round-robin load balancing."""
        if not nodes:
            return None

        node = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index += 1
        return node

    def _least_loaded(self, nodes: List[ClusterNode], task: Task) -> ClusterNode:
        """Select least loaded node."""
        return min(nodes, key=lambda n: n.utilization)

    def _weighted_selection(self, nodes: List[ClusterNode], task: Task) -> ClusterNode:
        """Weighted selection based on node performance."""
        # Calculate weights based on inverse utilization and success rate
        weights = []
        for node in nodes:
            success_rate = (
                node.total_tasks_completed /
                max(1, node.total_tasks_completed + node.total_tasks_failed)
            )
            weight = (1.0 - node.utilization) * success_rate
            weights.append(weight)

        if not weights:
            return nodes[0]

        # Select node based on weights
        total_weight = sum(weights)
        if total_weight == 0:
            return self._least_loaded(nodes, task)

        import random
        threshold = random.uniform(0, total_weight)
        cumulative = 0

        for i, weight in enumerate(weights):
            cumulative += weight
            if cumulative >= threshold:
                return nodes[i]

        return nodes[-1]

    def _capability_aware(self, nodes: List[ClusterNode], task: Task) -> ClusterNode:
        """Select node based on capabilities and specialization."""
        # For now, just use least loaded among capable nodes
        return self._least_loaded(nodes, task)


class TaskQueue:
    """Distributed task queue with priority and persistence."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.pending_queue: List[str] = []  # Task IDs sorted by priority
        self.assigned_tasks: Dict[str, str] = {}  # task_id -> node_id
        self.completed_tasks: Dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        """Add task to queue."""
        self.tasks[task.task_id] = task

        # Insert in priority order (higher priority first)
        inserted = False
        for i, task_id in enumerate(self.pending_queue):
            if task.priority > self.tasks[task_id].priority:
                self.pending_queue.insert(i, task.task_id)
                inserted = True
                break

        if not inserted:
            self.pending_queue.append(task.task_id)

        logger.debug("Added task %s with priority %d", task.task_id, task.priority)

    def get_next_task(self, node_capabilities: Set[str] = None) -> Optional[Task]:
        """Get next available task for execution."""
        for i, task_id in enumerate(self.pending_queue):
            task = self.tasks.get(task_id)

            if not task or task.status != TaskStatus.PENDING:
                # Remove invalid task from queue
                self.pending_queue.pop(i)
                continue

            # Check capabilities if specified
            if (node_capabilities and
                hasattr(task, 'required_capabilities') and
                task.required_capabilities and
                not task.required_capabilities.issubset(node_capabilities)):
                continue

            # Remove from pending queue and return
            self.pending_queue.pop(i)
            return task

        return None

    def assign_task(self, task_id: str, node_id: str) -> bool:
        """Assign task to a node."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task.status != TaskStatus.PENDING:
            return False

        task.status = TaskStatus.ASSIGNED
        task.assigned_node = node_id
        task.assigned_at = time.time()
        self.assigned_tasks[task_id] = node_id

        logger.debug("Assigned task %s to node %s", task_id, node_id)
        return True

    def start_task(self, task_id: str) -> bool:
        """Mark task as started."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        logger.debug("Started task %s", task_id)
        return True

    def complete_task(self, task_id: str, result: Any = None, error: str = None) -> bool:
        """Mark task as completed."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.completed_at = time.time()
        task.result = result
        task.error = error
        task.status = TaskStatus.COMPLETED if error is None else TaskStatus.FAILED

        # Move to completed tasks
        self.completed_tasks[task_id] = task

        # Remove from assigned tasks
        if task_id in self.assigned_tasks:
            del self.assigned_tasks[task_id]

        logger.debug("Completed task %s with status %s", task_id, task.status.value)
        return True

    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if task.retry_count >= task.max_retries:
            logger.warning("Task %s exceeded max retries", task_id)
            return False

        task.retry_count += 1
        task.status = TaskStatus.PENDING
        task.assigned_node = None
        task.assigned_at = None
        task.started_at = None
        task.error = None

        # Re-add to pending queue
        self.add_task(task)

        logger.info("Retrying task %s (attempt %d)", task_id, task.retry_count + 1)
        return True

    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        status_counts = {}
        for task in self.tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

        return {
            "total_tasks": len(self.tasks),
            "pending": len(self.pending_queue),
            "assigned": len(self.assigned_tasks),
            "completed": len(self.completed_tasks),
            "status_breakdown": status_counts
        }


class ClusterCoordinator:
    """Cluster coordinator for managing distributed processing."""

    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"coordinator_{uuid.uuid4().hex[:8]}"
        self.nodes: Dict[str, ClusterNode] = {}
        self.task_queue = TaskQueue()
        self.load_balancer = LoadBalancer()
        self.running = False

        # Performance tracking
        self.cluster_stats = {
            "tasks_processed": 0,
            "total_processing_time": 0.0,
            "average_task_time": 0.0,
            "node_failures": 0,
            "task_failures": 0
        }

    def register_node(self, node: ClusterNode) -> bool:
        """Register a new node in the cluster."""
        if node.node_id in self.nodes:
            logger.warning("Node %s already registered", node.node_id)
            return False

        self.nodes[node.node_id] = node
        logger.info("Registered node %s with role %s", node.node_id, node.role.value)
        return True

    def unregister_node(self, node_id: str) -> bool:
        """Unregister a node from the cluster."""
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]

        # Reassign any tasks assigned to this node
        self._reassign_node_tasks(node_id)

        del self.nodes[node_id]
        logger.info("Unregistered node %s", node_id)
        return True

    def _reassign_node_tasks(self, failed_node_id: str) -> None:
        """Reassign tasks from a failed node."""
        reassigned_count = 0

        for task_id, assigned_node in list(self.task_queue.assigned_tasks.items()):
            if assigned_node == failed_node_id:
                task = self.task_queue.tasks.get(task_id)
                if task and task.status in [TaskStatus.ASSIGNED, TaskStatus.RUNNING]:
                    # Reset task for reassignment
                    if self.task_queue.retry_task(task_id):
                        reassigned_count += 1

        if reassigned_count > 0:
            logger.info("Reassigned %d tasks from failed node %s",
                       reassigned_count, failed_node_id)
            self.cluster_stats["node_failures"] += 1

    def submit_task(self, task: Task) -> str:
        """Submit task for distributed processing."""
        self.task_queue.add_task(task)
        logger.debug("Submitted task %s for processing", task.task_id)
        return task.task_id

    async def process_tasks(self) -> None:
        """Main task processing loop."""
        self.running = True
        logger.info("Started cluster coordinator %s", self.node_id)

        while self.running:
            try:
                # Health check nodes
                await self._health_check_nodes()

                # Assign tasks to available nodes
                await self._assign_pending_tasks()

                # Check for completed tasks
                await self._collect_task_results()

                # Clean up expired tasks
                self._cleanup_expired_tasks()

                # Update statistics
                self._update_statistics()

                # Short delay before next iteration
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error("Error in task processing loop: %s", e)
                await asyncio.sleep(5.0)

    async def _health_check_nodes(self) -> None:
        """Perform health checks on cluster nodes."""
        current_time = time.time()

        for node_id, node in list(self.nodes.items()):
            # Check heartbeat
            if not node.is_alive():
                logger.warning("Node %s appears to be offline", node_id)
                node.status = NodeStatus.OFFLINE
                self._reassign_node_tasks(node_id)

            # Update node status based on resource usage
            elif node.cpu_usage > 90 or node.memory_usage > 90:
                node.status = NodeStatus.DEGRADED
            else:
                node.status = NodeStatus.HEALTHY

    async def _assign_pending_tasks(self) -> None:
        """Assign pending tasks to available nodes."""
        while True:
            # Get available nodes
            available_nodes = [
                node for node in self.nodes.values()
                if node.is_available
            ]

            if not available_nodes:
                break

            # Get next task
            task = self.task_queue.get_next_task()
            if not task:
                break

            # Select optimal node
            selected_node = self.load_balancer.select_node(available_nodes, task)
            if not selected_node:
                # Put task back in queue
                self.task_queue.add_task(task)
                break

            # Assign task
            if self.task_queue.assign_task(task.task_id, selected_node.node_id):
                selected_node.current_tasks += 1
                logger.debug("Assigned task %s to node %s",
                           task.task_id, selected_node.node_id)

                # In a real implementation, would send task to worker node
                await self._send_task_to_node(task, selected_node)

    async def _send_task_to_node(self, task: Task, node: ClusterNode) -> None:
        """Send task to worker node (placeholder for real implementation)."""
        # In production, this would use network communication
        # For now, just mark as started
        self.task_queue.start_task(task.task_id)

        # Simulate task execution
        await asyncio.sleep(0.1)  # Placeholder

        # Simulate completion
        success_rate = 0.9  # 90% success rate for simulation
        import random
        if random.random() < success_rate:
            result = {"status": "completed", "data": "simulated_result"}
            self.task_queue.complete_task(task.task_id, result=result)
        else:
            error = "Simulated task failure"
            self.task_queue.complete_task(task.task_id, error=error)
            self.cluster_stats["task_failures"] += 1

        # Update node stats
        node.current_tasks = max(0, node.current_tasks - 1)
        if task.status == TaskStatus.COMPLETED:
            node.total_tasks_completed += 1
        else:
            node.total_tasks_failed += 1

    async def _collect_task_results(self) -> None:
        """Collect results from completed tasks."""
        # In production, would collect results from worker nodes
        # For now, results are already collected in _send_task_to_node
        pass

    def _cleanup_expired_tasks(self) -> None:
        """Clean up expired tasks."""
        current_time = time.time()
        expired_tasks = []

        for task_id, task in self.task_queue.tasks.items():
            if task.is_expired and task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                expired_tasks.append(task_id)

        for task_id in expired_tasks:
            task = self.task_queue.tasks[task_id]
            self.task_queue.complete_task(task_id, error="Task expired")
            logger.warning("Task %s expired and was removed", task_id)

    def _update_statistics(self) -> None:
        """Update cluster statistics."""
        completed_tasks = list(self.task_queue.completed_tasks.values())

        if completed_tasks:
            total_time = sum(
                task.duration for task in completed_tasks
                if task.duration is not None
            )

            self.cluster_stats["tasks_processed"] = len(completed_tasks)
            self.cluster_stats["total_processing_time"] = total_time
            self.cluster_stats["average_task_time"] = (
                total_time / len(completed_tasks) if completed_tasks else 0.0
            )

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status."""
        return {
            "coordinator_id": self.node_id,
            "total_nodes": len(self.nodes),
            "healthy_nodes": sum(
                1 for node in self.nodes.values()
                if node.status == NodeStatus.HEALTHY
            ),
            "queue_stats": self.task_queue.get_queue_stats(),
            "cluster_stats": self.cluster_stats,
            "nodes": {
                node_id: {
                    "status": node.status.value,
                    "utilization": node.utilization,
                    "tasks_completed": node.total_tasks_completed,
                    "tasks_failed": node.total_tasks_failed
                }
                for node_id, node in self.nodes.items()
            }
        }

    def stop(self) -> None:
        """Stop the cluster coordinator."""
        self.running = False
        logger.info("Stopped cluster coordinator %s", self.node_id)


class DistributedContractProcessor:
    """High-level distributed contract processing interface."""

    def __init__(self):
        self.coordinator = ClusterCoordinator()
        self.worker_nodes: List[ClusterNode] = []

    def start_cluster(self, num_workers: int = 4) -> None:
        """Start distributed cluster."""
        # Create worker nodes
        for i in range(num_workers):
            worker = ClusterNode(
                node_id=f"worker_{i}",
                role=NodeRole.WORKER,
                host="localhost",
                port=8000 + i,
                capabilities={"contract_processing", "ocr", "nlp"},
                max_concurrent_tasks=2
            )

            self.coordinator.register_node(worker)
            self.worker_nodes.append(worker)

        logger.info("Started distributed cluster with %d workers", num_workers)

    async def process_documents_distributed(
        self,
        document_paths: List[Path],
        processing_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple documents using distributed cluster."""
        if not document_paths:
            return []

        # Create tasks for each document
        tasks = []
        for i, doc_path in enumerate(document_paths):
            task = Task(
                task_id=f"process_doc_{i}_{uuid.uuid4().hex[:8]}",
                task_type="document_processing",
                data={
                    "document_path": str(doc_path),
                    "config": processing_config or {}
                },
                priority=1
            )
            tasks.append(task)

        # Submit tasks to cluster
        task_ids = []
        for task in tasks:
            task_id = self.coordinator.submit_task(task)
            task_ids.append(task_id)

        # Start processing
        processing_task = asyncio.create_task(self.coordinator.process_tasks())

        # Wait for all tasks to complete
        await self._wait_for_tasks_completion(task_ids)

        # Stop processing loop
        self.coordinator.stop()
        await processing_task

        # Collect results
        results = []
        for task_id in task_ids:
            task = self.coordinator.task_queue.completed_tasks.get(task_id)
            if task:
                if task.error:
                    results.append({"error": task.error, "task_id": task_id})
                else:
                    results.append(task.result)
            else:
                results.append({"error": "Task not found", "task_id": task_id})

        return results

    async def _wait_for_tasks_completion(
        self,
        task_ids: List[str],
        timeout: float = 300.0
    ) -> None:
        """Wait for all tasks to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            completed_count = sum(
                1 for task_id in task_ids
                if task_id in self.coordinator.task_queue.completed_tasks
            )

            if completed_count == len(task_ids):
                logger.info("All %d tasks completed", len(task_ids))
                return

            logger.debug("Waiting for tasks: %d/%d completed",
                        completed_count, len(task_ids))
            await asyncio.sleep(2.0)

        logger.warning("Timeout waiting for task completion")

    def get_cluster_performance(self) -> Dict[str, Any]:
        """Get cluster performance metrics."""
        status = self.coordinator.get_cluster_status()

        # Add throughput calculations
        stats = status["cluster_stats"]
        if stats["average_task_time"] > 0:
            throughput = 1.0 / stats["average_task_time"]  # tasks per second
            status["throughput_tasks_per_second"] = throughput

        return status


# Global distributed processor
_distributed_processor: Optional[DistributedContractProcessor] = None


def get_distributed_processor() -> DistributedContractProcessor:
    """Get global distributed processor instance."""
    global _distributed_processor
    if _distributed_processor is None:
        _distributed_processor = DistributedContractProcessor()
    return _distributed_processor


class DistributedConfig(BaseModel):
    """Configuration for distributed computing."""

    enable_distributed_processing: bool = False
    num_worker_nodes: int = Field(default=4, ge=1, le=32)
    max_tasks_per_node: int = Field(default=2, ge=1, le=16)
    task_timeout: float = Field(default=300.0, gt=0.0)
    load_balancing_strategy: str = Field(default="least_loaded")
    heartbeat_interval: float = Field(default=10.0, gt=0.0)
    node_failure_timeout: float = Field(default=30.0, gt=0.0)
    enable_task_retry: bool = True
    max_task_retries: int = Field(default=3, ge=0, le=10)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda x: round(x, 3)
        }
