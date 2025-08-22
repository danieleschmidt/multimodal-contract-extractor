"""Adaptive ML model selection for optimal contract extraction.

Generation 1 Enhanced Feature: Automatically selects the best ML model
based on document characteristics, content type, and processing requirements.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available ML model types."""
    OCR_LIGHTWEIGHT = "ocr_lightweight"
    OCR_ADVANCED = "ocr_advanced"
    NLP_TRANSFORMER = "nlp_transformer"
    VISION_LANGUAGE = "vision_language"
    MULTIMODAL_FUSION = "multimodal_fusion"
    LEGAL_SPECIALIST = "legal_specialist"
    NEUROMORPHIC = "neuromorphic"
    QUANTUM_ENHANCED = "quantum_enhanced"


class DocumentComplexity(Enum):
    """Document complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


@dataclass
class ModelCapabilities:
    """ML model capabilities and characteristics."""
    model_type: ModelType
    accuracy_score: float
    processing_speed: float  # pages per second
    memory_usage_mb: float
    language_support: List[str]
    document_types: List[str]
    min_confidence: float
    max_file_size_mb: float
    specialized_features: List[str]


@dataclass
class ModelSelection:
    """Result of model selection process."""
    model_type: ModelType
    confidence: float
    reasoning: str
    fallback_models: List[ModelType]
    estimated_processing_time: float
    estimated_accuracy: float
    resource_requirements: Dict[str, Any]


class ModelSelector:
    """Intelligent ML model selector for contract extraction."""
    
    def __init__(self):
        """Initialize model selector with available models."""
        self.available_models = self._initialize_models()
        self.performance_history = {}
        self.selection_cache = {}
        
    def select_optimal_model(self, document_type: str, file_size: int,
                           language_code: str = "en",
                           quality_priority: bool = True,
                           speed_priority: bool = False) -> ModelSelection:
        """Select optimal ML model for document processing.
        
        Args:
            document_type: File extension or document type
            file_size: File size in bytes
            language_code: Language code for processing
            quality_priority: Prioritize accuracy over speed
            speed_priority: Prioritize speed over accuracy
            
        Returns:
            ModelSelection with optimal model and metadata
        """
        start_time = time.perf_counter()
        
        # Create cache key
        cache_key = f"{document_type}_{file_size}_{language_code}_{quality_priority}_{speed_priority}"
        if cache_key in self.selection_cache:
            cached = self.selection_cache[cache_key]
            logger.debug("Using cached model selection: %s", cached.model_type.value)
            return cached
        
        # Analyze document characteristics
        complexity = self._assess_document_complexity(document_type, file_size)
        
        # Filter compatible models
        compatible_models = self._filter_compatible_models(
            document_type, file_size, language_code
        )
        
        if not compatible_models:
            # Fallback to basic OCR
            logger.warning("No compatible models found, falling back to basic OCR")
            return self._create_fallback_selection()
            
        # Score and rank models
        scored_models = self._score_models(
            compatible_models, complexity, quality_priority, speed_priority
        )
        
        # Select best model
        best_model = max(scored_models, key=lambda x: x['total_score'])
        
        # Generate model selection
        selection = ModelSelection(
            model_type=best_model['model_type'],
            confidence=best_model['confidence'],
            reasoning=best_model['reasoning'],
            fallback_models=self._get_fallback_models(best_model['model_type']),
            estimated_processing_time=best_model['estimated_time'],
            estimated_accuracy=best_model['estimated_accuracy'],
            resource_requirements=best_model['resources']
        )
        
        # Cache selection
        self.selection_cache[cache_key] = selection
        
        selection_time = time.perf_counter() - start_time
        logger.info("Model selection completed in %.3fs: %s (confidence: %.3f)",
                   selection_time, selection.model_type.value, selection.confidence)
        
        return selection
        
    def _initialize_models(self) -> Dict[ModelType, ModelCapabilities]:
        """Initialize available ML models with their capabilities."""
        return {
            ModelType.OCR_LIGHTWEIGHT: ModelCapabilities(
                model_type=ModelType.OCR_LIGHTWEIGHT,
                accuracy_score=0.75,
                processing_speed=15.0,
                memory_usage_mb=128,
                language_support=["en", "es", "fr", "de"],
                document_types=[".pdf", ".png", ".jpg", ".jpeg"],
                min_confidence=0.6,
                max_file_size_mb=10,
                specialized_features=["fast_processing", "low_memory"]
            ),
            ModelType.OCR_ADVANCED: ModelCapabilities(
                model_type=ModelType.OCR_ADVANCED,
                accuracy_score=0.88,
                processing_speed=8.0,
                memory_usage_mb=512,
                language_support=["en", "es", "fr", "de", "it", "pt", "zh", "ja"],
                document_types=[".pdf", ".png", ".jpg", ".jpeg", ".tiff"],
                min_confidence=0.75,
                max_file_size_mb=50,
                specialized_features=["multilingual", "handwriting_support"]
            ),
            ModelType.NLP_TRANSFORMER: ModelCapabilities(
                model_type=ModelType.NLP_TRANSFORMER,
                accuracy_score=0.92,
                processing_speed=5.0,
                memory_usage_mb=1024,
                language_support=["en", "es", "fr", "de", "it", "pt"],
                document_types=[".pdf", ".txt", ".docx"],
                min_confidence=0.85,
                max_file_size_mb=25,
                specialized_features=["context_understanding", "semantic_analysis"]
            ),
            ModelType.VISION_LANGUAGE: ModelCapabilities(
                model_type=ModelType.VISION_LANGUAGE,
                accuracy_score=0.94,
                processing_speed=3.0,
                memory_usage_mb=2048,
                language_support=["en", "es", "fr", "de"],
                document_types=[".pdf", ".png", ".jpg", ".jpeg"],
                min_confidence=0.88,
                max_file_size_mb=100,
                specialized_features=["visual_understanding", "layout_analysis"]
            ),
            ModelType.MULTIMODAL_FUSION: ModelCapabilities(
                model_type=ModelType.MULTIMODAL_FUSION,
                accuracy_score=0.96,
                processing_speed=2.0,
                memory_usage_mb=3072,
                language_support=["en", "es", "fr", "de", "it", "pt", "zh", "ja"],
                document_types=[".pdf", ".png", ".jpg", ".jpeg", ".tiff"],
                min_confidence=0.90,
                max_file_size_mb=200,
                specialized_features=["fusion_processing", "advanced_layout"]
            ),
            ModelType.LEGAL_SPECIALIST: ModelCapabilities(
                model_type=ModelType.LEGAL_SPECIALIST,
                accuracy_score=0.97,
                processing_speed=1.5,
                memory_usage_mb=4096,
                language_support=["en", "es", "fr", "de"],
                document_types=[".pdf", ".docx"],
                min_confidence=0.92,
                max_file_size_mb=150,
                specialized_features=["legal_terminology", "clause_recognition"]
            ),
            ModelType.NEUROMORPHIC: ModelCapabilities(
                model_type=ModelType.NEUROMORPHIC,
                accuracy_score=0.95,
                processing_speed=4.0,
                memory_usage_mb=1536,
                language_support=["en", "es", "fr", "de"],
                document_types=[".pdf", ".png", ".jpg"],
                min_confidence=0.88,
                max_file_size_mb=75,
                specialized_features=["neuromorphic_processing", "pattern_recognition"]
            ),
            ModelType.QUANTUM_ENHANCED: ModelCapabilities(
                model_type=ModelType.QUANTUM_ENHANCED,
                accuracy_score=0.98,
                processing_speed=1.0,
                memory_usage_mb=8192,
                language_support=["en", "es", "fr", "de", "it", "pt"],
                document_types=[".pdf", ".png", ".jpg", ".jpeg"],
                min_confidence=0.95,
                max_file_size_mb=500,
                specialized_features=["quantum_analysis", "entanglement_processing"]
            )
        }
        
    def _assess_document_complexity(self, document_type: str, 
                                  file_size: int) -> DocumentComplexity:
        """Assess document complexity based on characteristics."""
        file_size_mb = file_size / (1024 * 1024)
        
        # Base complexity on file size and type
        if document_type.lower() in ['.txt', '.docx']:
            # Text documents are generally simpler
            if file_size_mb < 1:
                return DocumentComplexity.SIMPLE
            elif file_size_mb < 5:
                return DocumentComplexity.MODERATE
            else:
                return DocumentComplexity.COMPLEX
        elif document_type.lower() in ['.pdf']:
            # PDFs can vary widely in complexity
            if file_size_mb < 2:
                return DocumentComplexity.SIMPLE
            elif file_size_mb < 10:
                return DocumentComplexity.MODERATE
            elif file_size_mb < 50:
                return DocumentComplexity.COMPLEX
            else:
                return DocumentComplexity.HIGHLY_COMPLEX
        else:
            # Image documents
            if file_size_mb < 5:
                return DocumentComplexity.MODERATE
            elif file_size_mb < 20:
                return DocumentComplexity.COMPLEX
            else:
                return DocumentComplexity.HIGHLY_COMPLEX
                
    def _filter_compatible_models(self, document_type: str, file_size: int,
                                 language_code: str) -> List[ModelCapabilities]:
        """Filter models compatible with document requirements."""
        compatible = []
        file_size_mb = file_size / (1024 * 1024)
        
        for model in self.available_models.values():
            # Check file type compatibility
            if document_type.lower() not in model.document_types:
                continue
                
            # Check file size limits
            if file_size_mb > model.max_file_size_mb:
                continue
                
            # Check language support
            if language_code not in model.language_support:
                continue
                
            compatible.append(model)
            
        return compatible
        
    def _score_models(self, models: List[ModelCapabilities], 
                     complexity: DocumentComplexity,
                     quality_priority: bool,
                     speed_priority: bool) -> List[Dict[str, Any]]:
        """Score and rank models based on requirements."""
        scored_models = []
        
        for model in models:
            # Base scores
            accuracy_score = model.accuracy_score
            speed_score = min(1.0, model.processing_speed / 20.0)  # Normalize to 0-1
            memory_score = max(0.1, 1.0 - (model.memory_usage_mb / 8192))  # Lower memory = higher score
            
            # Adjust for complexity
            complexity_factor = self._get_complexity_factor(complexity, model)
            accuracy_score *= complexity_factor
            
            # Apply priority weights
            if quality_priority:
                total_score = (accuracy_score * 0.6 + speed_score * 0.2 + memory_score * 0.2)
            elif speed_priority:
                total_score = (accuracy_score * 0.3 + speed_score * 0.6 + memory_score * 0.1)
            else:
                # Balanced
                total_score = (accuracy_score * 0.5 + speed_score * 0.3 + memory_score * 0.2)
                
            # Calculate confidence based on model characteristics
            confidence = self._calculate_selection_confidence(model, complexity)
            
            # Generate reasoning
            reasoning = self._generate_selection_reasoning(model, complexity, quality_priority, speed_priority)
            
            # Estimate processing time and accuracy
            estimated_time = self._estimate_processing_time(model, complexity)
            estimated_accuracy = accuracy_score
            
            scored_models.append({
                'model_type': model.model_type,
                'total_score': total_score,
                'confidence': confidence,
                'reasoning': reasoning,
                'estimated_time': estimated_time,
                'estimated_accuracy': estimated_accuracy,
                'resources': {
                    'memory_mb': model.memory_usage_mb,
                    'processing_speed': model.processing_speed,
                    'specialized_features': model.specialized_features
                }
            })
            
        return scored_models
        
    def _get_complexity_factor(self, complexity: DocumentComplexity,
                              model: ModelCapabilities) -> float:
        """Get complexity adjustment factor for model scoring."""
        complexity_requirements = {
            DocumentComplexity.SIMPLE: 0.8,
            DocumentComplexity.MODERATE: 0.9,
            DocumentComplexity.COMPLEX: 1.0,
            DocumentComplexity.HIGHLY_COMPLEX: 1.1
        }
        
        model_complexity_handling = {
            ModelType.OCR_LIGHTWEIGHT: 0.8,
            ModelType.OCR_ADVANCED: 0.9,
            ModelType.NLP_TRANSFORMER: 1.0,
            ModelType.VISION_LANGUAGE: 1.1,
            ModelType.MULTIMODAL_FUSION: 1.2,
            ModelType.LEGAL_SPECIALIST: 1.3,
            ModelType.NEUROMORPHIC: 1.1,
            ModelType.QUANTUM_ENHANCED: 1.4
        }
        
        requirement = complexity_requirements[complexity]
        capability = model_complexity_handling[model.model_type]
        
        # Return factor based on how well model matches complexity
        return min(1.2, capability / requirement)
        
    def _calculate_selection_confidence(self, model: ModelCapabilities,
                                      complexity: DocumentComplexity) -> float:
        """Calculate confidence in model selection."""
        base_confidence = model.accuracy_score
        
        # Adjust based on model-complexity match
        complexity_match = self._get_complexity_factor(complexity, model)
        
        # Higher confidence for better matches
        confidence = base_confidence * min(1.0, complexity_match)
        
        return round(confidence, 3)
        
    def _generate_selection_reasoning(self, model: ModelCapabilities,
                                    complexity: DocumentComplexity,
                                    quality_priority: bool,
                                    speed_priority: bool) -> str:
        """Generate human-readable reasoning for model selection."""
        reasons = []
        
        # Model-specific reasons
        if model.model_type == ModelType.LEGAL_SPECIALIST:
            reasons.append("Specialized for legal document processing")
        elif model.model_type == ModelType.QUANTUM_ENHANCED:
            reasons.append("Highest accuracy available with quantum processing")
        elif model.model_type == ModelType.OCR_LIGHTWEIGHT:
            reasons.append("Optimized for fast processing with low memory usage")
        elif model.model_type == ModelType.VISION_LANGUAGE:
            reasons.append("Excellent for complex layouts and visual elements")
            
        # Complexity-based reasons
        if complexity == DocumentComplexity.HIGHLY_COMPLEX:
            reasons.append("Selected for handling highly complex documents")
        elif complexity == DocumentComplexity.SIMPLE:
            reasons.append("Appropriate for simple document structure")
            
        # Priority-based reasons
        if quality_priority:
            reasons.append("Prioritized for maximum accuracy")
        elif speed_priority:
            reasons.append("Optimized for fast processing")
            
        return "; ".join(reasons) if reasons else "Best overall match for requirements"
        
    def _estimate_processing_time(self, model: ModelCapabilities,
                                complexity: DocumentComplexity) -> float:
        """Estimate processing time for the model."""
        base_time = 1.0 / model.processing_speed  # seconds per page
        
        # Adjust for complexity
        complexity_multipliers = {
            DocumentComplexity.SIMPLE: 0.8,
            DocumentComplexity.MODERATE: 1.0,
            DocumentComplexity.COMPLEX: 1.5,
            DocumentComplexity.HIGHLY_COMPLEX: 2.5
        }
        
        multiplier = complexity_multipliers[complexity]
        estimated_time = base_time * multiplier
        
        return round(estimated_time, 2)
        
    def _get_fallback_models(self, primary_model: ModelType) -> List[ModelType]:
        """Get fallback models for the primary selection."""
        fallback_hierarchy = {
            ModelType.QUANTUM_ENHANCED: [ModelType.LEGAL_SPECIALIST, ModelType.MULTIMODAL_FUSION],
            ModelType.LEGAL_SPECIALIST: [ModelType.MULTIMODAL_FUSION, ModelType.VISION_LANGUAGE],
            ModelType.MULTIMODAL_FUSION: [ModelType.VISION_LANGUAGE, ModelType.NLP_TRANSFORMER],
            ModelType.VISION_LANGUAGE: [ModelType.NLP_TRANSFORMER, ModelType.OCR_ADVANCED],
            ModelType.NEUROMORPHIC: [ModelType.VISION_LANGUAGE, ModelType.OCR_ADVANCED],
            ModelType.NLP_TRANSFORMER: [ModelType.OCR_ADVANCED, ModelType.OCR_LIGHTWEIGHT],
            ModelType.OCR_ADVANCED: [ModelType.OCR_LIGHTWEIGHT],
            ModelType.OCR_LIGHTWEIGHT: []
        }
        
        return fallback_hierarchy.get(primary_model, [ModelType.OCR_ADVANCED])
        
    def _create_fallback_selection(self) -> ModelSelection:
        """Create fallback selection when no models are compatible."""
        return ModelSelection(
            model_type=ModelType.OCR_LIGHTWEIGHT,
            confidence=0.5,
            reasoning="Fallback to basic OCR due to compatibility constraints",
            fallback_models=[],
            estimated_processing_time=2.0,
            estimated_accuracy=0.75,
            resource_requirements={
                'memory_mb': 128,
                'processing_speed': 15.0,
                'specialized_features': ['basic_ocr']
            }
        )
        
    def update_performance_history(self, model_type: ModelType,
                                 actual_accuracy: float,
                                 actual_processing_time: float):
        """Update performance history for model selection improvement."""
        if model_type not in self.performance_history:
            self.performance_history[model_type] = {
                'accuracies': [],
                'processing_times': [],
                'usage_count': 0
            }
            
        history = self.performance_history[model_type]
        history['accuracies'].append(actual_accuracy)
        history['processing_times'].append(actual_processing_time)
        history['usage_count'] += 1
        
        # Keep only recent history (last 100 runs)
        if len(history['accuracies']) > 100:
            history['accuracies'] = history['accuracies'][-100:]
            history['processing_times'] = history['processing_times'][-100:]
            
        logger.debug("Updated performance history for %s: avg_accuracy=%.3f, avg_time=%.2fs",
                    model_type.value,
                    sum(history['accuracies']) / len(history['accuracies']),
                    sum(history['processing_times']) / len(history['processing_times']))
                    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get recommendations based on performance history."""
        recommendations = {
            'best_accuracy_model': None,
            'fastest_model': None,
            'most_reliable_model': None,
            'underutilized_models': [],
            'performance_summary': {}
        }
        
        if not self.performance_history:
            return recommendations
            
        # Analyze performance data
        model_stats = {}
        for model_type, history in self.performance_history.items():
            if history['usage_count'] > 0:
                avg_accuracy = sum(history['accuracies']) / len(history['accuracies'])
                avg_time = sum(history['processing_times']) / len(history['processing_times'])
                
                model_stats[model_type] = {
                    'avg_accuracy': avg_accuracy,
                    'avg_processing_time': avg_time,
                    'usage_count': history['usage_count']
                }
                
        if model_stats:
            # Find best models
            recommendations['best_accuracy_model'] = max(
                model_stats.keys(), 
                key=lambda k: model_stats[k]['avg_accuracy']
            ).value
            
            recommendations['fastest_model'] = min(
                model_stats.keys(),
                key=lambda k: model_stats[k]['avg_processing_time']
            ).value
            
            # Find underutilized models (low usage count)
            avg_usage = sum(stats['usage_count'] for stats in model_stats.values()) / len(model_stats)
            recommendations['underutilized_models'] = [
                model_type.value for model_type, stats in model_stats.items()
                if stats['usage_count'] < avg_usage * 0.5
            ]
            
        recommendations['performance_summary'] = {
            model_type.value: stats for model_type, stats in model_stats.items()
        }
        
        return recommendations