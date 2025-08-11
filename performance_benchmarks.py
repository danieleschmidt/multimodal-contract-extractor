#!/usr/bin/env python3
"""Performance benchmarking script for the multimodal contract extractor."""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict
from unittest.mock import Mock

import psutil


class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite."""

    def __init__(self):
        self.results = {}

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        print("🚀 Running Performance Benchmarks...")

        results = {
            "system_info": self.get_system_info(),
            "neuromorphic_benchmark": self.benchmark_neuromorphic(),
            "quantum_benchmark": self.benchmark_quantum(),
            "validation_benchmark": self.benchmark_validation(),
            "orchestrator_benchmark": self.benchmark_orchestrator(),
            "memory_benchmark": self.benchmark_memory_usage(),
            "concurrent_benchmark": self.benchmark_concurrent_processing()
        }

        return results

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "python_version": f"Python {psutil.__version__}"
        }

    def benchmark_neuromorphic(self) -> Dict[str, Any]:
        """Benchmark neuromorphic processing components."""
        print("  🧠 Benchmarking neuromorphic processing...")

        try:
            # Import neuromorphic components
            import sys
            sys.path.insert(0, '.')
            from src.multimodal_contract_extractor.neuromorphic_processing import (
                NeuromorphicLayer,
                PhotonicNeuromorphicProcessor,
                PhotonicNeuron,
            )

            # Benchmark neuron operations
            neuron_times = []
            for _ in range(1000):
                start = time.perf_counter()
                neuron = PhotonicNeuron("bench_neuron")
                neuron.receive_input(0.7)
                neuron.spike(time.time())
                neuron_times.append(time.perf_counter() - start)

            # Benchmark layer processing
            layer = NeuromorphicLayer("bench_layer")
            for i in range(64):
                layer.neurons.append(PhotonicNeuron(f"n{i}"))

            layer_times = []
            for _ in range(100):
                start = time.perf_counter()
                inputs = [0.5] * 64
                layer.process_batch(inputs, time.time())
                layer_times.append(time.perf_counter() - start)

            # Benchmark processor initialization
            start = time.perf_counter()
            processor = PhotonicNeuromorphicProcessor(layers=5, neurons_per_layer=32)
            init_time = time.perf_counter() - start

            return {
                "neuron_operation_avg_us": statistics.mean(neuron_times) * 1_000_000,
                "layer_processing_avg_ms": statistics.mean(layer_times) * 1000,
                "processor_init_time_ms": init_time * 1000,
                "memory_per_neuron_bytes": 1024,  # Estimated
                "success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def benchmark_quantum(self) -> Dict[str, Any]:
        """Benchmark quantum processing components."""
        print("  ⚛️  Benchmarking quantum processing...")

        try:
            import sys
            sys.path.insert(0, '.')
            from src.multimodal_contract_extractor.quantum_enhanced_extraction import (
                QuantumCircuit,
                QuantumContractProcessor,
                Qubit,
            )

            # Benchmark qubit operations
            qubit_times = []
            for _ in range(1000):
                start = time.perf_counter()
                qubit = Qubit("bench_qubit")
                qubit.apply_rotation(3.14159/4)
                qubit.measure(time.time())
                qubit_times.append(time.perf_counter() - start)

            # Benchmark circuit operations
            circuit_times = []
            for _ in range(100):
                start = time.perf_counter()
                circuit = QuantumCircuit("bench_circuit")
                for i in range(8):
                    circuit.add_qubit(f"q{i}")
                circuit.apply_hadamard("q0")
                circuit.apply_cnot("q0", "q1")
                circuit.measure_all(time.time())
                circuit_times.append(time.perf_counter() - start)

            # Benchmark processor initialization
            start = time.perf_counter()
            processor = QuantumContractProcessor(num_qubits=16)
            init_time = time.perf_counter() - start

            return {
                "qubit_operation_avg_us": statistics.mean(qubit_times) * 1_000_000,
                "circuit_processing_avg_ms": statistics.mean(circuit_times) * 1000,
                "processor_init_time_ms": init_time * 1000,
                "qubits_per_mb": 1024,  # Theoretical
                "success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def benchmark_validation(self) -> Dict[str, Any]:
        """Benchmark validation components."""
        print("  🔍 Benchmarking validation...")

        try:
            import sys
            sys.path.insert(0, '.')
            from src.multimodal_contract_extractor.advanced_validation import (
                AdvancedValidator,
                ProcessingMode,
            )

            validator = AdvancedValidator()

            # Create mock document
            mock_document = Mock()
            mock_document.pages = [Mock() for _ in range(5)]
            for i, page in enumerate(mock_document.pages):
                page.image = Mock()
                page.number = i + 1

            # Benchmark validation operations
            validation_times = []
            for _ in range(50):
                start = time.perf_counter()
                # Simulate validation (can't run async in sync context)
                validator._validate_document_structure(
                    mock_document, ProcessingMode.NEUROMORPHIC, {}
                )
                validation_times.append(time.perf_counter() - start)

            return {
                "validation_avg_ms": statistics.mean(validation_times) * 1000,
                "validation_rules_count": len(validator.validation_rules),
                "success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def benchmark_orchestrator(self) -> Dict[str, Any]:
        """Benchmark orchestrator components."""
        print("  🎭 Benchmarking orchestrator...")

        try:
            import sys
            sys.path.insert(0, '.')
            from src.multimodal_contract_extractor.hybrid_orchestrator import (
                LoadBalancer,
                ProcessorPool,
                ProcessorType,
            )

            # Benchmark processor pool operations
            pool_times = []
            for _ in range(100):
                start = time.perf_counter()
                pool = ProcessorPool()
                pool.update_metrics(ProcessorType.NEUROMORPHIC, 0.5, True, 0.9, 2.0)
                pool.get_metrics_summary()
                pool_times.append(time.perf_counter() - start)

            # Benchmark load balancer
            balancer_times = []
            load_balancer = LoadBalancer()
            for _ in range(1000):
                start = time.perf_counter()
                load_balancer.allocate_processor(ProcessorType.NEUROMORPHIC)
                load_balancer.release_processor(ProcessorType.NEUROMORPHIC)
                balancer_times.append(time.perf_counter() - start)

            return {
                "pool_operation_avg_us": statistics.mean(pool_times) * 1_000_000,
                "load_balancer_avg_us": statistics.mean(balancer_times) * 1_000_000,
                "processor_types_count": len(list(ProcessorType)),
                "success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage of components."""
        print("  💾 Benchmarking memory usage...")

        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

        try:
            import sys
            sys.path.insert(0, '.')

            # Load modules and measure memory impact
            from src.multimodal_contract_extractor.neuromorphic_processing import (
                PhotonicNeuromorphicProcessor,
            )
            neuro_memory = psutil.Process().memory_info().rss / (1024 * 1024) - initial_memory

            from src.multimodal_contract_extractor.quantum_enhanced_extraction import (
                QuantumContractProcessor,
            )
            quantum_memory = psutil.Process().memory_info().rss / (1024 * 1024) - initial_memory - neuro_memory

            # Create large instances to measure scaling
            large_neuro = PhotonicNeuromorphicProcessor(layers=10, neurons_per_layer=128)
            large_neuro_memory = psutil.Process().memory_info().rss / (1024 * 1024) - initial_memory - neuro_memory - quantum_memory

            large_quantum = QuantumContractProcessor(num_qubits=32)
            large_quantum_memory = psutil.Process().memory_info().rss / (1024 * 1024) - initial_memory - neuro_memory - quantum_memory - large_neuro_memory

            return {
                "initial_memory_mb": round(initial_memory, 2),
                "neuromorphic_base_mb": round(max(neuro_memory, 0), 2),
                "quantum_base_mb": round(max(quantum_memory, 0), 2),
                "large_neuromorphic_mb": round(max(large_neuro_memory, 0), 2),
                "large_quantum_mb": round(max(large_quantum_memory, 0), 2),
                "total_memory_mb": round(psutil.Process().memory_info().rss / (1024 * 1024), 2),
                "success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def benchmark_concurrent_processing(self) -> Dict[str, Any]:
        """Benchmark concurrent processing capabilities."""
        print("  🔄 Benchmarking concurrent processing...")

        def mock_processing_task(task_id: int) -> Dict[str, Any]:
            """Mock processing task for benchmarking."""
            start = time.perf_counter()
            # Simulate processing work
            time.sleep(0.01)  # 10ms simulated work
            return {
                "task_id": task_id,
                "processing_time": time.perf_counter() - start,
                "success": True
            }

        # Sequential processing benchmark
        sequential_start = time.perf_counter()
        sequential_results = []
        for i in range(10):
            result = mock_processing_task(i)
            sequential_results.append(result)
        sequential_time = time.perf_counter() - sequential_start

        # Concurrent processing benchmark
        concurrent_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(mock_processing_task, range(10)))
        concurrent_time = time.perf_counter() - concurrent_start

        # Calculate speedup
        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 1.0

        return {
            "sequential_time_ms": round(sequential_time * 1000, 2),
            "concurrent_time_ms": round(concurrent_time * 1000, 2),
            "speedup_factor": round(speedup, 2),
            "parallel_efficiency": round((speedup / 4) * 100, 1),  # 4 workers
            "success": True
        }

    def print_benchmark_report(self, results: Dict[str, Any]):
        """Print comprehensive benchmark report."""
        print("\n🚀 PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)

        # System information
        system = results.get("system_info", {})
        print("\n💻 System Information:")
        print(f"   CPU Cores: {system.get('cpu_count', 'Unknown')}")
        print(f"   Memory: {system.get('memory_total_gb', 'Unknown')} GB total, {system.get('memory_available_gb', 'Unknown')} GB available")
        print(f"   Disk Usage: {system.get('disk_usage_percent', 'Unknown')}%")

        # Component benchmarks
        components = [
            ("neuromorphic_benchmark", "🧠 Neuromorphic Processing", "us"),
            ("quantum_benchmark", "⚛️  Quantum Processing", "us"),
            ("validation_benchmark", "🔍 Validation System", "ms"),
            ("orchestrator_benchmark", "🎭 Orchestrator", "us")
        ]

        total_score = 0
        successful_benchmarks = 0

        for key, name, unit in components:
            benchmark = results.get(key, {})
            if benchmark.get("success", False):
                print(f"\n{name}:")

                if key == "neuromorphic_benchmark":
                    print(f"   Neuron Operation: {benchmark.get('neuron_operation_avg_us', 0):.2f} μs")
                    print(f"   Layer Processing: {benchmark.get('layer_processing_avg_ms', 0):.2f} ms")
                    print(f"   Processor Init: {benchmark.get('processor_init_time_ms', 0):.2f} ms")
                    score = max(0, 100 - benchmark.get('layer_processing_avg_ms', 0))

                elif key == "quantum_benchmark":
                    print(f"   Qubit Operation: {benchmark.get('qubit_operation_avg_us', 0):.2f} μs")
                    print(f"   Circuit Processing: {benchmark.get('circuit_processing_avg_ms', 0):.2f} ms")
                    print(f"   Processor Init: {benchmark.get('processor_init_time_ms', 0):.2f} ms")
                    score = max(0, 100 - benchmark.get('circuit_processing_avg_ms', 0))

                elif key == "validation_benchmark":
                    print(f"   Validation Time: {benchmark.get('validation_avg_ms', 0):.2f} ms")
                    print(f"   Validation Rules: {benchmark.get('validation_rules_count', 0)}")
                    score = max(0, 100 - benchmark.get('validation_avg_ms', 0) * 10)

                elif key == "orchestrator_benchmark":
                    print(f"   Pool Operations: {benchmark.get('pool_operation_avg_us', 0):.2f} μs")
                    print(f"   Load Balancer: {benchmark.get('load_balancer_avg_us', 0):.2f} μs")
                    score = max(0, 100 - benchmark.get('pool_operation_avg_us', 0) / 10)

                total_score += score
                successful_benchmarks += 1
                print(f"   Performance Score: {score:.1f}/100")
            else:
                print(f"\n{name}: ❌ Failed - {benchmark.get('error', 'Unknown error')}")

        # Memory benchmark
        memory = results.get("memory_benchmark", {})
        if memory.get("success", False):
            print("\n💾 Memory Usage:")
            print(f"   Base Memory: {memory.get('total_memory_mb', 0)} MB")
            print(f"   Neuromorphic: +{memory.get('neuromorphic_base_mb', 0)} MB")
            print(f"   Quantum: +{memory.get('quantum_base_mb', 0)} MB")
            memory_score = max(0, 100 - memory.get('total_memory_mb', 0) / 10)
            print(f"   Memory Efficiency: {memory_score:.1f}/100")
            total_score += memory_score
            successful_benchmarks += 1

        # Concurrency benchmark
        concurrent = results.get("concurrent_benchmark", {})
        if concurrent.get("success", False):
            print("\n🔄 Concurrent Processing:")
            print(f"   Sequential Time: {concurrent.get('sequential_time_ms', 0)} ms")
            print(f"   Concurrent Time: {concurrent.get('concurrent_time_ms', 0)} ms")
            print(f"   Speedup Factor: {concurrent.get('speedup_factor', 0)}x")
            print(f"   Parallel Efficiency: {concurrent.get('parallel_efficiency', 0)}%")
            concurrent_score = min(100, concurrent.get('speedup_factor', 0) * 25)
            print(f"   Concurrency Score: {concurrent_score:.1f}/100")
            total_score += concurrent_score
            successful_benchmarks += 1

        # Overall performance score
        if successful_benchmarks > 0:
            overall_score = total_score / successful_benchmarks
            print(f"\n🏆 OVERALL PERFORMANCE SCORE: {overall_score:.1f}/100")

            if overall_score >= 90:
                print("✅ Excellent performance")
            elif overall_score >= 75:
                print("✅ Good performance")
            elif overall_score >= 60:
                print("⚠️  Fair performance")
            else:
                print("🔴 Poor performance - optimization needed")

            return overall_score
        else:
            print("\n❌ No successful benchmarks completed")
            return 0


def main():
    """Run performance benchmarks."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()
    score = benchmark.print_benchmark_report(results)

    # Save results to file
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n📄 Detailed results saved to benchmark_results.json")

    # Exit with appropriate code
    if score >= 75:
        exit(0)
    elif score >= 50:
        exit(1)
    else:
        exit(2)


if __name__ == "__main__":
    main()
