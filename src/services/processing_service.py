"""Core processing service that orchestrates the contract extraction pipeline."""

from __future__ import annotations

import logging
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from ..models.contract import Contract
from ..models.processing import ProcessingResult, ProcessingStage, ProcessingStatus
from .extraction_service import ExtractionService
from .validation_service import ValidationService

logger = logging.getLogger(__name__)


class ProcessingService:
    """Main service that orchestrates the complete contract processing pipeline."""

    def __init__(self):
        """Initialize the processing service with required components."""
        self.validation_service = ValidationService()
        self.extraction_service = ExtractionService()

    def process_document(self, file_path: Path, config: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process a contract document through the complete pipeline.
        
        Args:
            file_path: Path to the document to process
            config: Optional configuration overrides
            
        Returns:
            ProcessingResult with complete processing information
        """
        result = ProcessingResult(
            document_path=str(file_path),
            processing_config=config or {}
        )

        try:
            logger.info(f"Starting document processing for {file_path}")
            result.set_status(ProcessingStatus.IN_PROGRESS)

            # Stage 1: Document Validation
            result.current_stage = ProcessingStage.VALIDATION
            if not self._validate_document(file_path, result):
                return result

            # Stage 2: Document Preprocessing
            result.current_stage = ProcessingStage.PREPROCESSING
            if not self._preprocess_document(file_path, result):
                return result

            # Stage 3: OCR Text Extraction
            result.current_stage = ProcessingStage.OCR_EXTRACTION
            extracted_text = self._extract_text(file_path, result)
            if not extracted_text:
                return result

            # Stage 4: Clause Detection and Classification
            result.current_stage = ProcessingStage.CLAUSE_DETECTION
            clauses = self._detect_clauses(file_path, result)
            if clauses is None:
                return result

            # Stage 5: Entity Extraction
            result.current_stage = ProcessingStage.ENTITY_EXTRACTION
            entities = self._extract_entities(clauses, result)

            # Stage 6: Contract Assembly
            result.current_stage = ProcessingStage.VALIDATION_FINAL
            contract = self._assemble_contract(file_path, clauses, entities, result)
            if not contract:
                return result

            # Stage 7: Final Serialization
            result.current_stage = ProcessingStage.SERIALIZATION
            extracted_data = self._serialize_results(contract, result)

            # Finalize results
            result.contract = contract
            result.extracted_data = extracted_data
            result.metrics.calculate_overall_confidence()
            result.set_status(ProcessingStatus.COMPLETED)

            logger.info(f"Document processing completed successfully for {file_path}")
            return result

        except Exception as e:
            logger.exception(f"Processing failed for {file_path}: {str(e)}")
            result.add_error(
                stage=result.current_stage,
                error_type=type(e).__name__,
                message=str(e),
                stack_trace=traceback.format_exc(),
                recoverable=False
            )
            result.set_status(ProcessingStatus.FAILED)
            return result

    def _validate_document(self, file_path: Path, result: ProcessingResult) -> bool:
        """Validate the input document."""
        start_time = time.perf_counter()

        try:
            validation_result = self.validation_service.validate_document(file_path)
            result.validation = validation_result

            if not validation_result.is_valid:
                result.add_error(
                    stage=ProcessingStage.VALIDATION,
                    error_type="ValidationError",
                    message=f"Document validation failed: {'; '.join(validation_result.errors)}",
                    recoverable=False
                )
                return False

            # Update metrics
            if validation_result.pages_detected:
                result.metrics.pages_processed = validation_result.pages_detected

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.VALIDATION, stage_time)

            logger.debug(f"Document validation completed in {stage_time:.2f}s")
            return True

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.VALIDATION,
                error_type=type(e).__name__,
                message=f"Validation stage failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=False
            )
            return False

    def _preprocess_document(self, file_path: Path, result: ProcessingResult) -> bool:
        """Preprocess the document for optimal extraction."""
        start_time = time.perf_counter()

        try:
            # Document preprocessing (image enhancement, format conversion)
            # This is where we would implement image enhancement, noise reduction, etc.
            logger.debug("Preprocessing document for optimal extraction")

            # Simulate preprocessing work
            time.sleep(0.1)  # Placeholder for actual preprocessing

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.PREPROCESSING, stage_time)

            logger.debug(f"Document preprocessing completed in {stage_time:.2f}s")
            return True

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.PREPROCESSING,
                error_type=type(e).__name__,
                message=f"Preprocessing stage failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=True  # Preprocessing failures might be recoverable
            )
            return False

    def _extract_text(self, file_path: Path, result: ProcessingResult) -> Optional[str]:
        """Extract text content from the document using OCR."""
        start_time = time.perf_counter()

        try:
            # Use the existing extraction service
            extracted_text = self.extraction_service.extract_text_from_document(file_path)

            if not extracted_text:
                result.add_error(
                    stage=ProcessingStage.OCR_EXTRACTION,
                    error_type="ExtractionError",
                    message="No text could be extracted from document",
                    recoverable=False
                )
                return None

            # Update metrics
            result.metrics.text_extracted_chars = len(extracted_text)
            result.metrics.ocr_confidence = self.extraction_service.get_last_ocr_confidence()

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.OCR_EXTRACTION, stage_time)

            logger.debug(f"Text extraction completed in {stage_time:.2f}s, extracted {len(extracted_text)} characters")
            return extracted_text

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.OCR_EXTRACTION,
                error_type=type(e).__name__,
                message=f"Text extraction failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=False
            )
            return None

    def _detect_clauses(self, file_path: Path, result: ProcessingResult) -> Optional[list]:
        """Detect and classify clauses in the document."""
        start_time = time.perf_counter()

        try:
            # Use the existing extraction service for clause detection
            clauses = self.extraction_service.detect_clauses_from_document(file_path)

            if not clauses:
                logger.warning(f"No clauses detected in {file_path}")
                clauses = []  # Empty list is valid, not an error

            # Update metrics
            result.metrics.clauses_detected = len(clauses)
            if clauses:
                # Calculate average clause confidence
                confidences = [clause.confidence for clause in clauses if hasattr(clause, 'confidence')]
                if confidences:
                    result.metrics.clause_detection_confidence = sum(confidences) / len(confidences)

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.CLAUSE_DETECTION, stage_time)

            logger.debug(f"Clause detection completed in {stage_time:.2f}s, found {len(clauses)} clauses")
            return clauses

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.CLAUSE_DETECTION,
                error_type=type(e).__name__,
                message=f"Clause detection failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=False
            )
            return None

    def _extract_entities(self, clauses: list, result: ProcessingResult) -> Dict[str, Any]:
        """Extract named entities and relationships from clauses."""
        start_time = time.perf_counter()

        try:
            entities = {
                'parties': [],
                'dates': [],
                'amounts': [],
                'locations': [],
                'organizations': []
            }

            # Extract entities from each clause
            total_entities = 0
            for clause in clauses:
                if hasattr(clause, 'entities') and clause.entities:
                    for entity_type, entity_list in clause.entities.items():
                        if entity_type in entities:
                            entities[entity_type].extend(entity_list)
                            total_entities += len(entity_list)

            # Remove duplicates
            for entity_type in entities:
                entities[entity_type] = list(set(entities[entity_type]))

            result.metrics.entities_extracted = total_entities

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.ENTITY_EXTRACTION, stage_time)

            logger.debug(f"Entity extraction completed in {stage_time:.2f}s, found {total_entities} entities")
            return entities

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.ENTITY_EXTRACTION,
                error_type=type(e).__name__,
                message=f"Entity extraction failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=True  # Can continue without entity extraction
            )
            return {}

    def _assemble_contract(self, file_path: Path, clauses: list, entities: Dict[str, Any],
                          result: ProcessingResult) -> Optional[Contract]:
        """Assemble the final Contract object from extracted components."""
        start_time = time.perf_counter()

        try:
            # Create contract with basic metadata
            contract = Contract(
                filename=file_path.name,
                pages=result.metrics.pages_processed,
                file_size_bytes=file_path.stat().st_size if file_path.exists() else None,
                processing_time_seconds=result.metrics.total_time_seconds,
                overall_confidence=result.metrics.overall_confidence,
                clauses=clauses,
            )

            # Add parties from entities
            if entities.get('parties'):
                for party_name in entities['parties'][:5]:  # Limit to first 5 parties
                    try:
                        from ..models.contract import ContractParty
                        party = ContractParty(name=party_name, role="party")
                        contract.add_party(party)
                    except Exception as party_error:
                        logger.warning(f"Failed to add party {party_name}: {party_error}")

            # Classify contract type based on clauses
            contract.contract_type = contract.classify_contract_type()

            # Extract key terms
            contract.key_terms = contract.extract_financial_terms()

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.VALIDATION_FINAL, stage_time)

            logger.debug(f"Contract assembly completed in {stage_time:.2f}s")
            return contract

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.VALIDATION_FINAL,
                error_type=type(e).__name__,
                message=f"Contract assembly failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=False
            )
            return None

    def _serialize_results(self, contract: Contract, result: ProcessingResult) -> Dict[str, Any]:
        """Serialize the final results to the standard output format."""
        start_time = time.perf_counter()

        try:
            # Convert to the documented JSON format
            extracted_data = {
                "document_info": {
                    "filename": contract.filename,
                    "pages": contract.pages,
                    "processing_time": round(contract.processing_time_seconds, 2),
                    "overall_confidence": round(contract.overall_confidence, 2),
                    "document_type": contract.contract_type.value,
                },
                "parties": [party.to_dict() for party in contract.parties],
                "clauses": [
                    clause.to_dict() if hasattr(clause, 'to_dict') else {
                        "id": getattr(clause, 'id', f"clause_{i:03d}"),
                        "type": getattr(clause, 'type', 'unknown'),
                        "text": getattr(clause, 'text', str(clause)),
                        "page": getattr(clause, 'page', 1),
                        "coordinates": getattr(clause, 'coordinates', []),
                        "confidence": getattr(clause, 'confidence', 0.0),
                    }
                    for i, clause in enumerate(contract.clauses, 1)
                ],
                "metadata": {
                    "extraction_timestamp": result.started_at.isoformat(),
                    "model_version": "v0.1.0-enhanced",
                    "processing_method": "enhanced_multimodal_pipeline",
                },
                "key_terms": contract.key_terms,
                "contract_summary": contract.get_summary(),
            }

            stage_time = time.perf_counter() - start_time
            result.metrics.add_stage_time(ProcessingStage.SERIALIZATION, stage_time)

            logger.debug(f"Results serialization completed in {stage_time:.2f}s")
            return extracted_data

        except Exception as e:
            result.add_error(
                stage=ProcessingStage.SERIALIZATION,
                error_type=type(e).__name__,
                message=f"Results serialization failed: {str(e)}",
                stack_trace=traceback.format_exc(),
                recoverable=True  # Can provide partial results
            )
            return {"error": "Serialization failed", "partial_contract": str(contract)}

    def get_processing_status(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a processing operation."""
        # This would typically query a database or cache
        # For now, return a placeholder
        return {
            "id": result_id,
            "status": "not_implemented",
            "message": "Status tracking not yet implemented"
        }

    def cancel_processing(self, result_id: str) -> bool:
        """Cancel an in-progress processing operation."""
        # This would typically signal a background task to stop
        # For now, return False to indicate not implemented
        logger.warning(f"Processing cancellation not implemented for {result_id}")
        return False
