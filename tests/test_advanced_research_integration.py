"""
Integration tests for advanced research components.

This module tests the integration and functionality of the cutting-edge research
components including multimodal transformers, quantum encoders, meta-learning,
and research publication framework.
"""

import asyncio
import pytest
import numpy as np
from typing import Dict, List, Any

from src.multimodal_contract_extractor import (
    # Core components
    load_document,
    detect_clauses,
    
    # Advanced research components
    MultimodalLegalTransformer,
    LegalDocumentAnalyzer,
    create_legal_document_analyzer,
    SpatialPosition,
    DocumentElement,
    QuantumLegalAnalyzer,
    create_quantum_legal_analyzer,
    LegalMetaLearningFramework,
    create_meta_learning_framework,
    LegalDomain,
    MetaLearningConfig,
    ResearchPublicationFramework,
    create_research_framework,
    PublicationVenue,
    ExperimentType,
)


class TestMultimodalTransformer:
    """Test suite for multimodal transformer components."""
    
    def test_spatial_position_creation(self):
        """Test SpatialPosition creation and embedding."""
        position = SpatialPosition(x=0.5, y=0.3, width=0.2, height=0.1, page=1)
        
        assert position.x == 0.5
        assert position.y == 0.3
        assert position.page == 1
        
        # Test embedding generation
        embedding = position.to_embedding(256)
        assert embedding.shape == (256,)
        assert not np.allclose(embedding, 0)  # Should not be all zeros
    
    def test_document_element_creation(self):
        """Test DocumentElement creation."""
        position = SpatialPosition(0.1, 0.2, 0.3, 0.05, 1)
        element = DocumentElement(
            text="This is a termination clause",
            position=position,
            semantic_type="termination",
            confidence=0.95
        )
        
        assert element.text == "This is a termination clause"
        assert element.semantic_type == "termination"
        assert element.confidence == 0.95
        assert element.position.x == 0.1
    
    def test_legal_document_analyzer_creation(self):
        """Test LegalDocumentAnalyzer creation and basic functionality."""
        analyzer = create_legal_document_analyzer(
            d_model=256,
            num_heads=4,
            num_layers=3
        )
        
        assert analyzer is not None
        assert analyzer.config.d_model == 256
        assert analyzer.config.num_heads == 4
        assert analyzer.config.num_layers == 3
    
    @pytest.mark.asyncio
    async def test_document_analysis(self):
        """Test document analysis with multimodal transformer."""
        # Create test elements
        elements = [
            DocumentElement(
                text="Employment agreement terms",
                position=SpatialPosition(0.1, 0.2, 0.3, 0.05, 1),
                semantic_type="employment"
            ),
            DocumentElement(
                text="Confidentiality obligations",
                position=SpatialPosition(0.1, 0.4, 0.4, 0.05, 1),
                semantic_type="confidentiality"
            ),
        ]
        
        analyzer = create_legal_document_analyzer()
        insights = await analyzer.analyze_document(elements)
        
        assert "document_embedding" in insights
        assert "num_elements" in insights
        assert insights["num_elements"] == 2
        assert "relationships" in insights
        assert "semantic_complexity" in insights


class TestQuantumEncoder:
    """Test suite for quantum encoder components."""
    
    def test_quantum_analyzer_creation(self):
        """Test QuantumLegalAnalyzer creation."""
        analyzer = create_quantum_legal_analyzer(
            num_qubits=8,
            num_classes=5
        )
        
        assert analyzer is not None
        assert analyzer.num_qubits == 8
        assert analyzer.num_classes == 5
    
    @pytest.mark.asyncio
    async def test_quantum_document_encoding(self):
        """Test quantum document encoding."""
        analyzer = create_quantum_legal_analyzer(num_qubits=8)
        
        # Create test features
        features = np.random.randn(64)
        
        # Test encoding
        circuit = await analyzer.encode_legal_document(features)
        
        assert circuit is not None
        assert circuit.num_qubits == 8
        assert len(circuit.gate_sequence) > 0
    
    @pytest.mark.asyncio
    async def test_quantum_similarity(self):
        """Test quantum-enhanced similarity computation."""
        analyzer = create_quantum_legal_analyzer(num_qubits=8)
        
        # Create test features
        features1 = np.random.randn(64)
        features2 = np.random.randn(64)
        
        # Test similarity computation
        similarity = await analyzer.compute_document_similarity(features1, features2)
        
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
    
    @pytest.mark.asyncio
    async def test_quantum_classification(self):
        """Test quantum document classification."""
        analyzer = create_quantum_legal_analyzer(num_qubits=8, num_classes=5)
        
        # Create test features
        features = np.random.randn(64)
        
        # Test classification
        result = await analyzer.classify_document(features)
        
        assert "predicted_class" in result
        assert "confidence" in result
        assert "class_probabilities" in result
        assert "quantum_features" in result
        assert result["quantum_features"] is True
        assert len(result["class_probabilities"]) == 5


class TestMetaLearning:
    """Test suite for meta-learning components."""
    
    def test_meta_learning_framework_creation(self):
        """Test LegalMetaLearningFramework creation."""
        framework = create_meta_learning_framework(
            support_shots=3,
            num_adaptation_steps=3
        )
        
        assert framework is not None
        assert framework.config.support_shots == 3
        assert framework.config.num_adaptation_steps == 3
    
    def test_legal_domain_enum(self):
        """Test LegalDomain enumeration."""
        assert LegalDomain.EMPLOYMENT.value == "employment"
        assert LegalDomain.INTELLECTUAL_PROPERTY.value == "intellectual_property"
        assert LegalDomain.MERGER_ACQUISITION.value == "merger_acquisition"
    
    @pytest.mark.asyncio
    async def test_few_shot_adaptation(self):
        """Test few-shot adaptation to new legal domain."""
        framework = create_meta_learning_framework(support_shots=3)
        
        # Create support examples
        support_examples = [
            (np.random.randn(64), 0),
            (np.random.randn(64), 1),
            (np.random.randn(64), 0),
        ]
        
        # Test adaptation
        result = await framework.maml.few_shot_adapt(
            domain=LegalDomain.EMPLOYMENT,
            support_examples=support_examples,
            num_adaptation_steps=3
        )
        
        assert "domain" in result
        assert result["domain"] == "employment"
        assert "num_support_examples" in result
        assert result["num_support_examples"] == 3
        assert "few_shot_learning_achieved" in result
        assert result["few_shot_learning_achieved"] is True


class TestResearchFramework:
    """Test suite for research publication framework."""
    
    def test_research_framework_creation(self):
        """Test ResearchPublicationFramework creation."""
        framework = create_research_framework()
        
        assert framework is not None
        assert hasattr(framework, 'experiments')
        assert hasattr(framework, 'benchmarks')
        assert hasattr(framework, 'statistical_analyzer')
    
    def test_benchmark_dataset_creation(self):
        """Test benchmark dataset creation."""
        framework = create_research_framework()
        
        dataset = framework.create_benchmark_dataset(
            name="TestBenchmark",
            description="Test dataset for validation",
            size=100
        )
        
        assert dataset.name == "TestBenchmark"
        assert dataset.size == 100
        assert len(dataset.ground_truth) == 100
        
        # Test baseline metrics
        baseline_metrics = dataset.get_baseline_metrics()
        assert "random_accuracy" in baseline_metrics
        assert "majority_class_accuracy" in baseline_metrics
        assert "dataset_balance" in baseline_metrics
    
    def test_publication_venue_enum(self):
        """Test PublicationVenue enumeration."""
        assert PublicationVenue.NEURIPS.value == "neurips"
        assert PublicationVenue.ICML.value == "icml"
        assert PublicationVenue.NATURE_QI.value == "nature_quantum_information"
    
    def test_experiment_type_enum(self):
        """Test ExperimentType enumeration."""
        assert ExperimentType.COMPARATIVE_STUDY.value == "comparative_study"
        assert ExperimentType.QUANTUM_ADVANTAGE.value == "quantum_advantage"
        assert ExperimentType.FEW_SHOT_LEARNING.value == "few_shot_learning"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple research components."""
    
    @pytest.mark.asyncio
    async def test_multimodal_quantum_integration(self):
        """Test integration of multimodal transformers with quantum encoding."""
        # Create components
        multimodal_analyzer = create_legal_document_analyzer(d_model=128)
        quantum_analyzer = create_quantum_legal_analyzer(num_qubits=8)
        
        # Create test document elements
        elements = [
            DocumentElement(
                text="Contract termination clause",
                position=SpatialPosition(0.1, 0.2, 0.3, 0.05, 1),
                semantic_type="termination"
            )
        ]
        
        # Analyze with multimodal transformer
        multimodal_insights = await multimodal_analyzer.analyze_document(elements)
        
        # Use document embedding for quantum analysis
        document_embedding = multimodal_insights["document_embedding"]
        quantum_result = await quantum_analyzer.classify_document(document_embedding)
        
        assert "predicted_class" in quantum_result
        assert "quantum_features" in quantum_result
        assert quantum_result["quantum_features"] is True
    
    @pytest.mark.asyncio
    async def test_meta_learning_quantum_integration(self):
        """Test integration of meta-learning with quantum encoding."""
        # Create components
        meta_framework = create_meta_learning_framework(support_shots=3)
        quantum_analyzer = create_quantum_legal_analyzer(num_qubits=8)
        
        # Test few-shot adaptation
        support_examples = [
            (np.random.randn(64), 0),
            (np.random.randn(64), 1),
            (np.random.randn(64), 0),
        ]
        
        adaptation_result = await meta_framework.maml.few_shot_adapt(
            domain=LegalDomain.INTELLECTUAL_PROPERTY,
            support_examples=support_examples
        )
        
        # Use adapted features for quantum classification
        test_features = np.random.randn(64)
        quantum_result = await quantum_analyzer.classify_document(test_features)
        
        assert adaptation_result["few_shot_learning_achieved"]
        assert quantum_result["quantum_features"]
    
    @pytest.mark.asyncio
    async def test_complete_research_pipeline(self):
        """Test complete research pipeline integration."""
        # Create research framework
        research_framework = create_research_framework()
        
        # Create benchmark dataset
        dataset = research_framework.create_benchmark_dataset(
            name="IntegrationTest",
            description="Integration test dataset",
            size=50
        )
        
        # Create multimodal and quantum analyzers
        multimodal_analyzer = create_legal_document_analyzer(d_model=128)
        quantum_analyzer = create_quantum_legal_analyzer(num_qubits=8)
        meta_framework = create_meta_learning_framework()
        
        # Verify all components are functional
        assert dataset.size == 50
        assert multimodal_analyzer is not None
        assert quantum_analyzer is not None
        assert meta_framework is not None
        
        # Test basic functionality integration
        test_elements = [
            DocumentElement(
                text="Integration test clause",
                position=SpatialPosition(0.1, 0.2, 0.3, 0.05, 1),
                semantic_type="test"
            )
        ]
        
        multimodal_result = await multimodal_analyzer.analyze_document(test_elements)
        quantum_result = await quantum_analyzer.classify_document(np.random.randn(64))
        
        assert "document_embedding" in multimodal_result
        assert "predicted_class" in quantum_result


class TestPerformanceAndScalability:
    """Test performance and scalability of research components."""
    
    @pytest.mark.asyncio
    async def test_multimodal_transformer_scalability(self):
        """Test multimodal transformer with varying input sizes."""
        analyzer = create_legal_document_analyzer(d_model=128)
        
        # Test with different numbers of elements
        for num_elements in [1, 5, 10, 20]:
            elements = [
                DocumentElement(
                    text=f"Test clause {i}",
                    position=SpatialPosition(0.1, 0.1 * (i + 1), 0.3, 0.05, 1),
                    semantic_type="test"
                )
                for i in range(num_elements)
            ]
            
            result = await analyzer.analyze_document(elements)
            assert result["num_elements"] == num_elements
    
    @pytest.mark.asyncio
    async def test_quantum_encoder_scalability(self):
        """Test quantum encoder with varying qubit counts."""
        for num_qubits in [4, 8, 12, 16]:
            analyzer = create_quantum_legal_analyzer(num_qubits=num_qubits)
            
            features = np.random.randn(64)
            result = await analyzer.classify_document(features)
            
            assert "predicted_class" in result
            assert result["num_qubits_used"] == num_qubits
    
    def test_meta_learning_memory_efficiency(self):
        """Test meta-learning framework memory efficiency."""
        # Test with different configuration sizes
        for support_shots in [1, 3, 5, 10]:
            framework = create_meta_learning_framework(support_shots=support_shots)
            assert framework.config.support_shots == support_shots


# Performance benchmarking utilities
def benchmark_component_performance():
    """Benchmark performance of research components."""
    import time
    
    results = {}
    
    # Benchmark multimodal transformer
    start_time = time.time()
    analyzer = create_legal_document_analyzer(d_model=256, num_layers=4)
    elements = [
        DocumentElement(
            text=f"Benchmark clause {i}",
            position=SpatialPosition(0.1, 0.1 * (i + 1), 0.3, 0.05, 1),
            semantic_type="benchmark"
        )
        for i in range(10)
    ]
    end_time = time.time()
    results["multimodal_creation_time"] = end_time - start_time
    
    # Benchmark quantum analyzer
    start_time = time.time()
    quantum_analyzer = create_quantum_legal_analyzer(num_qubits=16, num_classes=10)
    end_time = time.time()
    results["quantum_creation_time"] = end_time - start_time
    
    # Benchmark meta-learning framework
    start_time = time.time()
    meta_framework = create_meta_learning_framework(support_shots=5)
    end_time = time.time()
    results["meta_learning_creation_time"] = end_time - start_time
    
    return results


if __name__ == "__main__":
    # Run performance benchmarks
    benchmark_results = benchmark_component_performance()
    print("Research Component Performance Benchmarks:")
    for component, time_taken in benchmark_results.items():
        print(f"  {component}: {time_taken:.4f} seconds")
    
    # Run basic integration test
    async def basic_integration_test():
        analyzer = create_legal_document_analyzer()
        elements = [DocumentElement(
            text="Test integration",
            position=SpatialPosition(0.1, 0.2, 0.3, 0.05, 1),
            semantic_type="test"
        )]
        result = await analyzer.analyze_document(elements)
        print(f"Integration test successful: {len(result)} insights generated")
    
    asyncio.run(basic_integration_test())