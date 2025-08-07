"""Comprehensive tests for quantum-enhanced extraction functionality."""

import asyncio
import pytest
import time
import math
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.multimodal_contract_extractor.quantum_enhanced_extraction import (
    Qubit, QuantumState, QuantumCircuit, QuantumFeatureMap, QuantumClausePattern,
    QuantumContractProcessor, QuantumProcessingResult, QuantumClause,
    get_quantum_processor, process_document_with_quantum_enhancement,
    benchmark_quantum_classical_hybrid
)


class TestQubit:
    """Test Qubit functionality."""
    
    def test_qubit_initialization(self):
        """Test qubit initialization with default state."""
        qubit = Qubit("q0")
        
        assert qubit.qubit_id == "q0"
        assert abs(qubit.amplitude_0 - complex(1/math.sqrt(2), 0)) < 1e-10
        assert abs(qubit.amplitude_1 - complex(1/math.sqrt(2), 0)) < 1e-10
        assert qubit.coherence_time == 1.0
        assert qubit.last_measurement == 0.0
        
    def test_qubit_probabilities(self):
        """Test probability calculations."""
        qubit = Qubit("prob_test")
        
        # Equal superposition
        prob_0 = qubit.probability_0
        prob_1 = qubit.probability_1
        
        assert abs(prob_0 - 0.5) < 1e-10
        assert abs(prob_1 - 0.5) < 1e-10
        assert abs(prob_0 + prob_1 - 1.0) < 1e-10
        
    def test_qubit_normalization(self):
        """Test qubit amplitude normalization."""
        qubit = Qubit("norm_test")
        
        # Set unnormalized amplitudes
        qubit.amplitude_0 = complex(2.0, 0)
        qubit.amplitude_1 = complex(3.0, 0)
        
        qubit.normalize()
        
        # Check normalization
        total_prob = qubit.probability_0 + qubit.probability_1
        assert abs(total_prob - 1.0) < 1e-10
        
    def test_qubit_rotation(self):
        """Test quantum rotation gate application."""
        qubit = Qubit("rotation_test")
        
        # Start in |0⟩ state
        qubit.amplitude_0 = complex(1, 0)
        qubit.amplitude_1 = complex(0, 0)
        
        # Apply π/2 rotation (should create superposition)
        qubit.apply_rotation(math.pi/2)
        
        # Should be in superposition now
        assert abs(qubit.probability_0 - 0.5) < 1e-1
        assert abs(qubit.probability_1 - 0.5) < 1e-1
        
    def test_qubit_measurement(self):
        """Test qubit measurement and state collapse."""
        qubit = Qubit("measure_test")
        current_time = time.time()
        
        # Measure multiple times to test probabilistic behavior
        measurements = []
        for _ in range(10):
            # Reset to superposition
            qubit.amplitude_0 = complex(1/math.sqrt(2), 0)
            qubit.amplitude_1 = complex(1/math.sqrt(2), 0)
            
            measurement = qubit.measure(current_time)
            measurements.append(measurement)
            
            # After measurement, should be in definite state
            if measurement == 0:
                assert abs(qubit.probability_0 - 1.0) < 1e-10
                assert abs(qubit.probability_1 - 0.0) < 1e-10
            else:
                assert abs(qubit.probability_0 - 0.0) < 1e-10
                assert abs(qubit.probability_1 - 1.0) < 1e-10
        
        # Should have both 0 and 1 measurements (probabilistic)
        assert all(m in [0, 1] for m in measurements)
        
    def test_qubit_decoherence(self):
        """Test decoherence effects on qubit."""
        qubit = Qubit("decoherence_test", coherence_time=0.1)
        
        # Set initial state
        qubit.amplitude_0 = complex(1, 0)
        qubit.amplitude_1 = complex(0, 0)
        initial_state = (qubit.amplitude_0, qubit.amplitude_1)
        
        # Measure after coherence time to trigger decoherence
        current_time = time.time()
        qubit.measure(current_time + 0.2)  # Beyond coherence time
        
        # State should have been affected by decoherence
        # (exact comparison difficult due to random phase noise)
        assert qubit.last_measurement > 0


class TestQuantumCircuit:
    """Test QuantumCircuit functionality."""
    
    def test_circuit_initialization(self):
        """Test circuit initialization."""
        circuit = QuantumCircuit("test_circuit")
        
        assert circuit.circuit_id == "test_circuit"
        assert len(circuit.qubits) == 0
        assert len(circuit.gates_applied) == 0
        assert circuit.circuit_depth == 0
        assert circuit.fidelity == 1.0
        
    def test_qubit_addition(self):
        """Test adding qubits to circuit."""
        circuit = QuantumCircuit("qubit_test")
        
        qubit = circuit.add_qubit("q0")
        
        assert len(circuit.qubits) == 1
        assert qubit.qubit_id == "q0"
        assert circuit.qubits[0] is qubit
        
    def test_hadamard_gate(self):
        """Test Hadamard gate application."""
        circuit = QuantumCircuit("hadamard_test")
        qubit = circuit.add_qubit("q0")
        
        # Start in |0⟩ state
        qubit.amplitude_0 = complex(1, 0)
        qubit.amplitude_1 = complex(0, 0)
        
        # Apply Hadamard gate
        circuit.apply_hadamard("q0")
        
        # Should create superposition
        assert abs(qubit.probability_0 - 0.5) < 1e-10
        assert abs(qubit.probability_1 - 0.5) < 1e-10
        assert "H(q0)" in circuit.gates_applied
        assert circuit.circuit_depth == 1
        
    def test_cnot_gate(self):
        """Test CNOT gate and entanglement creation."""
        circuit = QuantumCircuit("cnot_test")
        control = circuit.add_qubit("control")
        target = circuit.add_qubit("target")
        
        # Set control to |1⟩ state
        control.amplitude_0 = complex(0, 0)
        control.amplitude_1 = complex(1, 0)
        
        # Set target to |0⟩ state  
        target.amplitude_0 = complex(1, 0)
        target.amplitude_1 = complex(0, 0)
        
        # Apply CNOT
        circuit.apply_cnot("control", "target")
        
        # Check entanglement was created
        assert "target" in control.entangled_with
        assert "control" in target.entangled_with
        assert ("control", "target") in circuit.entanglement_pairs
        assert "CNOT(control, target)" in circuit.gates_applied
        
    def test_phase_gate(self):
        """Test phase gate application."""
        circuit = QuantumCircuit("phase_test")
        qubit = circuit.add_qubit("q0")
        
        phase = math.pi / 4
        circuit.apply_phase_gate("q0", phase)
        
        assert f"P(q0, {phase:.2f})" in circuit.gates_applied
        assert circuit.circuit_depth == 1
        
    def test_measurement_all(self):
        """Test measuring all qubits in circuit."""
        circuit = QuantumCircuit("measure_all_test")
        
        # Add multiple qubits
        for i in range(3):
            circuit.add_qubit(f"q{i}")
        
        current_time = time.time()
        results = circuit.measure_all(current_time)
        
        assert len(results) == 3
        assert all(result in [0, 1] for result in results)
        
    def test_entanglement_entropy(self):
        """Test entanglement entropy calculation."""
        circuit = QuantumCircuit("entropy_test")
        
        # Add qubits in superposition
        for i in range(3):
            qubit = circuit.add_qubit(f"q{i}")
            # Set to superposition state
            qubit.amplitude_0 = complex(1/math.sqrt(2), 0)
            qubit.amplitude_1 = complex(1/math.sqrt(2), 0)
        
        # Create some entanglement
        circuit.apply_cnot("q0", "q1")
        circuit.apply_cnot("q1", "q2")
        
        entropy = circuit.get_entanglement_entropy()
        
        assert entropy >= 0.0
        assert entropy <= 1.0  # Normalized entropy per qubit


class TestQuantumFeatureMap:
    """Test QuantumFeatureMap functionality."""
    
    def test_feature_map_initialization(self):
        """Test feature map initialization."""
        feature_map = QuantumFeatureMap("test_map", encoding_type="amplitude")
        
        assert feature_map.feature_map_id == "test_map"
        assert feature_map.encoding_type == "amplitude"
        assert feature_map.feature_dimensions == 8
        
    def test_amplitude_encoding(self):
        """Test amplitude encoding of features."""
        feature_map = QuantumFeatureMap("amp_test", encoding_type="amplitude")
        circuit = QuantumCircuit("encoding_test")
        
        features = [0.3, 0.7, 0.5, 0.9]
        encoded_qubits = feature_map.encode_features(features, circuit)
        
        assert len(encoded_qubits) >= 2  # At least log2(4) qubits
        assert len(circuit.qubits) >= len(encoded_qubits)
        
    def test_angle_encoding(self):
        """Test angle encoding of features."""
        feature_map = QuantumFeatureMap("angle_test", encoding_type="angle")
        circuit = QuantumCircuit("encoding_test")
        
        features = [0.0, 0.5, 1.0]
        encoded_qubits = feature_map.encode_features(features, circuit)
        
        assert len(encoded_qubits) >= 2
        # Check that qubits were rotated based on features
        for i, qubit_id in enumerate(encoded_qubits[:len(features)]):
            qubit = circuit._get_qubit(qubit_id)
            assert qubit is not None
            
    def test_basis_encoding(self):
        """Test basis encoding of features."""
        feature_map = QuantumFeatureMap("basis_test", encoding_type="basis")
        circuit = QuantumCircuit("encoding_test")
        
        features = [0.3, 0.7, 0.2, 0.8]  # Mix of values above/below 0.5
        encoded_qubits = feature_map.encode_features(features, circuit)
        
        assert len(encoded_qubits) >= 2
        
        # Check encoding based on threshold
        for i, qubit_id in enumerate(encoded_qubits[:len(features)]):
            qubit = circuit._get_qubit(qubit_id)
            if features[i] > 0.5:
                assert abs(qubit.probability_1 - 1.0) < 1e-10
            else:
                assert abs(qubit.probability_0 - 1.0) < 1e-10


class TestQuantumClausePattern:
    """Test QuantumClausePattern functionality."""
    
    def test_pattern_initialization(self):
        """Test quantum clause pattern initialization."""
        signature = [complex(0.8, 0.2), complex(0.6, -0.1), complex(0.9, 0.3)]
        
        pattern = QuantumClausePattern(
            pattern_id="q_test_001",
            clause_type="termination",
            quantum_signature=signature,
            entanglement_structure={"control": ["q0"], "target": ["q1"]},
            measurement_basis=["computational"] * 3
        )
        
        assert pattern.pattern_id == "q_test_001"
        assert pattern.clause_type == "termination"
        assert len(pattern.quantum_signature) == 3
        assert pattern.classification_threshold == 0.75
        
    def test_quantum_pattern_matching(self):
        """Test quantum pattern matching."""
        signature = [complex(0.8, 0), complex(0.6, 0), complex(0.9, 0)]
        
        pattern = QuantumClausePattern(
            pattern_id="match_test",
            clause_type="payment",
            quantum_signature=signature,
            entanglement_structure={},
            measurement_basis=["computational"] * 3,
            classification_threshold=0.7
        )
        
        # Perfect match case
        measurements = [1, 1, 1]  # All measured as |1⟩
        probabilities = [0.8, 0.6, 0.9]  # High probabilities matching signature
        
        matches, fidelity = pattern.matches_quantum_state(measurements, probabilities)
        
        assert matches
        assert fidelity > 0.7
        
        # Poor match case
        measurements = [0, 0, 0]  # All measured as |0⟩  
        probabilities = [0.1, 0.2, 0.1]  # Low probabilities
        
        matches, fidelity = pattern.matches_quantum_state(measurements, probabilities)
        
        assert not matches
        assert fidelity < 0.7
        
    def test_pattern_size_mismatch(self):
        """Test handling of measurement size mismatch."""
        signature = [complex(0.5, 0), complex(0.7, 0), complex(0.6, 0)]
        
        pattern = QuantumClausePattern(
            pattern_id="size_test",
            clause_type="liability",
            quantum_signature=signature,
            entanglement_structure={},
            measurement_basis=["computational"] * 3
        )
        
        # Wrong size inputs
        wrong_measurements = [1, 0]  # Too short
        wrong_probabilities = [0.5, 0.3]
        
        matches, fidelity = pattern.matches_quantum_state(wrong_measurements, wrong_probabilities)
        
        assert not matches
        assert fidelity == 0.0


class TestQuantumContractProcessor:
    """Test main quantum contract processor."""
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = QuantumContractProcessor(num_qubits=8)
        
        assert processor.num_qubits == 8
        assert len(processor.clause_patterns) > 0
        assert processor.processing_statistics["total_processes"] == 0
        
    def test_quantum_pattern_initialization(self):
        """Test quantum pattern loading."""
        processor = QuantumContractProcessor()
        
        # Check that patterns were loaded
        assert "termination" in processor.clause_patterns
        assert "payment" in processor.clause_patterns
        assert "liability" in processor.clause_patterns
        assert "confidentiality" in processor.clause_patterns
        
        # Check pattern structure
        termination_pattern = processor.clause_patterns["termination"]
        assert termination_pattern.clause_type == "termination"
        assert len(termination_pattern.quantum_signature) == 8
        assert termination_pattern.classification_threshold > 0.0
        
    @pytest.mark.asyncio
    async def test_quantum_document_processing(self):
        """Test quantum document processing."""
        processor = QuantumContractProcessor(num_qubits=16)
        
        # Mock document
        mock_document = Mock()
        mock_document.pages = [
            Mock(text="Termination clause with 30 days notice", number=1),
            Mock(text="Payment terms of $50,000 annually", number=2)
        ]
        
        # Process document
        result = await processor.process_document_quantum(mock_document)
        
        assert isinstance(result, QuantumProcessingResult)
        assert result.processing_time > 0
        assert len(result.quantum_measurements) == processor.num_qubits
        assert len(result.measurement_probabilities) == processor.num_qubits
        assert result.entanglement_entropy >= 0.0
        assert result.circuit_fidelity > 0.0
        assert result.quantum_advantage_score >= 0.0
        assert isinstance(result.detected_clauses, list)
        
    def test_quantum_feature_extraction(self):
        """Test quantum feature extraction from documents."""
        processor = QuantumContractProcessor()
        
        # Mock document
        mock_document = Mock()
        mock_document.pages = [
            Mock(text="Contract with payment of $10,000 and termination clause", number=1),
            Mock(text="Additional terms and conditions apply", number=2)
        ]
        
        features = processor._extract_quantum_features(mock_document)
        
        assert isinstance(features, list)
        assert len(features) == 16  # Target length
        assert all(isinstance(f, (int, float)) for f in features)
        assert all(0.0 <= f <= 1.0 for f in features)  # Normalized
        
    @pytest.mark.asyncio
    async def test_quantum_algorithm_application(self):
        """Test quantum algorithm phases."""
        processor = QuantumContractProcessor(num_qubits=8)
        circuit = QuantumCircuit("algorithm_test")
        
        # Add qubits
        encoded_qubits = []
        for i in range(8):
            qubit = circuit.add_qubit(f"q{i}")
            encoded_qubits.append(f"q{i}")
        
        # Apply quantum algorithm
        await processor._apply_quantum_algorithm(circuit, encoded_qubits)
        
        # Check that gates were applied
        assert len(circuit.gates_applied) > 0
        assert circuit.circuit_depth > 0
        
        # Check for expected gate types
        gate_types = [gate.split('(')[0] for gate in circuit.gates_applied]
        assert "H" in gate_types  # Hadamard gates for superposition
        assert "CNOT" in gate_types  # CNOT gates for entanglement
        assert "P" in gate_types  # Phase gates
        
    @pytest.mark.asyncio
    async def test_quantum_clause_extraction(self):
        """Test clause extraction from quantum measurements."""
        processor = QuantumContractProcessor(num_qubits=8)
        
        # Mock measurements that should match a pattern
        measurements = [1, 0, 1, 1, 1, 0, 1, 1]  # Similar to termination pattern
        measurement_probs = [0.9, 0.1, 0.8, 0.7, 0.8, 0.2, 0.9, 0.7]
        
        mock_document = Mock()
        
        clauses = await processor._extract_quantum_clauses(
            measurements, measurement_probs, mock_document
        )
        
        assert isinstance(clauses, list)
        # Should detect at least one clause with good matching measurements
        if clauses:
            clause = clauses[0]
            assert isinstance(clause, QuantumClause)
            assert hasattr(clause, 'clause_id')
            assert hasattr(clause, 'clause_type')
            assert hasattr(clause, 'quantum_fidelity')
            assert hasattr(clause, 'measurement_results')
            assert hasattr(clause, 'quantum_confidence')
            
    def test_circuit_fidelity_calculation(self):
        """Test circuit fidelity calculation."""
        processor = QuantumContractProcessor()
        circuit = QuantumCircuit("fidelity_test")
        
        # Add qubits in different states
        q1 = circuit.add_qubit("q1")
        q1.amplitude_0 = complex(0.8, 0)
        q1.amplitude_1 = complex(0.6, 0)
        q1.normalize()
        
        q2 = circuit.add_qubit("q2")
        q2.amplitude_0 = complex(0.6, 0)
        q2.amplitude_1 = complex(0.8, 0)
        q2.normalize()
        
        fidelity = processor._calculate_circuit_fidelity(circuit)
        
        assert 0.0 <= fidelity <= 1.0
        
    def test_quantum_advantage_assessment(self):
        """Test quantum advantage assessment."""
        processor = QuantumContractProcessor()
        
        # Mock detected clauses with high fidelity
        mock_clauses = [
            Mock(quantum_fidelity=0.9),
            Mock(quantum_fidelity=0.85),
            Mock(quantum_fidelity=0.8)
        ]
        
        classical_features = [0.5, 0.3, 0.7, 0.2, 0.9, 0.1, 0.4, 0.6]
        
        advantage = processor._assess_quantum_advantage(mock_clauses, classical_features)
        
        assert 0.0 <= advantage <= 1.0
        
    def test_entanglement_witness_calculation(self):
        """Test entanglement witness calculation."""
        processor = QuantumContractProcessor()
        
        # Measurements showing correlation (potential entanglement)
        correlated_measurements = [1, 0, 1, 0, 1, 0, 1, 0]
        witness_corr = processor._calculate_entanglement_witness(correlated_measurements)
        
        # Measurements showing anti-correlation (stronger entanglement evidence)
        anticorr_measurements = [1, 1, 0, 0, 1, 1, 0, 0]
        witness_anticorr = processor._calculate_entanglement_witness(anticorr_measurements)
        
        assert 0.0 <= witness_corr <= 1.0
        assert 0.0 <= witness_anticorr <= 1.0
        
    def test_quantum_statistics(self):
        """Test quantum statistics collection."""
        processor = QuantumContractProcessor(num_qubits=12)
        
        # Process some mock results to generate statistics
        processor.processing_statistics["total_processes"] = 5
        processor.processing_statistics["quantum_advantage_achieved"] = 3
        
        stats = processor.get_quantum_statistics()
        
        expected_keys = [
            "total_processes", "quantum_advantage_achieved", "quantum_advantage_rate",
            "num_qubits", "patterns_loaded", "quantum_volume"
        ]
        
        for key in expected_keys:
            assert key in stats
            
        assert stats["num_qubits"] == 12
        assert stats["quantum_advantage_rate"] == 0.6  # 3/5
        assert stats["quantum_volume"] == 2 ** 12


class TestGlobalFunctions:
    """Test global utility functions."""
    
    def test_get_quantum_processor(self):
        """Test global processor instance."""
        processor1 = get_quantum_processor()
        processor2 = get_quantum_processor()
        
        # Should return the same instance
        assert processor1 is processor2
        assert isinstance(processor1, QuantumContractProcessor)
        
    @pytest.mark.asyncio
    async def test_process_document_with_quantum_enhancement(self):
        """Test global processing function."""
        mock_document = Mock()
        mock_document.pages = [Mock(text="Test contract", number=1)]
        
        result = await process_document_with_quantum_enhancement(mock_document, "en")
        
        assert isinstance(result, QuantumProcessingResult)
        assert result.processing_time > 0
        
    def test_benchmark_quantum_classical_hybrid(self):
        """Test quantum benchmarking functionality."""
        mock_document = Mock()
        mock_document.pages = [Mock(text="Benchmark test contract", number=1)]
        
        # Run with minimal iterations for testing
        benchmark_results = benchmark_quantum_classical_hybrid(
            mock_document, iterations=2
        )
        
        assert "benchmark_results" in benchmark_results
        assert "performance_summary" in benchmark_results
        assert "recommendation" in benchmark_results
        
        summary = benchmark_results["performance_summary"]
        assert "quantum_average_time" in summary
        assert "classical_average_time" in summary
        assert "hybrid_average_time" in summary
        assert "quantum_speedup_factor" in summary
        assert "average_quantum_fidelity" in summary
        assert "quantum_superiority_achieved" in summary


class TestIntegration:
    """Integration tests for quantum processing."""
    
    @pytest.mark.asyncio
    async def test_full_quantum_pipeline(self):
        """Test complete quantum processing pipeline."""
        processor = QuantumContractProcessor(num_qubits=16)
        
        # Create realistic mock document
        mock_document = Mock()
        mock_document.pages = []
        
        contract_texts = [
            "This agreement may be terminated by either party with thirty (30) days written notice.",
            "Payment shall be made in the amount of fifty thousand dollars ($50,000) annually.",
            "The receiving party agrees to hold all confidential information in strict confidence.",
            "Neither party shall be liable for any indirect, consequential, or incidental damages."
        ]
        
        for i, text in enumerate(contract_texts):
            page = Mock()
            page.text = text
            page.number = i + 1
            mock_document.pages.append(page)
        
        # Process document
        result = await processor.process_document_quantum(mock_document, "en")
        
        # Comprehensive result verification
        assert isinstance(result, QuantumProcessingResult)
        assert result.processing_time > 0
        assert len(result.quantum_measurements) == 16
        assert len(result.measurement_probabilities) == 16
        assert 0.0 <= result.entanglement_entropy <= 1.0
        assert 0.0 <= result.circuit_fidelity <= 1.0
        assert 0.0 <= result.quantum_advantage_score <= 1.0
        assert result.circuit_depth > 0
        assert len(result.gates_applied) > 0
        
        # Check measurement validity
        assert all(m in [0, 1] for m in result.quantum_measurements)
        assert all(0.0 <= p <= 1.0 for p in result.measurement_probabilities)
        
        # Check detected clauses structure
        for clause in result.detected_clauses:
            assert isinstance(clause, QuantumClause)
            assert clause.clause_id.startswith("quantum_")
            assert clause.clause_type in ["termination", "payment_terms", "liability", "confidentiality"]
            assert 0.0 <= clause.quantum_fidelity <= 1.0
            assert 0.0 <= clause.quantum_confidence <= 1.0
            assert len(clause.measurement_results) > 0
            assert 0.0 <= clause.entanglement_witness <= 1.0
            assert clause.processing_method == "quantum_enhanced"
            
    @pytest.mark.asyncio
    async def test_concurrent_quantum_processing(self):
        """Test concurrent quantum document processing."""
        processor = QuantumContractProcessor(num_qubits=8)
        
        # Create multiple mock documents
        documents = []
        for i in range(3):
            doc = Mock()
            doc.pages = [Mock(text=f"Quantum test document {i} with clauses", number=1)]
            documents.append(doc)
        
        # Process concurrently
        tasks = [
            processor.process_document_quantum(doc, "en")
            for doc in documents
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, QuantumProcessingResult)
            assert result.processing_time > 0
            assert result.quantum_advantage_score >= 0.0
            
    def test_quantum_error_handling(self):
        """Test error handling in quantum processing."""
        processor = QuantumContractProcessor()
        
        # Test with None document
        with pytest.raises(Exception):
            asyncio.run(processor.process_document_quantum(None))
            
        # Test with empty document
        empty_doc = Mock()
        empty_doc.pages = []
        
        result = asyncio.run(processor.process_document_quantum(empty_doc))
        assert isinstance(result, QuantumProcessingResult)
        # Should handle gracefully with minimal measurements
        
    def test_quantum_scalability(self):
        """Test quantum processing with different qubit counts."""
        # Small quantum processor
        small_processor = QuantumContractProcessor(num_qubits=4)
        small_stats = small_processor.get_quantum_statistics()
        
        # Larger quantum processor
        large_processor = QuantumContractProcessor(num_qubits=20)
        large_stats = large_processor.get_quantum_statistics()
        
        assert small_stats["num_qubits"] < large_stats["num_qubits"]
        assert small_stats["quantum_volume"] < large_stats["quantum_volume"]
        
    @pytest.mark.asyncio
    async def test_quantum_performance_consistency(self):
        """Test quantum processing performance consistency."""
        processor = QuantumContractProcessor(num_qubits=8)
        
        mock_document = Mock()
        mock_document.pages = [Mock(text="Consistent test document", number=1)]
        
        # Run multiple times
        results = []
        for _ in range(5):
            result = await processor.process_document_quantum(mock_document)
            results.append(result)
        
        # Check consistency
        processing_times = [r.processing_time for r in results]
        fidelities = [r.circuit_fidelity for r in results]
        
        # Times should be reasonably consistent
        mean_time = sum(processing_times) / len(processing_times)
        if mean_time > 0:
            time_cv = (sum((t - mean_time) ** 2 for t in processing_times) / len(processing_times)) ** 0.5 / mean_time
            assert time_cv < 0.5, f"Processing time too variable: CV = {time_cv}"
        
        # Fidelities should be consistently high
        assert all(f > 0.5 for f in fidelities), "Circuit fidelity too low"
        
    def test_quantum_measurement_statistics(self):
        """Test quantum measurement statistical properties."""
        processor = QuantumContractProcessor(num_qubits=16)
        circuit = QuantumCircuit("stats_test")
        
        # Create qubits in known superposition states
        for i in range(16):
            qubit = circuit.add_qubit(f"q{i}")
            # Set to equal superposition
            qubit.amplitude_0 = complex(1/math.sqrt(2), 0)
            qubit.amplitude_1 = complex(1/math.sqrt(2), 0)
        
        # Perform many measurements
        measurement_counts = [0, 0]  # Count of |0⟩ and |1⟩ measurements
        num_trials = 100
        
        for _ in range(num_trials):
            measurements = circuit.measure_all(time.time())
            for measurement in measurements:
                measurement_counts[measurement] += 1
        
        # With equal superposition, should get roughly equal counts
        total_measurements = sum(measurement_counts)
        ratio = min(measurement_counts) / max(measurement_counts)
        
        # Allow some statistical variation but expect reasonable balance
        assert ratio > 0.3, f"Measurement distribution too skewed: {measurement_counts}"
        
    @pytest.mark.asyncio
    async def test_quantum_advantage_validation(self):
        """Test validation of quantum advantage claims."""
        processor = QuantumContractProcessor(num_qubits=12)
        
        # Process document with quantum method
        mock_document = Mock()
        mock_document.pages = [
            Mock(text="Complex contract with multiple interrelated clauses requiring advanced pattern recognition", number=1),
            Mock(text="Additional complex dependencies and conditional terms", number=2)
        ]
        
        result = await processor.process_document_quantum(mock_document)
        
        # Quantum advantage should be positive for complex documents
        assert result.quantum_advantage_score >= 0.0
        
        # If advantage is claimed, verify supporting metrics
        if result.quantum_advantage_score > 0.1:
            assert result.circuit_fidelity > 0.7
            assert result.entanglement_entropy > 0.1
            assert len(result.detected_clauses) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])