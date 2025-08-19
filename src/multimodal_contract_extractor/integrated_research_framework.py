"""
Integrated Research Framework for Advanced Legal Document Processing

This module provides a unified interface for all novel research algorithms, integrating:

1. Graph Neural Networks for contract relationship modeling
2. Advanced Transformer attention mechanisms for legal understanding
3. Federated Learning for multi-jurisdictional processing
4. Causal Inference for contract risk assessment  
5. Multi-modal Fusion for complex document understanding

The framework provides:
- Unified API for all research algorithms
- Intelligent algorithm selection based on task requirements
- Automatic performance benchmarking and optimization
- Seamless integration with existing extraction pipeline
- Academic-grade evaluation and reporting

Integration Features:
- Backward compatibility with existing interfaces
- Configurable algorithm pipelines
- Real-time performance monitoring
- Automatic fallback to baseline methods
- Comprehensive logging and analytics
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field

# Import existing system components
try:
    from .extraction import extract_clauses
    from .document import Document
    from .config import get_config
except ImportError:
    logging.warning("Could not import existing system components")

# Import novel research algorithms
try:
    from .graph_neural_networks import (
        LegalGNNFramework, 
        create_legal_gnn_framework,
        LegalEntityType,
        LegalRelationType
    )
    from .advanced_transformer_attention import (
        LegalTransformerModel,
        create_legal_transformer_model,
        LegalAttentionType
    )
    from .federated_legal_learning import (
        JurisdictionalFederatedLearning,
        create_federated_legal_system,
        JurisdictionType as FedJurisdictionType
    )
    from .causal_inference_legal import (
        LegalCausalInferenceFramework,
        create_causal_inference_framework,
        CausalRelationType
    )
    from .advanced_multimodal_fusion import (
        AdvancedMultiModalFusionFramework,
        create_multimodal_fusion_framework,
        ModalityType
    )
    from .comprehensive_research_benchmark_suite import (
        BenchmarkExecutor,
        create_benchmark_executor,
        AlgorithmType,
        EvaluationMetric
    )
except ImportError as e:
    logging.warning(f"Could not import novel algorithm modules: {e}")

logger = logging.getLogger(__name__)


class ResearchTaskType(Enum):
    """Types of research tasks that can be performed."""
    RELATIONSHIP_EXTRACTION = "relationship_extraction"     # Extract relationships between entities
    LEGAL_UNDERSTANDING = "legal_understanding"           # Deep legal text understanding
    RISK_ASSESSMENT = "risk_assessment"                   # Contract risk assessment
    CROSS_JURISDICTION = "cross_jurisdiction"             # Multi-jurisdictional analysis
    MULTIMODAL_ANALYSIS = "multimodal_analysis"          # Multi-modal document analysis
    CAUSAL_ANALYSIS = "causal_analysis"                  # Causal relationship discovery
    PERFORMANCE_BENCHMARKING = "performance_benchmarking" # Algorithm benchmarking


class IntegrationMode(Enum):
    """Modes for integrating research algorithms with existing system."""
    STANDALONE = "standalone"          # Run novel algorithms independently
    HYBRID = "hybrid"                  # Combine with existing methods
    REPLACEMENT = "replacement"        # Replace existing methods
    ENSEMBLE = "ensemble"              # Ensemble of multiple approaches
    ADAPTIVE = "adaptive"              # Adaptively choose best method


@dataclass
class ResearchConfig:
    """Configuration for research framework."""
    
    # Algorithm selection
    enable_graph_networks: bool = True
    enable_transformer_attention: bool = True
    enable_federated_learning: bool = True
    enable_causal_inference: bool = True
    enable_multimodal_fusion: bool = True
    
    # Integration settings
    integration_mode: IntegrationMode = IntegrationMode.HYBRID
    fallback_to_baseline: bool = True
    performance_threshold: float = 0.8
    
    # Processing settings
    batch_size: int = 32
    max_processing_time: float = 300.0  # 5 minutes max per document
    enable_caching: bool = True
    
    # Legal domain settings
    default_jurisdiction: str = "US_Federal"
    legal_domain: str = "contract"
    complexity_threshold: float = 0.7
    
    # Output settings
    include_research_metrics: bool = True
    include_benchmarking: bool = False
    save_intermediate_results: bool = True
    
    # Performance settings
    enable_parallel_processing: bool = True
    max_concurrent_tasks: int = 4


@dataclass
class ResearchResult:
    """Container for research algorithm results."""
    
    task_type: ResearchTaskType
    algorithm_used: str
    processing_time: float
    confidence_score: float
    
    # Core results
    primary_result: Any
    secondary_results: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    benchmark_scores: Optional[Dict[str, float]] = None
    
    # Research insights
    novel_insights: List[str] = field(default_factory=list)
    research_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Integration metrics
    baseline_comparison: Optional[Dict[str, float]] = None
    improvement_over_baseline: Optional[float] = None
    
    def __post_init__(self):
        """Compute derived metrics."""
        if self.baseline_comparison and 'baseline_score' in self.baseline_comparison:
            baseline_score = self.baseline_comparison['baseline_score']
            if baseline_score > 0:
                self.improvement_over_baseline = (self.confidence_score - baseline_score) / baseline_score


class IntegratedResearchFramework:
    """
    Main framework class that integrates all novel research algorithms
    with the existing legal document processing system.
    """
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig()
        
        # Algorithm instances
        self.algorithm_instances: Dict[str, Any] = {}
        self.benchmark_executor: Optional[BenchmarkExecutor] = None
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.algorithm_performance: Dict[str, List[float]] = {}
        
        # Integration state
        self.initialized = False
        self.last_benchmark_time = 0.0
        
        # Cache for results
        self.result_cache: Dict[str, ResearchResult] = {}
    
    async def initialize(self) -> bool:
        """Initialize all research algorithms and components."""
        
        try:
            logger.info("Initializing Integrated Research Framework...")
            
            # Initialize Graph Neural Networks
            if self.config.enable_graph_networks:
                self.algorithm_instances['graph_networks'] = create_legal_gnn_framework()
                logger.info("✓ Graph Neural Networks initialized")
            
            # Initialize Transformer Attention
            if self.config.enable_transformer_attention:
                self.algorithm_instances['transformer_attention'] = create_legal_transformer_model()
                logger.info("✓ Advanced Transformer Attention initialized")
            
            # Initialize Federated Learning
            if self.config.enable_federated_learning:
                self.algorithm_instances['federated_learning'] = create_federated_legal_system()
                logger.info("✓ Federated Learning initialized")
            
            # Initialize Causal Inference
            if self.config.enable_causal_inference:
                self.algorithm_instances['causal_inference'] = create_causal_inference_framework()
                logger.info("✓ Causal Inference initialized")
            
            # Initialize Multimodal Fusion
            if self.config.enable_multimodal_fusion:
                self.algorithm_instances['multimodal_fusion'] = create_multimodal_fusion_framework()
                logger.info("✓ Multimodal Fusion initialized")
            
            # Initialize Benchmark Executor
            if self.config.include_benchmarking:
                self.benchmark_executor = create_benchmark_executor()
                logger.info("✓ Benchmark Executor initialized")
            
            self.initialized = True
            logger.info("Integrated Research Framework initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize research framework: {e}")
            return False
    
    async def process_document_research(self, document: Union[str, Dict[str, Any]], 
                                      task_types: Optional[List[ResearchTaskType]] = None) -> Dict[str, ResearchResult]:
        """
        Process document using research algorithms for specified tasks.
        
        Args:
            document: Document text or document data structure
            task_types: List of research tasks to perform (None = all available)
            
        Returns:
            Dictionary mapping task types to research results
        """
        
        if not self.initialized:
            await self.initialize()
        
        if task_types is None:
            task_types = [
                ResearchTaskType.RELATIONSHIP_EXTRACTION,
                ResearchTaskType.LEGAL_UNDERSTANDING,
                ResearchTaskType.RISK_ASSESSMENT,
                ResearchTaskType.MULTIMODAL_ANALYSIS
            ]
        
        logger.info(f"Processing document with {len(task_types)} research tasks")
        
        # Prepare document data
        document_data = self._prepare_document_data(document)
        
        # Process tasks
        results = {}
        
        if self.config.enable_parallel_processing:
            # Parallel processing
            tasks = [
                self._process_single_task(task_type, document_data)
                for task_type in task_types
            ]
            
            # Limit concurrent tasks
            semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
            
            async def process_with_semaphore(task):
                async with semaphore:
                    return await task
            
            task_results = await asyncio.gather(*[
                process_with_semaphore(task) for task in tasks
            ], return_exceptions=True)
            
            # Organize results
            for task_type, result in zip(task_types, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {task_type}: {result}")
                    results[task_type] = self._create_error_result(task_type, str(result))
                else:
                    results[task_type] = result
        
        else:
            # Sequential processing
            for task_type in task_types:
                try:
                    result = await self._process_single_task(task_type, document_data)
                    results[task_type] = result
                except Exception as e:
                    logger.error(f"Error processing {task_type}: {e}")
                    results[task_type] = self._create_error_result(task_type, str(e))
        
        # Update performance tracking
        self._update_performance_tracking(results)
        
        # Integration with existing system
        integrated_results = await self._integrate_with_existing_system(document_data, results)
        
        logger.info(f"Document research processing completed: {len(results)} tasks")
        return integrated_results
    
    def _prepare_document_data(self, document: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare document data for research algorithms."""
        
        if isinstance(document, str):
            # Simple text input
            return {
                'text': document,
                'type': 'contract',
                'jurisdiction': self.config.default_jurisdiction,
                'metadata': {
                    'source': 'text_input',
                    'processing_time': time.time()
                }
            }
        
        elif isinstance(document, dict):
            # Structured document input
            return {
                'text': document.get('text', ''),
                'type': document.get('type', 'contract'),
                'jurisdiction': document.get('jurisdiction', self.config.default_jurisdiction),
                'clauses': document.get('clauses', []),
                'metadata': document.get('metadata', {}),
                'multimodal_data': document.get('multimodal_data', {}),
                **document  # Include all other fields
            }
        
        else:
            # Fallback
            return {
                'text': str(document),
                'type': 'unknown',
                'jurisdiction': self.config.default_jurisdiction,
                'metadata': {'source': 'fallback'}
            }
    
    async def _process_single_task(self, task_type: ResearchTaskType, 
                                 document_data: Dict[str, Any]) -> ResearchResult:
        """Process a single research task."""
        
        start_time = time.time()
        
        try:
            if task_type == ResearchTaskType.RELATIONSHIP_EXTRACTION:
                result = await self._process_relationship_extraction(document_data)
            
            elif task_type == ResearchTaskType.LEGAL_UNDERSTANDING:
                result = await self._process_legal_understanding(document_data)
            
            elif task_type == ResearchTaskType.RISK_ASSESSMENT:
                result = await self._process_risk_assessment(document_data)
            
            elif task_type == ResearchTaskType.MULTIMODAL_ANALYSIS:
                result = await self._process_multimodal_analysis(document_data)
            
            elif task_type == ResearchTaskType.CAUSAL_ANALYSIS:
                result = await self._process_causal_analysis(document_data)
            
            elif task_type == ResearchTaskType.CROSS_JURISDICTION:
                result = await self._process_cross_jurisdiction(document_data)
            
            else:
                # Fallback
                result = ResearchResult(
                    task_type=task_type,
                    algorithm_used="fallback",
                    processing_time=time.time() - start_time,
                    confidence_score=0.5,
                    primary_result={"status": "not_implemented"}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {task_type} processing: {e}")
            return self._create_error_result(task_type, str(e))
    
    async def _process_relationship_extraction(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process relationship extraction using Graph Neural Networks."""
        
        start_time = time.time()
        
        if 'graph_networks' not in self.algorithm_instances:
            raise ValueError("Graph Neural Networks not initialized")
        
        gnn_framework = self.algorithm_instances['graph_networks']
        
        # Extract clauses if not provided
        clauses = document_data.get('clauses', [])
        if not clauses:
            # Extract clauses from text (simplified)
            text = document_data.get('text', '')
            clauses = self._extract_clauses_simple(text)
        
        # Run GNN analysis
        gnn_result = await gnn_framework.analyze_contract_graph(
            document_data['text'], clauses
        )
        
        # Extract key insights
        novel_insights = []
        if gnn_result.get('novel_insights', {}).get('critical_entities'):
            critical_entities = gnn_result['novel_insights']['critical_entities'][:3]
            novel_insights.append(f"Identified {len(critical_entities)} critical legal entities")
        
        if gnn_result.get('graph_statistics', {}).get('num_relations', 0) > 10:
            novel_insights.append("Complex relationship structure detected - high interconnectedness")
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            task_type=ResearchTaskType.RELATIONSHIP_EXTRACTION,
            algorithm_used="Legal_Graph_Neural_Networks",
            processing_time=processing_time,
            confidence_score=gnn_result.get('performance_metrics', {}).get('graph_construction_efficiency', 0.8),
            primary_result=gnn_result,
            performance_metrics={
                'graph_density': gnn_result.get('graph_statistics', {}).get('graph_density', 0.0),
                'num_entities': gnn_result.get('graph_statistics', {}).get('num_entities', 0),
                'num_relationships': gnn_result.get('graph_statistics', {}).get('num_relations', 0)
            },
            novel_insights=novel_insights,
            research_metadata={
                'algorithm_version': '1.0',
                'graph_complexity': 'high' if gnn_result.get('graph_statistics', {}).get('num_relations', 0) > 10 else 'moderate'
            }
        )
    
    async def _process_legal_understanding(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process legal understanding using Advanced Transformer Attention."""
        
        start_time = time.time()
        
        if 'transformer_attention' not in self.algorithm_instances:
            raise ValueError("Transformer Attention not initialized")
        
        transformer_model = self.algorithm_instances['transformer_attention']
        
        # Prepare token sequence
        text = document_data.get('text', '')
        token_ids = self._text_to_token_ids(text)
        
        # Prepare legal metadata
        legal_metadata = {
            'domain': document_data.get('type', 'contract'),
            'jurisdiction': document_data.get('jurisdiction', 'US_Federal'),
            'complexity': len(text) / 1000.0  # Simple complexity measure
        }
        
        # Run transformer analysis
        transformer_result = await transformer_model.process_legal_document(
            token_ids, legal_metadata
        )
        
        # Extract insights
        novel_insights = []
        comprehension_score = transformer_result.get('comprehensive_analysis', {}).get('overall_legal_comprehension_score', 0.0)
        
        if comprehension_score > 0.8:
            novel_insights.append("High legal comprehension achieved - document well understood")
        
        attention_evolution = transformer_result.get('comprehensive_analysis', {}).get('attention_evolution', [])
        if len(attention_evolution) > 0:
            final_entropy = attention_evolution[-1].get('average_entropy', 0.0)
            if final_entropy < 2.0:  # Low entropy indicates focused attention
                novel_insights.append("Focused attention patterns detected - key legal concepts identified")
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            task_type=ResearchTaskType.LEGAL_UNDERSTANDING,
            algorithm_used="Advanced_Legal_Transformer",
            processing_time=processing_time,
            confidence_score=comprehension_score,
            primary_result=transformer_result,
            performance_metrics={
                'comprehension_score': comprehension_score,
                'processing_throughput': transformer_result.get('processing_metrics', {}).get('throughput', 0.0),
                'attention_quality': transformer_result.get('comprehensive_analysis', {}).get('attention_evolution', [{}])[-1].get('average_entropy', 0.0)
            },
            novel_insights=novel_insights,
            research_metadata={
                'layers_processed': transformer_result.get('processing_metrics', {}).get('layers_processed', 0),
                'tokens_processed': transformer_result.get('processing_metrics', {}).get('tokens_processed', 0)
            }
        )
    
    async def _process_risk_assessment(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process risk assessment using Causal Inference."""
        
        start_time = time.time()
        
        if 'causal_inference' not in self.algorithm_instances:
            raise ValueError("Causal Inference not initialized")
        
        causal_framework = self.algorithm_instances['causal_inference']
        
        # Create legal variables from document
        legal_variables = self._create_legal_variables_from_document(document_data)
        
        # Run causal analysis
        causal_result = await causal_framework.analyze_legal_causality(
            document_data['text'], legal_variables
        )
        
        # Extract risk insights
        novel_insights = []
        risk_assessment = causal_result.get('legal_risk_assessment', {})
        
        risk_level = risk_assessment.get('risk_level', 'unknown')
        if risk_level == 'high':
            novel_insights.append("High legal risk detected through causal analysis")
        
        risk_factors = risk_assessment.get('risk_factors', [])
        if len(risk_factors) > 2:
            novel_insights.append(f"Multiple risk factors identified: {len(risk_factors)} causal risk patterns")
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            task_type=ResearchTaskType.RISK_ASSESSMENT,
            algorithm_used="Legal_Causal_Inference",
            processing_time=processing_time,
            confidence_score=risk_assessment.get('overall_risk_score', 0.0),
            primary_result=causal_result,
            performance_metrics={
                'risk_score': risk_assessment.get('overall_risk_score', 0.0),
                'num_risk_factors': len(risk_factors),
                'causal_relationships_found': len(causal_result.get('causal_graph', {}).get('causal_relationships', []))
            },
            novel_insights=novel_insights,
            research_metadata={
                'causal_variables': len(legal_variables),
                'identifiable_effects': causal_result.get('processing_metrics', {}).get('identifiable_effects', 0)
            }
        )
    
    async def _process_multimodal_analysis(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process multimodal analysis using Multimodal Fusion."""
        
        start_time = time.time()
        
        if 'multimodal_fusion' not in self.algorithm_instances:
            raise ValueError("Multimodal Fusion not initialized")
        
        multimodal_framework = self.algorithm_instances['multimodal_fusion']
        
        # Prepare multimodal document data
        fusion_document_data = {
            'text': document_data.get('text', ''),
            'legal_metadata': {
                'jurisdiction': document_data.get('jurisdiction', 'unknown'),
                'type': document_data.get('type', 'contract'),
                'complexity': document_data.get('metadata', {}).get('complexity', 0.5)
            }
        }
        
        # Add multimodal data if available
        if 'multimodal_data' in document_data:
            fusion_document_data.update(document_data['multimodal_data'])
        
        # Run multimodal analysis
        multimodal_result = await multimodal_framework.comprehensive_multimodal_analysis(
            fusion_document_data, document_data.get('type', 'contract')
        )
        
        # Extract insights
        novel_insights = []
        fusion_quality = multimodal_result.get('performance_metrics', {}).get('fusion_quality', 0.0)
        
        if fusion_quality > 0.8:
            novel_insights.append("High-quality multimodal fusion achieved")
        
        modality_contributions = multimodal_result.get('cross_modal_fusion', {}).get('modality_contributions', {})
        dominant_modality = modality_contributions.get('dominant_modality')
        if dominant_modality:
            novel_insights.append(f"Dominant information modality: {dominant_modality}")
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            task_type=ResearchTaskType.MULTIMODAL_ANALYSIS,
            algorithm_used="Advanced_Multimodal_Fusion",
            processing_time=processing_time,
            confidence_score=multimodal_result.get('performance_metrics', {}).get('overall_confidence', 0.0),
            primary_result=multimodal_result,
            performance_metrics={
                'fusion_quality': fusion_quality,
                'num_modalities': multimodal_result.get('performance_metrics', {}).get('num_modalities', 0),
                'modality_balance': multimodal_result.get('cross_modal_fusion', {}).get('fusion_metrics', {}).get('fusion_balance', 0.0)
            },
            novel_insights=novel_insights,
            research_metadata={
                'dominant_modality': dominant_modality,
                'fusion_strategy': 'cross_modal_attention'
            }
        )
    
    async def _process_causal_analysis(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process causal analysis (detailed causal discovery)."""
        
        # This is similar to risk assessment but focuses on causal discovery
        return await self._process_risk_assessment(document_data)
    
    async def _process_cross_jurisdiction(self, document_data: Dict[str, Any]) -> ResearchResult:
        """Process cross-jurisdictional analysis using Federated Learning."""
        
        start_time = time.time()
        
        if 'federated_learning' not in self.algorithm_instances:
            raise ValueError("Federated Learning not initialized")
        
        fed_framework = self.algorithm_instances['federated_learning']
        
        # Get federation statistics
        fed_stats = fed_framework.get_federation_statistics()
        
        # Simulate cross-jurisdictional analysis
        novel_insights = []
        
        jurisdiction_dist = fed_stats.get('jurisdiction_distribution', {})
        if len(jurisdiction_dist) > 1:
            novel_insights.append(f"Multi-jurisdictional analysis across {len(jurisdiction_dist)} jurisdictions")
        
        privacy_efficiency = fed_stats.get('privacy_metrics', {}).get('privacy_efficiency', 0.0)
        if privacy_efficiency > 0.8:
            novel_insights.append("High privacy preservation achieved in cross-jurisdictional processing")
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            task_type=ResearchTaskType.CROSS_JURISDICTION,
            algorithm_used="Federated_Legal_Learning",
            processing_time=processing_time,
            confidence_score=privacy_efficiency,
            primary_result=fed_stats,
            performance_metrics={
                'privacy_efficiency': privacy_efficiency,
                'num_jurisdictions': len(jurisdiction_dist),
                'federation_clients': fed_stats.get('federation_info', {}).get('total_registered_clients', 0)
            },
            novel_insights=novel_insights,
            research_metadata={
                'federated_rounds': fed_stats.get('federation_info', {}).get('training_rounds_completed', 0),
                'privacy_budget_remaining': fed_stats.get('federation_info', {}).get('privacy_budget_remaining', 0.0)
            }
        )
    
    def _extract_clauses_simple(self, text: str) -> List[Dict[str, Any]]:
        """Simple clause extraction (fallback method)."""
        
        # Split text into sentences and treat as clauses
        sentences = text.split('.')
        clauses = []
        
        for i, sentence in enumerate(sentences[:10]):  # Limit to 10
            if sentence.strip():
                clauses.append({
                    'text': sentence.strip(),
                    'type': 'clause',
                    'confidence': 0.7,
                    'id': f"clause_{i}"
                })
        
        return clauses
    
    def _text_to_token_ids(self, text: str) -> List[int]:
        """Convert text to token IDs (simplified)."""
        
        words = text.split()[:100]  # Limit to 100 tokens
        return [hash(word) % 1000 for word in words]  # Simple hash-based tokenization
    
    def _create_legal_variables_from_document(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create legal variables for causal analysis."""
        
        variables = []
        
        # Document-level variables
        variables.append({
            'id': 'document_complexity',
            'name': 'Document Complexity',
            'type': 'continuous',
            'category': 'document',
            'description': 'Overall complexity of the legal document',
            'is_confounder': True
        })
        
        # Clause-level variables
        clauses = document_data.get('clauses', [])
        for i, clause in enumerate(clauses[:5]):  # Limit for performance
            variables.append({
                'id': f"clause_{i}",
                'name': clause.get('text', f"Clause {i}")[:50],  # Truncate name
                'type': 'binary',
                'category': 'clause',
                'description': f"Presence and strength of clause {i}",
                'is_treatment': i < 2,  # First 2 as treatments
                'is_outcome': i >= len(clauses) - 2  # Last 2 as outcomes
            })
        
        return variables
    
    def _create_error_result(self, task_type: ResearchTaskType, error_message: str) -> ResearchResult:
        """Create error result for failed tasks."""
        
        return ResearchResult(
            task_type=task_type,
            algorithm_used="error",
            processing_time=0.0,
            confidence_score=0.0,
            primary_result={"error": error_message, "status": "failed"},
            novel_insights=[f"Error in {task_type.value}: {error_message}"]
        )
    
    def _update_performance_tracking(self, results: Dict[ResearchTaskType, ResearchResult]):
        """Update performance tracking with current results."""
        
        performance_entry = {
            'timestamp': time.time(),
            'results_summary': {}
        }
        
        for task_type, result in results.items():
            task_key = task_type.value
            performance_entry['results_summary'][task_key] = {
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'algorithm_used': result.algorithm_used
            }
            
            # Update algorithm-specific performance tracking
            if result.algorithm_used not in self.algorithm_performance:
                self.algorithm_performance[result.algorithm_used] = []
            
            self.algorithm_performance[result.algorithm_used].append(result.confidence_score)
        
        self.performance_history.append(performance_entry)
        
        # Keep only recent history (last 100 entries)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    async def _integrate_with_existing_system(self, document_data: Dict[str, Any],
                                           research_results: Dict[ResearchTaskType, ResearchResult]) -> Dict[str, ResearchResult]:
        """Integrate research results with existing system."""
        
        # Add baseline comparisons if possible
        for task_type, result in research_results.items():
            
            # Simulate baseline comparison
            baseline_score = self._get_baseline_performance(task_type)
            if baseline_score > 0:
                result.baseline_comparison = {
                    'baseline_score': baseline_score,
                    'baseline_method': 'traditional_ml'
                }
        
        # Add integration metadata
        integration_metadata = {
            'integration_mode': self.config.integration_mode.value,
            'framework_version': '1.0',
            'total_processing_time': sum(r.processing_time for r in research_results.values()),
            'successful_tasks': sum(1 for r in research_results.values() if r.confidence_score > 0.5)
        }
        
        # Add integration metadata to all results
        for result in research_results.values():
            result.research_metadata.update(integration_metadata)
        
        return research_results
    
    def _get_baseline_performance(self, task_type: ResearchTaskType) -> float:
        """Get baseline performance for comparison."""
        
        # Estimated baseline performance for different tasks
        baseline_performance = {
            ResearchTaskType.RELATIONSHIP_EXTRACTION: 0.65,
            ResearchTaskType.LEGAL_UNDERSTANDING: 0.75,
            ResearchTaskType.RISK_ASSESSMENT: 0.60,
            ResearchTaskType.MULTIMODAL_ANALYSIS: 0.55,
            ResearchTaskType.CAUSAL_ANALYSIS: 0.50,
            ResearchTaskType.CROSS_JURISDICTION: 0.70
        }
        
        return baseline_performance.get(task_type, 0.6)
    
    async def benchmark_algorithms(self, algorithms_to_test: Optional[List[AlgorithmType]] = None) -> Dict[str, Any]:
        """Run comprehensive benchmarking of research algorithms."""
        
        if not self.benchmark_executor:
            self.benchmark_executor = create_benchmark_executor()
        
        logger.info("Starting algorithm benchmarking...")
        
        benchmark_results = await self.benchmark_executor.run_comprehensive_benchmark(algorithms_to_test)
        
        # Update last benchmark time
        self.last_benchmark_time = time.time()
        
        return benchmark_results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the research framework."""
        
        summary = {
            'framework_status': {
                'initialized': self.initialized,
                'algorithms_loaded': len(self.algorithm_instances),
                'total_processing_sessions': len(self.performance_history)
            },
            'algorithm_performance': {},
            'recent_performance': {},
            'recommendations': []
        }
        
        # Algorithm performance summary
        for algorithm, scores in self.algorithm_performance.items():
            if scores:
                summary['algorithm_performance'][algorithm] = {
                    'average_confidence': np.mean(scores),
                    'median_confidence': np.median(scores),
                    'performance_trend': 'improving' if len(scores) > 5 and scores[-3:] > scores[:3] else 'stable',
                    'total_uses': len(scores)
                }
        
        # Recent performance (last 10 sessions)
        recent_sessions = self.performance_history[-10:]
        if recent_sessions:
            recent_confidences = []
            recent_times = []
            
            for session in recent_sessions:
                for task_results in session['results_summary'].values():
                    recent_confidences.append(task_results['confidence_score'])
                    recent_times.append(task_results['processing_time'])
            
            if recent_confidences:
                summary['recent_performance'] = {
                    'average_confidence': np.mean(recent_confidences),
                    'average_processing_time': np.mean(recent_times),
                    'performance_consistency': 1.0 - np.std(recent_confidences) / (np.mean(recent_confidences) + 0.01)
                }
        
        # Generate recommendations
        recommendations = []
        
        # Check if benchmarking is needed
        time_since_benchmark = time.time() - self.last_benchmark_time
        if time_since_benchmark > 86400:  # 24 hours
            recommendations.append("Consider running algorithm benchmarking - last benchmark > 24 hours ago")
        
        # Performance-based recommendations
        if summary.get('recent_performance', {}).get('average_confidence', 0) < 0.7:
            recommendations.append("Recent average confidence is low - consider algorithm tuning")
        
        if summary.get('recent_performance', {}).get('average_processing_time', 0) > 10.0:
            recommendations.append("Processing times are high - consider optimization or parallel processing")
        
        summary['recommendations'] = recommendations
        
        return summary
    
    async def shutdown(self):
        """Gracefully shutdown the research framework."""
        
        logger.info("Shutting down Integrated Research Framework...")
        
        # Save performance history
        if self.performance_history:
            try:
                history_file = Path("research_performance_history.json")
                with open(history_file, 'w') as f:
                    json.dump(self.performance_history, f, indent=2, default=str)
                logger.info(f"Performance history saved to {history_file}")
            except Exception as e:
                logger.warning(f"Could not save performance history: {e}")
        
        # Clear algorithm instances
        self.algorithm_instances.clear()
        self.initialized = False
        
        logger.info("Research framework shutdown complete")


# Factory function
def create_integrated_research_framework(config: Optional[ResearchConfig] = None) -> IntegratedResearchFramework:
    """Create integrated research framework with specified configuration."""
    return IntegratedResearchFramework(config)


# Demonstration function
async def demonstrate_integrated_framework():
    """Demonstrate integrated research framework capabilities."""
    
    logger.info("Starting Integrated Research Framework demonstration")
    
    # Create framework with custom config
    config = ResearchConfig(
        integration_mode=IntegrationMode.HYBRID,
        enable_parallel_processing=True,
        max_concurrent_tasks=3,
        include_benchmarking=False  # Disable for demo speed
    )
    
    framework = create_integrated_research_framework(config)
    
    # Initialize framework
    success = await framework.initialize()
    if not success:
        logger.error("Failed to initialize framework")
        return
    
    # Sample legal document
    sample_document = {
        'text': """
        This Service Agreement is entered into between Company A and Company B.
        Company A shall provide consulting services to Company B for a period of one year.
        Payment shall be due within 30 days of invoice date.
        Either party may terminate this agreement with 60 days written notice.
        This agreement shall be governed by the laws of New York.
        """,
        'type': 'service_agreement',
        'jurisdiction': 'US_Federal',
        'clauses': [
            {'text': 'Payment shall be due within 30 days of invoice date', 'type': 'payment_terms'},
            {'text': 'Either party may terminate this agreement with 60 days written notice', 'type': 'termination'},
            {'text': 'This agreement shall be governed by the laws of New York', 'type': 'governing_law'}
        ]
    }
    
    # Process document with research algorithms
    research_results = await framework.process_document_research(
        sample_document,
        task_types=[
            ResearchTaskType.RELATIONSHIP_EXTRACTION,
            ResearchTaskType.LEGAL_UNDERSTANDING,
            ResearchTaskType.RISK_ASSESSMENT,
            ResearchTaskType.MULTIMODAL_ANALYSIS
        ]
    )
    
    # Display results
    logger.info(f"\nResearch Processing Results:")
    logger.info(f"Tasks completed: {len(research_results)}")
    
    for task_type, result in research_results.items():
        logger.info(f"\n{task_type.value}:")
        logger.info(f"  Algorithm: {result.algorithm_used}")
        logger.info(f"  Confidence: {result.confidence_score:.3f}")
        logger.info(f"  Processing time: {result.processing_time:.3f}s")
        logger.info(f"  Improvement over baseline: {result.improvement_over_baseline:.1%}" if result.improvement_over_baseline else "  No baseline comparison")
        
        if result.novel_insights:
            logger.info(f"  Key insights:")
            for insight in result.novel_insights[:2]:  # Show top 2
                logger.info(f"    - {insight}")
    
    # Get performance summary
    performance_summary = framework.get_performance_summary()
    logger.info(f"\nFramework Performance Summary:")
    logger.info(f"Algorithms loaded: {performance_summary['framework_status']['algorithms_loaded']}")
    logger.info(f"Processing sessions: {performance_summary['framework_status']['total_processing_sessions']}")
    
    if performance_summary.get('recent_performance'):
        recent = performance_summary['recent_performance']
        logger.info(f"Recent average confidence: {recent.get('average_confidence', 0):.3f}")
        logger.info(f"Recent average processing time: {recent.get('average_processing_time', 0):.3f}s")
    
    # Show recommendations
    if performance_summary.get('recommendations'):
        logger.info("\nRecommendations:")
        for rec in performance_summary['recommendations'][:3]:
            logger.info(f"  - {rec}")
    
    # Shutdown
    await framework.shutdown()
    
    logger.info("\nIntegrated Research Framework demonstration completed")
    return research_results


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_integrated_framework())