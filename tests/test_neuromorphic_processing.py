"""Comprehensive tests for neuromorphic processing functionality."""

import asyncio
import time
from unittest.mock import Mock

import pytest

from src.multimodal_contract_extractor.neuromorphic_processing import (
    ClausePattern,
    NeuromorphicClause,
    NeuromorphicContractProcessor,
    NeuromorphicLayer,
    NeuromorphicProcessingResult,
    PhotonicNeuromorphicProcessor,
    PhotonicNeuron,
    SynapticWeight,
    benchmark_neuromorphic_vs_traditional,
    get_neuromorphic_processor,
    process_document_with_neuromorphics,
)


class TestPhotonicNeuron:
    """Test PhotonicNeuron functionality."""

    def test_neuron_initialization(self):
        """Test neuron initialization with default parameters."""
        neuron = PhotonicNeuron("test_neuron_001")

        assert neuron.neuron_id == "test_neuron_001"
        assert neuron.activation_threshold == 0.7
        assert neuron.membrane_potential == 0.0
        assert neuron.last_spike_time == 0.0
        assert neuron.refractory_period == 0.001

    def test_neuron_spike_threshold(self):
        """Test neuron spiking behavior."""
        neuron = PhotonicNeuron("spike_test", activation_threshold=0.5)
        current_time = time.time()

        # Below threshold - should not spike
        neuron.membrane_potential = 0.3
        assert not neuron.spike(current_time)

        # Above threshold - should spike
        neuron.membrane_potential = 0.6
        assert neuron.spike(current_time)

        # Reset potential after spike
        assert neuron.membrane_potential < 0.6

    def test_neuron_refractory_period(self):
        """Test neuron refractory period behavior."""
        neuron = PhotonicNeuron("refractory_test", refractory_period=0.01)
        current_time = time.time()

        # First spike
        neuron.membrane_potential = 1.0
        assert neuron.spike(current_time)

        # Immediate second attempt - should be blocked by refractory period
        neuron.membrane_potential = 1.0
        assert not neuron.spike(current_time)

        # After refractory period
        neuron.membrane_potential = 1.0
        assert neuron.spike(current_time + 0.02)

    def test_neuron_input_processing(self):
        """Test synaptic input processing."""
        neuron = PhotonicNeuron("input_test")
        initial_potential = neuron.membrane_potential

        # Excitatory input
        neuron.receive_input(0.2, SynapticWeight.EXCITATORY)
        assert neuron.membrane_potential > initial_potential

        # Inhibitory input
        current_potential = neuron.membrane_potential
        neuron.receive_input(0.1, SynapticWeight.INHIBITORY)
        assert neuron.membrane_potential < current_potential

        # Modulatory input
        neuron.receive_input(0.1, SynapticWeight.MODULATORY)

    def test_neuron_threshold_adaptation(self):
        """Test adaptive threshold mechanism."""
        neuron = PhotonicNeuron("adapt_test", adaptation_rate=0.1)
        initial_threshold = neuron.activation_threshold

        # High spike rate should increase threshold
        neuron.adapt_threshold(0.5)  # 50% spike rate, above target
        assert neuron.activation_threshold > initial_threshold

        # Low spike rate should decrease threshold
        neuron.adapt_threshold(0.05)  # 5% spike rate, below target
        assert neuron.activation_threshold < initial_threshold


class TestNeuromorphicLayer:
    """Test NeuromorphicLayer functionality."""

    def test_layer_initialization(self):
        """Test layer initialization."""
        layer = NeuromorphicLayer("test_layer")

        assert layer.layer_id == "test_layer"
        assert layer.layer_type == "processing"
        assert layer.lateral_inhibition == 0.1
        assert len(layer.neurons) == 0

    def test_layer_batch_processing(self):
        """Test batch input processing."""
        layer = NeuromorphicLayer("batch_test")

        # Add neurons
        for i in range(4):
            neuron = PhotonicNeuron(f"neuron_{i}", activation_threshold=0.5)
            layer.neurons.append(neuron)

        # Process batch inputs
        inputs = [0.6, 0.4, 0.8, 0.3]
        current_time = time.time()

        spikes = layer.process_batch(inputs, current_time)

        assert len(spikes) == 4
        assert isinstance(spikes[0], bool)

        # Check that high inputs are more likely to spike
        assert spikes[2] == True  # 0.8 input should spike (> 0.5 threshold)
        assert spikes[3] == False  # 0.3 input should not spike (< 0.5 threshold)

    def test_layer_lateral_inhibition(self):
        """Test lateral inhibition mechanism."""
        layer = NeuromorphicLayer("inhibition_test", lateral_inhibition=0.2)

        # Add neurons with different initial potentials
        layer.neurons = [
            PhotonicNeuron("n1", activation_threshold=0.5),
            PhotonicNeuron("n2", activation_threshold=0.5),
            PhotonicNeuron("n3", activation_threshold=0.5)
        ]

        # Set different membrane potentials
        layer.neurons[0].membrane_potential = 0.8  # Highest
        layer.neurons[1].membrane_potential = 0.6  # Medium
        layer.neurons[2].membrane_potential = 0.4  # Lowest

        # Apply lateral inhibition
        layer._apply_lateral_inhibition()

        # Highest potential neuron should be least affected
        # Lower potential neurons should be inhibited more
        assert layer.neurons[0].membrane_potential > layer.neurons[1].membrane_potential
        assert layer.neurons[1].membrane_potential > layer.neurons[2].membrane_potential

    def test_layer_input_size_mismatch(self):
        """Test handling of input size mismatch."""
        layer = NeuromorphicLayer("mismatch_test")
        layer.neurons = [PhotonicNeuron(f"n{i}") for i in range(3)]

        inputs = [0.5, 0.6]  # Only 2 inputs for 3 neurons
        current_time = time.time()

        with pytest.raises(ValueError, match="Input size .* doesn't match neuron count"):
            layer.process_batch(inputs, current_time)


class TestClausePattern:
    """Test ClausePattern functionality."""

    def test_pattern_matching(self):
        """Test clause pattern matching."""
        pattern = ClausePattern(
            pattern_id="test_pattern",
            clause_type="termination",
            feature_vector=[0.8, 0.6, 0.9, 0.7],
            confidence_threshold=0.75
        )

        # Perfect match
        perfect_match = [0.8, 0.6, 0.9, 0.7]
        matches, confidence = pattern.matches_input(perfect_match)
        assert matches
        assert confidence > 0.95

        # Close match
        close_match = [0.85, 0.65, 0.85, 0.75]
        matches, confidence = pattern.matches_input(close_match)
        assert matches
        assert confidence > 0.75

        # Poor match
        poor_match = [0.1, 0.2, 0.1, 0.3]
        matches, confidence = pattern.matches_input(poor_match)
        assert not matches
        assert confidence < 0.75

    def test_pattern_size_mismatch(self):
        """Test handling of feature vector size mismatch."""
        pattern = ClausePattern(
            pattern_id="size_test",
            clause_type="payment",
            feature_vector=[0.5, 0.6, 0.7]
        )

        wrong_size_input = [0.5, 0.6]  # Too short
        matches, confidence = pattern.matches_input(wrong_size_input)

        assert not matches
        assert confidence == 0.0


class TestPhotonicNeuromorphicProcessor:
    """Test main neuromorphic processor."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = PhotonicNeuromorphicProcessor(layers=3, neurons_per_layer=64)

        assert len(processor.layers) == 3
        assert len(processor.layers[0].neurons) == 64
        assert len(processor.clause_patterns) > 0
        assert processor.processing_time == 0.0

    def test_network_architecture(self):
        """Test network layer architecture."""
        processor = PhotonicNeuromorphicProcessor(layers=5, neurons_per_layer=32)

        # Check layer types
        expected_types = ["input", "feature", "context", "classification", "output"]
        for i, layer in enumerate(processor.layers):
            expected_type = expected_types[min(i, len(expected_types) - 1)]
            assert layer.layer_type == expected_type

        # Check threshold progression
        thresholds = [layer.neurons[0].activation_threshold for layer in processor.layers]
        for i in range(1, len(thresholds)):
            assert thresholds[i] >= thresholds[i-1]  # Increasing thresholds

    @pytest.mark.asyncio
    async def test_document_processing(self):
        """Test neuromorphic document processing."""
        processor = PhotonicNeuromorphicProcessor(layers=3, neurons_per_layer=16)

        # Mock document
        mock_document = Mock()
        mock_document.pages = [
            Mock(image=Mock(), number=1, text="Test contract clause"),
            Mock(image=Mock(), number=2, text="Payment terms and conditions")
        ]

        # Process document
        result = await processor.process_document_neuromorphic(mock_document)

        assert isinstance(result, NeuromorphicProcessingResult)
        assert result.processing_time > 0
        assert result.total_spikes >= 0
        assert result.energy_consumption >= 0
        assert isinstance(result.detected_clauses, list)

    def test_neural_feature_extraction(self):
        """Test conversion of document to neural features."""
        processor = PhotonicNeuromorphicProcessor()

        # Mock document
        mock_document = Mock()
        mock_document.pages = [
            Mock(number=1, text="Sample contract text with payment terms"),
            Mock(number=2, text="Additional clauses and conditions")
        ]

        features = processor._extract_neural_features(mock_document)

        assert isinstance(features, list)
        assert len(features) == 128  # Expected feature vector length
        assert all(isinstance(f, (int, float)) for f in features)
        assert all(0.0 <= f <= 1.0 for f in features)  # Normalized features

    @pytest.mark.asyncio
    async def test_clause_extraction_from_patterns(self):
        """Test clause extraction from neural patterns."""
        processor = PhotonicNeuromorphicProcessor(layers=2, neurons_per_layer=8)

        # Mock layer outputs with specific pattern
        layer_outputs = [
            [True, False, True, False, True, False, True, False],
            [False, True, False, True, True, True, False, True]
        ]

        mock_document = Mock()

        clauses = await processor._extract_clauses_from_patterns(layer_outputs, mock_document)

        assert isinstance(clauses, list)
        # Should find at least one clause match
        if clauses:
            clause = clauses[0]
            assert isinstance(clause, NeuromorphicClause)
            assert hasattr(clause, 'clause_id')
            assert hasattr(clause, 'clause_type')
            assert hasattr(clause, 'confidence')

    def test_network_statistics(self):
        """Test network statistics collection."""
        processor = PhotonicNeuromorphicProcessor(layers=3, neurons_per_layer=16)

        stats = processor.get_network_statistics()

        assert "total_neurons" in stats
        assert "total_layers" in stats
        assert "average_threshold" in stats
        assert "recent_activity_rate" in stats
        assert "patterns_loaded" in stats

        assert stats["total_neurons"] == 48  # 3 layers * 16 neurons
        assert stats["total_layers"] == 3
        assert stats["patterns_loaded"] > 0

    def test_network_state_reset(self):
        """Test network state reset functionality."""
        processor = PhotonicNeuromorphicProcessor(layers=2, neurons_per_layer=4)

        # Modify neuron states
        processor.layers[0].neurons[0].membrane_potential = 0.8
        processor.layers[0].neurons[0].last_spike_time = 123.45
        processor.spike_history = [[True, False, True, False]]
        processor.energy_consumption = 5.0

        # Reset network
        processor.reset_network_state()

        # Check reset state
        assert processor.layers[0].neurons[0].membrane_potential == 0.0
        assert processor.layers[0].neurons[0].last_spike_time == 0.0
        assert len(processor.spike_history) == 0
        assert processor.energy_consumption == 0.0


class TestNeuromorphicContractProcessor:
    """Test high-level contract processor."""

    @pytest.mark.asyncio
    async def test_contract_processing(self):
        """Test high-level contract processing."""
        processor = NeuromorphicContractProcessor()

        # Mock document
        mock_document = Mock()
        mock_document.pages = [Mock(image=Mock(), number=1)]

        result = await processor.process_contract_neuromorphic(mock_document)

        assert isinstance(result, NeuromorphicProcessingResult)
        assert len(processor.processing_history) == 1

    def test_performance_trend_analysis(self):
        """Test performance trend analysis."""
        processor = NeuromorphicContractProcessor()

        # Add mock processing history
        for i in range(6):
            mock_result = Mock()
            mock_result.processing_time = 1.0 + i * 0.1
            mock_result.energy_consumption = 2.0 + i * 0.05
            mock_result.spike_efficiency = 0.8 - i * 0.01
            mock_result.detected_clauses = [Mock() for _ in range(3 + i)]
            processor.processing_history.append(mock_result)

        # Trigger performance analysis
        processor._analyze_performance_trends()

        # Should have analyzed trends without errors
        assert len(processor.processing_history) == 6

    def test_processing_statistics(self):
        """Test processing statistics collection."""
        processor = NeuromorphicContractProcessor()

        # Add some mock history
        mock_result = Mock()
        mock_result.processing_time = 1.5
        mock_result.energy_consumption = 3.0
        mock_result.detected_clauses = [Mock(), Mock()]
        mock_result.spike_efficiency = 0.85
        processor.processing_history.append(mock_result)

        stats = processor.get_processing_statistics()

        expected_keys = [
            "total_neurons", "total_layers", "total_documents_processed",
            "average_processing_time", "total_energy_consumed"
        ]

        for key in expected_keys:
            assert key in stats


class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_neuromorphic_processor(self):
        """Test global processor instance."""
        processor1 = get_neuromorphic_processor()
        processor2 = get_neuromorphic_processor()

        # Should return the same instance
        assert processor1 is processor2
        assert isinstance(processor1, NeuromorphicContractProcessor)

    @pytest.mark.asyncio
    async def test_process_document_with_neuromorphics(self):
        """Test global processing function."""
        mock_document = Mock()
        mock_document.pages = [Mock(image=Mock(), number=1)]

        result = await process_document_with_neuromorphics(mock_document, "en")

        assert isinstance(result, NeuromorphicProcessingResult)
        assert result.processing_time > 0

    def test_benchmark_neuromorphic_vs_traditional(self):
        """Test benchmarking functionality."""
        mock_document = Mock()
        mock_document.pages = [Mock(image=Mock(), number=1)]

        # Run with minimal iterations for testing
        benchmark_results = benchmark_neuromorphic_vs_traditional(
            mock_document, iterations=2
        )

        assert "traditional" in benchmark_results
        assert "neuromorphic" in benchmark_results
        assert "comparison" in benchmark_results

        assert "average_time" in benchmark_results["traditional"]
        assert "average_time" in benchmark_results["neuromorphic"]
        assert "speedup_factor" in benchmark_results["comparison"]


class TestIntegration:
    """Integration tests for neuromorphic processing."""

    @pytest.mark.asyncio
    async def test_full_processing_pipeline(self):
        """Test complete processing pipeline."""
        processor = NeuromorphicContractProcessor()

        # Create more realistic mock document
        mock_document = Mock()
        mock_document.pages = []

        for i in range(3):
            page = Mock()
            page.image = Mock()
            page.number = i + 1
            page.text = f"Page {i+1}: Contract clause with payment terms of $5000 and termination conditions."
            mock_document.pages.append(page)

        # Process document
        result = await processor.process_contract_neuromorphic(mock_document, "en")

        # Verify result structure
        assert isinstance(result, NeuromorphicProcessingResult)
        assert result.processing_time > 0
        assert result.total_spikes >= 0
        assert result.energy_consumption >= 0
        assert result.adaptation_cycles >= 0
        assert isinstance(result.detected_clauses, list)
        assert isinstance(result.layer_activations, list)

        # Verify detected clauses structure if any found
        if result.detected_clauses:
            clause = result.detected_clauses[0]
            assert hasattr(clause, 'clause_id')
            assert hasattr(clause, 'clause_type')
            assert hasattr(clause, 'text')
            assert hasattr(clause, 'confidence')
            assert hasattr(clause, 'neural_pattern_id')
            assert hasattr(clause, 'processing_layer')

    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test concurrent document processing."""
        processor = NeuromorphicContractProcessor()

        # Create multiple mock documents
        documents = []
        for i in range(3):
            doc = Mock()
            doc.pages = [Mock(image=Mock(), number=1, text=f"Document {i} content")]
            documents.append(doc)

        # Process concurrently
        tasks = [
            processor.process_contract_neuromorphic(doc, "en")
            for doc in documents
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, NeuromorphicProcessingResult)
            assert result.processing_time > 0

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        processor = PhotonicNeuromorphicProcessor()

        # Test with None document
        with pytest.raises(Exception):
            # This should raise an exception due to None document
            asyncio.run(processor.process_document_neuromorphic(None))

        # Test with empty document
        empty_doc = Mock()
        empty_doc.pages = []

        # Should handle gracefully
        result = asyncio.run(processor.process_document_neuromorphic(empty_doc))
        assert isinstance(result, NeuromorphicProcessingResult)
        assert len(result.detected_clauses) == 0

    def test_memory_efficiency(self):
        """Test memory usage efficiency."""
        # Create processor with different sizes
        small_processor = PhotonicNeuromorphicProcessor(layers=2, neurons_per_layer=8)
        large_processor = PhotonicNeuromorphicProcessor(layers=5, neurons_per_layer=64)

        # Small processor should use less memory
        small_stats = small_processor.get_network_statistics()
        large_stats = large_processor.get_network_statistics()

        assert small_stats["total_neurons"] < large_stats["total_neurons"]
        assert small_stats["total_layers"] < large_stats["total_layers"]

    @pytest.mark.asyncio
    async def test_performance_consistency(self):
        """Test processing performance consistency."""
        processor = NeuromorphicContractProcessor()

        mock_document = Mock()
        mock_document.pages = [Mock(image=Mock(), number=1, text="Test content")]

        # Run multiple times
        processing_times = []
        for _ in range(5):
            result = await processor.process_contract_neuromorphic(mock_document)
            processing_times.append(result.processing_time)

        # Times should be reasonably consistent (coefficient of variation < 50%)
        mean_time = sum(processing_times) / len(processing_times)
        if mean_time > 0:
            std_time = (sum((t - mean_time) ** 2 for t in processing_times) / len(processing_times)) ** 0.5
            cv = std_time / mean_time
            assert cv < 0.5, f"Processing time too variable: CV = {cv}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
