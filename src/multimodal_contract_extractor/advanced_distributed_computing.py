"""
Advanced Distributed Computing Architecture for Multi-Node Contract Processing.

This module provides enterprise-grade distributed computing capabilities with multi-node
processing, intelligent load balancing, fault tolerance, and resource scheduling to
scale the contract extraction system across multiple servers and cloud regions.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import socket
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, AsyncGenerator
import threading
import pickle
import base64

import psutil

logger = logging.getLogger(__name__)

# Try to import distributed computing libraries
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

try:
    import consul
    HAS_CONSUL = True
except ImportError:
    HAS_CONSUL = False
    consul = None


class NodeType(Enum):
    """Types of nodes in the distributed cluster."""
    COORDINATOR = "coordinator"
    WORKER = "worker"
    HYBRID = "hybrid"
    GATEWAY = "gateway"
    STORAGE = "storage"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """Task execution status."""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


class DistributionStrategy(Enum):
    """Data distribution strategies."""
    ROUND_ROBIN = "round_robin"
    HASH_BASED = "hash_based"
    LOAD_BALANCED = "load_balanced"
    AFFINITY_BASED = "affinity_based"
    GEOGRAPHIC = "geographic"
    CAPABILITY_BASED = "capability_based"


class ConsistencyLevel(Enum):
    """Data consistency levels."""
    EVENTUAL = "eventual"
    STRONG = "strong"
    CAUSAL = "causal"
    MONOTONIC = "monotonic"


@dataclass
class NodeInfo:
    """Information about a cluster node."""
    node_id: str
    node_type: NodeType
    hostname: str
    ip_address: str
    port: int
    region: str
    zone: str
    capabilities: Dict[str, Any]
    resource_capacity: Dict[str, float]
    current_load: Dict[str, float]
    health_status: str = "healthy"
    last_heartbeat: float = field(default_factory=time.time)
    join_time: float = field(default_factory=time.time)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributedTask:
    """Distributed task definition."""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    requirements: Dict[str, Any]
    constraints: Dict[str, Any]
    deadline: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    assigned_node: Optional[str] = None
    status: TaskStatus = TaskStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusterMetrics:
    """Cluster-wide metrics."""
    total_nodes: int
    healthy_nodes: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_task_duration: float
    cluster_utilization: float
    network_latency: Dict[str, float]
    resource_utilization: Dict[str, float]
    fault_tolerance_level: float
    timestamp: float = field(default_factory=time.time)


class DistributedTaskQueue:
    """Advanced distributed task queue with priority and affinity."""
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        self.queues: Dict[TaskPriority, deque] = {
            priority: deque() for priority in TaskPriority
        }
        self.task_registry: Dict[str, DistributedTask] = {}
        self.node_affinities: Dict[str, Set[str]] = defaultdict(set)
        self.lock = threading.RLock()
    
    async def enqueue_task(self, task: DistributedTask) -> bool:
        """Enqueue a task with priority ordering."""
        try:
            with self.lock:
                self.task_registry[task.task_id] = task
                self.queues[task.priority].append(task.task_id)
                
                # Store in Redis if available
                if self.redis_client and HAS_REDIS:
                    task_data = self._serialize_task(task)
                    await self.redis_client.hset("tasks", task.task_id, task_data)
                    await self.redis_client.zadd(
                        f"queue:{task.priority.value}", 
                        {task.task_id: task.created_at}
                    )
                
                logger.info(f"Enqueued task {task.task_id} with priority {task.priority.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.task_id}: {e}")
            return False
    
    async def dequeue_task(self, node_id: str, capabilities: Dict[str, Any]) -> Optional[DistributedTask]:
        """Dequeue the next appropriate task for a node."""
        try:
            with self.lock:
                # Check queues in priority order
                for priority in TaskPriority:
                    queue = self.queues[priority]
                    
                    # Find a suitable task
                    for i, task_id in enumerate(queue):
                        task = self.task_registry.get(task_id)
                        if not task or task.status != TaskStatus.QUEUED:
                            continue
                        
                        # Check if node can handle this task
                        if self._can_node_handle_task(node_id, task, capabilities):
                            # Remove from queue
                            queue.remove(task_id)
                            task.status = TaskStatus.ASSIGNED
                            task.assigned_node = node_id
                            
                            # Update Redis
                            if self.redis_client and HAS_REDIS:
                                await self.redis_client.zrem(f"queue:{priority.value}", task_id)
                                await self.redis_client.hset("tasks", task_id, self._serialize_task(task))
                            
                            logger.info(f"Assigned task {task_id} to node {node_id}")
                            return task
                
                return None  # No suitable tasks
                
        except Exception as e:
            logger.error(f"Failed to dequeue task for node {node_id}: {e}")
            return None
    
    def _can_node_handle_task(self, node_id: str, task: DistributedTask, capabilities: Dict[str, Any]) -> bool:
        """Check if a node can handle a specific task."""
        try:
            # Check basic requirements
            for req, value in task.requirements.items():
                if req not in capabilities:
                    return False
                if isinstance(value, (int, float)) and capabilities[req] < value:
                    return False
                if isinstance(value, str) and capabilities[req] != value:
                    return False
            
            # Check constraints
            for constraint, value in task.constraints.items():
                if constraint == "excluded_nodes" and node_id in value:
                    return False
                if constraint == "required_region" and capabilities.get("region") != value:
                    return False
                if constraint == "min_memory" and capabilities.get("memory", 0) < value:
                    return False
            
            # Check node affinity
            if task.task_type in self.node_affinities[node_id]:
                return True  # Preferred node
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking node capability: {e}")
            return False
    
    def _serialize_task(self, task: DistributedTask) -> str:
        """Serialize task for storage."""
        try:
            # Convert task to dictionary, handling enums and non-serializable objects
            task_dict = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "priority": task.priority.value,
                "payload": task.payload,
                "requirements": task.requirements,
                "constraints": task.constraints,
                "deadline": task.deadline,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "assigned_node": task.assigned_node,
                "status": task.status.value,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "result": task.result,
                "error": task.error,
                "execution_context": task.execution_context
            }
            return base64.b64encode(pickle.dumps(task_dict)).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to serialize task: {e}")
            return "{}"


class LoadBalancer:
    """Advanced load balancer for distributed task assignment."""
    
    def __init__(self, strategy: DistributionStrategy = DistributionStrategy.LOAD_BALANCED):
        self.strategy = strategy
        self.node_weights: Dict[str, float] = {}
        self.node_performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.task_completion_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.geographic_latency: Dict[Tuple[str, str], float] = {}
    
    def select_nodes_for_task(self, task: DistributedTask, available_nodes: List[NodeInfo], count: int = 1) -> List[NodeInfo]:
        """Select optimal nodes for task execution."""
        try:
            if not available_nodes:
                return []
            
            # Filter nodes that can handle the task
            capable_nodes = [node for node in available_nodes if self._can_node_handle_task(node, task)]
            
            if not capable_nodes:
                logger.warning(f"No capable nodes found for task {task.task_id}")
                return []
            
            # Apply selection strategy
            if self.strategy == DistributionStrategy.ROUND_ROBIN:
                return self._round_robin_selection(capable_nodes, count)
            elif self.strategy == DistributionStrategy.HASH_BASED:
                return self._hash_based_selection(capable_nodes, task, count)
            elif self.strategy == DistributionStrategy.LOAD_BALANCED:
                return self._load_balanced_selection(capable_nodes, count)
            elif self.strategy == DistributionStrategy.AFFINITY_BASED:
                return self._affinity_based_selection(capable_nodes, task, count)
            elif self.strategy == DistributionStrategy.GEOGRAPHIC:
                return self._geographic_selection(capable_nodes, task, count)
            elif self.strategy == DistributionStrategy.CAPABILITY_BASED:
                return self._capability_based_selection(capable_nodes, task, count)
            else:
                return capable_nodes[:count]
                
        except Exception as e:
            logger.error(f"Node selection failed: {e}")
            return []
    
    def _can_node_handle_task(self, node: NodeInfo, task: DistributedTask) -> bool:
        """Check if node can handle the task."""
        try:
            # Check resource requirements
            for resource, required in task.requirements.items():
                available = node.resource_capacity.get(resource, 0)
                current_used = node.current_load.get(resource, 0)
                if available - current_used < required:
                    return False
            
            # Check capabilities
            task_capabilities = task.requirements.get("capabilities", [])
            for capability in task_capabilities:
                if capability not in node.capabilities:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking node {node.node_id} for task: {e}")
            return False
    
    def _round_robin_selection(self, nodes: List[NodeInfo], count: int) -> List[NodeInfo]:
        """Round-robin node selection."""
        if not hasattr(self, '_rr_index'):
            self._rr_index = 0
        
        selected = []
        for i in range(count):
            if nodes:
                selected.append(nodes[self._rr_index % len(nodes)])
                self._rr_index = (self._rr_index + 1) % len(nodes)
        
        return selected
    
    def _hash_based_selection(self, nodes: List[NodeInfo], task: DistributedTask, count: int) -> List[NodeInfo]:
        """Hash-based consistent node selection."""
        task_hash = hashlib.md5(task.task_id.encode()).hexdigest()
        start_index = int(task_hash, 16) % len(nodes)
        
        selected = []
        for i in range(count):
            index = (start_index + i) % len(nodes)
            selected.append(nodes[index])
        
        return selected
    
    def _load_balanced_selection(self, nodes: List[NodeInfo], count: int) -> List[NodeInfo]:
        """Load-balanced node selection based on current utilization."""
        # Calculate load scores for each node
        node_scores = []
        for node in nodes:
            # Calculate weighted load score
            cpu_load = node.current_load.get("cpu", 0) / max(node.resource_capacity.get("cpu", 1), 1)
            memory_load = node.current_load.get("memory", 0) / max(node.resource_capacity.get("memory", 1), 1)
            network_load = node.current_load.get("network", 0) / max(node.resource_capacity.get("network", 1), 1)
            
            # Weighted average (CPU: 40%, Memory: 40%, Network: 20%)
            load_score = (cpu_load * 0.4) + (memory_load * 0.4) + (network_load * 0.2)
            
            # Factor in performance history
            perf_history = self.node_performance_history[node.node_id]
            performance_factor = 1.0
            if perf_history:
                avg_performance = sum(perf_history) / len(perf_history)
                performance_factor = min(2.0, max(0.5, avg_performance))
            
            final_score = load_score / performance_factor
            node_scores.append((node, final_score))
        
        # Sort by score (lower is better) and select top nodes
        node_scores.sort(key=lambda x: x[1])
        return [node for node, score in node_scores[:count]]
    
    def _affinity_based_selection(self, nodes: List[NodeInfo], task: DistributedTask, count: int) -> List[NodeInfo]:
        """Affinity-based selection considering data locality."""
        # Check for data locality hints
        preferred_nodes = task.constraints.get("preferred_nodes", [])
        data_locality = task.constraints.get("data_locality", {})
        
        # Score nodes based on affinity
        node_scores = []
        for node in nodes:
            score = 0.0
            
            # Preferred node bonus
            if node.node_id in preferred_nodes:
                score += 10.0
            
            # Data locality bonus
            for data_key, locations in data_locality.items():
                if node.region in locations:
                    score += 5.0
                if node.zone in locations:
                    score += 2.0
            
            # Historical performance bonus
            completion_times = self.task_completion_times[node.node_id]
            if completion_times:
                avg_time = sum(completion_times) / len(completion_times)
                score += max(0, 10.0 - avg_time)  # Faster nodes get higher scores
            
            node_scores.append((node, score))
        
        # Sort by score (higher is better)
        node_scores.sort(key=lambda x: x[1], reverse=True)
        return [node for node, score in node_scores[:count]]
    
    def _geographic_selection(self, nodes: List[NodeInfo], task: DistributedTask, count: int) -> List[NodeInfo]:
        """Geographic selection to minimize network latency."""
        source_region = task.constraints.get("source_region", "")
        if not source_region:
            return self._load_balanced_selection(nodes, count)
        
        # Group nodes by region and calculate latency
        regional_nodes = defaultdict(list)
        for node in nodes:
            regional_nodes[node.region].append(node)
        
        # Select nodes from closest regions first
        selected = []
        regions_by_latency = sorted(
            regional_nodes.keys(),
            key=lambda region: self.geographic_latency.get((source_region, region), float('inf'))
        )
        
        for region in regions_by_latency:
            if len(selected) >= count:
                break
            
            region_nodes = regional_nodes[region]
            needed = count - len(selected)
            selected.extend(self._load_balanced_selection(region_nodes, min(needed, len(region_nodes))))
        
        return selected
    
    def _capability_based_selection(self, nodes: List[NodeInfo], task: DistributedTask, count: int) -> List[NodeInfo]:
        """Select nodes based on specialized capabilities."""
        required_capabilities = task.requirements.get("specialized_capabilities", [])
        
        if not required_capabilities:
            return self._load_balanced_selection(nodes, count)
        
        # Score nodes based on capability match
        node_scores = []
        for node in nodes:
            score = 0.0
            
            for capability in required_capabilities:
                if capability in node.capabilities:
                    capability_level = node.capabilities[capability]
                    if isinstance(capability_level, (int, float)):
                        score += capability_level
                    else:
                        score += 1.0
            
            node_scores.append((node, score))
        
        # Sort by capability score (higher is better)
        node_scores.sort(key=lambda x: x[1], reverse=True)
        return [node for node, score in node_scores[:count]]
    
    def update_node_performance(self, node_id: str, task_duration: float, success: bool) -> None:
        """Update node performance metrics."""
        try:
            performance_score = 1.0 / max(task_duration, 0.001) if success else 0.0
            self.node_performance_history[node_id].append(performance_score)
            
            if success:
                self.task_completion_times[node_id].append(task_duration)
                
        except Exception as e:
            logger.error(f"Failed to update performance for node {node_id}: {e}")


class DistributedCoordinator:
    """Central coordinator for distributed processing."""
    
    def __init__(self, node_id: str, redis_url: Optional[str] = None):
        self.node_id = node_id
        self.node_registry: Dict[str, NodeInfo] = {}
        self.task_queue = DistributedTaskQueue()
        self.load_balancer = LoadBalancer()
        self.cluster_health = {"status": "healthy", "last_check": time.time()}
        self.election_lock = threading.RLock()
        self.is_leader = False
        self.heartbeat_interval = 30.0
        self.node_timeout = 120.0
        
        # Initialize Redis connection
        self.redis_client = None
        if redis_url and HAS_REDIS:
            try:
                self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.task_queue.redis_client = self.redis_client
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
        
        # Start background tasks
        self.background_tasks = []
        self._start_background_tasks()
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.background_tasks.append(heartbeat_task)
        
        # Health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self.background_tasks.append(health_task)
        
        # Leader election task
        election_task = asyncio.create_task(self._leader_election_loop())
        self.background_tasks.append(election_task)
    
    async def register_node(self, node_info: NodeInfo) -> bool:
        """Register a new node in the cluster."""
        try:
            self.node_registry[node_info.node_id] = node_info
            
            if self.redis_client:
                node_data = {
                    "node_type": node_info.node_type.value,
                    "hostname": node_info.hostname,
                    "ip_address": node_info.ip_address,
                    "port": node_info.port,
                    "region": node_info.region,
                    "zone": node_info.zone,
                    "capabilities": json.dumps(node_info.capabilities),
                    "resource_capacity": json.dumps(node_info.resource_capacity),
                    "health_status": node_info.health_status,
                    "last_heartbeat": node_info.last_heartbeat,
                    "version": node_info.version
                }
                await self.redis_client.hset(f"node:{node_info.node_id}", mapping=node_data)
                await self.redis_client.sadd("cluster:nodes", node_info.node_id)
            
            logger.info(f"Registered node {node_info.node_id} ({node_info.node_type.value}) from {node_info.region}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register node {node_info.node_id}: {e}")
            return False
    
    async def unregister_node(self, node_id: str) -> bool:
        """Unregister a node from the cluster."""
        try:
            if node_id in self.node_registry:
                del self.node_registry[node_id]
            
            if self.redis_client:
                await self.redis_client.delete(f"node:{node_id}")
                await self.redis_client.srem("cluster:nodes", node_id)
            
            logger.info(f"Unregistered node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister node {node_id}: {e}")
            return False
    
    async def submit_task(self, task: DistributedTask) -> bool:
        """Submit a task for distributed execution."""
        try:
            # Select appropriate nodes for the task
            available_nodes = [node for node in self.node_registry.values() if node.health_status == "healthy"]
            selected_nodes = self.load_balancer.select_nodes_for_task(task, available_nodes, 1)
            
            if not selected_nodes:
                logger.error(f"No suitable nodes available for task {task.task_id}")
                return False
            
            # Enqueue the task
            return await self.task_queue.enqueue_task(task)
            
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False
    
    async def get_cluster_metrics(self) -> ClusterMetrics:
        """Get comprehensive cluster metrics."""
        try:
            total_nodes = len(self.node_registry)
            healthy_nodes = sum(1 for node in self.node_registry.values() if node.health_status == "healthy")
            
            # Get task statistics
            total_tasks = len(self.task_queue.task_registry)
            completed_tasks = sum(1 for task in self.task_queue.task_registry.values() if task.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for task in self.task_queue.task_registry.values() if task.status == TaskStatus.FAILED)
            
            # Calculate average task duration
            durations = []
            for task in self.task_queue.task_registry.values():
                if task.completed_at and task.started_at:
                    durations.append(task.completed_at - task.started_at)
            
            average_duration = sum(durations) / len(durations) if durations else 0.0
            
            # Calculate cluster utilization
            total_capacity = 0.0
            total_usage = 0.0
            for node in self.node_registry.values():
                for resource, capacity in node.resource_capacity.items():
                    total_capacity += capacity
                    total_usage += node.current_load.get(resource, 0)
            
            cluster_utilization = (total_usage / max(total_capacity, 1)) * 100
            
            # Calculate resource utilization by type
            resource_utilization = {}
            resource_types = set()
            for node in self.node_registry.values():
                resource_types.update(node.resource_capacity.keys())
            
            for resource_type in resource_types:
                total_cap = sum(node.resource_capacity.get(resource_type, 0) for node in self.node_registry.values())
                total_use = sum(node.current_load.get(resource_type, 0) for node in self.node_registry.values())
                resource_utilization[resource_type] = (total_use / max(total_cap, 1)) * 100
            
            # Calculate fault tolerance level
            fault_tolerance = min(1.0, healthy_nodes / max(total_nodes, 1))
            
            return ClusterMetrics(
                total_nodes=total_nodes,
                healthy_nodes=healthy_nodes,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                average_task_duration=average_duration,
                cluster_utilization=cluster_utilization,
                network_latency={},  # Would be populated from actual measurements
                resource_utilization=resource_utilization,
                fault_tolerance_level=fault_tolerance
            )
            
        except Exception as e:
            logger.error(f"Failed to get cluster metrics: {e}")
            return ClusterMetrics(0, 0, 0, 0, 0, 0.0, 0.0, {}, {}, 0.0)
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Update node heartbeats
                current_time = time.time()
                expired_nodes = []
                
                for node_id, node in self.node_registry.items():
                    if current_time - node.last_heartbeat > self.node_timeout:
                        expired_nodes.append(node_id)
                        node.health_status = "offline"
                
                # Remove expired nodes
                for node_id in expired_nodes:
                    await self.unregister_node(node_id)
                    logger.warning(f"Removed expired node {node_id}")
                
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                # Update cluster health
                healthy_ratio = sum(1 for node in self.node_registry.values() if node.health_status == "healthy") / max(len(self.node_registry), 1)
                
                if healthy_ratio >= 0.8:
                    self.cluster_health["status"] = "healthy"
                elif healthy_ratio >= 0.5:
                    self.cluster_health["status"] = "degraded"
                else:
                    self.cluster_health["status"] = "unhealthy"
                
                self.cluster_health["last_check"] = time.time()
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _leader_election_loop(self) -> None:
        """Background leader election loop."""
        while True:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
                with self.election_lock:
                    # Simple leader election based on node ID
                    if self.node_registry:
                        leader_id = min(self.node_registry.keys())
                        self.is_leader = (leader_id == self.node_id)
                    else:
                        self.is_leader = True
                
                if self.is_leader:
                    logger.debug(f"Node {self.node_id} is the cluster leader")
                
            except Exception as e:
                logger.error(f"Leader election error: {e}")


class DistributedWorker:
    """Distributed worker node for task execution."""
    
    def __init__(self, node_id: str, coordinator_url: str, node_type: NodeType = NodeType.WORKER):
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.node_type = node_type
        self.is_running = False
        self.current_tasks: Dict[str, DistributedTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        
        # Node information
        self.node_info = self._create_node_info()
        
        # Background task for worker loop
        self.worker_task: Optional[asyncio.Task] = None
    
    def _create_node_info(self) -> NodeInfo:
        """Create node information."""
        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except:
            ip_address = "127.0.0.1"
        
        # Get system resources
        cpu_count = psutil.cpu_count()
        memory_total = psutil.virtual_memory().total // (1024 * 1024)  # MB
        
        return NodeInfo(
            node_id=self.node_id,
            node_type=self.node_type,
            hostname=hostname,
            ip_address=ip_address,
            port=0,  # Would be assigned dynamically
            region=os.getenv("CLUSTER_REGION", "us-east-1"),
            zone=os.getenv("CLUSTER_ZONE", "us-east-1a"),
            capabilities={
                "contract_extraction": True,
                "ocr_processing": True,
                "gpu_acceleration": False,  # Would be detected
                "streaming_processing": True
            },
            resource_capacity={
                "cpu": float(cpu_count),
                "memory": float(memory_total),
                "network": 1000.0,  # Mbps
                "storage": 1000.0  # GB
            },
            current_load={
                "cpu": 0.0,
                "memory": 0.0,
                "network": 0.0,
                "storage": 0.0
            }
        )
    
    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """Register a task handler for a specific task type."""
        self.task_handlers[task_type] = handler
    
    async def start(self) -> None:
        """Start the worker node."""
        try:
            self.is_running = True
            
            # Start worker loop
            self.worker_task = asyncio.create_task(self._worker_loop())
            
            logger.info(f"Started distributed worker {self.node_id}")
            
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
    
    async def stop(self) -> None:
        """Stop the worker node."""
        try:
            self.is_running = False
            
            if self.worker_task:
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            
            logger.info(f"Stopped distributed worker {self.node_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop worker: {e}")
    
    async def _worker_loop(self) -> None:
        """Main worker loop for processing tasks."""
        while self.is_running:
            try:
                # Update resource utilization
                self._update_resource_utilization()
                
                # Get next task (would communicate with coordinator)
                # For now, simulate task processing
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5.0)  # Back off on error
    
    def _update_resource_utilization(self) -> None:
        """Update current resource utilization."""
        try:
            self.node_info.current_load["cpu"] = psutil.cpu_percent()
            self.node_info.current_load["memory"] = psutil.virtual_memory().percent
            # Network and storage would be monitored with additional tools
            
        except Exception as e:
            logger.error(f"Failed to update resource utilization: {e}")


# Global instances
_coordinator: Optional[DistributedCoordinator] = None
_worker: Optional[DistributedWorker] = None


def get_distributed_coordinator(node_id: str = None, redis_url: str = None) -> DistributedCoordinator:
    """Get the global distributed coordinator instance."""
    global _coordinator
    if _coordinator is None:
        node_id = node_id or f"coordinator_{uuid.uuid4().hex[:8]}"
        _coordinator = DistributedCoordinator(node_id, redis_url)
    return _coordinator


def get_distributed_worker(node_id: str = None, coordinator_url: str = "localhost:6379") -> DistributedWorker:
    """Get the global distributed worker instance."""
    global _worker
    if _worker is None:
        node_id = node_id or f"worker_{uuid.uuid4().hex[:8]}"
        _worker = DistributedWorker(node_id, coordinator_url)
    return _worker


@asynccontextmanager
async def distributed_processing_context(
    task_type: str,
    requirements: Dict[str, Any] = None,
    constraints: Dict[str, Any] = None
) -> AsyncGenerator[DistributedTask, None]:
    """Context manager for distributed task processing."""
    task = DistributedTask(
        task_id=f"task_{uuid.uuid4().hex}",
        task_type=task_type,
        priority=TaskPriority.NORMAL,
        payload={},
        requirements=requirements or {},
        constraints=constraints or {}
    )
    
    try:
        coordinator = get_distributed_coordinator()
        await coordinator.submit_task(task)
        yield task
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        logger.error(f"Distributed processing failed: {e}")
        raise
    finally:
        # Cleanup would happen here
        pass