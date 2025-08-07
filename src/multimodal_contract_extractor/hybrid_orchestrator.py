"""Hybrid orchestrator for coordinating neuromorphic, quantum, and classical processing.

This module provides intelligent orchestration of different processing modes,
dynamic load balancing, and adaptive strategy selection for optimal performance.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    """Orchestrator processing modes."""
    AUTO_SELECT = "auto_select"
    PARALLEL_ENSEMBLE = "parallel_ensemble"
    SEQUENTIAL_FALLBACK = "sequential_fallback"
    WEIGHTED_CONSENSUS = "weighted_consensus"
    ADAPTIVE_ROUTING = "adaptive_routing"


class ProcessorType(Enum):
    """Available processor types."""
    NEUROMORPHIC = "neuromorphic"
    QUANTUM = "quantum"  
    CLASSICAL = "classical"
    HYBRID = "hybrid"


@dataclass
class ProcessorMetrics:
    """Performance metrics for a processor."""
    
    processor_type: ProcessorType
    success_rate: float = 0.0
    average_time: float = 0.0
    accuracy_score: float = 0.0
    energy_efficiency: float = 0.0
    reliability_score: float = 0.0
    cost_per_operation: float = 0.0
    last_updated: float = field(default_factory=time.time)
    
    def overall_score(self) -> float:
        """Calculate overall performance score."""
        weights = {
            "success_rate": 0.25,
            "accuracy_score": 0.25,
            "energy_efficiency": 0.15,
            "reliability_score": 0.15,
            "speed": 0.2  # Inverse of processing time
        }
        
        speed_score = max(0, 1.0 - (self.average_time / 30.0))  # Normalize to 30s max
        
        score = (
            self.success_rate * weights["success_rate"] +
            self.accuracy_score * weights["accuracy_score"] +
            self.energy_efficiency * weights["energy_efficiency"] +
            self.reliability_score * weights["reliability_score"] +
            speed_score * weights["speed"]
        )
        
        return min(max(score, 0.0), 1.0)


@dataclass
class ProcessingTask:
    """Represents a processing task with requirements."""
    
    task_id: str
    document: Any
    language_code: str = "en"
    priority: int = 1  # 1=low, 5=high
    deadline: Optional[float] = None
    accuracy_requirement: float = 0.8
    max_processing_time: float = 30.0
    energy_constraint: Optional[float] = None
    preferred_processors: List[ProcessorType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result from hybrid processing."""
    
    task_id: str
    success: bool
    processor_used: ProcessorType
    clauses_detected: List[Any]
    confidence_score: float
    processing_time: float
    energy_consumed: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ProcessorPool:
    """Pool of available processors with load balancing."""
    
    def __init__(self):
        self.processors: Dict[ProcessorType, Any] = {}
        self.metrics: Dict[ProcessorType, ProcessorMetrics] = {}
        self.load_balancer = LoadBalancer()
        self.health_monitor = ProcessorHealthMonitor()
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize available processors."""
        # Initialize metrics for all processor types
        for processor_type in ProcessorType:
            self.metrics[processor_type] = ProcessorMetrics(
                processor_type=processor_type,
                success_rate=0.8,  # Initial estimate
                average_time=10.0,
                accuracy_score=0.75,
                energy_efficiency=0.7,
                reliability_score=0.8
            )
        
        logger.info("Processor pool initialized with all processor types")
    
    def get_processor(self, processor_type: ProcessorType):
        """Get processor instance (lazy loading)."""
        if processor_type not in self.processors:
            if processor_type == ProcessorType.NEUROMORPHIC:
                try:
                    from .neuromorphic_processing import get_neuromorphic_processor
                    self.processors[processor_type] = get_neuromorphic_processor()
                except ImportError as e:
                    logger.error(f"Failed to load neuromorphic processor: {e}")
                    return None
            elif processor_type == ProcessorType.QUANTUM:
                try:
                    from .quantum_enhanced_extraction import get_quantum_processor
                    self.processors[processor_type] = get_quantum_processor()
                except ImportError as e:
                    logger.error(f"Failed to load quantum processor: {e}")
                    return None
            elif processor_type == ProcessorType.CLASSICAL:
                # Classical processor would be implemented here
                from . import detect_clauses  # Use existing clause detection
                self.processors[processor_type] = detect_clauses
            else:
                logger.error(f"Unknown processor type: {processor_type}")
                return None
        
        return self.processors.get(processor_type)
    
    def update_metrics(self, processor_type: ProcessorType, 
                      processing_time: float, success: bool, 
                      accuracy: float, energy_used: float = 0.0):
        """Update processor performance metrics."""
        if processor_type not in self.metrics:
            return
        
        metrics = self.metrics[processor_type]
        
        # Exponential moving average for metrics
        alpha = 0.1  # Learning rate
        
        if success:
            metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * 1.0
            metrics.accuracy_score = (1 - alpha) * metrics.accuracy_score + alpha * accuracy
        else:
            metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * 0.0
        
        metrics.average_time = (1 - alpha) * metrics.average_time + alpha * processing_time
        
        if energy_used > 0:
            # Energy efficiency: higher is better (less energy per operation)
            efficiency = 1.0 / (1.0 + energy_used)
            metrics.energy_efficiency = (1 - alpha) * metrics.energy_efficiency + alpha * efficiency
        
        metrics.last_updated = time.time()
        
        logger.debug(f"Updated {processor_type.value} metrics: "
                    f"success={metrics.success_rate:.3f}, "
                    f"time={metrics.average_time:.3f}, "
                    f"accuracy={metrics.accuracy_score:.3f}")
    
    def get_best_processor(self, requirements: ProcessingTask) -> Optional[ProcessorType]:
        """Select best processor based on requirements and current metrics."""
        available_processors = []
        
        # Filter by preferred processors if specified
        if requirements.preferred_processors:
            candidate_types = requirements.preferred_processors
        else:
            candidate_types = list(ProcessorType)
        
        # Check availability and health
        for proc_type in candidate_types:
            if self.health_monitor.is_healthy(proc_type):
                processor = self.get_processor(proc_type)
                if processor is not None:
                    available_processors.append(proc_type)
        
        if not available_processors:
            logger.warning("No healthy processors available")
            return None
        
        # Score processors based on requirements
        processor_scores = {}
        for proc_type in available_processors:
            score = self._score_processor(proc_type, requirements)
            processor_scores[proc_type] = score
        
        # Select processor with highest score
        best_processor = max(processor_scores.items(), key=lambda x: x[1])
        
        logger.info(f"Selected {best_processor[0].value} processor "
                   f"(score: {best_processor[1]:.3f}) for task {requirements.task_id}")
        
        return best_processor[0]
    
    def _score_processor(self, processor_type: ProcessorType, requirements: ProcessingTask) -> float:
        """Score processor for given requirements."""
        metrics = self.metrics.get(processor_type)
        if not metrics:
            return 0.0
        
        score = metrics.overall_score()
        
        # Apply requirement-specific adjustments
        # Accuracy requirement
        if metrics.accuracy_score < requirements.accuracy_requirement:
            score *= 0.5  # Heavy penalty for insufficient accuracy
        
        # Time constraint
        if metrics.average_time > requirements.max_processing_time:
            score *= 0.7  # Penalty for slow processing
        
        # Energy constraint
        if (requirements.energy_constraint and 
            metrics.energy_efficiency < requirements.energy_constraint):
            score *= 0.8  # Penalty for high energy usage
        
        # Priority boost for high-priority tasks
        if requirements.priority >= 4:
            score *= 1.1
        
        # Processor-specific bonuses
        processor_bonuses = {
            ProcessorType.NEUROMORPHIC: 0.05,  # Bonus for pattern recognition
            ProcessorType.QUANTUM: 0.1,        # Bonus for complex problems
            ProcessorType.CLASSICAL: 0.0,      # Baseline
            ProcessorType.HYBRID: 0.15         # Bonus for versatility
        }
        
        bonus = processor_bonuses.get(processor_type, 0.0)
        score += bonus
        
        return min(score, 1.0)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all processor metrics."""
        summary = {}
        for proc_type, metrics in self.metrics.items():
            summary[proc_type.value] = {
                "overall_score": metrics.overall_score(),
                "success_rate": metrics.success_rate,
                "average_time": metrics.average_time,
                "accuracy_score": metrics.accuracy_score,
                "energy_efficiency": metrics.energy_efficiency,
                "reliability_score": metrics.reliability_score,
                "last_updated": metrics.last_updated
            }
        return summary


class LoadBalancer:
    """Intelligent load balancing for processor allocation."""
    
    def __init__(self):
        self.current_loads: Dict[ProcessorType, int] = {}
        self.max_concurrent: Dict[ProcessorType, int] = {
            ProcessorType.NEUROMORPHIC: 3,
            ProcessorType.QUANTUM: 2,
            ProcessorType.CLASSICAL: 5,
            ProcessorType.HYBRID: 2
        }
        self.queue_depths: Dict[ProcessorType, int] = {}
    
    def can_process(self, processor_type: ProcessorType) -> bool:
        """Check if processor can handle another task."""
        current_load = self.current_loads.get(processor_type, 0)
        max_load = self.max_concurrent.get(processor_type, 1)
        return current_load < max_load
    
    def allocate_processor(self, processor_type: ProcessorType) -> bool:
        """Attempt to allocate processor resources."""
        if self.can_process(processor_type):
            self.current_loads[processor_type] = self.current_loads.get(processor_type, 0) + 1
            logger.debug(f"Allocated {processor_type.value} processor "
                        f"({self.current_loads[processor_type]}/{self.max_concurrent[processor_type]})")
            return True
        return False
    
    def release_processor(self, processor_type: ProcessorType):
        """Release processor resources."""
        if processor_type in self.current_loads:
            self.current_loads[processor_type] = max(0, self.current_loads[processor_type] - 1)
            logger.debug(f"Released {processor_type.value} processor "
                        f"({self.current_loads[processor_type]}/{self.max_concurrent[processor_type]})")
    
    def get_load_status(self) -> Dict[str, Any]:
        """Get current load status."""
        return {
            "current_loads": {k.value: v for k, v in self.current_loads.items()},
            "max_concurrent": {k.value: v for k, v in self.max_concurrent.items()},
            "utilization": {
                k.value: (self.current_loads.get(k, 0) / v) * 100
                for k, v in self.max_concurrent.items()
            }
        }


class ProcessorHealthMonitor:
    """Monitors processor health and availability."""
    
    def __init__(self):
        self.health_status: Dict[ProcessorType, bool] = {}
        self.last_health_check: Dict[ProcessorType, float] = {}
        self.health_check_interval = 60.0  # 1 minute
    
    def is_healthy(self, processor_type: ProcessorType) -> bool:
        """Check if processor is healthy."""
        current_time = time.time()
        last_check = self.last_health_check.get(processor_type, 0)
        
        # Perform health check if needed
        if current_time - last_check > self.health_check_interval:
            self._perform_health_check(processor_type)
            self.last_health_check[processor_type] = current_time
        
        return self.health_status.get(processor_type, True)  # Default to healthy
    
    def _perform_health_check(self, processor_type: ProcessorType):
        """Perform health check on processor."""
        try:
            # Basic availability check (would be more comprehensive in real implementation)
            if processor_type == ProcessorType.NEUROMORPHIC:
                from .neuromorphic_processing import get_neuromorphic_processor
                processor = get_neuromorphic_processor()
                # Simple check - can get statistics
                stats = processor.get_processing_statistics()
                self.health_status[processor_type] = True
            elif processor_type == ProcessorType.QUANTUM:
                from .quantum_enhanced_extraction import get_quantum_processor
                processor = get_quantum_processor()
                stats = processor.get_quantum_statistics()
                self.health_status[processor_type] = True
            elif processor_type == ProcessorType.CLASSICAL:
                # Classical processing is always healthy
                self.health_status[processor_type] = True
            else:
                self.health_status[processor_type] = True
        except Exception as e:
            logger.warning(f"Health check failed for {processor_type.value}: {e}")
            self.health_status[processor_type] = False


class HybridOrchestrator:
    """Main orchestrator for hybrid processing strategies."""
    
    def __init__(self, mode: OrchestratorMode = OrchestratorMode.AUTO_SELECT):
        self.mode = mode
        self.processor_pool = ProcessorPool()
        self.task_queue: List[ProcessingTask] = []
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: Dict[str, ProcessingResult] = {}
        self.orchestration_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "average_processing_time": 0.0,
            "processor_usage": {pt.value: 0 for pt in ProcessorType}
        }
        
        logger.info(f"Hybrid orchestrator initialized with mode: {mode.value}")
    
    async def process_document(self, document, language_code: str = "en",
                              priority: int = 1, **kwargs) -> ProcessingResult:
        """Process single document using optimal strategy."""
        task = ProcessingTask(
            task_id=f"task_{int(time.time() * 1000)}",
            document=document,
            language_code=language_code,
            priority=priority,
            accuracy_requirement=kwargs.get("accuracy_requirement", 0.8),
            max_processing_time=kwargs.get("max_processing_time", 30.0),
            energy_constraint=kwargs.get("energy_constraint"),
            preferred_processors=kwargs.get("preferred_processors", []),
            metadata=kwargs
        )
        
        return await self._execute_task(task)
    
    async def process_batch(self, tasks: List[ProcessingTask]) -> List[ProcessingResult]:
        """Process multiple documents in batch."""
        logger.info(f"Processing batch of {len(tasks)} tasks")
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        results = []
        
        if self.mode == OrchestratorMode.PARALLEL_ENSEMBLE:
            # Process tasks in parallel where possible
            results = await self._process_parallel_ensemble(sorted_tasks)
        elif self.mode == OrchestratorMode.SEQUENTIAL_FALLBACK:
            # Process tasks sequentially with fallback
            for task in sorted_tasks:
                result = await self._execute_task_with_fallback(task)
                results.append(result)
        else:
            # Auto-select mode - process individually with best processor
            batch_tasks = []
            for task in sorted_tasks:
                batch_tasks.append(self._execute_task(task))
            
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {sorted_tasks[i].task_id} failed: {result}")
                    results[i] = ProcessingResult(
                        task_id=sorted_tasks[i].task_id,
                        success=False,
                        processor_used=ProcessorType.CLASSICAL,
                        clauses_detected=[],
                        confidence_score=0.0,
                        processing_time=0.0,
                        energy_consumed=0.0,
                        error_message=str(result)
                    )
        
        return results
    
    async def _execute_task(self, task: ProcessingTask) -> ProcessingResult:
        """Execute a single processing task."""
        start_time = time.perf_counter()
        self.active_tasks[task.task_id] = task
        
        logger.info(f"Executing task {task.task_id} with priority {task.priority}")
        
        try:
            # Select best processor
            processor_type = self.processor_pool.get_best_processor(task)
            if not processor_type:
                raise Exception("No available processors")
            
            # Allocate processor resources
            if not self.processor_pool.load_balancer.allocate_processor(processor_type):
                # Try fallback processor
                processor_type = await self._select_fallback_processor(task)
                if not processor_type:
                    raise Exception("All processors are busy")
                self.processor_pool.load_balancer.allocate_processor(processor_type)
            
            try:
                # Process document
                result = await self._process_with_processor(task, processor_type)
                
                # Update metrics
                processing_time = time.perf_counter() - start_time
                self.processor_pool.update_metrics(
                    processor_type, processing_time, result.success, 
                    result.confidence_score, result.energy_consumed
                )
                
                # Update orchestration stats
                self._update_orchestration_stats(processor_type, processing_time, result.success)
                
                return result
                
            finally:
                # Release processor resources
                self.processor_pool.load_balancer.release_processor(processor_type)
                
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            processing_time = time.perf_counter() - start_time
            
            return ProcessingResult(
                task_id=task.task_id,
                success=False,
                processor_used=ProcessorType.CLASSICAL,
                clauses_detected=[],
                confidence_score=0.0,
                processing_time=processing_time,
                energy_consumed=0.0,
                error_message=str(e)
            )
        finally:
            # Clean up
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _process_with_processor(self, task: ProcessingTask, 
                                    processor_type: ProcessorType) -> ProcessingResult:
        """Process task with specific processor type."""
        start_time = time.perf_counter()
        
        try:
            if processor_type == ProcessorType.NEUROMORPHIC:
                from .neuromorphic_processing import process_document_with_neuromorphics
                neuro_result = await process_document_with_neuromorphics(
                    task.document, task.language_code
                )
                
                clauses = []
                for clause in neuro_result.detected_clauses:
                    clauses.append({
                        "id": clause.clause_id,
                        "type": clause.clause_type,
                        "text": clause.text,
                        "confidence": clause.confidence,
                        "page": clause.page
                    })
                
                return ProcessingResult(
                    task_id=task.task_id,
                    success=True,
                    processor_used=processor_type,
                    clauses_detected=clauses,
                    confidence_score=neuro_result.spike_efficiency,
                    processing_time=neuro_result.processing_time,
                    energy_consumed=neuro_result.energy_consumption,
                    metadata={"total_spikes": neuro_result.total_spikes}
                )
                
            elif processor_type == ProcessorType.QUANTUM:
                from .quantum_enhanced_extraction import process_document_with_quantum_enhancement
                quantum_result = await process_document_with_quantum_enhancement(
                    task.document, task.language_code
                )
                
                clauses = []
                for clause in quantum_result.detected_clauses:
                    clauses.append({
                        "id": clause.clause_id,
                        "type": clause.clause_type,
                        "text": clause.text,
                        "confidence": clause.quantum_confidence,
                        "page": clause.page,
                        "quantum_fidelity": clause.quantum_fidelity
                    })
                
                return ProcessingResult(
                    task_id=task.task_id,
                    success=True,
                    processor_used=processor_type,
                    clauses_detected=clauses,
                    confidence_score=quantum_result.circuit_fidelity,
                    processing_time=quantum_result.processing_time,
                    energy_consumed=0.0,  # Quantum energy not modeled
                    metadata={
                        "entanglement_entropy": quantum_result.entanglement_entropy,
                        "quantum_advantage": quantum_result.quantum_advantage_score
                    }
                )
                
            elif processor_type == ProcessorType.CLASSICAL:
                from . import detect_clauses
                
                # Simulate classical processing
                await asyncio.sleep(0.1)  # Simulate processing time
                clauses = detect_clauses(task.document, language_code=task.language_code)
                
                clauses_data = []
                for clause in clauses:
                    clauses_data.append({
                        "id": clause.id,
                        "type": clause.type,
                        "text": clause.text,
                        "confidence": clause.confidence,
                        "page": clause.page
                    })
                
                processing_time = time.perf_counter() - start_time
                
                return ProcessingResult(
                    task_id=task.task_id,
                    success=True,
                    processor_used=processor_type,
                    clauses_detected=clauses_data,
                    confidence_score=0.8,  # Default confidence
                    processing_time=processing_time,
                    energy_consumed=1.0,  # Baseline energy
                    metadata={"method": "classical"}
                )
                
            else:
                raise Exception(f"Unsupported processor type: {processor_type}")
                
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error(f"Processing failed with {processor_type.value}: {e}")
            
            return ProcessingResult(
                task_id=task.task_id,
                success=False,
                processor_used=processor_type,
                clauses_detected=[],
                confidence_score=0.0,
                processing_time=processing_time,
                energy_consumed=0.0,
                error_message=str(e)
            )
    
    async def _select_fallback_processor(self, task: ProcessingTask) -> Optional[ProcessorType]:
        """Select fallback processor when primary is unavailable."""
        fallback_order = [
            ProcessorType.CLASSICAL,  # Most reliable
            ProcessorType.NEUROMORPHIC,
            ProcessorType.QUANTUM
        ]
        
        for processor_type in fallback_order:
            if (self.processor_pool.load_balancer.can_process(processor_type) and
                self.processor_pool.health_monitor.is_healthy(processor_type)):
                logger.info(f"Selected fallback processor: {processor_type.value}")
                return processor_type
        
        return None
    
    async def _process_parallel_ensemble(self, tasks: List[ProcessingTask]) -> List[ProcessingResult]:
        """Process tasks using parallel ensemble approach."""
        logger.info("Using parallel ensemble processing")
        
        # Group tasks by estimated processing requirements
        high_priority = [t for t in tasks if t.priority >= 4]
        normal_priority = [t for t in tasks if t.priority < 4]
        
        results = []
        
        # Process high priority tasks first
        if high_priority:
            high_priority_tasks = [self._execute_task(task) for task in high_priority]
            high_priority_results = await asyncio.gather(*high_priority_tasks, return_exceptions=True)
            results.extend(high_priority_results)
        
        # Process normal priority tasks in parallel
        if normal_priority:
            # Limit concurrent tasks to avoid overload
            batch_size = 3
            for i in range(0, len(normal_priority), batch_size):
                batch = normal_priority[i:i + batch_size]
                batch_tasks = [self._execute_task(task) for task in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                results.extend(batch_results)
        
        return results
    
    async def _execute_task_with_fallback(self, task: ProcessingTask) -> ProcessingResult:
        """Execute task with fallback strategy."""
        fallback_processors = [
            ProcessorType.QUANTUM,
            ProcessorType.NEUROMORPHIC, 
            ProcessorType.CLASSICAL
        ]
        
        last_error = None
        
        for processor_type in fallback_processors:
            try:
                if (self.processor_pool.health_monitor.is_healthy(processor_type) and
                    self.processor_pool.load_balancer.allocate_processor(processor_type)):
                    
                    try:
                        result = await self._process_with_processor(task, processor_type)
                        if result.success:
                            return result
                        else:
                            last_error = result.error_message
                    finally:
                        self.processor_pool.load_balancer.release_processor(processor_type)
                        
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Fallback attempt with {processor_type.value} failed: {e}")
                continue
        
        # All fallback attempts failed
        return ProcessingResult(
            task_id=task.task_id,
            success=False,
            processor_used=ProcessorType.CLASSICAL,
            clauses_detected=[],
            confidence_score=0.0,
            processing_time=0.0,
            energy_consumed=0.0,
            error_message=f"All fallback attempts failed. Last error: {last_error}"
        )
    
    def _update_orchestration_stats(self, processor_type: ProcessorType, 
                                  processing_time: float, success: bool):
        """Update orchestration statistics."""
        self.orchestration_stats["total_tasks"] += 1
        
        if success:
            self.orchestration_stats["successful_tasks"] += 1
        
        # Update average processing time
        total_tasks = self.orchestration_stats["total_tasks"]
        current_avg = self.orchestration_stats["average_processing_time"]
        self.orchestration_stats["average_processing_time"] = (
            (current_avg * (total_tasks - 1) + processing_time) / total_tasks
        )
        
        # Update processor usage
        self.orchestration_stats["processor_usage"][processor_type.value] += 1
    
    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration statistics."""
        stats = self.orchestration_stats.copy()
        
        # Calculate success rate
        if stats["total_tasks"] > 0:
            stats["success_rate"] = stats["successful_tasks"] / stats["total_tasks"]
        else:
            stats["success_rate"] = 0.0
        
        # Add processor metrics
        stats["processor_metrics"] = self.processor_pool.get_metrics_summary()
        
        # Add load balancing status
        stats["load_balancing"] = self.processor_pool.load_balancer.get_load_status()
        
        # Add active task count
        stats["active_tasks"] = len(self.active_tasks)
        
        return stats
    
    def optimize_configuration(self):
        """Optimize orchestrator configuration based on performance history."""
        metrics_summary = self.processor_pool.get_metrics_summary()
        
        # Find best performing processor
        best_processor = None
        best_score = 0.0
        
        for proc_type_str, metrics in metrics_summary.items():
            if metrics["overall_score"] > best_score:
                best_score = metrics["overall_score"]
                best_processor = proc_type_str
        
        if best_processor:
            logger.info(f"Best performing processor: {best_processor} (score: {best_score:.3f})")
            
            # Adjust load balancer limits based on performance
            proc_type = ProcessorType(best_processor)
            current_limit = self.processor_pool.load_balancer.max_concurrent.get(proc_type, 1)
            
            if best_score > 0.8 and current_limit < 5:
                # Increase capacity for high-performing processors
                self.processor_pool.load_balancer.max_concurrent[proc_type] = current_limit + 1
                logger.info(f"Increased {best_processor} capacity to {current_limit + 1}")


# Global orchestrator instance
_orchestrator: Optional[HybridOrchestrator] = None


def get_orchestrator(mode: OrchestratorMode = OrchestratorMode.AUTO_SELECT) -> HybridOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HybridOrchestrator(mode)
    return _orchestrator


async def process_document_hybrid(document, language_code: str = "en", **kwargs) -> ProcessingResult:
    """Main entry point for hybrid document processing."""
    orchestrator = get_orchestrator()
    return await orchestrator.process_document(document, language_code, **kwargs)


async def process_batch_hybrid(documents: List[Any], language_code: str = "en", 
                              priorities: Optional[List[int]] = None, **kwargs) -> List[ProcessingResult]:
    """Process multiple documents using hybrid orchestration."""
    orchestrator = get_orchestrator()
    
    if priorities is None:
        priorities = [1] * len(documents)
    
    tasks = []
    for i, document in enumerate(documents):
        task = ProcessingTask(
            task_id=f"batch_task_{i}",
            document=document,
            language_code=language_code,
            priority=priorities[i] if i < len(priorities) else 1,
            **kwargs
        )
        tasks.append(task)
    
    return await orchestrator.process_batch(tasks)