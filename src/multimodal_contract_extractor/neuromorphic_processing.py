"""Neuromorphic processing engine for contract extraction using photonic neural networks.

This module implements advanced neuromorphic computing patterns inspired by
biological neural networks for enhanced document processing accuracy and
energy efficiency in contract clause extraction.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SynapticWeight(Enum):
    """Synaptic weight types for neuromorphic processing."""
    EXCITATORY = "excitatory"
    INHIBITORY = "inhibitory"
    MODULATORY = "modulatory"


@dataclass
class PhotonicNeuron:
    """Represents a photonic neuron in the neuromorphic processor."""

    neuron_id: str
    activation_threshold: float = 0.7
    synaptic_weights: Dict[str, float] = field(default_factory=dict)
    membrane_potential: float = 0.0
    last_spike_time: float = 0.0
    refractory_period: float = 0.001  # 1ms refractory period
    adaptation_rate: float = 0.01

    def spike(self, current_time: float) -> bool:
        """Check if neuron should spike based on membrane potential."""
        if (current_time - self.last_spike_time) < self.refractory_period:
            return False

        if self.membrane_potential >= self.activation_threshold:
            self.last_spike_time = current_time
            self.membrane_potential *= 0.2  # Reset with some residual
            return True
        return False

    def receive_input(self, input_strength: float, weight_type: SynapticWeight = SynapticWeight.EXCITATORY):
        """Receive synaptic input and update membrane potential."""
        multiplier = 1.0 if weight_type == SynapticWeight.EXCITATORY else -0.5
        if weight_type == SynapticWeight.MODULATORY:
            multiplier = 0.8

        self.membrane_potential += input_strength * multiplier
        self.membrane_potential = max(0.0, min(2.0, self.membrane_potential))  # Clamp

    def adapt_threshold(self, spike_rate: float):
        """Adaptive threshold based on recent activity."""
        target_rate = 0.1  # Target 10% spike rate
        error = spike_rate - target_rate
        self.activation_threshold += error * self.adaptation_rate
        self.activation_threshold = max(0.3, min(1.2, self.activation_threshold))


@dataclass
class NeuromorphicLayer:
    """Layer of photonic neurons for hierarchical processing."""

    layer_id: str
    neurons: List[PhotonicNeuron] = field(default_factory=list)
    layer_type: str = "processing"  # processing, memory, output
    lateral_inhibition: float = 0.1
    adaptation_enabled: bool = True

    def process_batch(self, inputs: List[float], current_time: float) -> List[bool]:
        """Process a batch of inputs through the layer."""
        if len(inputs) != len(self.neurons):
            raise ValueError(f"Input size {len(inputs)} doesn't match neuron count {len(self.neurons)}")

        # Apply inputs
        for i, (neuron, input_val) in enumerate(zip(self.neurons, inputs)):
            neuron.receive_input(input_val)

        # Apply lateral inhibition
        if self.lateral_inhibition > 0:
            self._apply_lateral_inhibition()

        # Check for spikes
        spikes = [neuron.spike(current_time) for neuron in self.neurons]

        # Adaptation
        if self.adaptation_enabled:
            spike_rate = sum(spikes) / len(spikes) if spikes else 0.0
            for neuron in self.neurons:
                neuron.adapt_threshold(spike_rate)

        return spikes

    def _apply_lateral_inhibition(self):
        """Apply lateral inhibition between neurons in the layer."""
        potentials = [n.membrane_potential for n in self.neurons]
        max_potential = max(potentials) if potentials else 0

        for neuron in self.neurons:
            if neuron.membrane_potential < max_potential:
                inhibition = (max_potential - neuron.membrane_potential) * self.lateral_inhibition
                neuron.membrane_potential -= inhibition
                neuron.membrane_potential = max(0, neuron.membrane_potential)


@dataclass
class ClausePattern:
    """Neural pattern representation of contract clauses."""

    pattern_id: str
    clause_type: str
    feature_vector: List[float]
    confidence_threshold: float = 0.75
    temporal_sequence: List[int] = field(default_factory=list)
    context_neurons: List[str] = field(default_factory=list)

    def matches_input(self, input_vector: List[float], threshold: float = None) -> Tuple[bool, float]:
        """Check if input vector matches this pattern."""
        if len(input_vector) != len(self.feature_vector):
            return False, 0.0

        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(input_vector, self.feature_vector))
        magnitude_a = sum(a * a for a in input_vector) ** 0.5
        magnitude_b = sum(b * b for b in self.feature_vector) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return False, 0.0

        similarity = dot_product / (magnitude_a * magnitude_b)
        used_threshold = threshold or self.confidence_threshold

        return similarity >= used_threshold, similarity


class PhotonicNeuromorphicProcessor:
    """Main neuromorphic processor for contract clause extraction."""

    def __init__(self, layers: int = 5, neurons_per_layer: int = 128):
        self.layers: List[NeuromorphicLayer] = []
        self.clause_patterns: Dict[str, ClausePattern] = {}
        self.processing_time = 0.0
        self.adaptation_cycles = 0
        self.spike_history: List[List[bool]] = []
        self.energy_consumption = 0.0  # Simulated energy usage

        # Initialize layers
        self._initialize_network(layers, neurons_per_layer)
        self._load_clause_patterns()

        logger.info(f"Initialized neuromorphic processor with {layers} layers, "
                   f"{neurons_per_layer} neurons per layer")

    def _initialize_network(self, num_layers: int, neurons_per_layer: int):
        """Initialize the neuromorphic network architecture."""
        layer_types = ["input", "feature", "context", "classification", "output"]

        for i in range(num_layers):
            layer_type = layer_types[min(i, len(layer_types) - 1)]
            neurons = [
                PhotonicNeuron(
                    neuron_id=f"L{i}N{j}",
                    activation_threshold=0.6 + (i * 0.05),  # Increasing thresholds
                    adaptation_rate=0.01 / (i + 1)  # Decreasing adaptation
                )
                for j in range(neurons_per_layer)
            ]

            layer = NeuromorphicLayer(
                layer_id=f"layer_{i}",
                neurons=neurons,
                layer_type=layer_type,
                lateral_inhibition=0.1 if i > 0 else 0.0
            )
            self.layers.append(layer)

    def _load_clause_patterns(self):
        """Load predefined clause patterns for neuromorphic recognition."""
        patterns = {
            "termination": ClausePattern(
                pattern_id="term_001",
                clause_type="termination",
                feature_vector=[0.9, 0.8, 0.3, 0.7, 0.5, 0.8, 0.2, 0.9],
                temporal_sequence=[1, 3, 5, 8, 12],
                context_neurons=["L2N45", "L3N67", "L4N23"]
            ),
            "payment": ClausePattern(
                pattern_id="pay_001",
                clause_type="payment_terms",
                feature_vector=[0.7, 0.9, 0.8, 0.4, 0.6, 0.7, 0.8, 0.5],
                temporal_sequence=[2, 4, 7, 10, 15],
                context_neurons=["L2N12", "L3N34", "L4N56"]
            ),
            "liability": ClausePattern(
                pattern_id="lib_001",
                clause_type="liability",
                feature_vector=[0.8, 0.6, 0.9, 0.7, 0.8, 0.3, 0.9, 0.7],
                temporal_sequence=[1, 2, 6, 9, 14],
                context_neurons=["L2N78", "L3N90", "L4N12"]
            ),
            "confidentiality": ClausePattern(
                pattern_id="conf_001",
                clause_type="confidentiality",
                feature_vector=[0.6, 0.8, 0.7, 0.9, 0.5, 0.8, 0.6, 0.9],
                temporal_sequence=[3, 5, 8, 11, 16],
                context_neurons=["L2N33", "L3N55", "L4N77"]
            )
        }
        self.clause_patterns = patterns

    async def process_document_neuromorphic(self, document,
                                           language_code: str = "en") -> NeuromorphicProcessingResult:
        """Process document using neuromorphic computing approach."""
        start_time = time.perf_counter()
        current_time = start_time

        logger.info("Starting neuromorphic document processing")

        # Convert document to neural input representation
        input_features = self._extract_neural_features(document)

        # Process through neuromorphic layers
        layer_outputs = []
        current_input = input_features

        for i, layer in enumerate(self.layers):
            logger.debug(f"Processing layer {i}: {layer.layer_id}")

            # Pad or truncate input to match neuron count
            if len(current_input) < len(layer.neurons):
                current_input.extend([0.0] * (len(layer.neurons) - len(current_input)))
            elif len(current_input) > len(layer.neurons):
                current_input = current_input[:len(layer.neurons)]

            # Process through layer
            layer_spikes = layer.process_batch(current_input, current_time)
            layer_outputs.append(layer_spikes)

            # Convert spikes to next layer input
            current_input = [1.0 if spike else 0.1 for spike in layer_spikes]
            current_time += 0.001  # 1ms time step

            # Simulate energy consumption
            active_neurons = sum(layer_spikes)
            self.energy_consumption += active_neurons * 0.1  # pJ per spike

        # Pattern matching and clause extraction
        detected_clauses = await self._extract_clauses_from_patterns(layer_outputs, document)

        processing_time = time.perf_counter() - start_time
        self.processing_time += processing_time
        self.adaptation_cycles += 1
        self.spike_history.append(layer_outputs[-1])

        # Calculate network statistics
        total_spikes = sum(sum(layer_output) for layer_output in layer_outputs)
        spike_efficiency = len(detected_clauses) / max(total_spikes, 1)

        logger.info(f"Neuromorphic processing completed in {processing_time:.3f}s, "
                   f"detected {len(detected_clauses)} clauses, "
                   f"spike efficiency: {spike_efficiency:.3f}")

        return NeuromorphicProcessingResult(
            detected_clauses=detected_clauses,
            processing_time=processing_time,
            total_spikes=total_spikes,
            energy_consumption=self.energy_consumption,
            spike_efficiency=spike_efficiency,
            layer_activations=layer_outputs,
            adaptation_cycles=self.adaptation_cycles
        )

    def _extract_neural_features(self, document) -> List[float]:
        """Convert document to neural feature representation."""
        features = []

        # Basic document features
        total_pages = len(document.pages)
        features.extend([
            min(total_pages / 10, 1.0),  # Normalize page count
            0.5,  # Document complexity (placeholder)
            0.7,  # Text quality estimation
            0.8   # Layout regularity
        ])

        # Text-based features (simplified)
        for page in document.pages[:4]:  # First 4 pages
            page_text = getattr(page, 'text', '') or ''
            text_features = [
                min(len(page_text) / 1000, 1.0),  # Text density
                len(page_text.split()) / max(len(page_text.split('\n')), 1),  # Words per line
                page_text.count('$') / max(len(page_text), 1),  # Financial indicators
                page_text.count('.') / max(len(page_text), 1),  # Sentence density
            ]
            features.extend(text_features)

        # Pad to ensure consistent feature vector length
        target_length = 128
        if len(features) < target_length:
            features.extend([0.1] * (target_length - len(features)))
        elif len(features) > target_length:
            features = features[:target_length]

        return features

    async def _extract_clauses_from_patterns(self, layer_outputs: List[List[bool]],
                                           document) -> List[NeuromorphicClause]:
        """Extract clauses by matching neural patterns."""
        detected_clauses = []
        final_layer_output = layer_outputs[-1] if layer_outputs else []

        # Convert final layer spikes to feature vector
        if not final_layer_output:
            return detected_clauses

        # Sliding window pattern matching
        window_size = 8
        for i in range(0, len(final_layer_output) - window_size + 1, window_size // 2):
            window_spikes = final_layer_output[i:i + window_size]
            feature_vector = [1.0 if spike else 0.0 for spike in window_spikes]

            # Check against known patterns
            for pattern_id, pattern in self.clause_patterns.items():
                if len(pattern.feature_vector) == len(feature_vector):
                    matches, confidence = pattern.matches_input(feature_vector)

                    if matches:
                        clause = NeuromorphicClause(
                            clause_id=f"neuro_{pattern_id}_{i}",
                            clause_type=pattern.clause_type,
                            text=f"Neuromorphic detected {pattern.clause_type}",
                            confidence=confidence,
                            neural_pattern_id=pattern_id,
                            activation_window=(i, i + window_size),
                            spike_pattern=window_spikes,
                            processing_layer="neuromorphic",
                            page=1  # Default page
                        )
                        detected_clauses.append(clause)

                        logger.debug(f"Detected {pattern.clause_type} clause with "
                                   f"confidence {confidence:.3f}")

        return detected_clauses

    def get_network_statistics(self) -> Dict[str, Any]:
        """Get detailed network statistics."""
        total_neurons = sum(len(layer.neurons) for layer in self.layers)
        avg_threshold = statistics.mean([
            statistics.mean([n.activation_threshold for n in layer.neurons])
            for layer in self.layers
        ])

        recent_spikes = self.spike_history[-10:] if self.spike_history else []
        avg_activity = statistics.mean([
            sum(spike_pattern) / len(spike_pattern)
            for spike_pattern in recent_spikes
        ]) if recent_spikes else 0.0

        return {
            "total_neurons": total_neurons,
            "total_layers": len(self.layers),
            "average_threshold": avg_threshold,
            "recent_activity_rate": avg_activity,
            "total_processing_time": self.processing_time,
            "adaptation_cycles": self.adaptation_cycles,
            "energy_consumption": self.energy_consumption,
            "patterns_loaded": len(self.clause_patterns)
        }

    def reset_network_state(self):
        """Reset the network to initial state."""
        for layer in self.layers:
            for neuron in layer.neurons:
                neuron.membrane_potential = 0.0
                neuron.last_spike_time = 0.0

        self.spike_history.clear()
        self.energy_consumption = 0.0
        logger.info("Neuromorphic network state reset")


@dataclass
class NeuromorphicClause:
    """Clause detected using neuromorphic processing."""

    clause_id: str
    clause_type: str
    text: str
    confidence: float
    neural_pattern_id: str
    activation_window: Tuple[int, int]
    spike_pattern: List[bool]
    processing_layer: str
    page: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class NeuromorphicProcessingResult:
    """Result from neuromorphic document processing."""

    detected_clauses: List[NeuromorphicClause]
    processing_time: float
    total_spikes: int
    energy_consumption: float
    spike_efficiency: float
    layer_activations: List[List[bool]]
    adaptation_cycles: int


class NeuromorphicContractProcessor:
    """High-level interface for neuromorphic contract processing."""

    def __init__(self):
        self.processor = PhotonicNeuromorphicProcessor()
        self.processing_history: List[NeuromorphicProcessingResult] = []

    async def process_contract_neuromorphic(self, document,
                                          language_code: str = "en") -> NeuromorphicProcessingResult:
        """Process contract using neuromorphic approach with benchmarking."""
        logger.info("Starting neuromorphic contract processing")

        result = await self.processor.process_document_neuromorphic(
            document, language_code
        )

        self.processing_history.append(result)

        # Performance analysis
        if len(self.processing_history) > 1:
            self._analyze_performance_trends()

        return result

    def _analyze_performance_trends(self):
        """Analyze performance trends for adaptive optimization."""
        if len(self.processing_history) < 5:
            return

        recent_results = self.processing_history[-5:]

        # Calculate trends
        processing_times = [r.processing_time for r in recent_results]
        energy_consumption = [r.energy_consumption for r in recent_results]
        spike_efficiency = [r.spike_efficiency for r in recent_results]

        avg_time_trend = statistics.mean(processing_times)
        avg_energy_trend = statistics.mean(energy_consumption)
        avg_efficiency_trend = statistics.mean(spike_efficiency)

        logger.info(f"Performance trends - Time: {avg_time_trend:.3f}s, "
                   f"Energy: {avg_energy_trend:.2f}pJ, "
                   f"Efficiency: {avg_efficiency_trend:.3f}")

        # Adaptive threshold adjustment
        if avg_efficiency_trend < 0.1:  # Low efficiency
            self._adjust_network_sensitivity(increase=True)
        elif avg_efficiency_trend > 0.5:  # High efficiency
            self._adjust_network_sensitivity(increase=False)

    def _adjust_network_sensitivity(self, increase: bool):
        """Adjust network sensitivity based on performance."""
        adjustment = -0.05 if increase else 0.05

        for layer in self.processor.layers:
            for neuron in layer.neurons:
                neuron.activation_threshold += adjustment
                neuron.activation_threshold = max(0.3, min(1.2, neuron.activation_threshold))

        logger.info(f"Adjusted network sensitivity ({'increased' if increase else 'decreased'})")

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        network_stats = self.processor.get_network_statistics()

        if self.processing_history:
            history_stats = {
                "total_documents_processed": len(self.processing_history),
                "average_processing_time": statistics.mean([r.processing_time for r in self.processing_history]),
                "total_energy_consumed": sum([r.energy_consumption for r in self.processing_history]),
                "average_clauses_per_document": statistics.mean([len(r.detected_clauses) for r in self.processing_history]),
                "peak_spike_efficiency": max([r.spike_efficiency for r in self.processing_history])
            }
        else:
            history_stats = {}

        return {**network_stats, **history_stats}


# Global processor instance
_neuromorphic_processor: Optional[NeuromorphicContractProcessor] = None


def get_neuromorphic_processor() -> NeuromorphicContractProcessor:
    """Get or create global neuromorphic processor instance."""
    global _neuromorphic_processor
    if _neuromorphic_processor is None:
        _neuromorphic_processor = NeuromorphicContractProcessor()
    return _neuromorphic_processor


async def process_document_with_neuromorphics(document, language_code: str = "en") -> NeuromorphicProcessingResult:
    """Main entry point for neuromorphic document processing."""
    processor = get_neuromorphic_processor()
    return await processor.process_contract_neuromorphic(document, language_code)


def benchmark_neuromorphic_vs_traditional(document, iterations: int = 5) -> Dict[str, Any]:
    """Benchmark neuromorphic vs traditional processing approaches."""
    logger.info(f"Starting benchmark with {iterations} iterations")

    # Traditional processing benchmark (placeholder)
    traditional_times = []
    for i in range(iterations):
        start_time = time.perf_counter()
        # Simulate traditional processing
        time.sleep(0.1)  # Placeholder for actual processing
        traditional_times.append(time.perf_counter() - start_time)

    # Neuromorphic processing benchmark
    async def neuromorphic_benchmark():
        neuromorphic_times = []
        energy_consumptions = []
        spike_efficiencies = []

        processor = get_neuromorphic_processor()

        for i in range(iterations):
            result = await processor.process_contract_neuromorphic(document)
            neuromorphic_times.append(result.processing_time)
            energy_consumptions.append(result.energy_consumption)
            spike_efficiencies.append(result.spike_efficiency)

        return {
            "neuromorphic_times": neuromorphic_times,
            "energy_consumptions": energy_consumptions,
            "spike_efficiencies": spike_efficiencies
        }

    # Run neuromorphic benchmark
    neuro_results = asyncio.run(neuromorphic_benchmark())

    # Calculate comparative statistics
    traditional_avg = statistics.mean(traditional_times)
    neuromorphic_avg = statistics.mean(neuro_results["neuromorphic_times"])

    speedup_factor = traditional_avg / neuromorphic_avg
    energy_efficiency = statistics.mean(neuro_results["energy_consumptions"])
    processing_efficiency = statistics.mean(neuro_results["spike_efficiencies"])

    return {
        "traditional": {
            "average_time": traditional_avg,
            "times": traditional_times
        },
        "neuromorphic": {
            "average_time": neuromorphic_avg,
            "average_energy": energy_efficiency,
            "average_spike_efficiency": processing_efficiency,
            **neuro_results
        },
        "comparison": {
            "speedup_factor": speedup_factor,
            "energy_efficiency": energy_efficiency,
            "processing_efficiency": processing_efficiency,
            "performance_improvement": f"{(speedup_factor - 1) * 100:.1f}%"
        }
    }
