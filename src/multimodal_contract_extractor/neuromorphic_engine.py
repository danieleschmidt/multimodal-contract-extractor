"""Neuromorphic Computing Engine for Contract Processing.

This module implements neuromorphic computing principles for contract analysis,
incorporating spike-based neural networks and brain-inspired processing patterns
for enhanced document understanding and clause extraction.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SpikePattern(Enum):
    """Neuromorphic spike patterns for different processing modes."""
    
    BURST = "burst"  # High-frequency spikes for critical clauses
    REGULAR = "regular"  # Steady spikes for standard processing
    SPARSE = "sparse"  # Low-frequency spikes for background processing
    ADAPTIVE = "adaptive"  # Dynamic pattern based on content


@dataclass
class NeuronState:
    """State representation for artificial neurons in the neuromorphic network."""
    
    membrane_potential: float = 0.0
    threshold: float = 1.0
    last_spike_time: float = 0.0
    refractory_period: float = 0.1
    adaptation_factor: float = 0.95
    connections: Dict[int, float] = field(default_factory=dict)
    spike_history: List[float] = field(default_factory=list)
    
    def update_potential(self, input_current: float, dt: float = 0.01) -> bool:
        """Update membrane potential and check for spike generation."""
        if time.time() - self.last_spike_time < self.refractory_period:
            return False
            
        # Leaky integrate-and-fire model
        self.membrane_potential *= (1 - dt)  # Leak
        self.membrane_potential += input_current * dt  # Integration
        
        if self.membrane_potential >= self.threshold:
            self.spike()
            return True
        return False
    
    def spike(self) -> None:
        """Generate a spike and reset the neuron."""
        self.last_spike_time = time.time()
        self.spike_history.append(self.last_spike_time)
        self.membrane_potential = 0.0
        # Adaptive threshold
        self.threshold *= self.adaptation_factor


class NeuromorphicCluster:
    """Neuromorphic processing cluster for parallel clause analysis."""
    
    def __init__(self, cluster_id: str, size: int = 100):
        self.cluster_id = cluster_id
        self.neurons = {i: NeuronState() for i in range(size)}
        self.synaptic_weights = np.random.uniform(-0.5, 0.5, (size, size))
        self.learning_rate = 0.01
        self.spike_count = 0
        self.processing_history: List[Dict[str, Any]] = []
        
    def process_input(self, input_vector: np.ndarray) -> Dict[str, Any]:
        """Process input through the neuromorphic cluster."""
        start_time = time.time()
        spikes_generated = []
        
        # Stimulate neurons with input
        for neuron_id, neuron in self.neurons.items():
            if neuron_id < len(input_vector):
                input_current = input_vector[neuron_id]
                if neuron.update_potential(input_current):
                    spikes_generated.append(neuron_id)
                    self.spike_count += 1
        
        # Lateral interactions between neurons
        self._process_lateral_interactions(spikes_generated)
        
        processing_time = time.time() - start_time
        
        result = {
            "cluster_id": self.cluster_id,
            "spikes_generated": len(spikes_generated),
            "spike_neurons": spikes_generated,
            "processing_time": processing_time,
            "total_spike_count": self.spike_count,
            "activation_pattern": self._get_activation_pattern()
        }
        
        self.processing_history.append(result)
        return result
    
    def _process_lateral_interactions(self, spiking_neurons: List[int]) -> None:
        """Process lateral interactions between spiking neurons."""
        for neuron_id in spiking_neurons:
            for target_id, weight in self.neurons[neuron_id].connections.items():
                if target_id in self.neurons:
                    # Synaptic current from spiking neuron
                    synaptic_current = weight * 0.5  # Scaled synaptic strength
                    self.neurons[target_id].membrane_potential += synaptic_current
    
    def _get_activation_pattern(self) -> Dict[str, float]:
        """Get current activation pattern of the cluster."""
        potentials = [neuron.membrane_potential for neuron in self.neurons.values()]
        return {
            "mean_potential": np.mean(potentials),
            "max_potential": np.max(potentials),
            "active_neurons": sum(1 for p in potentials if p > 0.1),
            "synchrony_index": self._calculate_synchrony()
        }
    
    def _calculate_synchrony(self) -> float:
        """Calculate synchrony index of neural activity."""
        recent_spikes = []
        current_time = time.time()
        
        for neuron in self.neurons.values():
            recent = [t for t in neuron.spike_history if current_time - t < 1.0]
            recent_spikes.extend(recent)
        
        if len(recent_spikes) < 2:
            return 0.0
            
        # Calculate coefficient of variation (inverse of synchrony)
        if len(recent_spikes) > 1:
            intervals = np.diff(sorted(recent_spikes))
            if len(intervals) > 0 and np.mean(intervals) > 0:
                cv = np.std(intervals) / np.mean(intervals)
                return max(0.0, 1.0 - cv)  # Higher synchrony = lower CV
        
        return 0.0


class NeuromorphicProcessor:
    """Main neuromorphic processing engine for contract analysis."""
    
    def __init__(self, num_clusters: int = 4, cluster_size: int = 100):
        self.clusters = {
            f"cluster_{i}": NeuromorphicCluster(f"cluster_{i}", cluster_size)
            for i in range(num_clusters)
        }
        self.executor = ThreadPoolExecutor(max_workers=num_clusters)
        self.processing_stats = {
            "documents_processed": 0,
            "total_spikes": 0,
            "avg_processing_time": 0.0,
            "peak_synchrony": 0.0
        }
        
    async def process_document_neuromorphic(
        self, 
        document_features: Dict[str, Any],
        clause_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process document using neuromorphic computing principles."""
        start_time = time.time()
        
        # Convert document features to neural input
        input_vectors = self._encode_features_to_spikes(document_features, clause_data)
        
        # Parallel processing across clusters
        tasks = []
        for cluster_id, input_vector in zip(self.clusters.keys(), input_vectors):
            cluster = self.clusters[cluster_id]
            task = asyncio.create_task(
                self._process_cluster_async(cluster, input_vector)
            )
            tasks.append(task)
        
        # Wait for all clusters to complete
        cluster_results = await asyncio.gather(*tasks)
        
        # Integrate results across clusters
        integrated_result = self._integrate_cluster_results(cluster_results)
        
        # Update statistics
        processing_time = time.time() - start_time
        self._update_stats(cluster_results, processing_time)
        
        return {
            "neuromorphic_analysis": integrated_result,
            "processing_time": processing_time,
            "clusters_used": len(cluster_results),
            "total_spikes": sum(r["spikes_generated"] for r in cluster_results),
            "synchrony_metrics": self._calculate_global_synchrony(cluster_results)
        }
    
    def _encode_features_to_spikes(
        self, 
        document_features: Dict[str, Any], 
        clause_data: List[Dict[str, Any]]
    ) -> List[np.ndarray]:
        """Encode document features into spike-train representations."""
        # Extract numerical features
        features = []
        
        # Document-level features
        doc_features = [
            document_features.get("page_count", 1),
            document_features.get("word_count", 100) / 1000.0,  # Normalize
            document_features.get("confidence", 0.5),
            len(clause_data) / 10.0  # Normalize clause count
        ]
        
        # Clause-level features
        for clause in clause_data[:10]:  # Limit to first 10 clauses
            clause_features = [
                len(clause.get("text", "")) / 1000.0,  # Text length
                clause.get("confidence", 0.5),
                clause.get("page", 1) / 10.0,  # Page number
                len(clause.get("key_terms", [])) / 10.0  # Key terms count
            ]
            features.extend(clause_features)
        
        # Pad or truncate to ensure consistent size
        target_size = 100
        if len(features) < target_size:
            features.extend([0.0] * (target_size - len(features)))
        else:
            features = features[:target_size]
        
        # Convert to spike rates (0-1 range to 0-10 Hz equivalent)
        spike_rates = np.array(features) * 10.0
        
        # Split into vectors for different clusters
        chunk_size = len(spike_rates) // len(self.clusters)
        vectors = []
        for i in range(len(self.clusters)):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < len(self.clusters) - 1 else len(spike_rates)
            vectors.append(spike_rates[start_idx:end_idx])
        
        return vectors
    
    async def _process_cluster_async(
        self, 
        cluster: NeuromorphicCluster, 
        input_vector: np.ndarray
    ) -> Dict[str, Any]:
        """Process input through a cluster asynchronously."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, 
            cluster.process_input, 
            input_vector
        )
        return result
    
    def _integrate_cluster_results(self, cluster_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integrate results from all clusters into a unified analysis."""
        total_spikes = sum(r["spikes_generated"] for r in cluster_results)
        avg_processing_time = np.mean([r["processing_time"] for r in cluster_results])
        
        # Aggregate activation patterns
        activation_patterns = []
        for result in cluster_results:
            activation_patterns.append(result["activation_pattern"])
        
        # Neuromorphic confidence score based on spike patterns
        confidence_score = self._calculate_neuromorphic_confidence(cluster_results)
        
        # Detect emergent patterns
        emergent_patterns = self._detect_emergent_patterns(cluster_results)
        
        return {
            "total_neural_spikes": total_spikes,
            "average_cluster_time": avg_processing_time,
            "neuromorphic_confidence": confidence_score,
            "activation_patterns": activation_patterns,
            "emergent_patterns": emergent_patterns,
            "cluster_synchrony": self._calculate_inter_cluster_synchrony(cluster_results),
            "processing_efficiency": total_spikes / avg_processing_time if avg_processing_time > 0 else 0
        }
    
    def _calculate_neuromorphic_confidence(self, cluster_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on neuromorphic processing patterns."""
        spike_consistency = []
        activation_strengths = []
        
        for result in cluster_results:
            # Spike count consistency (moderate activity is good)
            spike_count = result["spikes_generated"]
            optimal_range = (10, 50)  # Optimal spike count range
            if optimal_range[0] <= spike_count <= optimal_range[1]:
                consistency = 1.0
            else:
                consistency = max(0.1, 1.0 - abs(spike_count - 30) / 30.0)
            spike_consistency.append(consistency)
            
            # Activation pattern strength
            pattern = result["activation_pattern"]
            strength = min(1.0, pattern["active_neurons"] / 100.0)  # Normalize to 0-1
            activation_strengths.append(strength)
        
        # Combine metrics
        avg_consistency = np.mean(spike_consistency)
        avg_strength = np.mean(activation_strengths)
        
        # Weighted combination
        confidence = 0.6 * avg_consistency + 0.4 * avg_strength
        return round(confidence, 3)
    
    def _detect_emergent_patterns(self, cluster_results: List[Dict[str, Any]]) -> List[str]:
        """Detect emergent patterns in cluster behavior."""
        patterns = []
        
        spike_counts = [r["spikes_generated"] for r in cluster_results]
        
        # High activity pattern
        if np.mean(spike_counts) > 40:
            patterns.append("high_neural_activity")
        
        # Synchronized clusters
        synchrony_values = [r["activation_pattern"]["synchrony_index"] for r in cluster_results]
        if np.mean(synchrony_values) > 0.7:
            patterns.append("cluster_synchronization")
        
        # Sparse coding pattern
        if np.std(spike_counts) > 20:
            patterns.append("sparse_distributed_coding")
        
        # Balanced activation
        active_neurons = [r["activation_pattern"]["active_neurons"] for r in cluster_results]
        if 20 <= np.mean(active_neurons) <= 80:
            patterns.append("balanced_activation")
        
        return patterns
    
    def _calculate_inter_cluster_synchrony(self, cluster_results: List[Dict[str, Any]]) -> float:
        """Calculate synchrony between different clusters."""
        processing_times = [r["processing_time"] for r in cluster_results]
        if len(processing_times) < 2:
            return 0.0
        
        # Coefficient of variation for processing times (lower = more synchronized)
        mean_time = np.mean(processing_times)
        std_time = np.std(processing_times)
        
        if mean_time > 0:
            cv = std_time / mean_time
            return max(0.0, 1.0 - cv)  # Convert to synchrony measure
        
        return 0.0
    
    def _calculate_global_synchrony(self, cluster_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate global synchrony metrics across all clusters."""
        return {
            "inter_cluster_sync": self._calculate_inter_cluster_synchrony(cluster_results),
            "avg_intra_cluster_sync": np.mean([
                r["activation_pattern"]["synchrony_index"] for r in cluster_results
            ]),
            "temporal_coherence": self._calculate_temporal_coherence(cluster_results)
        }
    
    def _calculate_temporal_coherence(self, cluster_results: List[Dict[str, Any]]) -> float:
        """Calculate temporal coherence of neural activity."""
        # Simple measure based on processing time variance
        times = [r["processing_time"] for r in cluster_results]
        if len(times) < 2:
            return 1.0
        
        # Lower variance in timing = higher coherence
        normalized_variance = np.var(times) / (np.mean(times) ** 2) if np.mean(times) > 0 else 0
        coherence = max(0.0, 1.0 - normalized_variance)
        return round(coherence, 3)
    
    def _update_stats(self, cluster_results: List[Dict[str, Any]], processing_time: float) -> None:
        """Update processing statistics."""
        self.processing_stats["documents_processed"] += 1
        
        total_spikes = sum(r["spikes_generated"] for r in cluster_results)
        self.processing_stats["total_spikes"] += total_spikes
        
        # Update average processing time
        n = self.processing_stats["documents_processed"]
        prev_avg = self.processing_stats["avg_processing_time"]
        self.processing_stats["avg_processing_time"] = (prev_avg * (n-1) + processing_time) / n
        
        # Update peak synchrony
        current_synchrony = np.mean([
            r["activation_pattern"]["synchrony_index"] for r in cluster_results
        ])
        if current_synchrony > self.processing_stats["peak_synchrony"]:
            self.processing_stats["peak_synchrony"] = current_synchrony
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            "documents_processed": 0,
            "total_spikes": 0,
            "avg_processing_time": 0.0,
            "peak_synchrony": 0.0
        }
    
    def shutdown(self) -> None:
        """Shutdown the neuromorphic processor."""
        self.executor.shutdown(wait=True)


# Global neuromorphic processor instance
_neuromorphic_processor: Optional[NeuromorphicProcessor] = None


def get_neuromorphic_processor() -> NeuromorphicProcessor:
    """Get the global neuromorphic processor instance."""
    global _neuromorphic_processor
    if _neuromorphic_processor is None:
        _neuromorphic_processor = NeuromorphicProcessor()
    return _neuromorphic_processor


async def analyze_with_neuromorphic_computing(
    document_info: Dict[str, Any],
    clauses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze document using neuromorphic computing principles."""
    processor = get_neuromorphic_processor()
    
    try:
        result = await processor.process_document_neuromorphic(
            document_info, clauses
        )
        logger.info(
            "Neuromorphic analysis completed: %d spikes, %.3f confidence",
            result["total_spikes"],
            result["neuromorphic_analysis"]["neuromorphic_confidence"]
        )
        return result
        
    except Exception as e:
        logger.error("Neuromorphic analysis failed: %s", e)
        return {
            "error": str(e),
            "neuromorphic_analysis": {"neuromorphic_confidence": 0.0},
            "total_spikes": 0
        }


class NeuromorphicConfig(BaseModel):
    """Configuration for neuromorphic processing."""
    
    num_clusters: int = Field(default=4, ge=1, le=16)
    cluster_size: int = Field(default=100, ge=10, le=1000)
    enable_adaptation: bool = True
    spike_threshold: float = Field(default=1.0, gt=0.0)
    refractory_period: float = Field(default=0.1, gt=0.0)
    learning_rate: float = Field(default=0.01, gt=0.0, le=1.0)
    synchrony_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda x: round(x, 6)
        }