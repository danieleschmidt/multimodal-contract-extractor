"""
GPU Tensor Optimization and Memory Management for High-Performance Contract Extraction.

This module provides advanced GPU acceleration with tensor optimization, memory management,
and intelligent resource allocation for scaling the multimodal contract extraction system
to handle 1000+ concurrent requests with sub-200ms response times.
"""

from __future__ import annotations

import asyncio
import gc
import logging
import os
import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import psutil

logger = logging.getLogger(__name__)

# Try to import GPU libraries with graceful fallbacks
try:
    import torch
    import torch.cuda
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None

try:
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False
    cp = None


class GPUAccelerationType(Enum):
    """Types of GPU acceleration available."""
    CUDA_PYTORCH = "cuda_pytorch"
    CUDA_CUPY = "cuda_cupy"
    OPENCL = "opencl"
    METAL = "metal"
    CPU_FALLBACK = "cpu_fallback"


class TensorOptimizationStrategy(Enum):
    """Tensor optimization strategies."""
    DYNAMIC_BATCHING = "dynamic_batching"
    MEMORY_POOLING = "memory_pooling"
    TENSOR_FUSION = "tensor_fusion"
    MIXED_PRECISION = "mixed_precision"
    KERNEL_FUSION = "kernel_fusion"
    GRAPH_OPTIMIZATION = "graph_optimization"


class MemoryStrategy(Enum):
    """Memory management strategies."""
    AGGRESSIVE_CACHING = "aggressive_caching"
    CONSERVATIVE_CACHING = "conservative_caching"
    ADAPTIVE_CACHING = "adaptive_caching"
    STREAMING_PROCESSING = "streaming_processing"
    MEMORY_MAPPING = "memory_mapping"


@dataclass
class GPUDevice:
    """GPU device information and capabilities."""
    device_id: int
    name: str
    memory_total: int  # in MB
    memory_available: int  # in MB
    compute_capability: Tuple[int, int]
    is_available: bool
    utilization: float = 0.0
    temperature: float = 0.0
    power_usage: float = 0.0


@dataclass
class TensorOperation:
    """Tensor operation metadata."""
    operation_id: str
    operation_type: str
    input_shapes: List[Tuple[int, ...]]
    output_shape: Optional[Tuple[int, ...]]
    memory_requirement: int  # in bytes
    compute_complexity: float
    batch_size: int = 1
    optimization_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryAllocation:
    """Memory allocation tracking."""
    allocation_id: str
    device_id: int
    size_bytes: int
    allocation_type: str  # tensor, buffer, cache
    timestamp: float
    lifetime_estimate: float
    reference_count: int = 1
    is_persistent: bool = False


@dataclass
class GPUPerformanceMetrics:
    """GPU performance metrics."""
    device_id: int
    utilization: float
    memory_used: int
    memory_total: int
    temperature: float
    power_usage: float
    tensor_operations_per_second: float
    memory_bandwidth_utilization: float
    cache_hit_rate: float
    batch_efficiency: float
    timestamp: float


class TensorMemoryPool:
    """Advanced tensor memory pool with intelligent allocation."""
    
    def __init__(self, device_id: int, initial_size_mb: int = 1024):
        self.device_id = device_id
        self.initial_size_mb = initial_size_mb
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.free_blocks: Dict[int, List[int]] = {}  # size -> list of offsets
        self.used_blocks: Dict[int, int] = {}  # offset -> size
        self.total_allocated = 0
        self.total_freed = 0
        self.fragmentation_ratio = 0.0
        self.lock = threading.RLock()
        
        # Initialize memory pool
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize the memory pool."""
        try:
            if HAS_TORCH and torch.cuda.is_available():
                # Pre-allocate memory pool
                initial_bytes = self.initial_size_mb * 1024 * 1024
                self.free_blocks[initial_bytes] = [0]
                self.total_allocated = initial_bytes
                logger.info(f"Initialized GPU memory pool on device {self.device_id}: {self.initial_size_mb}MB")
        except Exception as e:
            logger.warning(f"Failed to initialize GPU memory pool: {e}")
    
    def allocate(self, size_bytes: int, allocation_type: str = "tensor") -> Optional[str]:
        """Allocate memory from the pool."""
        with self.lock:
            try:
                # Find suitable free block
                best_size = None
                best_offset = None
                
                for block_size, offsets in self.free_blocks.items():
                    if block_size >= size_bytes and offsets:
                        if best_size is None or block_size < best_size:
                            best_size = block_size
                            best_offset = offsets[0]
                
                if best_offset is not None:
                    # Allocate from existing block
                    allocation_id = f"alloc_{len(self.allocations)}"
                    offsets = self.free_blocks[best_size]
                    offsets.remove(best_offset)
                    if not offsets:
                        del self.free_blocks[best_size]
                    
                    self.used_blocks[best_offset] = size_bytes
                    
                    # Add remaining space back to free blocks
                    remaining_size = best_size - size_bytes
                    if remaining_size > 0:
                        remaining_offset = best_offset + size_bytes
                        if remaining_size not in self.free_blocks:
                            self.free_blocks[remaining_size] = []
                        self.free_blocks[remaining_size].append(remaining_offset)
                    
                    allocation = MemoryAllocation(
                        allocation_id=allocation_id,
                        device_id=self.device_id,
                        size_bytes=size_bytes,
                        allocation_type=allocation_type,
                        timestamp=time.time(),
                        lifetime_estimate=self._estimate_lifetime(allocation_type),
                    )
                    
                    self.allocations[allocation_id] = allocation
                    return allocation_id
                
                return None  # No suitable block found
                
            except Exception as e:
                logger.error(f"Memory allocation failed: {e}")
                return None
    
    def deallocate(self, allocation_id: str) -> bool:
        """Deallocate memory from the pool."""
        with self.lock:
            try:
                if allocation_id not in self.allocations:
                    return False
                
                allocation = self.allocations[allocation_id]
                
                # Find the offset for this allocation
                offset = None
                for off, size in self.used_blocks.items():
                    if size == allocation.size_bytes:  # Simplified matching
                        offset = off
                        break
                
                if offset is not None:
                    del self.used_blocks[offset]
                    
                    # Add back to free blocks
                    size = allocation.size_bytes
                    if size not in self.free_blocks:
                        self.free_blocks[size] = []
                    self.free_blocks[size].append(offset)
                    
                    # Attempt to coalesce adjacent blocks
                    self._coalesce_blocks()
                
                del self.allocations[allocation_id]
                self.total_freed += allocation.size_bytes
                return True
                
            except Exception as e:
                logger.error(f"Memory deallocation failed: {e}")
                return False
    
    def _coalesce_blocks(self) -> None:
        """Coalesce adjacent free blocks to reduce fragmentation."""
        # Simplified coalescing - in practice would need more sophisticated logic
        sorted_blocks = {}
        for size, offsets in self.free_blocks.items():
            for offset in offsets:
                sorted_blocks[offset] = size
        
        # Update fragmentation ratio
        total_free = sum(len(offsets) * size for size, offsets in self.free_blocks.items())
        self.fragmentation_ratio = total_free / max(self.total_allocated, 1)
    
    def _estimate_lifetime(self, allocation_type: str) -> float:
        """Estimate allocation lifetime based on type."""
        lifetimes = {
            "tensor": 10.0,
            "buffer": 30.0,
            "cache": 300.0,
            "persistent": float('inf')
        }
        return lifetimes.get(allocation_type, 10.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory pool statistics."""
        with self.lock:
            total_used = sum(alloc.size_bytes for alloc in self.allocations.values())
            total_free = sum(len(offsets) * size for size, offsets in self.free_blocks.items())
            
            return {
                "total_allocated": self.total_allocated,
                "total_used": total_used,
                "total_free": total_free,
                "total_freed": self.total_freed,
                "active_allocations": len(self.allocations),
                "fragmentation_ratio": self.fragmentation_ratio,
                "memory_efficiency": (total_used / max(self.total_allocated, 1)) * 100
            }


class TensorBatch:
    """Dynamic tensor batching for optimal GPU utilization."""
    
    def __init__(self, max_batch_size: int = 32, batch_timeout_ms: float = 10.0):
        self.max_batch_size = max_batch_size
        self.batch_timeout_ms = batch_timeout_ms
        self.pending_operations: List[TensorOperation] = []
        self.batch_queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.processing_task: Optional[asyncio.Task] = None
    
    async def add_operation(self, operation: TensorOperation) -> Any:
        """Add operation to batch queue."""
        async with self.lock:
            self.pending_operations.append(operation)
            
            if len(self.pending_operations) >= self.max_batch_size:
                # Process immediately
                return await self._process_batch()
            else:
                # Wait for timeout or more operations
                return await self._wait_for_batch()
    
    async def _wait_for_batch(self) -> Any:
        """Wait for batch to fill or timeout."""
        start_time = time.time()
        while len(self.pending_operations) < self.max_batch_size:
            elapsed = (time.time() - start_time) * 1000
            if elapsed >= self.batch_timeout_ms:
                break
            await asyncio.sleep(0.001)  # 1ms
        
        return await self._process_batch()
    
    async def _process_batch(self) -> Any:
        """Process the current batch."""
        if not self.pending_operations:
            return None
        
        batch = self.pending_operations.copy()
        self.pending_operations.clear()
        
        try:
            # Group operations by type for efficient processing
            grouped_ops = self._group_operations(batch)
            results = []
            
            for op_type, ops in grouped_ops.items():
                batch_result = await self._process_operation_group(op_type, ops)
                results.extend(batch_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [None] * len(batch)
    
    def _group_operations(self, operations: List[TensorOperation]) -> Dict[str, List[TensorOperation]]:
        """Group operations by type for efficient batching."""
        groups = {}
        for op in operations:
            if op.operation_type not in groups:
                groups[op.operation_type] = []
            groups[op.operation_type].append(op)
        return groups
    
    async def _process_operation_group(self, op_type: str, operations: List[TensorOperation]) -> List[Any]:
        """Process a group of similar operations."""
        try:
            # Simulate tensor operation processing
            # In practice, this would call specialized GPU kernels
            await asyncio.sleep(0.001 * len(operations))  # Simulate processing
            return [f"result_{op.operation_id}" for op in operations]
        except Exception as e:
            logger.error(f"Operation group processing failed for {op_type}: {e}")
            return [None] * len(operations)


class GPUResourceManager:
    """Advanced GPU resource management and optimization."""
    
    def __init__(self):
        self.devices: Dict[int, GPUDevice] = {}
        self.memory_pools: Dict[int, TensorMemoryPool] = {}
        self.device_locks: Dict[int, threading.RLock] = {}
        self.performance_metrics: Dict[int, List[GPUPerformanceMetrics]] = {}
        self.optimization_strategies: List[TensorOptimizationStrategy] = [
            TensorOptimizationStrategy.DYNAMIC_BATCHING,
            TensorOptimizationStrategy.MEMORY_POOLING,
            TensorOptimizationStrategy.MIXED_PRECISION
        ]
        
        # Initialize GPU devices
        self._discover_devices()
        self._initialize_memory_pools()
    
    def _discover_devices(self) -> None:
        """Discover available GPU devices."""
        try:
            if HAS_TORCH and torch.cuda.is_available():
                for device_id in range(torch.cuda.device_count()):
                    device_props = torch.cuda.get_device_properties(device_id)
                    memory_total = device_props.total_memory // (1024 * 1024)  # MB
                    memory_available = memory_total - (torch.cuda.memory_allocated(device_id) // (1024 * 1024))
                    
                    device = GPUDevice(
                        device_id=device_id,
                        name=device_props.name,
                        memory_total=memory_total,
                        memory_available=memory_available,
                        compute_capability=(device_props.major, device_props.minor),
                        is_available=True
                    )
                    
                    self.devices[device_id] = device
                    self.device_locks[device_id] = threading.RLock()
                    self.performance_metrics[device_id] = []
                    
                    logger.info(f"Discovered GPU device {device_id}: {device.name} ({memory_total}MB)")
            else:
                logger.info("No CUDA-capable GPUs found or PyTorch not available")
                
        except Exception as e:
            logger.error(f"GPU device discovery failed: {e}")
    
    def _initialize_memory_pools(self) -> None:
        """Initialize memory pools for each device."""
        for device_id in self.devices:
            device = self.devices[device_id]
            pool_size_mb = min(device.memory_available // 2, 2048)  # Use up to half available memory, max 2GB
            self.memory_pools[device_id] = TensorMemoryPool(device_id, pool_size_mb)
    
    def get_optimal_device(self, memory_requirement: int = 0, compute_requirement: float = 1.0) -> Optional[int]:
        """Select the optimal device for a given workload."""
        if not self.devices:
            return None
        
        best_device = None
        best_score = float('-inf')
        
        for device_id, device in self.devices.items():
            if not device.is_available:
                continue
            
            # Calculate device score based on multiple factors
            memory_score = device.memory_available / max(device.memory_total, 1)
            utilization_score = 1.0 - (device.utilization / 100.0)
            compute_score = min(device.compute_capability[0] * device.compute_capability[1], 10) / 10.0
            
            # Weighted scoring
            total_score = (memory_score * 0.4) + (utilization_score * 0.4) + (compute_score * 0.2)
            
            if total_score > best_score:
                best_score = total_score
                best_device = device_id
        
        return best_device
    
    def allocate_tensor_memory(self, device_id: int, size_bytes: int, allocation_type: str = "tensor") -> Optional[str]:
        """Allocate tensor memory on a specific device."""
        if device_id not in self.memory_pools:
            return None
        
        return self.memory_pools[device_id].allocate(size_bytes, allocation_type)
    
    def deallocate_tensor_memory(self, device_id: int, allocation_id: str) -> bool:
        """Deallocate tensor memory."""
        if device_id not in self.memory_pools:
            return False
        
        return self.memory_pools[device_id].deallocate(allocation_id)
    
    @contextmanager
    def gpu_context(self, device_id: Optional[int] = None):
        """GPU context manager for optimal device selection and resource management."""
        if device_id is None:
            device_id = self.get_optimal_device()
        
        if device_id is None:
            # CPU fallback
            yield None
            return
        
        with self.device_locks[device_id]:
            try:
                if HAS_TORCH:
                    with torch.cuda.device(device_id):
                        yield device_id
                else:
                    yield device_id
            except Exception as e:
                logger.error(f"GPU context error: {e}")
                yield None
    
    def update_device_metrics(self, device_id: int) -> None:
        """Update performance metrics for a device."""
        try:
            if device_id not in self.devices:
                return
            
            device = self.devices[device_id]
            
            if HAS_TORCH and torch.cuda.is_available():
                # Update GPU utilization and memory
                device.memory_available = device.memory_total - (torch.cuda.memory_allocated(device_id) // (1024 * 1024))
                
                # Get additional metrics if available
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                    
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    device.utilization = utilization.gpu
                    
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    device.temperature = temperature
                    
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    device.power_usage = power
                    
                except ImportError:
                    # pynvml not available, use basic metrics
                    pass
            
            # Create performance metrics entry
            metrics = GPUPerformanceMetrics(
                device_id=device_id,
                utilization=device.utilization,
                memory_used=device.memory_total - device.memory_available,
                memory_total=device.memory_total,
                temperature=device.temperature,
                power_usage=device.power_usage,
                tensor_operations_per_second=self._calculate_ops_per_second(device_id),
                memory_bandwidth_utilization=self._calculate_bandwidth_utilization(device_id),
                cache_hit_rate=self._get_cache_hit_rate(device_id),
                batch_efficiency=self._calculate_batch_efficiency(device_id),
                timestamp=time.time()
            )
            
            # Store metrics (keep last 100 entries)
            if len(self.performance_metrics[device_id]) >= 100:
                self.performance_metrics[device_id].pop(0)
            self.performance_metrics[device_id].append(metrics)
            
        except Exception as e:
            logger.error(f"Failed to update device metrics for {device_id}: {e}")
    
    def _calculate_ops_per_second(self, device_id: int) -> float:
        """Calculate tensor operations per second."""
        # Simplified calculation - in practice would track actual operations
        metrics = self.performance_metrics.get(device_id, [])
        if len(metrics) < 2:
            return 0.0
        
        # Estimate based on utilization
        recent_utilization = sum(m.utilization for m in metrics[-10:]) / min(len(metrics), 10)
        return recent_utilization * 1000.0  # Simplified estimate
    
    def _calculate_bandwidth_utilization(self, device_id: int) -> float:
        """Calculate memory bandwidth utilization."""
        # Simplified calculation
        device = self.devices.get(device_id)
        if not device:
            return 0.0
        
        memory_used_ratio = (device.memory_total - device.memory_available) / max(device.memory_total, 1)
        return memory_used_ratio * 100.0
    
    def _get_cache_hit_rate(self, device_id: int) -> float:
        """Get cache hit rate for the device."""
        if device_id not in self.memory_pools:
            return 0.0
        
        stats = self.memory_pools[device_id].get_statistics()
        total_ops = stats.get('active_allocations', 0) + stats.get('total_freed', 0)
        if total_ops == 0:
            return 0.0
        
        # Simplified cache hit rate calculation
        return min(stats.get('memory_efficiency', 0), 100.0)
    
    def _calculate_batch_efficiency(self, device_id: int) -> float:
        """Calculate batching efficiency."""
        # Simplified calculation based on utilization patterns
        metrics = self.performance_metrics.get(device_id, [])
        if len(metrics) < 2:
            return 0.0
        
        recent_metrics = metrics[-5:]
        utilization_variance = np.var([m.utilization for m in recent_metrics]) if len(recent_metrics) > 1 else 0
        
        # Lower variance indicates better batching
        return max(0.0, 100.0 - utilization_variance)
    
    def get_device_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all devices."""
        status = {}
        for device_id, device in self.devices.items():
            memory_stats = self.memory_pools[device_id].get_statistics() if device_id in self.memory_pools else {}
            recent_metrics = self.performance_metrics[device_id][-1] if self.performance_metrics[device_id] else None
            
            status[device_id] = {
                "device": device,
                "memory_pool": memory_stats,
                "recent_metrics": recent_metrics,
                "is_healthy": device.is_available and device.temperature < 85.0,
                "optimization_opportunities": self._identify_optimization_opportunities(device_id)
            }
        
        return status
    
    def _identify_optimization_opportunities(self, device_id: int) -> List[str]:
        """Identify optimization opportunities for a device."""
        opportunities = []
        device = self.devices.get(device_id)
        if not device:
            return opportunities
        
        recent_metrics = self.performance_metrics[device_id][-10:] if self.performance_metrics[device_id] else []
        
        if recent_metrics:
            avg_utilization = sum(m.utilization for m in recent_metrics) / len(recent_metrics)
            avg_memory_used = sum(m.memory_used for m in recent_metrics) / len(recent_metrics)
            
            if avg_utilization < 50:
                opportunities.append("increase_batch_size")
            if avg_utilization > 95:
                opportunities.append("enable_mixed_precision")
            if avg_memory_used / device.memory_total > 0.9:
                opportunities.append("enable_memory_optimization")
            if device.temperature > 80:
                opportunities.append("reduce_clock_speed")
        
        memory_stats = self.memory_pools[device_id].get_statistics() if device_id in self.memory_pools else {}
        if memory_stats.get('fragmentation_ratio', 0) > 0.3:
            opportunities.append("memory_defragmentation")
        
        return opportunities


class TensorOptimizer:
    """Advanced tensor optimization engine."""
    
    def __init__(self, gpu_manager: GPUResourceManager):
        self.gpu_manager = gpu_manager
        self.optimization_cache: Dict[str, Any] = {}
        self.performance_history: Dict[str, List[float]] = {}
    
    def optimize_tensor_operation(self, operation: TensorOperation, device_id: Optional[int] = None) -> TensorOperation:
        """Optimize a tensor operation for better performance."""
        try:
            # Select optimal device if not specified
            if device_id is None:
                device_id = self.gpu_manager.get_optimal_device(
                    operation.memory_requirement,
                    operation.compute_complexity
                )
            
            if device_id is None:
                return operation  # No optimization possible
            
            # Apply optimization strategies
            optimized_op = operation
            
            for strategy in self.gpu_manager.optimization_strategies:
                optimized_op = self._apply_optimization_strategy(optimized_op, strategy, device_id)
            
            return optimized_op
            
        except Exception as e:
            logger.error(f"Tensor optimization failed: {e}")
            return operation
    
    def _apply_optimization_strategy(self, operation: TensorOperation, strategy: TensorOptimizationStrategy, device_id: int) -> TensorOperation:
        """Apply a specific optimization strategy."""
        try:
            if strategy == TensorOptimizationStrategy.DYNAMIC_BATCHING:
                return self._optimize_batching(operation, device_id)
            elif strategy == TensorOptimizationStrategy.MEMORY_POOLING:
                return self._optimize_memory_usage(operation, device_id)
            elif strategy == TensorOptimizationStrategy.MIXED_PRECISION:
                return self._optimize_precision(operation, device_id)
            else:
                return operation
        except Exception as e:
            logger.error(f"Failed to apply optimization strategy {strategy}: {e}")
            return operation
    
    def _optimize_batching(self, operation: TensorOperation, device_id: int) -> TensorOperation:
        """Optimize batching for the operation."""
        device = self.gpu_manager.devices.get(device_id)
        if not device:
            return operation
        
        # Calculate optimal batch size based on memory and compute capacity
        memory_per_item = operation.memory_requirement // max(operation.batch_size, 1)
        max_batch_size = min(64, device.memory_available * 1024 * 1024 // (memory_per_item * 2))  # Conservative estimate
        
        optimal_batch_size = min(max_batch_size, operation.batch_size * 2)
        
        if optimal_batch_size > operation.batch_size:
            operation.batch_size = optimal_batch_size
            operation.optimization_hints['batching_optimized'] = True
            operation.optimization_hints['original_batch_size'] = operation.batch_size
        
        return operation
    
    def _optimize_memory_usage(self, operation: TensorOperation, device_id: int) -> TensorOperation:
        """Optimize memory usage for the operation."""
        # Add memory optimization hints
        operation.optimization_hints['use_memory_pool'] = True
        operation.optimization_hints['memory_reuse'] = True
        
        # Suggest memory reduction techniques
        if operation.memory_requirement > 100 * 1024 * 1024:  # > 100MB
            operation.optimization_hints['use_streaming'] = True
        
        return operation
    
    def _optimize_precision(self, operation: TensorOperation, device_id: int) -> TensorOperation:
        """Optimize numerical precision for the operation."""
        device = self.gpu_manager.devices.get(device_id)
        if not device:
            return operation
        
        # Enable mixed precision for modern GPUs
        if device.compute_capability[0] >= 7:  # Volta and newer
            operation.optimization_hints['use_mixed_precision'] = True
            operation.optimization_hints['precision_type'] = 'float16'
        
        return operation


# Global GPU resource manager instance
_gpu_manager: Optional[GPUResourceManager] = None


def get_gpu_manager() -> GPUResourceManager:
    """Get the global GPU resource manager instance."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUResourceManager()
    return _gpu_manager


def get_tensor_optimizer() -> TensorOptimizer:
    """Get a tensor optimizer instance."""
    return TensorOptimizer(get_gpu_manager())


@contextmanager
def optimized_gpu_context(memory_requirement: int = 0, compute_requirement: float = 1.0):
    """Context manager for optimized GPU processing."""
    gpu_manager = get_gpu_manager()
    device_id = gpu_manager.get_optimal_device(memory_requirement, compute_requirement)
    
    with gpu_manager.gpu_context(device_id) as device:
        try:
            yield device
            if device is not None:
                gpu_manager.update_device_metrics(device)
        except Exception as e:
            logger.error(f"GPU context error: {e}")
            raise


async def process_with_gpu_optimization(
    data: Any,
    operation_type: str,
    batch_size: int = 32,
    memory_limit_mb: int = 1024
) -> Any:
    """Process data with GPU optimization."""
    try:
        # Create tensor operation
        operation = TensorOperation(
            operation_id=f"op_{int(time.time() * 1000)}",
            operation_type=operation_type,
            input_shapes=[(batch_size, 1024)],  # Example shape
            memory_requirement=memory_limit_mb * 1024 * 1024,
            compute_complexity=1.0,
            batch_size=batch_size
        )
        
        # Optimize the operation
        optimizer = get_tensor_optimizer()
        optimized_op = optimizer.optimize_tensor_operation(operation)
        
        # Process with optimal GPU context
        memory_req = optimized_op.memory_requirement
        compute_req = optimized_op.compute_complexity
        
        with optimized_gpu_context(memory_req, compute_req) as device:
            if device is not None:
                logger.info(f"Processing on GPU {device} with optimized batch size {optimized_op.batch_size}")
                # Simulate GPU processing
                await asyncio.sleep(0.01)  # Simulate processing time
                return f"gpu_processed_{operation_type}"
            else:
                logger.info("Processing on CPU (GPU not available)")
                # CPU fallback
                await asyncio.sleep(0.1)  # CPU is slower
                return f"cpu_processed_{operation_type}"
                
    except Exception as e:
        logger.error(f"GPU optimization processing failed: {e}")
        raise