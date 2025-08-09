"""Research framework for neuromorphic and quantum processing evaluation.

This module provides comprehensive research capabilities for benchmarking,
experimentation, and academic publication preparation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
import hashlib
import math
import random
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, namedtuple

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """Types of research experiments."""
    COMPARATIVE_STUDY = "comparative_study"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    ACCURACY_ANALYSIS = "accuracy_analysis"
    SCALABILITY_TEST = "scalability_test"
    ENERGY_EFFICIENCY = "energy_efficiency"
    QUANTUM_ADVANTAGE = "quantum_advantage"
    NEUROMORPHIC_EFFICIENCY = "neuromorphic_efficiency"
    ALGORITHM_COMPARISON = "algorithm_comparison"


class StatisticalTest(Enum):
    """Statistical test types for significance analysis."""
    T_TEST = "t_test"
    MANN_WHITNEY_U = "mann_whitney_u"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    KRUSKAL_WALLIS = "kruskal_wallis"
    ANOVA = "anova"
    CHI_SQUARE = "chi_square"
    BOOTSTRAP_TEST = "bootstrap_test"
    PERMUTATION_TEST = "permutation_test"
    BAYESIAN_T_TEST = "bayesian_t_test"
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
    

class MultipleComparisonCorrection(Enum):
    """Multiple comparison correction methods."""
    NONE = "none"
    BONFERRONI = "bonferroni"
    HOLM_BONFERRONI = "holm_bonferroni"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BENJAMINI_YEKUTIELI = "benjamini_yekutieli"
    

class CrossValidationType(Enum):
    """Cross-validation types for model evaluation."""
    K_FOLD = "k_fold"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    TIME_SERIES_SPLIT = "time_series_split"
    LEAVE_ONE_OUT = "leave_one_out"
    LEAVE_ONE_GROUP_OUT = "leave_one_group_out"
    

# Statistical test result structures
BootstrapResult = namedtuple('BootstrapResult', ['statistic', 'confidence_interval', 'p_value', 'bootstrap_samples'])
BayesianTestResult = namedtuple('BayesianTestResult', ['bayes_factor', 'posterior_prob', 'credible_interval'])
CrossValidationResult = namedtuple('CrossValidationResult', ['scores', 'mean_score', 'std_score', 'fold_results'])


@dataclass
class ExperimentConfig:
    """Configuration for research experiments."""
    
    experiment_id: str
    experiment_type: ExperimentType
    name: str
    description: str
    hypothesis: str
    success_criteria: Dict[str, Any]
    parameters: Dict[str, Any] = field(default_factory=dict)
    baseline_methods: List[str] = field(default_factory=list)
    novel_methods: List[str] = field(default_factory=list)
    datasets: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    repetitions: int = 10
    confidence_level: float = 0.95
    statistical_tests: List[StatisticalTest] = field(default_factory=list)
    multiple_comparison_correction: MultipleComparisonCorrection = MultipleComparisonCorrection.BENJAMINI_HOCHBERG
    cross_validation_type: CrossValidationType = CrossValidationType.STRATIFIED_K_FOLD
    cross_validation_folds: int = 5
    bootstrap_samples: int = 10000
    alpha_level: float = 0.05
    publication_ready: bool = False
    ethical_considerations: List[str] = field(default_factory=list)


@dataclass
class ExperimentResult:
    """Single experiment run result."""
    
    run_id: str
    method_name: str
    dataset_name: str
    timestamp: float = field(default_factory=time.time)
    processing_time: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    energy_consumption: float = 0.0
    memory_usage: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatisticalAnalysisResult:
    """Result of statistical analysis."""
    
    test_type: StatisticalTest
    statistic: float
    p_value: float
    significant: bool
    confidence_interval: Tuple[float, float]
    effect_size: float
    interpretation: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparativeAnalysis:
    """Comparative analysis between methods."""
    
    baseline_method: str
    novel_method: str
    improvement_percentage: Dict[str, float]
    statistical_significance: Dict[str, StatisticalAnalysisResult]
    practical_significance: Dict[str, bool]
    recommendation: str
    confidence_score: float


class ResearchDataGenerator:
    """Generates synthetic datasets for research purposes."""
    
    def __init__(self):
        self.document_templates = {
            "nda": self._generate_nda_template,
            "employment": self._generate_employment_template,
            "lease": self._generate_lease_template,
            "service": self._generate_service_template,
            "licensing": self._generate_licensing_template
        }
    
    def generate_synthetic_dataset(self, document_type: str, count: int = 100,
                                 complexity_levels: List[str] = None) -> List[Dict[str, Any]]:
        """Generate synthetic dataset for research."""
        if complexity_levels is None:
            complexity_levels = ["simple", "medium", "complex"]
        
        if document_type not in self.document_templates:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        dataset = []
        template_func = self.document_templates[document_type]
        
        for i in range(count):
            complexity = complexity_levels[i % len(complexity_levels)]
            document = template_func(i, complexity)
            dataset.append(document)
        
        logger.info(f"Generated {count} synthetic {document_type} documents")
        return dataset
    
    def _generate_nda_template(self, doc_id: int, complexity: str) -> Dict[str, Any]:
        """Generate NDA document template."""
        base_clauses = [
            {
                "type": "confidentiality",
                "text": f"The receiving party agrees to maintain confidentiality of all proprietary information disclosed during the term of this agreement.",
                "ground_truth": True,
                "page": 1
            },
            {
                "type": "term_duration",
                "text": f"This agreement shall remain in effect for a period of {2 + (doc_id % 3)} years from the effective date.",
                "ground_truth": True,
                "page": 1
            }
        ]
        
        if complexity in ["medium", "complex"]:
            base_clauses.extend([
                {
                    "type": "liability",
                    "text": "Neither party shall be liable for any indirect, incidental, or consequential damages arising from breach of this agreement.",
                    "ground_truth": True,
                    "page": 2
                },
                {
                    "type": "governing_law",
                    "text": "This agreement shall be governed by the laws of the State of California.",
                    "ground_truth": True,
                    "page": 2
                }
            ])
        
        if complexity == "complex":
            base_clauses.extend([
                {
                    "type": "dispute_resolution",
                    "text": "Any disputes arising under this agreement shall be resolved through binding arbitration in San Francisco, California.",
                    "ground_truth": True,
                    "page": 2
                },
                {
                    "type": "intellectual_property",
                    "text": "All intellectual property rights in the confidential information shall remain with the disclosing party.",
                    "ground_truth": True,
                    "page": 3
                }
            ])
        
        return {
            "document_id": f"nda_{doc_id:04d}",
            "document_type": "nda",
            "complexity": complexity,
            "pages": 2 if complexity == "simple" else (3 if complexity == "medium" else 4),
            "ground_truth_clauses": base_clauses,
            "text_quality": "high" if doc_id % 3 == 0 else ("medium" if doc_id % 3 == 1 else "low"),
            "language": "en",
            "metadata": {
                "generation_timestamp": time.time(),
                "synthetic": True
            }
        }
    
    def _generate_employment_template(self, doc_id: int, complexity: str) -> Dict[str, Any]:
        """Generate employment contract template."""
        # Similar structure to NDA but with employment-specific clauses
        base_clauses = [
            {
                "type": "payment_terms",
                "text": f"Employee shall receive an annual salary of ${45000 + (doc_id % 20) * 1000}, payable bi-weekly.",
                "ground_truth": True,
                "page": 1
            },
            {
                "type": "termination",
                "text": "Either party may terminate this employment with 30 days written notice.",
                "ground_truth": True,
                "page": 2
            }
        ]
        
        # Add complexity-specific clauses
        if complexity in ["medium", "complex"]:
            base_clauses.append({
                "type": "benefits",
                "text": "Employee shall be eligible for health insurance, dental coverage, and 401(k) matching after 90 days of employment.",
                "ground_truth": True,
                "page": 2
            })
        
        return {
            "document_id": f"emp_{doc_id:04d}",
            "document_type": "employment",
            "complexity": complexity,
            "pages": 3,
            "ground_truth_clauses": base_clauses,
            "text_quality": "high" if doc_id % 4 == 0 else "medium",
            "language": "en",
            "metadata": {
                "generation_timestamp": time.time(),
                "synthetic": True
            }
        }
    
    # Additional template methods would be implemented similarly
    def _generate_lease_template(self, doc_id: int, complexity: str) -> Dict[str, Any]:
        """Generate lease agreement template."""
        return {"document_id": f"lease_{doc_id:04d}", "document_type": "lease", "complexity": complexity}
    
    def _generate_service_template(self, doc_id: int, complexity: str) -> Dict[str, Any]:
        """Generate service agreement template."""
        return {"document_id": f"service_{doc_id:04d}", "document_type": "service", "complexity": complexity}
    
    def _generate_licensing_template(self, doc_id: int, complexity: str) -> Dict[str, Any]:
        """Generate licensing agreement template."""
        return {"document_id": f"license_{doc_id:04d}", "document_type": "licensing", "complexity": complexity}


class AdvancedStatisticalAnalyzer:
    """Performs comprehensive statistical analysis for research evaluation."""
    
    def __init__(self, significance_threshold: float = 0.05):
        self.significance_threshold = significance_threshold
        self.random_state = 42
        random.seed(self.random_state)
        np.random.seed(self.random_state)
    
    def perform_comprehensive_comparative_analysis(
        self,
        baseline_results: List[ExperimentResult],
        novel_results: List[ExperimentResult],
        metrics: List[str] = None,
        statistical_tests: List[StatisticalTest] = None,
        correction_method: MultipleComparisonCorrection = MultipleComparisonCorrection.BENJAMINI_HOCHBERG
    ) -> ComparativeAnalysis:
        """Perform comprehensive comparative analysis with advanced statistics."""
        if metrics is None:
            metrics = ["accuracy", "processing_time", "f1_score", "energy_consumption"]
        if statistical_tests is None:
            statistical_tests = [StatisticalTest.T_TEST, StatisticalTest.MANN_WHITNEY_U, 
                               StatisticalTest.BOOTSTRAP_TEST]
        
        # Calculate improvements and perform multiple statistical tests
        improvements = {}
        all_statistical_tests = {}
        practical_significance = {}
        
        for metric in metrics:
            baseline_values = [getattr(r, metric, 0.0) for r in baseline_results]
            novel_values = [getattr(r, metric, 0.0) for r in novel_results]
            
            if not baseline_values or not novel_values:
                continue
            
            # Calculate improvement percentage
            baseline_mean = statistics.mean(baseline_values)
            novel_mean = statistics.mean(novel_values)
            
            if baseline_mean != 0:
                if metric in ["processing_time", "error_rate", "energy_consumption"]:
                    improvement = ((baseline_mean - novel_mean) / baseline_mean) * 100
                else:
                    improvement = ((novel_mean - baseline_mean) / baseline_mean) * 100
            else:
                improvement = 0.0
            
            improvements[metric] = improvement
            
            # Perform multiple statistical tests
            metric_tests = {}
            for test_type in statistical_tests:
                if test_type == StatisticalTest.T_TEST:
                    metric_tests[test_type.value] = self._perform_t_test(baseline_values, novel_values)
                elif test_type == StatisticalTest.MANN_WHITNEY_U:
                    metric_tests[test_type.value] = self._perform_mann_whitney_u_test(baseline_values, novel_values)
                elif test_type == StatisticalTest.BOOTSTRAP_TEST:
                    metric_tests[test_type.value] = self._perform_bootstrap_test(baseline_values, novel_values)
                elif test_type == StatisticalTest.BAYESIAN_T_TEST:
                    metric_tests[test_type.value] = self._perform_bayesian_t_test(baseline_values, novel_values)
                elif test_type == StatisticalTest.KOLMOGOROV_SMIRNOV:
                    metric_tests[test_type.value] = self._perform_ks_test(baseline_values, novel_values)
            
            all_statistical_tests[metric] = metric_tests
            
            # Determine practical significance with Cohen's d threshold
            effect_size = self._calculate_cohens_d(baseline_values, novel_values)
            practical_significance[metric] = {
                'improvement_significant': abs(improvement) > 5.0,
                'effect_size_significant': abs(effect_size) >= 0.5,  # Medium effect size
                'combined_significance': abs(improvement) > 5.0 and abs(effect_size) >= 0.5
            }
        
        # Apply multiple comparison correction
        corrected_tests = self._apply_multiple_comparison_correction(
            all_statistical_tests, correction_method
        )
        
        # Generate comprehensive recommendation with Bayesian reasoning
        recommendation_data = self._generate_evidence_based_recommendation(
            improvements, corrected_tests, practical_significance
        )
        
        return ComparativeAnalysis(
            baseline_method=baseline_results[0].method_name if baseline_results else "unknown",
            novel_method=novel_results[0].method_name if novel_results else "unknown",
            improvement_percentage=improvements,
            statistical_significance=corrected_tests,
            practical_significance=practical_significance,
            recommendation=recommendation_data['recommendation'],
            confidence_score=recommendation_data['confidence_score']
        )
    
    def perform_comparative_analysis(self, baseline_results: List[ExperimentResult],
                                   novel_results: List[ExperimentResult],
                                   metrics: List[str] = None) -> ComparativeAnalysis:
        """Backward compatibility wrapper for existing code."""
        return self.perform_comprehensive_comparative_analysis(
            baseline_results, novel_results, metrics
        )
    
    def _perform_t_test(self, sample1: List[float], sample2: List[float]) -> StatisticalAnalysisResult:
        """Perform Welch's t-test (unequal variances assumed)."""
        if len(sample1) < 2 or len(sample2) < 2:
            return StatisticalAnalysisResult(
                test_type=StatisticalTest.T_TEST,
                statistic=0.0,
                p_value=1.0,
                significant=False,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                interpretation="Insufficient sample size"
            )
        
        # Calculate descriptive statistics
        mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
        var1 = statistics.variance(sample1) if len(sample1) > 1 else 0.0
        var2 = statistics.variance(sample2) if len(sample2) > 1 else 0.0
        n1, n2 = len(sample1), len(sample2)
        
        # Welch's t-test calculations
        se_diff = math.sqrt(var1/n1 + var2/n2) if (var1/n1 + var2/n2) > 0 else 1e-10
        t_stat = (mean1 - mean2) / se_diff
        
        # Welch-Satterthwaite degrees of freedom
        if var1 > 0 and var2 > 0:
            num = (var1/n1 + var2/n2) ** 2
            denom = (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
            df = num / denom if denom > 0 else n1 + n2 - 2
        else:
            df = n1 + n2 - 2
        
        # Improved p-value approximation using t-distribution properties
        p_value = self._t_distribution_p_value(abs(t_stat), df)
        
        significant = p_value < self.significance_threshold
        
        # Cohen's d effect size
        effect_size = self._calculate_cohens_d(sample1, sample2)
        
        # Confidence interval for difference of means
        t_critical = self._t_critical_value(0.05, df)  # 95% CI
        margin_error = t_critical * se_diff
        ci_lower = (mean1 - mean2) - margin_error
        ci_upper = (mean1 - mean2) + margin_error
        
        return StatisticalAnalysisResult(
            test_type=StatisticalTest.T_TEST,
            statistic=t_stat,
            p_value=p_value,
            significant=significant,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            interpretation=self._interpret_effect_size(effect_size),
            details={
                'degrees_of_freedom': df,
                'mean_difference': mean1 - mean2,
                'standard_error': se_diff,
                'group1_mean': mean1,
                'group2_mean': mean2,
                'group1_var': var1,
                'group2_var': var2
            }
        )
    
    def _perform_mann_whitney_u_test(self, sample1: List[float], sample2: List[float]) -> StatisticalAnalysisResult:
        """Perform Mann-Whitney U test (Wilcoxon rank-sum test)."""
        if len(sample1) < 3 or len(sample2) < 3:
            return StatisticalAnalysisResult(
                test_type=StatisticalTest.MANN_WHITNEY_U,
                statistic=0.0,
                p_value=1.0,
                significant=False,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                interpretation="Insufficient sample size for Mann-Whitney U test"
            )
        
        # Combine samples with group labels
        n1, n2 = len(sample1), len(sample2)
        combined = [(val, 1) for val in sample1] + [(val, 2) for val in sample2]
        combined.sort(key=lambda x: x[0])
        
        # Calculate ranks (handle ties by averaging)
        ranks = [0] * len(combined)
        i = 0
        while i < len(combined):
            # Find all values equal to current value
            j = i
            while j < len(combined) and combined[j][0] == combined[i][0]:
                j += 1
            # Assign average rank to tied values
            avg_rank = (i + j + 1) / 2  # +1 because ranks start at 1
            for k in range(i, j):
                ranks[k] = avg_rank
            i = j
        
        # Sum ranks for each group
        R1 = sum(ranks[i] for i in range(len(combined)) if combined[i][1] == 1)
        R2 = sum(ranks[i] for i in range(len(combined)) if combined[i][1] == 2)
        
        # Calculate U statistics
        U1 = R1 - n1 * (n1 + 1) / 2
        U2 = R2 - n2 * (n2 + 1) / 2
        U = min(U1, U2)
        
        # Normal approximation for p-value (valid for larger samples)
        mu_u = n1 * n2 / 2
        sigma_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        
        if sigma_u > 0:
            z_score = (U - mu_u) / sigma_u
            p_value = 2 * (1 - self._standard_normal_cdf(abs(z_score)))
        else:
            p_value = 1.0
            z_score = 0.0
        
        significant = p_value < self.significance_threshold
        
        # Effect size (rank biserial correlation)
        effect_size = (U1 - U2) / (n1 * n2) if n1 * n2 > 0 else 0.0
        
        return StatisticalAnalysisResult(
            test_type=StatisticalTest.MANN_WHITNEY_U,
            statistic=U,
            p_value=p_value,
            significant=significant,
            confidence_interval=(0.0, 0.0),  # CI calculation is complex for U test
            effect_size=abs(effect_size),
            interpretation=f"Rank-based effect size: {abs(effect_size):.3f}",
            details={
                'U1': U1,
                'U2': U2,
                'z_score': z_score,
                'rank_sum_1': R1,
                'rank_sum_2': R2
            }
        )
    
    def _perform_bootstrap_test(self, sample1: List[float], sample2: List[float], 
                               n_bootstrap: int = 10000) -> StatisticalAnalysisResult:
        """Perform bootstrap resampling test for difference in means."""
        if len(sample1) < 3 or len(sample2) < 3:
            return StatisticalAnalysisResult(
                test_type=StatisticalTest.BOOTSTRAP_TEST,
                statistic=0.0,
                p_value=1.0,
                significant=False,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                interpretation="Insufficient sample size for bootstrap test"
            )
        
        # Observed difference in means
        observed_diff = statistics.mean(sample1) - statistics.mean(sample2)
        
        # Bootstrap resampling under null hypothesis (no difference)
        combined = sample1 + sample2
        n1, n2 = len(sample1), len(sample2)
        bootstrap_diffs = []
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            bootstrap_combined = [random.choice(combined) for _ in range(len(combined))]
            bootstrap_sample1 = bootstrap_combined[:n1]
            bootstrap_sample2 = bootstrap_combined[n1:]
            
            bootstrap_diff = statistics.mean(bootstrap_sample1) - statistics.mean(bootstrap_sample2)
            bootstrap_diffs.append(bootstrap_diff)
        
        # Calculate p-value (two-tailed)
        extreme_diffs = sum(1 for diff in bootstrap_diffs if abs(diff) >= abs(observed_diff))
        p_value = extreme_diffs / n_bootstrap
        
        significant = p_value < self.significance_threshold
        
        # Bootstrap confidence interval for the difference
        bootstrap_diffs.sort()
        ci_lower_idx = int(0.025 * n_bootstrap)
        ci_upper_idx = int(0.975 * n_bootstrap)
        ci_lower = bootstrap_diffs[ci_lower_idx]
        ci_upper = bootstrap_diffs[ci_upper_idx]
        
        effect_size = self._calculate_cohens_d(sample1, sample2)
        
        return StatisticalAnalysisResult(
            test_type=StatisticalTest.BOOTSTRAP_TEST,
            statistic=observed_diff,
            p_value=p_value,
            significant=significant,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            interpretation=f"Bootstrap test with {n_bootstrap} resamples",
            details={
                'bootstrap_samples': n_bootstrap,
                'extreme_samples': extreme_diffs,
                'bootstrap_mean': statistics.mean(bootstrap_diffs),
                'bootstrap_std': statistics.stdev(bootstrap_diffs) if len(bootstrap_diffs) > 1 else 0
            }
        )
    
    def _perform_bayesian_t_test(self, sample1: List[float], sample2: List[float]) -> StatisticalAnalysisResult:
        """Perform Bayesian t-test using Bayes factors."""
        if len(sample1) < 2 or len(sample2) < 2:
            return StatisticalAnalysisResult(
                test_type=StatisticalTest.BAYESIAN_T_TEST,
                statistic=0.0,
                p_value=1.0,
                significant=False,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                interpretation="Insufficient sample size for Bayesian t-test"
            )
        
        # Calculate Bayes factor approximation (JZS Bayes factor)
        t_stat = self._perform_t_test(sample1, sample2).statistic
        n1, n2 = len(sample1), len(sample2)
        n_total = n1 + n2
        
        # Simplified Bayes factor calculation (Rouder et al., 2009)
        # This is an approximation - full calculation requires numerical integration
        r_scale = 0.707  # Default scale for Cauchy prior
        bf_01 = math.exp(-0.5 * t_stat**2) * math.sqrt((n_total * r_scale**2 + 1) / (n_total * r_scale**2))
        bf_10 = 1 / bf_01 if bf_01 > 0 else float('inf')
        
        # Posterior probability (assuming equal priors)
        posterior_h1 = bf_10 / (1 + bf_10)
        posterior_h0 = 1 - posterior_h1
        
        # Bayesian "significance" based on Bayes factor strength
        if bf_10 > 10:
            interpretation = "Strong evidence for difference"
            significant = True
        elif bf_10 > 3:
            interpretation = "Moderate evidence for difference"
            significant = True
        elif bf_01 > 10:
            interpretation = "Strong evidence for no difference"
            significant = False
        elif bf_01 > 3:
            interpretation = "Moderate evidence for no difference"
            significant = False
        else:
            interpretation = "Anecdotal evidence - inconclusive"
            significant = False
        
        effect_size = self._calculate_cohens_d(sample1, sample2)
        
        # Credible interval (approximation)
        mean_diff = statistics.mean(sample1) - statistics.mean(sample2)
        se_diff = math.sqrt(statistics.variance(sample1)/n1 + statistics.variance(sample2)/n2) \
                  if n1 > 1 and n2 > 1 else 1e-10
        
        # 95% credible interval (normal approximation)
        ci_lower = mean_diff - 1.96 * se_diff
        ci_upper = mean_diff + 1.96 * se_diff
        
        return StatisticalAnalysisResult(
            test_type=StatisticalTest.BAYESIAN_T_TEST,
            statistic=bf_10,
            p_value=1 - posterior_h1,  # Convert posterior to p-value-like metric
            significant=significant,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            interpretation=interpretation,
            details={
                'bayes_factor_10': bf_10,
                'bayes_factor_01': bf_01,
                'posterior_h1': posterior_h1,
                'posterior_h0': posterior_h0,
                'r_scale': r_scale
            }
        )
    
    def _perform_ks_test(self, sample1: List[float], sample2: List[float]) -> StatisticalAnalysisResult:
        """Perform two-sample Kolmogorov-Smirnov test."""
        if len(sample1) < 3 or len(sample2) < 3:
            return StatisticalAnalysisResult(
                test_type=StatisticalTest.KOLMOGOROV_SMIRNOV,
                statistic=0.0,
                p_value=1.0,
                significant=False,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                interpretation="Insufficient sample size for KS test"
            )
        
        # Sort samples
        sample1_sorted = sorted(sample1)
        sample2_sorted = sorted(sample2)
        
        # Get all unique values
        all_values = sorted(set(sample1 + sample2))
        
        n1, n2 = len(sample1), len(sample2)
        max_diff = 0.0
        
        # Calculate empirical CDFs and find maximum difference
        for value in all_values:
            # Empirical CDF values
            cdf1 = sum(1 for x in sample1_sorted if x <= value) / n1
            cdf2 = sum(1 for x in sample2_sorted if x <= value) / n2
            
            diff = abs(cdf1 - cdf2)
            max_diff = max(max_diff, diff)
        
        # Critical value approximation (asymptotic distribution)
        critical_value = 1.36 * math.sqrt((n1 + n2) / (n1 * n2))
        
        # Approximate p-value using asymptotic distribution
        if max_diff == 0:
            p_value = 1.0
        else:
            # Kolmogorov distribution approximation
            lambda_val = max_diff * math.sqrt(n1 * n2 / (n1 + n2))
            p_value = 2 * math.exp(-2 * lambda_val**2)
            p_value = min(p_value, 1.0)
        
        significant = p_value < self.significance_threshold
        
        # Effect size (magnitude of maximum difference)
        effect_size = max_diff
        
        return StatisticalAnalysisResult(
            test_type=StatisticalTest.KOLMOGOROV_SMIRNOV,
            statistic=max_diff,
            p_value=p_value,
            significant=significant,
            confidence_interval=(0.0, 0.0),
            effect_size=effect_size,
            interpretation=f"Maximum CDF difference: {max_diff:.3f}",
            details={
                'critical_value': critical_value,
                'lambda': lambda_val if max_diff > 0 else 0,
                'sample1_size': n1,
                'sample2_size': n2
            }
        )
    
    def _interpret_effect_size(self, effect_size: float) -> str:
        """Interpret Cohen's d effect size with more nuanced categories."""
        abs_effect = abs(effect_size)
        if abs_effect < 0.1:
            return "negligible effect (< 0.1)"
        elif abs_effect < 0.2:
            return "very small effect (0.1-0.2)"
        elif abs_effect < 0.5:
            return "small effect (0.2-0.5)"
        elif abs_effect < 0.8:
            return "medium effect (0.5-0.8)"
        elif abs_effect < 1.2:
            return "large effect (0.8-1.2)"
        elif abs_effect < 2.0:
            return "very large effect (1.2-2.0)"
        else:
            return "huge effect (≥ 2.0)"
    
    def _calculate_cohens_d(self, sample1: List[float], sample2: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        if len(sample1) < 2 or len(sample2) < 2:
            return 0.0
        
        mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
        
        # Calculate pooled standard deviation
        n1, n2 = len(sample1), len(sample2)
        var1 = statistics.variance(sample1) if n1 > 1 else 0.0
        var2 = statistics.variance(sample2) if n2 > 1 else 0.0
        
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        pooled_std = math.sqrt(pooled_var) if pooled_var > 0 else 1e-10
        
        return (mean1 - mean2) / pooled_std
    
    def _apply_multiple_comparison_correction(self, all_tests: Dict[str, Dict[str, StatisticalAnalysisResult]], 
                                            correction: MultipleComparisonCorrection) -> Dict[str, Dict[str, StatisticalAnalysisResult]]:
        """Apply multiple comparison correction to p-values."""
        if correction == MultipleComparisonCorrection.NONE:
            return all_tests
        
        # Collect all p-values
        p_values = []
        test_info = []
        
        for metric, tests in all_tests.items():
            for test_name, result in tests.items():
                p_values.append(result.p_value)
                test_info.append((metric, test_name, result))
        
        if not p_values:
            return all_tests
        
        # Apply correction
        if correction == MultipleComparisonCorrection.BONFERRONI:
            corrected_p = [min(1.0, p * len(p_values)) for p in p_values]
        elif correction == MultipleComparisonCorrection.HOLM_BONFERRONI:
            corrected_p = self._holm_bonferroni_correction(p_values)
        elif correction == MultipleComparisonCorrection.BENJAMINI_HOCHBERG:
            corrected_p = self._benjamini_hochberg_correction(p_values)
        else:
            corrected_p = p_values  # Default to no correction
        
        # Update results with corrected p-values
        corrected_tests = {}
        for i, (metric, test_name, original_result) in enumerate(test_info):
            if metric not in corrected_tests:
                corrected_tests[metric] = {}
            
            # Create new result with corrected p-value
            corrected_result = StatisticalAnalysisResult(
                test_type=original_result.test_type,
                statistic=original_result.statistic,
                p_value=corrected_p[i],
                significant=corrected_p[i] < self.significance_threshold,
                confidence_interval=original_result.confidence_interval,
                effect_size=original_result.effect_size,
                interpretation=original_result.interpretation,
                details={
                    **original_result.details,
                    'original_p_value': original_result.p_value,
                    'correction_method': correction.value,
                    'corrected': True
                }
            )
            
            corrected_tests[metric][test_name] = corrected_result
        
        return corrected_tests
    
    def _benjamini_hochberg_correction(self, p_values: List[float]) -> List[float]:
        """Apply Benjamini-Hochberg FDR correction."""
        n = len(p_values)
        if n == 0:
            return []
        
        # Sort p-values with original indices
        indexed_p = [(p, i) for i, p in enumerate(p_values)]
        indexed_p.sort()
        
        # Calculate corrected p-values
        corrected = [0] * n
        
        for rank, (p, original_idx) in enumerate(indexed_p):
            bh_value = p * n / (rank + 1)
            corrected[original_idx] = min(1.0, bh_value)
        
        # Ensure monotonicity (corrected p-values should be non-decreasing)
        sorted_corrected = [corrected[indexed_p[i][1]] for i in range(n)]
        for i in range(n-2, -1, -1):
            if sorted_corrected[i] > sorted_corrected[i+1]:
                sorted_corrected[i] = sorted_corrected[i+1]
        
        # Map back to original order
        final_corrected = [0] * n
        for i, (_, original_idx) in enumerate(indexed_p):
            final_corrected[original_idx] = sorted_corrected[i]
        
        return final_corrected
    
    def _holm_bonferroni_correction(self, p_values: List[float]) -> List[float]:
        """Apply Holm-Bonferroni correction."""
        n = len(p_values)
        if n == 0:
            return []
        
        # Sort p-values with original indices
        indexed_p = [(p, i) for i, p in enumerate(p_values)]
        indexed_p.sort()
        
        corrected = [0] * n
        
        for rank, (p, original_idx) in enumerate(indexed_p):
            holm_value = p * (n - rank)
            corrected[original_idx] = min(1.0, holm_value)
        
        return corrected
    
    def _generate_evidence_based_recommendation(self, improvements: Dict[str, float], 
                                              statistical_tests: Dict[str, Dict[str, StatisticalAnalysisResult]],
                                              practical_significance: Dict[str, Dict[str, bool]]) -> Dict[str, Any]:
        """Generate evidence-based recommendation using multiple criteria."""
        evidence_scores = []
        total_metrics = len(improvements)
        
        for metric in improvements.keys():
            metric_score = 0.0
            
            # Statistical significance evidence (40% weight)
            if metric in statistical_tests:
                significant_tests = sum(1 for test_result in statistical_tests[metric].values() 
                                      if test_result.significant)
                total_tests = len(statistical_tests[metric])
                if total_tests > 0:
                    metric_score += 0.4 * (significant_tests / total_tests)
            
            # Effect size evidence (30% weight)
            if metric in statistical_tests:
                avg_effect_size = statistics.mean([
                    abs(test_result.effect_size) 
                    for test_result in statistical_tests[metric].values()
                ])
                # Convert effect size to score (capped at 1.0)
                effect_score = min(1.0, avg_effect_size / 0.8)  # Large effect = 1.0
                metric_score += 0.3 * effect_score
            
            # Practical significance evidence (30% weight)
            if metric in practical_significance:
                practical_score = sum(practical_significance[metric].values()) / len(practical_significance[metric])
                metric_score += 0.3 * practical_score
            
            evidence_scores.append(metric_score)
        
        # Calculate overall confidence score
        confidence_score = statistics.mean(evidence_scores) if evidence_scores else 0.0
        
        # Generate recommendation based on evidence strength
        if confidence_score >= 0.8:
            recommendation = "Strong evidence for novel method superiority - Recommend production deployment"
            strength = "strong"
        elif confidence_score >= 0.65:
            recommendation = "Moderate to strong evidence - Recommend pilot testing"
            strength = "moderate_to_strong"
        elif confidence_score >= 0.5:
            recommendation = "Moderate evidence - Consider limited deployment with monitoring"
            strength = "moderate"
        elif confidence_score >= 0.35:
            recommendation = "Weak to moderate evidence - Recommend further research"
            strength = "weak_to_moderate"
        else:
            recommendation = "Insufficient evidence - Continue development and testing"
            strength = "insufficient"
        
        return {
            'recommendation': recommendation,
            'confidence_score': confidence_score,
            'evidence_strength': strength,
            'metric_scores': dict(zip(improvements.keys(), evidence_scores)),
            'total_metrics_evaluated': total_metrics
        }
    
    def calculate_statistical_power(self, effect_size: float, sample_size: int,
                                  alpha: float = 0.05) -> float:
        """Calculate statistical power using improved approximation."""
        if sample_size < 2:
            return 0.0
        
        # Cohen's power approximation for t-test
        delta = abs(effect_size) * math.sqrt(sample_size / 2)
        
        # Use normal approximation for power calculation
        z_alpha = self._z_critical_value(alpha)
        z_beta = delta - z_alpha
        
        power = self._standard_normal_cdf(z_beta)
        return max(0.0, min(1.0, power))
    
    def _t_distribution_p_value(self, t_stat: float, df: float) -> float:
        """Approximate p-value for t-distribution (two-tailed)."""
        if df <= 0:
            return 1.0
        
        # For large df, t-distribution approaches standard normal
        if df > 100:
            return 2 * (1 - self._standard_normal_cdf(abs(t_stat)))
        
        # Approximation for smaller df using gamma function properties
        # This is a simplified approximation - actual implementation would use
        # more sophisticated numerical methods
        x = t_stat**2 / (t_stat**2 + df)
        p_one_tail = 0.5 * self._incomplete_beta_approx(x, 0.5, df/2)
        return min(1.0, 2 * p_one_tail)
    
    def _t_critical_value(self, alpha: float, df: float) -> float:
        """Approximate critical value for t-distribution."""
        if df > 100:
            return self._z_critical_value(alpha)
        
        # Rough approximation - in practice would use inverse t-distribution
        z_alpha = self._z_critical_value(alpha)
        correction = (z_alpha**3 + z_alpha) / (4 * df)
        return z_alpha + correction
    
    def _z_critical_value(self, alpha: float) -> float:
        """Critical value for standard normal distribution."""
        # Common critical values
        critical_values = {
            0.10: 1.282,
            0.05: 1.645,
            0.02: 2.054,
            0.01: 2.326
        }
        
        if alpha in critical_values:
            return critical_values[alpha]
        
        # Approximation for other values
        return 1.645 if alpha <= 0.05 else 1.282
    
    def _standard_normal_cdf(self, z: float) -> float:
        """Cumulative distribution function for standard normal."""
        # Abramowitz & Stegun approximation
        if z < 0:
            return 1 - self._standard_normal_cdf(-z)
        
        # Constants for approximation
        a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
        p = 0.3275911
        
        t = 1 / (1 + p * z)
        y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z / 2)
        
        return y
    
    def _incomplete_beta_approx(self, x: float, a: float, b: float) -> float:
        """Rough approximation of incomplete beta function."""
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        
        # Very rough approximation - real implementation would use
        # continued fractions or series expansion
        if a == 0.5 and b > 1:
            return 2 * math.sqrt(x) - x
        
        return x**a * (1-x)**b  # Simplified approximation


class ExperimentRunner:
    """Runs controlled experiments for research evaluation."""
    
    def __init__(self):
        self.data_generator = ResearchDataGenerator()
        self.statistical_analyzer = AdvancedStatisticalAnalyzer()
        self.results_cache: Dict[str, List[ExperimentResult]] = {}
        
    async def run_experiment(self, config: ExperimentConfig) -> Dict[str, Any]:
        """Run a complete research experiment."""
        logger.info(f"Starting experiment: {config.name}")
        
        # Generate or load datasets
        datasets = await self._prepare_datasets(config)
        
        # Run experiments for each method and dataset combination
        all_results = {}
        
        for method_name in config.baseline_methods + config.novel_methods:
            method_results = []
            
            for dataset_name, dataset in datasets.items():
                for repetition in range(config.repetitions):
                    result = await self._run_single_experiment(
                        method_name, dataset_name, dataset, config, repetition
                    )
                    method_results.append(result)
            
            all_results[method_name] = method_results
        
        # Perform statistical analysis
        analysis_results = await self._analyze_experiment_results(all_results, config)
        
        # Generate research report
        report = self._generate_research_report(config, all_results, analysis_results)
        
        logger.info(f"Completed experiment: {config.name}")
        
        return {
            "experiment_config": asdict(config),
            "raw_results": all_results,
            "statistical_analysis": analysis_results,
            "research_report": report,
            "timestamp": time.time()
        }
    
    async def _prepare_datasets(self, config: ExperimentConfig) -> Dict[str, List[Dict[str, Any]]]:
        """Prepare datasets for experimentation."""
        datasets = {}
        
        for dataset_name in config.datasets:
            if dataset_name.startswith("synthetic_"):
                # Generate synthetic dataset
                doc_type = dataset_name.replace("synthetic_", "")
                dataset = self.data_generator.generate_synthetic_dataset(
                    doc_type, count=100, complexity_levels=["simple", "medium", "complex"]
                )
                datasets[dataset_name] = dataset
            else:
                # Load real dataset (placeholder)
                logger.warning(f"Real dataset loading not implemented: {dataset_name}")
                datasets[dataset_name] = []
        
        return datasets
    
    async def _run_single_experiment(self, method_name: str, dataset_name: str,
                                   dataset: List[Dict[str, Any]], config: ExperimentConfig,
                                   repetition: int) -> ExperimentResult:
        """Run single experiment iteration."""
        start_time = time.perf_counter()
        run_id = f"{config.experiment_id}_{method_name}_{dataset_name}_{repetition}"
        
        try:
            # Simulate processing with different methods
            if method_name == "classical":
                result = await self._run_classical_method(dataset, config)
            elif method_name == "neuromorphic":
                result = await self._run_neuromorphic_method(dataset, config)
            elif method_name == "quantum":
                result = await self._run_quantum_method(dataset, config)
            elif method_name == "hybrid":
                result = await self._run_hybrid_method(dataset, config)
            else:
                raise ValueError(f"Unknown method: {method_name}")
            
            processing_time = time.perf_counter() - start_time
            
            return ExperimentResult(
                run_id=run_id,
                method_name=method_name,
                dataset_name=dataset_name,
                processing_time=processing_time,
                accuracy=result.get("accuracy", 0.0),
                precision=result.get("precision", 0.0),
                recall=result.get("recall", 0.0),
                f1_score=result.get("f1_score", 0.0),
                energy_consumption=result.get("energy_consumption", 0.0),
                memory_usage=result.get("memory_usage", 0.0),
                throughput=len(dataset) / processing_time,
                error_rate=result.get("error_rate", 0.0),
                custom_metrics=result.get("custom_metrics", {}),
                success=True,
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error(f"Experiment run {run_id} failed: {e}")
            
            return ExperimentResult(
                run_id=run_id,
                method_name=method_name,
                dataset_name=dataset_name,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    async def _run_classical_method(self, dataset: List[Dict[str, Any]], 
                                  config: ExperimentConfig) -> Dict[str, Any]:
        """Run classical processing method."""
        # Simulate classical processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "accuracy": 0.78 + np.random.normal(0, 0.05),
            "precision": 0.76 + np.random.normal(0, 0.04),
            "recall": 0.80 + np.random.normal(0, 0.04),
            "f1_score": 0.78 + np.random.normal(0, 0.03),
            "energy_consumption": 5.0 + np.random.normal(0, 0.5),
            "memory_usage": 256 + np.random.normal(0, 32),
            "error_rate": 0.05 + np.random.normal(0, 0.01),
            "metadata": {"method": "classical"}
        }
    
    async def _run_neuromorphic_method(self, dataset: List[Dict[str, Any]],
                                     config: ExperimentConfig) -> Dict[str, Any]:
        """Run neuromorphic processing method."""
        # Simulate neuromorphic processing with improved accuracy but higher setup cost
        await asyncio.sleep(0.15)  # Slightly longer processing
        
        return {
            "accuracy": 0.85 + np.random.normal(0, 0.04),
            "precision": 0.83 + np.random.normal(0, 0.03),
            "recall": 0.87 + np.random.normal(0, 0.03),
            "f1_score": 0.85 + np.random.normal(0, 0.02),
            "energy_consumption": 3.5 + np.random.normal(0, 0.3),  # More energy efficient
            "memory_usage": 192 + np.random.normal(0, 24),
            "error_rate": 0.03 + np.random.normal(0, 0.008),
            "custom_metrics": {
                "spike_efficiency": 0.82 + np.random.normal(0, 0.05),
                "adaptation_cycles": 15 + int(np.random.normal(0, 3))
            },
            "metadata": {"method": "neuromorphic"}
        }
    
    async def _run_quantum_method(self, dataset: List[Dict[str, Any]],
                                config: ExperimentConfig) -> Dict[str, Any]:
        """Run quantum processing method."""
        # Simulate quantum processing with potential quantum advantage
        await asyncio.sleep(0.12)
        
        return {
            "accuracy": 0.88 + np.random.normal(0, 0.03),
            "precision": 0.86 + np.random.normal(0, 0.03),
            "recall": 0.90 + np.random.normal(0, 0.02),
            "f1_score": 0.88 + np.random.normal(0, 0.02),
            "energy_consumption": 2.8 + np.random.normal(0, 0.3),  # Most energy efficient
            "memory_usage": 128 + np.random.normal(0, 16),
            "error_rate": 0.02 + np.random.normal(0, 0.005),
            "custom_metrics": {
                "quantum_fidelity": 0.89 + np.random.normal(0, 0.03),
                "entanglement_entropy": 0.75 + np.random.normal(0, 0.05),
                "quantum_advantage": 0.23 + np.random.normal(0, 0.04)
            },
            "metadata": {"method": "quantum"}
        }
    
    async def _run_hybrid_method(self, dataset: List[Dict[str, Any]],
                               config: ExperimentConfig) -> Dict[str, Any]:
        """Run hybrid processing method."""
        # Simulate hybrid approach combining best of multiple methods
        await asyncio.sleep(0.18)  # Longer due to coordination overhead
        
        return {
            "accuracy": 0.91 + np.random.normal(0, 0.025),  # Best accuracy
            "precision": 0.89 + np.random.normal(0, 0.025),
            "recall": 0.93 + np.random.normal(0, 0.02),
            "f1_score": 0.91 + np.random.normal(0, 0.015),
            "energy_consumption": 4.2 + np.random.normal(0, 0.4),  # Moderate energy usage
            "memory_usage": 320 + np.random.normal(0, 40),  # Higher memory due to multiple methods
            "error_rate": 0.015 + np.random.normal(0, 0.003),
            "custom_metrics": {
                "method_selection_accuracy": 0.87 + np.random.normal(0, 0.03),
                "orchestration_overhead": 0.12 + np.random.normal(0, 0.02)
            },
            "metadata": {"method": "hybrid"}
        }
    
    async def _analyze_experiment_results(self, all_results: Dict[str, List[ExperimentResult]],
                                        config: ExperimentConfig) -> Dict[str, Any]:
        """Analyze experiment results statistically."""
        analysis = {}
        
        # Separate baseline and novel methods
        baseline_results = []
        novel_results = []
        
        for method_name, results in all_results.items():
            if method_name in config.baseline_methods:
                baseline_results.extend(results)
            else:
                novel_results.extend(results)
        
        if baseline_results and novel_results:
            # Perform comparative analysis
            comparative_analysis = self.statistical_analyzer.perform_comparative_analysis(
                baseline_results, novel_results, config.metrics
            )
            analysis["comparative_analysis"] = asdict(comparative_analysis)
        
        # Method-specific analysis
        method_analysis = {}
        for method_name, results in all_results.items():
            successful_results = [r for r in results if r.success]
            
            if successful_results:
                method_stats = self._calculate_method_statistics(successful_results, config.metrics)
                method_analysis[method_name] = method_stats
        
        analysis["method_analysis"] = method_analysis
        
        # Overall experiment summary
        total_runs = sum(len(results) for results in all_results.values())
        successful_runs = sum(len([r for r in results if r.success]) for results in all_results.values())
        
        analysis["experiment_summary"] = {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0.0,
            "methods_tested": len(all_results),
            "datasets_used": len(config.datasets),
            "repetitions_per_condition": config.repetitions
        }
        
        return analysis
    
    def _calculate_method_statistics(self, results: List[ExperimentResult], 
                                   metrics: List[str]) -> Dict[str, Any]:
        """Calculate statistical summary for a method."""
        stats = {}
        
        for metric in metrics:
            values = [getattr(r, metric, 0.0) for r in results]
            
            if values:
                stats[metric] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "min": min(values),
                    "max": max(values),
                    "median": statistics.median(values),
                    "count": len(values)
                }
        
        return stats
    
    def _generate_research_report(self, config: ExperimentConfig, 
                                all_results: Dict[str, List[ExperimentResult]],
                                analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive research report."""
        report = {
            "title": f"Research Report: {config.name}",
            "experiment_id": config.experiment_id,
            "hypothesis": config.hypothesis,
            "methodology": {
                "experiment_type": config.experiment_type.value,
                "methods_compared": list(all_results.keys()),
                "datasets": config.datasets,
                "repetitions": config.repetitions,
                "metrics_evaluated": config.metrics
            },
            "results_summary": analysis_results.get("experiment_summary", {}),
            "key_findings": self._extract_key_findings(analysis_results),
            "statistical_significance": self._summarize_statistical_results(analysis_results),
            "practical_implications": self._generate_practical_implications(analysis_results),
            "limitations": self._identify_limitations(config, analysis_results),
            "recommendations": self._generate_recommendations(analysis_results),
            "publication_readiness": self._assess_publication_readiness(config, analysis_results)
        }
        
        return report
    
    def _extract_key_findings(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract key findings from analysis."""
        findings = []
        
        if "comparative_analysis" in analysis_results:
            comp_analysis = analysis_results["comparative_analysis"]
            improvements = comp_analysis.get("improvement_percentage", {})
            
            for metric, improvement in improvements.items():
                if abs(improvement) > 10:  # Significant improvement threshold
                    direction = "improvement" if improvement > 0 else "degradation"
                    findings.append(f"{metric}: {abs(improvement):.1f}% {direction} over baseline")
        
        if "method_analysis" in analysis_results:
            method_stats = analysis_results["method_analysis"]
            
            # Find best performing method for each metric
            for metric in ["accuracy", "f1_score", "energy_consumption"]:
                best_method = None
                best_value = None
                
                for method, stats in method_stats.items():
                    if metric in stats:
                        value = stats[metric]["mean"]
                        if best_value is None or (
                            (metric in ["accuracy", "f1_score"] and value > best_value) or
                            (metric == "energy_consumption" and value < best_value)
                        ):
                            best_value = value
                            best_method = method
                
                if best_method:
                    findings.append(f"Best {metric}: {best_method} ({best_value:.3f})")
        
        return findings
    
    def _summarize_statistical_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize statistical significance results."""
        if "comparative_analysis" not in analysis_results:
            return {"status": "no_comparative_analysis"}
        
        comp_analysis = analysis_results["comparative_analysis"]
        statistical_tests = comp_analysis.get("statistical_significance", {})
        
        significant_results = {}
        for metric, test_result in statistical_tests.items():
            significant_results[metric] = {
                "significant": test_result["significant"],
                "p_value": test_result["p_value"],
                "effect_size": test_result["effect_size"],
                "interpretation": test_result["interpretation"]
            }
        
        return {
            "significant_metrics": [
                metric for metric, result in significant_results.items() 
                if result["significant"]
            ],
            "detailed_results": significant_results,
            "overall_confidence": comp_analysis.get("confidence_score", 0.0)
        }
    
    def _generate_practical_implications(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate practical implications from results."""
        implications = []
        
        if "comparative_analysis" in analysis_results:
            comp_analysis = analysis_results["comparative_analysis"]
            recommendation = comp_analysis.get("recommendation", "")
            
            if "strong evidence" in recommendation.lower():
                implications.append("Strong recommendation for adopting novel processing methods in production")
            elif "moderate evidence" in recommendation.lower():
                implications.append("Consider pilot deployment of novel methods for specific use cases")
            else:
                implications.append("Continue research and development before production deployment")
        
        # Add method-specific implications
        if "method_analysis" in analysis_results:
            implications.append("Detailed performance profiles available for method selection")
            implications.append("Energy efficiency varies significantly between methods")
        
        return implications
    
    def _identify_limitations(self, config: ExperimentConfig, 
                            analysis_results: Dict[str, Any]) -> List[str]:
        """Identify study limitations."""
        limitations = []
        
        if config.repetitions < 20:
            limitations.append(f"Limited repetitions ({config.repetitions}) may affect statistical power")
        
        if len(config.datasets) < 3:
            limitations.append("Limited dataset diversity may affect generalizability")
        
        synthetic_datasets = [d for d in config.datasets if d.startswith("synthetic_")]
        if len(synthetic_datasets) == len(config.datasets):
            limitations.append("All datasets are synthetic - real-world validation needed")
        
        return limitations
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate research and development recommendations."""
        recommendations = []
        
        if "comparative_analysis" in analysis_results:
            comp_analysis = analysis_results["comparative_analysis"]
            confidence = comp_analysis.get("confidence_score", 0.0)
            
            if confidence > 0.8:
                recommendations.append("Results support publication in high-impact venues")
                recommendations.append("Consider patent applications for novel methods")
            elif confidence > 0.6:
                recommendations.append("Results suitable for conference publication")
                recommendations.append("Conduct additional experiments to strengthen findings")
            else:
                recommendations.append("Conduct larger-scale studies before publication")
                recommendations.append("Investigate sources of variability in results")
        
        recommendations.append("Validate results with real-world datasets")
        recommendations.append("Conduct user studies for practical applicability assessment")
        
        return recommendations
    
    def _assess_publication_readiness(self, config: ExperimentConfig,
                                    analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness for academic publication."""
        readiness_score = 0.0
        criteria_met = []
        criteria_missing = []
        
        # Check statistical rigor
        if "comparative_analysis" in analysis_results:
            comp_analysis = analysis_results["comparative_analysis"]
            if comp_analysis.get("confidence_score", 0.0) > 0.7:
                readiness_score += 0.3
                criteria_met.append("Statistical significance demonstrated")
            else:
                criteria_missing.append("Insufficient statistical evidence")
        
        # Check experimental design
        if config.repetitions >= 10:
            readiness_score += 0.2
            criteria_met.append("Adequate repetitions for statistical analysis")
        else:
            criteria_missing.append("Insufficient repetitions")
        
        # Check novelty
        novel_methods = len(config.novel_methods)
        if novel_methods > 0:
            readiness_score += 0.2
            criteria_met.append("Novel methods included in comparison")
        else:
            criteria_missing.append("No novel methods evaluated")
        
        # Check comprehensiveness  
        if len(config.metrics) >= 5:
            readiness_score += 0.2
            criteria_met.append("Comprehensive metric evaluation")
        else:
            criteria_missing.append("Limited metric evaluation")
        
        # Check reproducibility
        if config.parameters:
            readiness_score += 0.1
            criteria_met.append("Experimental parameters documented")
        else:
            criteria_missing.append("Experimental parameters not fully documented")
        
        return {
            "readiness_score": readiness_score,
            "publication_ready": readiness_score >= 0.8,
            "criteria_met": criteria_met,
            "criteria_missing": criteria_missing,
            "recommendations": self._get_publication_recommendations(readiness_score)
        }
    
    def _get_publication_recommendations(self, readiness_score: float) -> List[str]:
        """Get publication-specific recommendations."""
        if readiness_score >= 0.8:
            return [
                "Submit to top-tier conferences (NeurIPS, ICML, ICLR)",
                "Consider journal submission for comprehensive analysis",
                "Prepare supplementary materials with detailed results"
            ]
        elif readiness_score >= 0.6:
            return [
                "Submit to specialized conferences or workshops",
                "Strengthen statistical analysis before journal submission",
                "Consider collaboration with domain experts"
            ]
        else:
            return [
                "Conduct additional experiments to strengthen findings",
                "Increase sample sizes and repetitions",
                "Validate with real-world datasets",
                "Consider preliminary workshop submission for feedback"
            ]


# Global research framework instance
_research_framework: Optional[ExperimentRunner] = None


def get_research_framework() -> ExperimentRunner:
    """Get or create global research framework instance."""
    global _research_framework
    if _research_framework is None:
        _research_framework = ExperimentRunner()
    return _research_framework


async def run_comparative_study(baseline_methods: List[str], novel_methods: List[str],
                              datasets: List[str], metrics: List[str] = None) -> Dict[str, Any]:
    """Run comparative study between baseline and novel methods."""
    framework = get_research_framework()
    
    if metrics is None:
        metrics = ["accuracy", "processing_time", "f1_score", "energy_consumption"]
    
    config = ExperimentConfig(
        experiment_id=f"comp_study_{int(time.time())}",
        experiment_type=ExperimentType.COMPARATIVE_STUDY,
        name="Neuromorphic vs Quantum vs Classical Processing Comparison",
        description="Comparative evaluation of processing methods for contract clause extraction",
        hypothesis="Novel neuromorphic and quantum methods outperform classical approaches",
        success_criteria={
            "accuracy_improvement": 0.10,  # 10% improvement
            "statistical_significance": 0.05,
            "energy_efficiency": 0.20  # 20% energy reduction
        },
        baseline_methods=baseline_methods,
        novel_methods=novel_methods,
        datasets=datasets,
        metrics=metrics,
        repetitions=20,
        statistical_tests=[StatisticalTest.T_TEST, StatisticalTest.MANN_WHITNEY_U]
    )
    
    return await framework.run_experiment(config)


def generate_research_dataset(document_type: str, count: int = 100,
                            complexity_levels: List[str] = None) -> List[Dict[str, Any]]:
    """Generate synthetic research dataset."""
    framework = get_research_framework()
    return framework.data_generator.generate_synthetic_dataset(
        document_type, count, complexity_levels
    )


def save_experiment_results(experiment_results: Dict[str, Any], 
                          output_path: str = "experiment_results.json"):
    """Save experiment results to file."""
    results_to_save = experiment_results.copy()
    
    # Convert numpy arrays and other non-serializable objects
    def make_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        else:
            return obj
    
    serializable_results = make_serializable(results_to_save)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Experiment results saved to {output_path}")


def load_experiment_results(input_path: str) -> Dict[str, Any]:
    """Load experiment results from file."""
    with open(input_path, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Experiment results loaded from {input_path}")
    return results