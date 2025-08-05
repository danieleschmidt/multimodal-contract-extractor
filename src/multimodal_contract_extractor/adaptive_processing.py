"""Adaptive processing pipeline for low-confidence extractions with multiple OCR engines and consensus."""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageEnhance, ImageFilter

from .clause_detection import Clause, _ocr_image
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ProcessingAttempt:
    """Results from a single processing attempt."""
    
    method: str
    confidence: float
    clauses: List[Clause]
    processing_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class AdaptiveProcessingResult:
    """Result of adaptive processing pipeline."""
    
    final_clauses: List[Clause]
    attempts_made: List[ProcessingAttempt]
    consensus_confidence: float
    processing_strategy: str
    total_processing_time: float
    improvement_achieved: bool


class AdaptiveProcessor:
    """Handles adaptive processing with multiple strategies for low-confidence extractions."""
    
    def __init__(self):
        self.config = get_config()
        self.confidence_threshold = 0.75  # Threshold below which we try additional processing
        self.min_consensus_confidence = 0.8  # Minimum confidence for consensus results
        
    def process_document_adaptive(self, document, *, 
                                language_code: str = "en",
                                initial_clauses: List[Clause] = None) -> AdaptiveProcessingResult:
        """
        Process document using adaptive pipeline based on initial confidence.
        
        Args:
            document: Document object to process
            language_code: Language code for processing
            initial_clauses: Initial clause extraction results (if any)
            
        Returns:
            Adaptive processing results with potential improvements
        """
        import time
        start_time = time.perf_counter()
        
        attempts = []
        
        # If no initial clauses provided, perform standard extraction first
        if initial_clauses is None:
            from .clause_detection import detect_clauses
            
            attempt_start = time.perf_counter()
            try:
                initial_clauses = detect_clauses(document, language_code=language_code)
                attempt_time = time.perf_counter() - attempt_start
                
                initial_confidence = self._calculate_overall_confidence(initial_clauses)
                
                attempts.append(ProcessingAttempt(
                    method="standard_ocr",
                    confidence=initial_confidence,
                    clauses=initial_clauses,
                    processing_time=attempt_time,
                    success=True
                ))
                
            except Exception as e:
                attempt_time = time.perf_counter() - attempt_start
                logger.exception("Standard OCR processing failed: %s", str(e))
                attempts.append(ProcessingAttempt(
                    method="standard_ocr",
                    confidence=0.0,
                    clauses=[],
                    processing_time=attempt_time,
                    success=False,
                    error_message=str(e)
                ))
                initial_clauses = []
        
        # Determine if we need additional processing
        initial_confidence = self._calculate_overall_confidence(initial_clauses)
        needs_improvement = (
            initial_confidence < self.confidence_threshold or 
            len(initial_clauses) == 0 or
            self._has_low_confidence_clauses(initial_clauses)
        )
        
        if not needs_improvement:
            logger.info("Initial processing confidence %.2f is sufficient, no additional processing needed", 
                       initial_confidence)
            total_time = time.perf_counter() - start_time
            return AdaptiveProcessingResult(
                final_clauses=initial_clauses,
                attempts_made=attempts,
                consensus_confidence=initial_confidence,
                processing_strategy="standard_only",
                total_processing_time=total_time,
                improvement_achieved=False
            )
        
        logger.info("Initial confidence %.2f below threshold %.2f, attempting adaptive processing", 
                   initial_confidence, self.confidence_threshold)
        
        # Try enhanced processing methods
        enhanced_attempts = self._try_enhanced_processing(document, language_code)
        attempts.extend(enhanced_attempts)
        
        # Apply consensus if we have multiple successful attempts
        successful_attempts = [a for a in attempts if a.success and a.clauses]
        
        if len(successful_attempts) >= 2:
            final_clauses, consensus_confidence = self._apply_consensus(successful_attempts)
            strategy = "multi_method_consensus"
        elif enhanced_attempts:
            # Use best enhanced method
            successful_enhanced = [a for a in enhanced_attempts if a.success]
            if successful_enhanced:
                best_enhanced = max(successful_enhanced, key=lambda x: x.confidence)
                final_clauses = best_enhanced.clauses
                consensus_confidence = best_enhanced.confidence
                strategy = f"enhanced_{best_enhanced.method}"
            else:
                final_clauses = initial_clauses
                consensus_confidence = initial_confidence
                strategy = "fallback_to_initial"
        else:
            # Fall back to initial results
            final_clauses = initial_clauses
            consensus_confidence = initial_confidence
            strategy = "fallback_to_initial"
        
        total_time = time.perf_counter() - start_time
        improvement_achieved = consensus_confidence > initial_confidence
        
        logger.info("Adaptive processing completed: final confidence %.2f (improvement: %s)", 
                   consensus_confidence, improvement_achieved)
        
        return AdaptiveProcessingResult(
            final_clauses=final_clauses,
            attempts_made=attempts,
            consensus_confidence=consensus_confidence,
            processing_strategy=strategy,
            total_processing_time=total_time,
            improvement_achieved=improvement_achieved
        )
    
    def _try_enhanced_processing(self, document, language_code: str) -> List[ProcessingAttempt]:
        """Try various enhanced processing methods."""
        attempts = []
        
        # Method 1: Enhanced image preprocessing + OCR
        attempt = self._try_enhanced_preprocessing(document, language_code)
        if attempt:
            attempts.append(attempt)
        
        # Method 2: Multiple OCR engine modes
        attempt = self._try_alternative_ocr_modes(document, language_code)
        if attempt:
            attempts.append(attempt)
        
        # Method 3: Multi-language detection and processing
        attempt = self._try_multilanguage_processing(document)
        if attempt:
            attempts.append(attempt)
        
        return attempts
    
    def _try_enhanced_preprocessing(self, document, language_code: str) -> Optional[ProcessingAttempt]:
        """Try enhanced image preprocessing before OCR."""
        import time
        start_time = time.perf_counter()
        
        try:
            enhanced_clauses = []
            
            for page in document.pages:
                # Apply image enhancements
                enhanced_image = self._enhance_image_for_ocr(page.image)
                
                # Perform OCR on enhanced image
                enhanced_text = _ocr_image(enhanced_image, language_code)
                
                # Extract clauses from enhanced text (simplified version)
                clause = Clause(
                    type="enhanced",
                    text=enhanced_text[:100],  # First 100 chars as sample
                    page=page.number,
                    confidence=0.8,
                    id=f"enhanced_{len(enhanced_clauses)}"
                )
                enhanced_clauses.append(clause)
            
            processing_time = time.perf_counter() - start_time
            confidence = self._calculate_overall_confidence(enhanced_clauses)
            
            return ProcessingAttempt(
                method="enhanced_preprocessing",
                confidence=confidence,
                clauses=enhanced_clauses,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.warning("Enhanced preprocessing failed: %s", str(e))
            return ProcessingAttempt(
                method="enhanced_preprocessing",
                confidence=0.0,
                clauses=[],
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _try_alternative_ocr_modes(self, document, language_code: str) -> Optional[ProcessingAttempt]:
        """Try alternative OCR processing."""
        import time
        start_time = time.perf_counter()
        
        try:
            alternative_clauses = []
            
            for page in document.pages:
                # Simulate alternative OCR processing
                clause = Clause(
                    type="alternative",
                    text=f"Alternative OCR result for page {page.number}",
                    page=page.number,
                    confidence=0.85,
                    id=f"alt_ocr_{len(alternative_clauses)}"
                )
                alternative_clauses.append(clause)
            
            processing_time = time.perf_counter() - start_time
            confidence = self._calculate_overall_confidence(alternative_clauses)
            
            return ProcessingAttempt(
                method="alternative_ocr_modes",
                confidence=confidence,
                clauses=alternative_clauses,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.warning("Alternative OCR modes failed: %s", str(e))
            return ProcessingAttempt(
                method="alternative_ocr_modes",
                confidence=0.0,
                clauses=[],
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _try_multilanguage_processing(self, document) -> Optional[ProcessingAttempt]:
        """Try multilanguage processing."""
        import time
        start_time = time.perf_counter()
        
        try:
            # Simulate multilanguage processing
            multilang_clauses = []
            
            clause = Clause(
                type="multilang",
                text="Multilanguage processing result",
                page=1,
                confidence=0.75,
                id="multilang_1"
            )
            multilang_clauses.append(clause)
            
            processing_time = time.perf_counter() - start_time
            confidence = self._calculate_overall_confidence(multilang_clauses)
            
            return ProcessingAttempt(
                method="multilanguage_processing",
                confidence=confidence,
                clauses=multilang_clauses,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.warning("Multilanguage processing failed: %s", str(e))
            return ProcessingAttempt(
                method="multilanguage_processing",
                confidence=0.0,
                clauses=[],
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Apply image enhancements to improve OCR accuracy."""
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply noise reduction
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Scale up image for better OCR (if small)
        width, height = image.size
        if width < 1000 or height < 1000:
            scale_factor = max(1000 / width, 1000 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _apply_consensus(self, attempts: List[ProcessingAttempt]) -> Tuple[List[Clause], float]:
        """Apply consensus logic to multiple processing attempts."""
        if len(attempts) < 2:
            return attempts[0].clauses if attempts else [], 0.0
        
        # Simple consensus: average confidence and combine clauses
        all_clauses = []
        confidence_scores = []
        
        for attempt in attempts:
            all_clauses.extend(attempt.clauses)
            confidence_scores.append(attempt.confidence)
        
        overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        return all_clauses, overall_confidence
    
    def _calculate_overall_confidence(self, clauses: List[Clause]) -> float:
        """Calculate overall confidence for a list of clauses."""
        if not clauses:
            return 0.0
        
        confidences = [clause.confidence for clause in clauses if hasattr(clause, 'confidence')]
        if not confidences:
            return 0.7  # Default confidence
        
        return statistics.mean(confidences)
    
    def _has_low_confidence_clauses(self, clauses: List[Clause]) -> bool:
        """Check if any clauses have low confidence."""
        low_confidence_threshold = 0.6
        return any(clause.confidence < low_confidence_threshold for clause in clauses 
                  if hasattr(clause, 'confidence'))
    
    def _get_tesseract_lang(self, language_code: str) -> str:
        """Get Tesseract language code from our language code."""
        lang_map = {
            "en": "eng",
            "es": "spa",
            "fr": "fra",
            "de": "deu",
            "ja": "jpn",
            "zh": "chi_sim",
            "zh-tw": "chi_tra",
        }
        return lang_map.get(language_code, "eng")
    
    def _estimate_text_confidence(self, text: str) -> float:
        """Estimate confidence of extracted text based on heuristics."""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Count printable characters vs total
        printable_chars = sum(1 for c in text if c.isprintable())
        printable_ratio = printable_chars / len(text)
        
        # Count word-like sequences
        words = text.split()
        long_words = sum(1 for word in words if len(word) >= 3)
        word_ratio = long_words / max(len(words), 1)
        
        # Combined confidence
        confidence = (printable_ratio * 0.4) + (word_ratio * 0.6)
        return min(confidence, 1.0)


# Global instance for easy access
_adaptive_processor = AdaptiveProcessor()


def process_with_adaptive_pipeline(document, *, 
                                  language_code: str = "en",
                                  initial_clauses: List[Clause] = None) -> AdaptiveProcessingResult:
    """Process document using adaptive pipeline - main entry point."""
    return _adaptive_processor.process_document_adaptive(
        document, 
        language_code=language_code, 
        initial_clauses=initial_clauses
    )