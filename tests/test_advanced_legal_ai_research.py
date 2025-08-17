"""Comprehensive tests for advanced legal AI research framework."""

import asyncio
import pytest

from multimodal_contract_extractor.advanced_legal_ai_research import (
    AlgorithmType,
    NovelAlgorithmFramework,
    ResearchDomain,
    ResearchExperiment,
    create_research_experiment,
    get_research_framework,
    run_causal_research,
    run_hyperbolic_research,
    run_neuromorphic_research,
    run_quantum_legal_research,
)


class TestResearchExperiment:
    """Test ResearchExperiment data class."""

    def test_experiment_creation(self):
        """Test creating a research experiment."""
        experiment = ResearchExperiment(
            id="test_exp",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Quantum advantage in legal document classification",
            success_metrics={"accuracy": 0.9, "speedup": 2.0}
        )
        
        assert experiment.id == "test_exp"
        assert experiment.domain == ResearchDomain.QUANTUM_LEGAL_ANALYSIS
        assert experiment.algorithm_type == AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER
        assert experiment.hypothesis == "Quantum advantage in legal document classification"
        assert experiment.success_metrics["accuracy"] == 0.9
        assert experiment.status == "initialized"


class TestNovelAlgorithmFramework:
    """Test NovelAlgorithmFramework class."""

    @pytest.fixture
    def framework(self):
        """Create a framework instance for testing."""
        return NovelAlgorithmFramework()

    @pytest.mark.asyncio
    async def test_create_experiment(self, framework):
        """Test creating an experiment through the framework."""
        experiment = await framework.create_experiment(
            experiment_id="test_quantum",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Test quantum hypothesis",
            success_metrics={"accuracy": 0.85}
        )
        
        assert experiment.id == "test_quantum"
        assert "test_quantum" in framework.experiments
        assert framework.experiments["test_quantum"] == experiment

    @pytest.mark.asyncio
    async def test_quantum_legal_classifier(self, framework):
        """Test quantum legal classifier implementation."""
        # Create experiment first
        await framework.create_experiment(
            experiment_id="quantum_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Quantum advantage test",
            success_metrics={"accuracy": 0.9}
        )
        
        # Run quantum implementation
        quantum_config = {"n_features": 16, "n_samples": 500}
        metrics = await framework.implement_quantum_legal_classifier(
            "quantum_test", quantum_config
        )
        
        # Verify metrics
        assert "quantum_accuracy" in metrics
        assert "quantum_speedup" in metrics
        assert "entanglement_measure" in metrics
        assert "quantum_fidelity" in metrics
        
        # Verify metrics are reasonable
        assert 0 <= metrics["quantum_accuracy"] <= 1
        assert metrics["quantum_speedup"] > 0
        assert 0 <= metrics["entanglement_measure"] <= 1
        assert 0 <= metrics["quantum_fidelity"] <= 1

    @pytest.mark.asyncio
    async def test_neuromorphic_processor(self, framework):
        """Test neuromorphic processor implementation."""
        # Create experiment
        await framework.create_experiment(
            experiment_id="neuromorphic_test",
            domain=ResearchDomain.NEUROMORPHIC_DOCUMENT_PROCESSING,
            algorithm_type=AlgorithmType.SPIKING_NEURAL_NETWORKS,
            hypothesis="Neuromorphic energy efficiency",
            success_metrics={"energy_efficiency": 0.2}
        )
        
        # Run neuromorphic implementation
        neuromorphic_config = {"n_neurons": 128, "time_steps": 50}
        metrics = await framework.implement_neuromorphic_processor(
            "neuromorphic_test", neuromorphic_config
        )
        
        # Verify metrics
        assert "spike_accuracy" in metrics
        assert "energy_efficiency" in metrics
        assert "temporal_dynamics" in metrics
        assert "plasticity_measure" in metrics
        
        # Verify energy efficiency is better than baseline
        assert metrics["energy_efficiency"] < 1.0  # Better than baseline

    @pytest.mark.asyncio
    async def test_hyperbolic_embeddings(self, framework):
        """Test hyperbolic embeddings implementation."""
        # Create experiment
        await framework.create_experiment(
            experiment_id="hyperbolic_test",
            domain=ResearchDomain.MULTIMODAL_LEGAL_UNDERSTANDING,
            algorithm_type=AlgorithmType.HYPERBOLIC_EMBEDDINGS,
            hypothesis="Hyperbolic hierarchy preservation",
            success_metrics={"hierarchy_preservation": 0.9}
        )
        
        # Run hyperbolic implementation
        embedding_config = {"dimensions": 32, "curvature": -0.5}
        metrics = await framework.implement_hyperbolic_embeddings(
            "hyperbolic_test", embedding_config
        )
        
        # Verify metrics
        assert "hierarchy_preservation" in metrics
        assert "embedding_quality" in metrics
        assert "geometric_consistency" in metrics
        assert "distortion_measure" in metrics
        
        # Verify hierarchy preservation is high
        assert metrics["hierarchy_preservation"] > 0.5

    @pytest.mark.asyncio
    async def test_causal_discovery(self, framework):
        """Test causal discovery implementation."""
        # Create experiment
        await framework.create_experiment(
            experiment_id="causal_test",
            domain=ResearchDomain.CAUSAL_LEGAL_REASONING,
            algorithm_type=AlgorithmType.CAUSAL_DISCOVERY_ALGORITHMS,
            hypothesis="Causal relationship discovery",
            success_metrics={"causal_accuracy": 0.8}
        )
        
        # Run causal implementation
        causal_config = {}
        metrics = await framework.implement_causal_discovery(
            "causal_test", causal_config
        )
        
        # Verify metrics
        assert "causal_accuracy" in metrics
        assert "edge_discovery_rate" in metrics
        assert "causal_strength" in metrics
        assert "confounding_control" in metrics
        
        # Verify reasonable causal accuracy
        assert metrics["causal_accuracy"] > 0.5

    @pytest.mark.asyncio
    async def test_comparative_study(self, framework):
        """Test comparative study functionality."""
        # Create experiment
        await framework.create_experiment(
            experiment_id="comparison_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Comparative analysis",
            success_metrics={"accuracy": 0.9}
        )
        
        # Add some metrics to the experiment
        framework.experiments["comparison_test"].current_metrics = {
            "accuracy": 0.88,
            "precision": 0.85,
            "processing_time": 0.5
        }
        
        # Run comparative study
        improvements = await framework.run_comparative_study(
            "comparison_test", "baseline_model"
        )
        
        # Verify improvements calculated
        assert "accuracy_improvement" in improvements
        assert "precision_improvement" in improvements
        assert "processing_time_improvement" in improvements

    def test_statistical_significance(self, framework):
        """Test statistical significance calculation."""
        # Create experiment with metrics
        framework.experiments["sig_test"] = ResearchExperiment(
            id="sig_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Significance test",
            success_metrics={"accuracy": 0.9},
            current_metrics={"accuracy": 0.88, "precision": 0.85}
        )
        
        significance = framework.calculate_statistical_significance("sig_test")
        
        # Verify significance results
        assert "accuracy_significant" in significance
        assert "precision_significant" in significance
        assert isinstance(significance["accuracy_significant"], bool)

    def test_research_report_generation(self, framework):
        """Test research report generation."""
        # Create experiment with complete data
        experiment = ResearchExperiment(
            id="report_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Report generation test",
            success_metrics={"accuracy": 0.9},
            current_metrics={"accuracy": 0.88, "precision": 0.85},
            baseline_metrics={"accuracy": 0.75, "precision": 0.72},
            dataset_size=1000,
            iterations=100,
            start_time=1000.0,
            status="completed"
        )
        framework.experiments["report_test"] = experiment
        
        report = framework.generate_research_report("report_test")
        
        # Verify report structure
        assert "experiment_summary" in report
        assert "methodology" in report
        assert "results" in report
        assert "conclusions" in report
        assert "future_work" in report
        
        # Verify experiment summary
        summary = report["experiment_summary"]
        assert summary["id"] == "report_test"
        assert summary["domain"] == "quantum_legal_analysis"
        assert summary["algorithm"] == "variational_quantum_classifier"
        
        # Verify methodology
        methodology = report["methodology"]
        assert methodology["dataset_size"] == 1000
        assert methodology["iterations"] == 100
        
        # Verify results
        results = report["results"]
        assert "current_metrics" in results
        assert "baseline_metrics" in results
        assert "statistical_significance" in results


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_create_research_experiment(self):
        """Test high-level experiment creation."""
        experiment = await create_research_experiment(
            experiment_id="api_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="API test hypothesis",
            success_metrics={"accuracy": 0.9}
        )
        
        assert experiment.id == "api_test"
        assert experiment.domain == ResearchDomain.QUANTUM_LEGAL_ANALYSIS

    @pytest.mark.asyncio
    async def test_run_quantum_legal_research(self):
        """Test high-level quantum research function."""
        # Create experiment first
        await create_research_experiment(
            experiment_id="quantum_api_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Quantum API test",
            success_metrics={"accuracy": 0.9}
        )
        
        metrics = await run_quantum_legal_research("quantum_api_test")
        
        assert "quantum_accuracy" in metrics
        assert "quantum_speedup" in metrics
        assert "entanglement_measure" in metrics
        assert "quantum_fidelity" in metrics

    @pytest.mark.asyncio
    async def test_run_neuromorphic_research(self):
        """Test high-level neuromorphic research function."""
        # Create experiment first
        await create_research_experiment(
            experiment_id="neuro_api_test",
            domain=ResearchDomain.NEUROMORPHIC_DOCUMENT_PROCESSING,
            algorithm_type=AlgorithmType.SPIKING_NEURAL_NETWORKS,
            hypothesis="Neuromorphic API test",
            success_metrics={"energy_efficiency": 0.2}
        )
        
        metrics = await run_neuromorphic_research("neuro_api_test")
        
        assert "spike_accuracy" in metrics
        assert "energy_efficiency" in metrics
        assert "temporal_dynamics" in metrics
        assert "plasticity_measure" in metrics

    @pytest.mark.asyncio
    async def test_run_hyperbolic_research(self):
        """Test high-level hyperbolic research function."""
        # Create experiment first
        await create_research_experiment(
            experiment_id="hyp_api_test",
            domain=ResearchDomain.MULTIMODAL_LEGAL_UNDERSTANDING,
            algorithm_type=AlgorithmType.HYPERBOLIC_EMBEDDINGS,
            hypothesis="Hyperbolic API test",
            success_metrics={"hierarchy_preservation": 0.9}
        )
        
        metrics = await run_hyperbolic_research("hyp_api_test")
        
        assert "hierarchy_preservation" in metrics
        assert "embedding_quality" in metrics
        assert "geometric_consistency" in metrics
        assert "distortion_measure" in metrics

    @pytest.mark.asyncio
    async def test_run_causal_research(self):
        """Test high-level causal research function."""
        # Create experiment first
        await create_research_experiment(
            experiment_id="causal_api_test",
            domain=ResearchDomain.CAUSAL_LEGAL_REASONING,
            algorithm_type=AlgorithmType.CAUSAL_DISCOVERY_ALGORITHMS,
            hypothesis="Causal API test",
            success_metrics={"causal_accuracy": 0.8}
        )
        
        metrics = await run_causal_research("causal_api_test")
        
        assert "causal_accuracy" in metrics
        assert "edge_discovery_rate" in metrics
        assert "causal_strength" in metrics
        assert "confounding_control" in metrics

    def test_get_research_framework(self):
        """Test getting the global research framework."""
        framework = get_research_framework()
        assert isinstance(framework, NovelAlgorithmFramework)


class TestResearchDomains:
    """Test research domain enumerations."""

    def test_research_domain_values(self):
        """Test research domain enum values."""
        assert ResearchDomain.QUANTUM_LEGAL_ANALYSIS.value == "quantum_legal_analysis"
        assert ResearchDomain.NEUROMORPHIC_DOCUMENT_PROCESSING.value == "neuromorphic_document_processing"
        assert ResearchDomain.META_LEARNING_CLAUSE_DETECTION.value == "meta_learning_clause_detection"
        assert ResearchDomain.MULTIMODAL_LEGAL_UNDERSTANDING.value == "multimodal_legal_understanding"
        assert ResearchDomain.FEDERATED_LEGAL_LEARNING.value == "federated_legal_learning"
        assert ResearchDomain.CAUSAL_LEGAL_REASONING.value == "causal_legal_reasoning"

    def test_algorithm_type_values(self):
        """Test algorithm type enum values."""
        assert AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER.value == "variational_quantum_classifier"
        assert AlgorithmType.SPIKING_NEURAL_NETWORKS.value == "spiking_neural_networks"
        assert AlgorithmType.GRAPH_ATTENTION_NETWORKS.value == "graph_attention_networks"
        assert AlgorithmType.HYPERBOLIC_EMBEDDINGS.value == "hyperbolic_embeddings"
        assert AlgorithmType.DIFFERENTIAL_PRIVACY_LEARNING.value == "differential_privacy_learning"
        assert AlgorithmType.CAUSAL_DISCOVERY_ALGORITHMS.value == "causal_discovery_algorithms"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple research components."""

    @pytest.mark.asyncio
    async def test_multi_algorithm_research_pipeline(self):
        """Test running multiple algorithms in a research pipeline."""
        framework = NovelAlgorithmFramework()
        
        # Create experiments for different algorithms
        experiments = []
        
        # Quantum experiment
        quantum_exp = await framework.create_experiment(
            experiment_id="multi_quantum",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Quantum multi-algorithm test",
            success_metrics={"accuracy": 0.9}
        )
        experiments.append(quantum_exp)
        
        # Neuromorphic experiment
        neuro_exp = await framework.create_experiment(
            experiment_id="multi_neuro",
            domain=ResearchDomain.NEUROMORPHIC_DOCUMENT_PROCESSING,
            algorithm_type=AlgorithmType.SPIKING_NEURAL_NETWORKS,
            hypothesis="Neuromorphic multi-algorithm test",
            success_metrics={"energy_efficiency": 0.2}
        )
        experiments.append(neuro_exp)
        
        # Run both algorithms
        quantum_metrics = await framework.implement_quantum_legal_classifier(
            "multi_quantum", {"n_features": 16, "n_samples": 500}
        )
        
        neuro_metrics = await framework.implement_neuromorphic_processor(
            "multi_neuro", {"n_neurons": 128, "time_steps": 50}
        )
        
        # Verify both experiments have results
        assert len(quantum_metrics) > 0
        assert len(neuro_metrics) > 0
        assert framework.experiments["multi_quantum"].current_metrics
        assert framework.experiments["multi_neuro"].current_metrics

    @pytest.mark.asyncio
    async def test_research_pipeline_with_comparison(self):
        """Test complete research pipeline with baseline comparison."""
        framework = NovelAlgorithmFramework()
        
        # Create experiment
        await framework.create_experiment(
            experiment_id="pipeline_test",
            domain=ResearchDomain.QUANTUM_LEGAL_ANALYSIS,
            algorithm_type=AlgorithmType.VARIATIONAL_QUANTUM_CLASSIFIER,
            hypothesis="Complete pipeline test",
            success_metrics={"accuracy": 0.9, "speedup": 2.0}
        )
        
        # Run algorithm
        metrics = await framework.implement_quantum_legal_classifier(
            "pipeline_test", {"n_features": 16, "n_samples": 1000}
        )
        
        # Run comparative study
        improvements = await framework.run_comparative_study(
            "pipeline_test", "baseline_classical"
        )
        
        # Calculate significance
        significance = framework.calculate_statistical_significance("pipeline_test")
        
        # Generate report
        report = framework.generate_research_report("pipeline_test")
        
        # Verify complete pipeline results
        assert metrics
        assert improvements
        assert significance
        assert report
        assert "experiment_summary" in report
        assert "results" in report
        assert "conclusions" in report