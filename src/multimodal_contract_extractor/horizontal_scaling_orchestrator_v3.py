#!/usr/bin/env python3
"""
Horizontal Scaling Orchestrator v3.0 - Generation 3: MAKE IT SCALE
Advanced horizontal scaling with auto-scaling, load balancing, distributed processing,
and cloud-native orchestration for the autonomous SDLC system.
"""

import asyncio
import time
import json
import threading
import uuid
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime, timedelta
from collections import defaultdict, deque
import concurrent.futures
import logging
import hashlib
import aiohttp
import psutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import queue
import socket
import pickle


class ScalingMode(Enum):
    """Scaling modes"""
    MANUAL = auto()
    AUTOMATIC = auto()
    PREDICTIVE = auto()
    REACTIVE = auto()
    HYBRID = auto()


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = auto()
    LEAST_CONNECTIONS = auto()
    WEIGHTED_ROUND_ROBIN = auto()
    IP_HASH = auto()
    LEAST_RESPONSE_TIME = auto()
    RESOURCE_BASED = auto()
    AI_OPTIMIZED = auto()


class NodeStatus(Enum):
    """Node status types"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    STARTING = auto()
    STOPPING = auto()
    MAINTENANCE = auto()


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkerNode:
    """Worker node representation"""
    node_id: str
    host: str
    port: int
    status: NodeStatus
    cpu_usage: float
    memory_usage: float
    active_tasks: int
    max_tasks: int
    last_heartbeat: datetime
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    total_processed: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0


@dataclass
class ScalingTask:
    """Task for distributed processing"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime
    timeout_seconds: int
    retry_count: int = 0
    max_retries: int = 3
    assigned_node: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ScalingMetrics:
    """Scaling system metrics"""
    timestamp: datetime
    total_nodes: int
    healthy_nodes: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_response_time: float
    cpu_utilization: float
    memory_utilization: float
    throughput: float
    queue_size: int
    scaling_events: int


@dataclass
class AutoScalingPolicy:
    """Auto-scaling policy configuration"""
    policy_id: str
    name: str
    min_nodes: int
    max_nodes: int
    target_cpu_utilization: float
    target_memory_utilization: float
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_cooldown: int  # seconds
    scale_down_cooldown: int  # seconds
    enabled: bool = True
    predictive_scaling: bool = True
    scaling_factor: float = 1.5


class DistributedTaskQueue:
    """High-performance distributed task queue"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[TaskPriority, queue.PriorityQueue] = {
            TaskPriority.CRITICAL: queue.PriorityQueue(),
            TaskPriority.HIGH: queue.PriorityQueue(),
            TaskPriority.MEDIUM: queue.PriorityQueue(),
            TaskPriority.LOW: queue.PriorityQueue()
        }
        
        self.pending_tasks: Dict[str, ScalingTask] = {}
        self.completed_tasks: Dict[str, ScalingTask] = {}
        self.task_results: Dict[str, Any] = {}
        
        self._lock = threading.RLock()
        self.stats = {
            'total_queued': 0,
            'total_completed': 0,
            'total_failed': 0,
            'queue_sizes': {p.name: 0 for p in TaskPriority}
        }
    
    def enqueue_task(self, task: ScalingTask) -> bool:
        """Add task to the appropriate priority queue"""
        with self._lock:
            if len(self.pending_tasks) >= self.max_size:
                return False
            
            # Calculate priority score (lower = higher priority)
            priority_score = task.priority.value * 1000 + int(time.time() * 1000) % 1000
            
            self.queues[task.priority].put((priority_score, task.task_id, task))
            self.pending_tasks[task.task_id] = task
            
            self.stats['total_queued'] += 1
            self.stats['queue_sizes'][task.priority.name] += 1
            
            return True
    
    def dequeue_task(self, node_id: str = None, capabilities: List[str] = None) -> Optional[ScalingTask]:
        """Get next task from queue based on priority"""
        with self._lock:
            # Try each priority level
            for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
                if not self.queues[priority].empty():
                    try:
                        priority_score, task_id, task = self.queues[priority].get_nowait()
                        
                        # Check if node can handle this task
                        if capabilities and task.task_type not in capabilities:
                            # Put task back and try next
                            self.queues[priority].put((priority_score, task_id, task))
                            continue
                        
                        task.assigned_node = node_id
                        task.started_at = datetime.utcnow()
                        
                        self.stats['queue_sizes'][priority.name] -= 1
                        return task
                        
                    except queue.Empty:
                        continue
            
            return None
    
    def complete_task(self, task_id: str, result: Dict[str, Any] = None, error: str = None):
        """Mark task as completed"""
        with self._lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task.completed_at = datetime.utcnow()
                task.result = result
                task.error = error
                
                # Move to completed tasks
                self.completed_tasks[task_id] = task
                del self.pending_tasks[task_id]
                
                if result:
                    self.task_results[task_id] = result
                
                if error:
                    self.stats['total_failed'] += 1
                else:
                    self.stats['total_completed'] += 1
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status and statistics"""
        with self._lock:
            return {
                'total_pending': len(self.pending_tasks),
                'total_completed': len(self.completed_tasks),
                'queue_sizes': {
                    priority.name: self.queues[priority].qsize() 
                    for priority in TaskPriority
                },
                'statistics': dict(self.stats)
            }


class IntelligentLoadBalancer:
    """AI-powered load balancing system"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.AI_OPTIMIZED):
        self.strategy = strategy
        self.nodes: Dict[str, WorkerNode] = {}
        self.request_history: deque = deque(maxlen=1000)
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Load balancing state
        self.round_robin_index = 0
        self.connection_counts: Dict[str, int] = defaultdict(int)
        
        self._lock = threading.RLock()
    
    def register_node(self, node: WorkerNode):
        """Register a new worker node"""
        with self._lock:
            self.nodes[node.node_id] = node
            logging.info(f"Registered node {node.node_id} at {node.host}:{node.port}")
    
    def unregister_node(self, node_id: str):
        """Unregister a worker node"""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                if node_id in self.connection_counts:
                    del self.connection_counts[node_id]
                logging.info(f"Unregistered node {node_id}")
    
    def select_node(self, task: ScalingTask) -> Optional[WorkerNode]:
        """Select best node for task using configured strategy"""
        with self._lock:
            healthy_nodes = [
                node for node in self.nodes.values() 
                if node.status == NodeStatus.HEALTHY and node.active_tasks < node.max_tasks
            ]
            
            if not healthy_nodes:
                return None
            
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_select(healthy_nodes)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_select(healthy_nodes)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(healthy_nodes)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_select(healthy_nodes)
            elif self.strategy == LoadBalancingStrategy.RESOURCE_BASED:
                return self._resource_based_select(healthy_nodes)
            elif self.strategy == LoadBalancingStrategy.AI_OPTIMIZED:
                return self._ai_optimized_select(healthy_nodes, task)
            else:
                return healthy_nodes[0]  # Fallback
    
    def _round_robin_select(self, nodes: List[WorkerNode]) -> WorkerNode:
        """Round-robin selection"""
        node = nodes[self.round_robin_index % len(nodes)]
        self.round_robin_index += 1
        return node
    
    def _least_connections_select(self, nodes: List[WorkerNode]) -> WorkerNode:
        """Select node with least active connections"""
        return min(nodes, key=lambda n: n.active_tasks)
    
    def _weighted_round_robin_select(self, nodes: List[WorkerNode]) -> WorkerNode:
        """Weighted round-robin based on node weights"""
        weighted_nodes = []
        for node in nodes:
            weight = max(1, int(node.weight * 10))
            weighted_nodes.extend([node] * weight)
        
        if weighted_nodes:
            selected = weighted_nodes[self.round_robin_index % len(weighted_nodes)]
            self.round_robin_index += 1
            return selected
        return nodes[0]
    
    def _least_response_time_select(self, nodes: List[WorkerNode]) -> WorkerNode:
        """Select node with lowest average response time"""
        return min(nodes, key=lambda n: n.avg_response_time)
    
    def _resource_based_select(self, nodes: List[WorkerNode]) -> WorkerNode:
        """Select based on available resources"""
        def resource_score(node: WorkerNode) -> float:
            cpu_available = max(0.1, 1.0 - (node.cpu_usage / 100))
            memory_available = max(0.1, 1.0 - (node.memory_usage / 100))
            task_capacity = max(0.1, 1.0 - (node.active_tasks / node.max_tasks))
            
            return cpu_available * memory_available * task_capacity
        
        return max(nodes, key=resource_score)
    
    def _ai_optimized_select(self, nodes: List[WorkerNode], task: ScalingTask) -> WorkerNode:
        """AI-powered node selection considering multiple factors"""
        def ai_score(node: WorkerNode) -> float:
            # Base resource score
            resource_score = self._resource_based_select([node])
            if resource_score != node:
                resource_score = 0.5
            else:
                resource_score = 1.0
            
            # Performance history score
            perf_history = self.performance_history[node.node_id]
            if perf_history:
                avg_performance = sum(perf_history) / len(perf_history)
                performance_score = max(0.1, 1.0 / (1.0 + avg_performance))
            else:
                performance_score = 0.5
            
            # Error rate penalty
            error_rate = node.error_count / max(node.total_processed, 1)
            error_penalty = max(0.1, 1.0 - error_rate)
            
            # Priority adjustment
            priority_boost = 1.0 + (task.priority.value / 10.0)
            
            # Task type affinity
            affinity_bonus = 1.2 if task.task_type in node.capabilities else 1.0
            
            final_score = (resource_score * 0.4 + 
                          performance_score * 0.3 + 
                          error_penalty * 0.2 + 
                          priority_boost * 0.1) * affinity_bonus
            
            return final_score
        
        return max(nodes, key=ai_score)
    
    def update_node_metrics(self, node_id: str, cpu_usage: float, memory_usage: float, 
                          active_tasks: int, response_time: float):
        """Update node performance metrics"""
        with self._lock:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.cpu_usage = cpu_usage
                node.memory_usage = memory_usage
                node.active_tasks = active_tasks
                node.last_heartbeat = datetime.utcnow()
                
                # Update average response time
                if node.avg_response_time == 0:
                    node.avg_response_time = response_time
                else:
                    node.avg_response_time = (node.avg_response_time * 0.8 + response_time * 0.2)
                
                # Store performance history
                self.performance_history[node_id].append(response_time)
    
    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        with self._lock:
            node_stats = {}
            for node_id, node in self.nodes.items():
                node_stats[node_id] = {
                    'status': node.status.name,
                    'cpu_usage': node.cpu_usage,
                    'memory_usage': node.memory_usage,
                    'active_tasks': node.active_tasks,
                    'max_tasks': node.max_tasks,
                    'total_processed': node.total_processed,
                    'error_count': node.error_count,
                    'avg_response_time': node.avg_response_time
                }
            
            return {
                'strategy': self.strategy.name,
                'total_nodes': len(self.nodes),
                'healthy_nodes': sum(1 for n in self.nodes.values() if n.status == NodeStatus.HEALTHY),
                'node_statistics': node_stats,
                'request_history_size': len(self.request_history)
            }


class AutoScalingController:
    """Intelligent auto-scaling controller"""
    
    def __init__(self, load_balancer: IntelligentLoadBalancer):
        self.load_balancer = load_balancer
        self.policies: Dict[str, AutoScalingPolicy] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.metrics_history: deque = deque(maxlen=100)
        
        self.scaling_active = False
        self.last_scale_up = datetime.min
        self.last_scale_down = datetime.min
        
        self._lock = threading.RLock()
    
    def add_scaling_policy(self, policy: AutoScalingPolicy):
        """Add auto-scaling policy"""
        with self._lock:
            self.policies[policy.policy_id] = policy
            logging.info(f"Added scaling policy: {policy.name}")
    
    def remove_scaling_policy(self, policy_id: str):
        """Remove auto-scaling policy"""
        with self._lock:
            if policy_id in self.policies:
                del self.policies[policy_id]
                logging.info(f"Removed scaling policy: {policy_id}")
    
    async def evaluate_scaling(self) -> List[Dict[str, Any]]:
        """Evaluate all scaling policies and return recommendations"""
        recommendations = []
        
        with self._lock:
            current_metrics = self._collect_current_metrics()
            self.metrics_history.append(current_metrics)
            
            for policy in self.policies.values():
                if not policy.enabled:
                    continue
                
                recommendation = await self._evaluate_policy(policy, current_metrics)
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _collect_current_metrics(self) -> ScalingMetrics:
        """Collect current system metrics"""
        nodes = list(self.load_balancer.nodes.values())
        
        if not nodes:
            return ScalingMetrics(
                timestamp=datetime.utcnow(),
                total_nodes=0,
                healthy_nodes=0,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                avg_response_time=0,
                cpu_utilization=0,
                memory_utilization=0,
                throughput=0,
                queue_size=0,
                scaling_events=len(self.scaling_history)
            )
        
        healthy_nodes = [n for n in nodes if n.status == NodeStatus.HEALTHY]
        
        avg_cpu = sum(n.cpu_usage for n in healthy_nodes) / len(healthy_nodes) if healthy_nodes else 0
        avg_memory = sum(n.memory_usage for n in healthy_nodes) / len(healthy_nodes) if healthy_nodes else 0
        avg_response_time = sum(n.avg_response_time for n in healthy_nodes) / len(healthy_nodes) if healthy_nodes else 0
        total_tasks = sum(n.active_tasks for n in nodes)
        total_processed = sum(n.total_processed for n in nodes)
        
        return ScalingMetrics(
            timestamp=datetime.utcnow(),
            total_nodes=len(nodes),
            healthy_nodes=len(healthy_nodes),
            total_tasks=total_tasks,
            completed_tasks=total_processed,
            failed_tasks=sum(n.error_count for n in nodes),
            avg_response_time=avg_response_time,
            cpu_utilization=avg_cpu,
            memory_utilization=avg_memory,
            throughput=total_processed / max(1, (datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0)).total_seconds()),
            queue_size=0,  # Would need task queue reference
            scaling_events=len(self.scaling_history)
        )
    
    async def _evaluate_policy(self, policy: AutoScalingPolicy, 
                              current_metrics: ScalingMetrics) -> Optional[Dict[str, Any]]:
        """Evaluate a specific scaling policy"""
        current_time = datetime.utcnow()
        
        # Check cooldown periods
        scale_up_ready = (current_time - self.last_scale_up).total_seconds() > policy.scale_up_cooldown
        scale_down_ready = (current_time - self.last_scale_down).total_seconds() > policy.scale_down_cooldown
        
        # Determine if scaling is needed
        cpu_overload = current_metrics.cpu_utilization > policy.scale_up_threshold
        memory_overload = current_metrics.memory_utilization > policy.scale_up_threshold
        cpu_underload = current_metrics.cpu_utilization < policy.scale_down_threshold
        memory_underload = current_metrics.memory_utilization < policy.scale_down_threshold
        
        # Scale up decision
        if (cpu_overload or memory_overload) and scale_up_ready:
            if current_metrics.healthy_nodes < policy.max_nodes:
                target_nodes = min(policy.max_nodes, 
                                 int(current_metrics.healthy_nodes * policy.scaling_factor))
                
                return {
                    'policy_id': policy.policy_id,
                    'action': 'scale_up',
                    'current_nodes': current_metrics.healthy_nodes,
                    'target_nodes': target_nodes,
                    'reason': f"CPU: {current_metrics.cpu_utilization:.1f}%, Memory: {current_metrics.memory_utilization:.1f}%",
                    'priority': 'high' if cpu_overload and memory_overload else 'medium',
                    'timestamp': current_time.isoformat()
                }
        
        # Scale down decision
        elif (cpu_underload and memory_underload) and scale_down_ready:
            if current_metrics.healthy_nodes > policy.min_nodes:
                target_nodes = max(policy.min_nodes,
                                 int(current_metrics.healthy_nodes / policy.scaling_factor))
                
                return {
                    'policy_id': policy.policy_id,
                    'action': 'scale_down',
                    'current_nodes': current_metrics.healthy_nodes,
                    'target_nodes': target_nodes,
                    'reason': f"CPU: {current_metrics.cpu_utilization:.1f}%, Memory: {current_metrics.memory_utilization:.1f}%",
                    'priority': 'low',
                    'timestamp': current_time.isoformat()
                }
        
        return None
    
    async def execute_scaling_action(self, recommendation: Dict[str, Any]) -> bool:
        """Execute a scaling recommendation"""
        try:
            action = recommendation['action']
            current_nodes = recommendation['current_nodes']
            target_nodes = recommendation['target_nodes']
            
            if action == 'scale_up':
                success = await self._scale_up(target_nodes - current_nodes)
                if success:
                    self.last_scale_up = datetime.utcnow()
            elif action == 'scale_down':
                success = await self._scale_down(current_nodes - target_nodes)
                if success:
                    self.last_scale_down = datetime.utcnow()
            else:
                return False
            
            # Record scaling event
            scaling_event = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': action,
                'policy_id': recommendation['policy_id'],
                'nodes_before': current_nodes,
                'nodes_after': target_nodes,
                'reason': recommendation['reason'],
                'success': success
            }
            
            self.scaling_history.append(scaling_event)
            
            if success:
                logging.info(f"Scaling {action} completed: {current_nodes} -> {target_nodes} nodes")
            else:
                logging.error(f"Scaling {action} failed")
            
            return success
            
        except Exception as e:
            logging.error(f"Error executing scaling action: {e}")
            return False
    
    async def _scale_up(self, node_count: int) -> bool:
        """Add new worker nodes"""
        # This would integrate with cloud providers or container orchestrators
        # For now, simulate node creation
        for i in range(node_count):
            node_id = f"worker_{uuid.uuid4().hex[:8]}"
            node = WorkerNode(
                node_id=node_id,
                host=f"10.0.0.{100 + i}",
                port=8080,
                status=NodeStatus.STARTING,
                cpu_usage=0.0,
                memory_usage=0.0,
                active_tasks=0,
                max_tasks=10,
                last_heartbeat=datetime.utcnow(),
                capabilities=["document_processing", "ml_inference"]
            )
            
            self.load_balancer.register_node(node)
            
            # Simulate startup time
            await asyncio.sleep(1)
            node.status = NodeStatus.HEALTHY
        
        return True
    
    async def _scale_down(self, node_count: int) -> bool:
        """Remove worker nodes gracefully"""
        healthy_nodes = [
            n for n in self.load_balancer.nodes.values() 
            if n.status == NodeStatus.HEALTHY
        ]
        
        # Select nodes to remove (prefer nodes with fewer active tasks)
        nodes_to_remove = sorted(healthy_nodes, key=lambda n: n.active_tasks)[:node_count]
        
        for node in nodes_to_remove:
            # Set to maintenance mode first
            node.status = NodeStatus.MAINTENANCE
            
            # Wait for tasks to complete (simplified)
            await asyncio.sleep(2)
            
            # Remove node
            self.load_balancer.unregister_node(node.node_id)
        
        return True
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get auto-scaling status"""
        with self._lock:
            recent_events = self.scaling_history[-10:] if self.scaling_history else []
            recent_metrics = list(self.metrics_history)[-5:] if self.metrics_history else []
            
            policy_status = {}
            for policy_id, policy in self.policies.items():
                policy_status[policy_id] = {
                    'name': policy.name,
                    'enabled': policy.enabled,
                    'min_nodes': policy.min_nodes,
                    'max_nodes': policy.max_nodes,
                    'target_cpu': policy.target_cpu_utilization,
                    'target_memory': policy.target_memory_utilization
                }
            
            return {
                'scaling_active': self.scaling_active,
                'total_policies': len(self.policies),
                'recent_scaling_events': recent_events,
                'recent_metrics': [asdict(m) for m in recent_metrics],
                'policy_status': policy_status,
                'cooldown_status': {
                    'scale_up_ready': (datetime.utcnow() - self.last_scale_up).total_seconds() > 300,
                    'scale_down_ready': (datetime.utcnow() - self.last_scale_down).total_seconds() > 600
                }
            }


class HorizontalScalingOrchestrator:
    """Main horizontal scaling orchestrator"""
    
    def __init__(self, max_nodes: int = 100):
        self.max_nodes = max_nodes
        
        # Core components
        self.task_queue = DistributedTaskQueue()
        self.load_balancer = IntelligentLoadBalancer(LoadBalancingStrategy.AI_OPTIMIZED)
        self.auto_scaler = AutoScalingController(self.load_balancer)
        
        # Processing
        self.processing_active = False
        self.processing_tasks: List[asyncio.Task] = []
        
        # Add default scaling policy
        default_policy = AutoScalingPolicy(
            policy_id="default_policy",
            name="Default Auto-Scaling Policy",
            min_nodes=2,
            max_nodes=max_nodes,
            target_cpu_utilization=70.0,
            target_memory_utilization=80.0,
            scale_up_threshold=85.0,
            scale_down_threshold=30.0,
            scale_up_cooldown=300,  # 5 minutes
            scale_down_cooldown=600,  # 10 minutes
            predictive_scaling=True
        )
        
        self.auto_scaler.add_scaling_policy(default_policy)
        
        # Initialize with some worker nodes
        self._initialize_worker_nodes()
    
    def _initialize_worker_nodes(self):
        """Initialize initial set of worker nodes"""
        for i in range(2):  # Start with 2 nodes
            node_id = f"worker_{uuid.uuid4().hex[:8]}"
            node = WorkerNode(
                node_id=node_id,
                host=f"10.0.0.{10 + i}",
                port=8080,
                status=NodeStatus.HEALTHY,
                cpu_usage=20.0 + i * 10,
                memory_usage=30.0 + i * 5,
                active_tasks=0,
                max_tasks=10,
                last_heartbeat=datetime.utcnow(),
                capabilities=["document_processing", "ml_inference", "data_analysis"]
            )
            
            self.load_balancer.register_node(node)
    
    async def start_processing(self):
        """Start horizontal scaling and task processing"""
        if self.processing_active:
            return
        
        self.processing_active = True
        
        # Start processing tasks
        tasks = [
            asyncio.create_task(self._task_processing_loop()),
            asyncio.create_task(self._auto_scaling_loop()),
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._metrics_collection_loop())
        ]
        
        self.processing_tasks.extend(tasks)
        logging.info("Horizontal scaling orchestrator started")
    
    async def _task_processing_loop(self):
        """Main task processing loop"""
        while self.processing_active:
            try:
                # Process tasks for each healthy node
                healthy_nodes = [
                    n for n in self.load_balancer.nodes.values()
                    if n.status == NodeStatus.HEALTHY and n.active_tasks < n.max_tasks
                ]
                
                for node in healthy_nodes:
                    # Try to assign a task to this node
                    task = self.task_queue.dequeue_task(node.node_id, node.capabilities)
                    if task:
                        # Simulate task processing
                        asyncio.create_task(self._process_task_on_node(task, node))
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logging.error(f"Task processing error: {e}")
                await asyncio.sleep(5)
    
    async def _process_task_on_node(self, task: ScalingTask, node: WorkerNode):
        """Process a task on a specific node"""
        try:
            start_time = time.time()
            
            # Update node status
            node.active_tasks += 1
            
            # Simulate task processing (would be actual work here)
            processing_time = 0.5 + task.priority.value * 0.2
            await asyncio.sleep(processing_time)
            
            # Simulate success/failure
            success = task.retry_count < 2 or task.priority != TaskPriority.LOW  # Most tasks succeed
            
            if success:
                result = {
                    'task_id': task.task_id,
                    'node_id': node.node_id,
                    'processing_time': processing_time,
                    'status': 'completed'
                }
                
                self.task_queue.complete_task(task.task_id, result)
                node.total_processed += 1
                
            else:
                # Task failed, retry if possible
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.assigned_node = None
                    task.started_at = None
                    self.task_queue.enqueue_task(task)  # Re-queue for retry
                else:
                    self.task_queue.complete_task(task.task_id, error="Max retries exceeded")
                    node.error_count += 1
            
            # Update node metrics
            processing_duration = time.time() - start_time
            self.load_balancer.update_node_metrics(
                node.node_id,
                node.cpu_usage,
                node.memory_usage,
                node.active_tasks - 1,
                processing_duration * 1000
            )
            
            node.active_tasks -= 1
            
        except Exception as e:
            logging.error(f"Task processing error on node {node.node_id}: {e}")
            node.active_tasks = max(0, node.active_tasks - 1)
            node.error_count += 1
            self.task_queue.complete_task(task.task_id, error=str(e))
    
    async def _auto_scaling_loop(self):
        """Auto-scaling evaluation and execution loop"""
        while self.processing_active:
            try:
                recommendations = await self.auto_scaler.evaluate_scaling()
                
                for recommendation in recommendations:
                    success = await self.auto_scaler.execute_scaling_action(recommendation)
                    if success:
                        logging.info(f"Executed scaling recommendation: {recommendation}")
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except Exception as e:
                logging.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(30)
    
    async def _health_monitoring_loop(self):
        """Monitor node health and update status"""
        while self.processing_active:
            try:
                current_time = datetime.utcnow()
                
                for node in list(self.load_balancer.nodes.values()):
                    # Check heartbeat timeout
                    time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > 300:  # 5 minutes timeout
                        node.status = NodeStatus.UNHEALTHY
                        logging.warning(f"Node {node.node_id} marked as unhealthy (no heartbeat)")
                    elif time_since_heartbeat > 120:  # 2 minutes warning
                        node.status = NodeStatus.DEGRADED
                    else:
                        if node.status in [NodeStatus.UNHEALTHY, NodeStatus.DEGRADED]:
                            node.status = NodeStatus.HEALTHY
                    
                    # Simulate heartbeat updates (would come from actual nodes)
                    if node.status == NodeStatus.HEALTHY:
                        # Simulate varying resource usage
                        node.cpu_usage = max(10, min(95, node.cpu_usage + (time.time() % 10 - 5)))
                        node.memory_usage = max(20, min(90, node.memory_usage + (time.time() % 8 - 4)))
                        node.last_heartbeat = current_time
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logging.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collection_loop(self):
        """Collect and log system metrics"""
        while self.processing_active:
            try:
                queue_status = self.task_queue.get_queue_status()
                lb_stats = self.load_balancer.get_load_balancing_stats()
                scaling_status = self.auto_scaler.get_scaling_status()
                
                metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_metrics': queue_status,
                    'load_balancer_metrics': lb_stats,
                    'scaling_metrics': scaling_status
                }
                
                logging.info(f"System metrics collected: "
                           f"Nodes: {lb_stats['healthy_nodes']}/{lb_stats['total_nodes']}, "
                           f"Pending tasks: {queue_status['total_pending']}, "
                           f"Completed: {queue_status['total_completed']}")
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    def submit_task(self, task_type: str, payload: Dict[str, Any], 
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   timeout_seconds: int = 300) -> str:
        """Submit a task for processing"""
        task_id = f"task_{uuid.uuid4().hex}"
        
        task = ScalingTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            payload=payload,
            created_at=datetime.utcnow(),
            timeout_seconds=timeout_seconds
        )
        
        success = self.task_queue.enqueue_task(task)
        if success:
            logging.info(f"Task {task_id} submitted successfully")
            return task_id
        else:
            logging.error(f"Failed to submit task {task_id} - queue full")
            raise Exception("Task queue is full")
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a completed task"""
        return self.task_queue.task_results.get(task_id)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        queue_status = self.task_queue.get_queue_status()
        lb_stats = self.load_balancer.get_load_balancing_stats()
        scaling_status = self.auto_scaler.get_scaling_status()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'processing_active': self.processing_active,
            'task_queue': queue_status,
            'load_balancing': lb_stats,
            'auto_scaling': scaling_status,
            'system_health': {
                'healthy_nodes': lb_stats['healthy_nodes'],
                'total_nodes': lb_stats['total_nodes'],
                'queue_utilization': queue_status['total_pending'] / 10000,  # Assuming max 10k queue
                'throughput': queue_status['statistics']['total_completed'] / max(1, time.time() - 3600)  # Last hour
            }
        }
    
    def stop_processing(self):
        """Stop horizontal scaling orchestrator"""
        self.processing_active = False
        
        for task in self.processing_tasks:
            task.cancel()
        
        self.processing_tasks.clear()
        logging.info("Horizontal scaling orchestrator stopped")


# Example usage and testing
if __name__ == "__main__":
    async def test_horizontal_scaling():
        """Test the horizontal scaling orchestrator"""
        print("🔄 Testing Horizontal Scaling Orchestrator v3.0")
        
        # Create orchestrator
        orchestrator = HorizontalScalingOrchestrator(max_nodes=10)
        
        # Start processing
        await orchestrator.start_processing()
        
        # Submit test tasks
        task_types = ["document_processing", "ml_inference", "data_analysis"]
        priorities = [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL]
        
        submitted_tasks = []
        
        for i in range(20):
            task_id = orchestrator.submit_task(
                task_type=task_types[i % len(task_types)],
                payload={"document_id": f"doc_{i}", "content": f"Test content {i}"},
                priority=priorities[i % len(priorities)]
            )
            submitted_tasks.append(task_id)
        
        print(f"Submitted {len(submitted_tasks)} tasks")
        
        # Let the system process for a while
        await asyncio.sleep(10)
        
        # Check results
        completed_results = 0
        for task_id in submitted_tasks:
            result = orchestrator.get_task_result(task_id)
            if result:
                completed_results += 1
        
        print(f"Completed {completed_results}/{len(submitted_tasks)} tasks")
        
        # Get comprehensive status
        status = orchestrator.get_comprehensive_status()
        print(f"\nSystem Status:")
        print(f"Healthy Nodes: {status['system_health']['healthy_nodes']}")
        print(f"Total Tasks Completed: {status['task_queue']['statistics']['total_completed']}")
        print(f"Queue Utilization: {status['system_health']['queue_utilization']:.2%}")
        
        # Stop processing
        orchestrator.stop_processing()
        print("\nHorizontal scaling test completed")
    
    # Run test
    asyncio.run(test_horizontal_scaling())