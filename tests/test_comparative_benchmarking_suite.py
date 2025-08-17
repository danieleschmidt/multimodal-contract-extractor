"""Comprehensive tests for comparative benchmarking suite."""

import asyncio
import pytest

from multimodal_contract_extractor.comparative_benchmarking_suite import (
    BenchmarkResult,
    BenchmarkType,
    ComparativeBenchmarkingSuite,
    ModelCategory,
    get_benchmarking_suite,
    register_benchmark_dataset,
    run_comprehensive_benchmark,
)


class TestBenchmarkResult:
    """Test BenchmarkResult data class."""

    def test_benchmark_result_creation(self):
        """Test creating a benchmark result."""
        result = BenchmarkResult(
            model_name="test_model",
            model_category=ModelCategory.QUANTUM_ENHANCED,
            benchmark_type=BenchmarkType.ACCURACY_BENCHMARK,
            metrics={"accuracy": 0.85, "precision": 0.82},
            timestamp=1000.0,
            dataset_size=500,
            execution_time=2.5,
            memory_usage=1.2
        )
        
        assert result.model_name == "test_model"
        assert result.model_category == ModelCategory.QUANTUM_ENHANCED
        assert result.benchmark_type == BenchmarkType.ACCURACY_BENCHMARK
        assert result.metrics["accuracy"] == 0.85
        assert result.dataset_size == 500
        assert result.execution_time == 2.5


class TestComparativeBenchmarkingSuite:
    """Test ComparativeBenchmarkingSuite class."""

    @pytest.fixture
    def suite(self):
        """Create a benchmarking suite for testing."""
        return ComparativeBenchmarkingSuite()

    @pytest.mark.asyncio
    async def test_register_dataset(self, suite):
        """Test dataset registration."""
        dataset_config = {
            "size": 1000,
            "complexity": "high",
            "domain": "contract_law"
        }
        
        await suite.register_dataset("test_dataset", dataset_config)
        
        assert "test_dataset" in suite.datasets
        assert suite.datasets["test_dataset"]["size"] == 1000
        assert suite.datasets["test_dataset"]["complexity"] == "high"
        assert suite.datasets["test_dataset"]["domain"] == "contract_law"

    @pytest.mark.asyncio
    async def test_accuracy_benchmark(self, suite):
        """Test accuracy benchmark."""
        # Register dataset first
        await suite.register_dataset("accuracy_test", {"size": 500})
        
        # Run accuracy benchmark
        result = await suite.run_accuracy_benchmark(
            model_name="test_model",
            model_category=ModelCategory.QUANTUM_ENHANCED,
            dataset_name="accuracy_test",
            model_config={}
        )
        
        # Verify result
        assert result.model_name == "test_model"
        assert result.model_category == ModelCategory.QUANTUM_ENHANCED
        assert result.benchmark_type == BenchmarkType.ACCURACY_BENCHMARK
        assert result.dataset_size == 500
        
        # Verify metrics
        assert "accuracy" in result.metrics
        assert "precision" in result.metrics
        assert "recall" in result.metrics
        assert "f1_score" in result.metrics
        
        # Verify metrics are in reasonable ranges
        assert 0 <= result.metrics["accuracy"] <= 1
        assert 0 <= result.metrics["precision"] <= 1
        assert 0 <= result.metrics["recall"] <= 1
        
        # Verify confidence intervals
        assert "accuracy" in result.confidence_intervals
        lower, upper = result.confidence_intervals["accuracy"]
        assert lower <= result.metrics["accuracy"] <= upper

    @pytest.mark.asyncio
    async def test_speed_benchmark(self, suite):
        """Test speed benchmark."""
        # Register dataset
        await suite.register_dataset("speed_test", {"size": 1000})
        
        # Run speed benchmark
        result = await suite.run_speed_benchmark(
            model_name="speed_model",
            model_category=ModelCategory.NEUROMORPHIC,
            dataset_name="speed_test",
            model_config={}
        )
        
        # Verify result
        assert result.benchmark_type == BenchmarkType.SPEED_BENCHMARK
        
        # Verify speed metrics
        assert "mean_inference_time" in result.metrics
        assert "median_inference_time" in result.metrics
        assert "throughput_docs_per_second" in result.metrics
        assert "latency_p95" in result.metrics
        assert "latency_p99" in result.metrics
        
        # Verify metrics are positive
        assert result.metrics["mean_inference_time"] > 0
        assert result.metrics["throughput_docs_per_second"] > 0

    @pytest.mark.asyncio
    async def test_scalability_benchmark(self, suite):
        """Test scalability benchmark."""
        # Register base dataset
        await suite.register_dataset("scalability_base", {"size": 100})
        
        # Run scalability benchmark
        results = await suite.run_scalability_benchmark(
            model_name="scalable_model",
            model_category=ModelCategory.HYBRID_APPROACHES,
            scale_factors=[1, 2, 4],
            base_dataset_name="scalability_base",
            model_config={}
        )
        
        # Verify results
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert result.benchmark_type == BenchmarkType.SCALABILITY_BENCHMARK
            assert result.metrics["scale_factor"] == [1, 2, 4][i]
            assert result.dataset_size == 100 * [1, 2, 4][i]
            
            # Verify scalability metrics
            assert "processing_time" in result.metrics
            assert "memory_scaling" in result.metrics
            assert "time_complexity" in result.metrics
            assert "efficiency_ratio" in result.metrics

    @pytest.mark.asyncio
    async def test_robustness_benchmark(self, suite):
        """Test robustness benchmark."""
        # Register dataset
        await suite.register_dataset("robustness_test", {"size": 800})
        
        # Run robustness benchmark
        result = await suite.run_robustness_benchmark(
            model_name="robust_model",
            model_category=ModelCategory.TRANSFORMER_BASED,
            dataset_name="robustness_test",
            adversarial_config={"noise_types": ["gaussian", "adversarial"]}
        )
        
        # Verify result
        assert result.benchmark_type == BenchmarkType.ROBUSTNESS_BENCHMARK
        
        # Verify robustness metrics
        assert "robustness_score" in result.metrics
        assert "noise_sensitivity" in result.metrics
        assert "min_robust_performance" in result.metrics
        assert "adversarial_accuracy" in result.metrics
        assert "defense_effectiveness" in result.metrics
        
        # Verify metrics are in reasonable ranges
        assert 0 <= result.metrics["robustness_score"] <= 1
        assert 0 <= result.metrics["adversarial_accuracy"] <= 1

    @pytest.mark.asyncio
    async def test_fairness_benchmark(self, suite):
        """Test fairness benchmark."""
        # Register dataset
        await suite.register_dataset("fairness_test", {"size": 600})
        
        # Run fairness benchmark
        result = await suite.run_fairness_benchmark(
            model_name="fair_model",
            model_category=ModelCategory.DEEP_LEARNING,
            dataset_name="fairness_test",
            fairness_config={"groups": ["group_a", "group_b", "group_c"]}
        )
        
        # Verify result
        assert result.benchmark_type == BenchmarkType.FAIRNESS_BENCHMARK
        
        # Verify fairness metrics
        assert "demographic_parity" in result.metrics
        assert "equalized_odds" in result.metrics
        assert "individual_fairness" in result.metrics
        assert "overall_fairness_score" in result.metrics
        assert "fairness_variance" in result.metrics
        
        # Verify group-specific metrics
        assert "group_a_accuracy" in result.metrics
        assert "group_b_accuracy" in result.metrics
        assert "group_c_accuracy" in result.metrics
        
        # Verify metrics are in reasonable ranges
        assert 0 <= result.metrics["overall_fairness_score"] <= 1

    def test_base_accuracy_by_category(self, suite):
        """Test base accuracy assignment by model category."""
        # Test different model categories
        quantum_acc = suite._get_base_accuracy(ModelCategory.QUANTUM_ENHANCED)
        classical_acc = suite._get_base_accuracy(ModelCategory.CLASSICAL_ML)
        transformer_acc = suite._get_base_accuracy(ModelCategory.TRANSFORMER_BASED)
        
        # Verify quantum and transformer models have higher base accuracy
        assert quantum_acc > classical_acc
        assert transformer_acc > classical_acc
        
        # Verify all accuracies are reasonable
        assert 0.5 <= classical_acc <= 1.0
        assert 0.5 <= quantum_acc <= 1.0
        assert 0.5 <= transformer_acc <= 1.0

    def test_memory_usage_simulation(self, suite):
        """Test memory usage simulation."""
        # Test different model categories
        classical_memory = suite._simulate_memory_usage(ModelCategory.CLASSICAL_ML, 1000)
        transformer_memory = suite._simulate_memory_usage(ModelCategory.TRANSFORMER_BASED, 1000)
        
        # Verify transformer models use more memory
        assert transformer_memory > classical_memory
        
        # Test scaling with dataset size
        small_memory = suite._simulate_memory_usage(ModelCategory.DEEP_LEARNING, 100)
        large_memory = suite._simulate_memory_usage(ModelCategory.DEEP_LEARNING, 10000)
        
        assert large_memory > small_memory

    def test_confidence_intervals(self, suite):
        """Test confidence interval calculation."""
        metrics = {
            "accuracy": 0.85,
            "precision": 0.82,
            "processing_time": 1.5
        }
        
        intervals = suite._calculate_confidence_intervals(metrics)
        
        # Verify intervals exist for all metrics
        assert "accuracy" in intervals
        assert "precision" in intervals
        assert "processing_time" in intervals
        
        # Verify interval structure
        for metric, (lower, upper) in intervals.items():
            assert lower <= metrics[metric] <= upper
            assert lower < upper

    def test_comparative_report_generation(self, suite):
        """Test comparative report generation."""
        # Add some mock results
        result1 = BenchmarkResult(
            model_name="model_a",
            model_category=ModelCategory.QUANTUM_ENHANCED,
            benchmark_type=BenchmarkType.ACCURACY_BENCHMARK,
            metrics={"accuracy": 0.85, "precision": 0.82},
            timestamp=1000.0,
            dataset_size=500,
            execution_time=2.0,
            memory_usage=1.5
        )
        
        result2 = BenchmarkResult(
            model_name="model_b",
            model_category=ModelCategory.CLASSICAL_ML,
            benchmark_type=BenchmarkType.ACCURACY_BENCHMARK,
            metrics={"accuracy": 0.78, "precision": 0.75},
            timestamp=1001.0,
            dataset_size=500,
            execution_time=1.0,
            memory_usage=0.8
        )
        
        suite.benchmark_results.extend([result1, result2])
        
        # Generate report
        report = suite.generate_comparative_report(["model_a", "model_b"])
        
        # Verify report structure
        assert "metadata" in report
        assert "comparative_analysis" in report
        assert "overall_rankings" in report
        assert "statistical_significance" in report
        assert "recommendations" in report
        assert "summary" in report
        
        # Verify metadata
        assert report["metadata"]["models_compared"] == ["model_a", "model_b"]
        assert report["metadata"]["total_benchmarks"] == 2
        
        # Verify rankings
        rankings = report["overall_rankings"]
        assert "model_a" in rankings
        assert "model_b" in rankings
        assert rankings["model_a"] != rankings["model_b"]

    def test_statistical_significance_tests(self, suite):
        """Test statistical significance testing."""
        # Add mock results for multiple models
        models = ["model_x", "model_y", "model_z"]
        for model in models:
            result = BenchmarkResult(
                model_name=model,
                model_category=ModelCategory.QUANTUM_ENHANCED,
                benchmark_type=BenchmarkType.ACCURACY_BENCHMARK,
                metrics={"accuracy": 0.8 + len(model) * 0.01},  # Slight differences
                timestamp=1000.0,
                dataset_size=500,
                execution_time=2.0,
                memory_usage=1.5
            )
            suite.benchmark_results.append(result)
        
        # Run significance tests
        significance = suite._run_significance_tests(suite.benchmark_results[-3:])
        
        # Verify pairwise comparisons exist
        assert "model_x_vs_model_y" in significance
        assert "model_x_vs_model_z" in significance
        assert "model_y_vs_model_z" in significance
        
        # Verify significance test structure
        for test_name, test_result in significance.items():
            assert "p_value" in test_result
            assert "significant" in test_result
            assert "effect_size" in test_result
            assert "confidence_interval" in test_result
            
            # Verify types
            assert isinstance(test_result["p_value"], float)
            assert isinstance(test_result["significant"], bool)
            assert isinstance(test_result["effect_size"], float)


class TestHighLevelAPI:
    """Test high-level API functions."""

    @pytest.mark.asyncio
    async def test_register_benchmark_dataset(self):
        """Test high-level dataset registration."""
        config = {"size": 2000, "complexity": "high"}
        await register_benchmark_dataset("api_dataset", config)
        
        # Verify dataset was registered in global suite
        suite = get_benchmarking_suite()
        assert "api_dataset" in suite.datasets
        assert suite.datasets["api_dataset"]["size"] == 2000

    @pytest.mark.asyncio
    async def test_run_comprehensive_benchmark(self):
        """Test high-level comprehensive benchmarking."""
        # Register dataset first
        await register_benchmark_dataset("comprehensive_test", {"size": 800})
        
        # Run comprehensive benchmark
        results = await run_comprehensive_benchmark(
            model_name="comprehensive_model",
            model_category=ModelCategory.HYBRID_APPROACHES,
            dataset_name="comprehensive_test",
            model_config={}
        )
        
        # Verify all benchmark types were run
        benchmark_types = {result.benchmark_type for result in results}
        
        assert BenchmarkType.ACCURACY_BENCHMARK in benchmark_types
        assert BenchmarkType.SPEED_BENCHMARK in benchmark_types
        assert BenchmarkType.SCALABILITY_BENCHMARK in benchmark_types
        assert BenchmarkType.ROBUSTNESS_BENCHMARK in benchmark_types
        assert BenchmarkType.FAIRNESS_BENCHMARK in benchmark_types
        
        # Verify scalability results (should have multiple results)
        scalability_results = [
            r for r in results if r.benchmark_type == BenchmarkType.SCALABILITY_BENCHMARK
        ]
        assert len(scalability_results) > 1  # Multiple scale factors

    def test_get_benchmarking_suite(self):
        """Test getting the global benchmarking suite."""
        suite = get_benchmarking_suite()
        assert isinstance(suite, ComparativeBenchmarkingSuite)


class TestEnumerations:
    """Test enumeration values."""

    def test_benchmark_type_values(self):
        """Test benchmark type enum values."""
        assert BenchmarkType.ACCURACY_BENCHMARK.value == "accuracy_benchmark"
        assert BenchmarkType.SPEED_BENCHMARK.value == "speed_benchmark"
        assert BenchmarkType.MEMORY_BENCHMARK.value == "memory_benchmark"
        assert BenchmarkType.SCALABILITY_BENCHMARK.value == "scalability_benchmark"
        assert BenchmarkType.ROBUSTNESS_BENCHMARK.value == "robustness_benchmark"
        assert BenchmarkType.FAIRNESS_BENCHMARK.value == "fairness_benchmark"

    def test_model_category_values(self):
        """Test model category enum values."""
        assert ModelCategory.CLASSICAL_ML.value == "classical_ml"
        assert ModelCategory.DEEP_LEARNING.value == "deep_learning"
        assert ModelCategory.TRANSFORMER_BASED.value == "transformer_based"
        assert ModelCategory.QUANTUM_ENHANCED.value == "quantum_enhanced"
        assert ModelCategory.NEUROMORPHIC.value == "neuromorphic"
        assert ModelCategory.HYBRID_APPROACHES.value == "hybrid_approaches"


class TestIntegrationScenarios:
    """Test integration scenarios for benchmarking."""

    @pytest.mark.asyncio
    async def test_multi_model_comparison(self):
        """Test comparing multiple models across benchmarks."""
        suite = ComparativeBenchmarkingSuite()
        
        # Register dataset
        await suite.register_dataset("comparison_dataset", {"size": 1000})
        
        # Create models with different categories
        models = [
            ("classical_model", ModelCategory.CLASSICAL_ML),
            ("quantum_model", ModelCategory.QUANTUM_ENHANCED),
            ("transformer_model", ModelCategory.TRANSFORMER_BASED)
        ]
        
        # Run accuracy benchmarks for all models
        for model_name, model_category in models:
            await suite.run_accuracy_benchmark(
                model_name=model_name,
                model_category=model_category,
                dataset_name="comparison_dataset",
                model_config={}
            )
        
        # Generate comparative report
        model_names = [name for name, _ in models]
        report = suite.generate_comparative_report(model_names)
        
        # Verify all models in report
        assert set(report["metadata"]["models_compared"]) == set(model_names)
        assert len(report["overall_rankings"]) == len(models)
        
        # Verify comparative analysis exists
        assert "accuracy_benchmark" in report["comparative_analysis"]
        analysis = report["comparative_analysis"]["accuracy_benchmark"]
        assert "model_statistics" in analysis
        assert "best_performers" in analysis

    @pytest.mark.asyncio
    async def test_end_to_end_benchmarking_workflow(self):
        """Test complete end-to-end benchmarking workflow."""
        suite = ComparativeBenchmarkingSuite()
        
        # Step 1: Register multiple datasets
        datasets = [
            ("small_dataset", {"size": 500, "complexity": "low"}),
            ("large_dataset", {"size": 2000, "complexity": "high"})
        ]
        
        for dataset_name, config in datasets:
            await suite.register_dataset(dataset_name, config)
        
        # Step 2: Run comprehensive benchmarks for a model
        model_name = "end_to_end_model"
        model_category = ModelCategory.HYBRID_APPROACHES
        
        # Run on small dataset
        small_results = await run_comprehensive_benchmark(
            model_name, model_category, "small_dataset", {}
        )
        
        # Run accuracy benchmark on large dataset
        large_result = await suite.run_accuracy_benchmark(
            model_name, model_category, "large_dataset", {}
        )
        
        # Step 3: Verify results
        assert len(small_results) >= 5  # All benchmark types
        assert large_result.dataset_size == 2000
        
        # Step 4: Generate comprehensive report
        report = suite.generate_comparative_report([model_name])
        
        # Verify complete workflow results
        assert report["metadata"]["models_compared"] == [model_name]
        assert len(report["comparative_analysis"]) >= 2  # Multiple benchmark types
        assert "summary" in report
        assert "recommendations" in report