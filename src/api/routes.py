"""API route registration and handlers."""

from __future__ import annotations

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..database import get_db_connection
from ..database.repositories import ContractRepository, ProcessingResultRepository
from ..models.contract import Contract, ContractType
from ..models.processing import ProcessingResult, ProcessingStatus
from ..services.processing_service import ProcessingService
from ..services.validation_service import ValidationService

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class ProcessingRequest(BaseModel):
    """Request model for document processing."""
    enable_ocr_cache: bool = Field(default=True, description="Enable OCR result caching")
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Minimum confidence threshold")
    extract_entities: bool = Field(default=True, description="Extract named entities from clauses")
    classify_risk: bool = Field(default=True, description="Perform risk level classification")


class ProcessingResponse(BaseModel):
    """Response model for document processing."""
    processing_id: str = Field(description="Unique processing request ID")
    status: str = Field(description="Current processing status")
    message: str = Field(description="Status message")
    estimated_completion: Optional[str] = Field(default=None, description="Estimated completion time")


class ContractSummary(BaseModel):
    """Contract summary for list responses."""
    id: str
    title: Optional[str]
    contract_type: str
    filename: Optional[str]
    pages: int
    overall_confidence: float
    processed_at: str
    parties_count: int
    clauses_count: int


class ProcessingStatusResponse(BaseModel):
    """Processing status response."""
    id: str
    status: str
    progress_percentage: float
    current_stage: str
    started_at: str
    completed_at: Optional[str]
    processing_time_seconds: Optional[float]
    error_message: Optional[str]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    database_status: str
    cache_status: str
    dependencies: dict


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""
    
    # Health and status endpoints
    @app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
    async def health_check():
        """Check API health and dependencies."""
        try:
            # Check database
            db = get_db_connection()
            db_stats = db.get_database_stats()
            db_status = "healthy" if "error" not in db_stats else "unhealthy"
            
            # Check cache (simplified)
            cache_status = "healthy"  # TODO: Implement actual cache health check
            
            return HealthCheckResponse(
                status="healthy",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                version="0.1.0",
                database_status=db_status,
                cache_status=cache_status,
                dependencies={
                    "tesseract": "available",  # TODO: Check actual availability
                    "pdf2image": "available",
                    "pillow": "available"
                }
            )
        except Exception as e:
            logger.exception("Health check failed")
            raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint."""
        # TODO: Implement actual Prometheus metrics
        return JSONResponse(content={
            "message": "Metrics endpoint - Prometheus integration pending",
            "placeholder_metrics": {
                "requests_total": 0,
                "processing_duration_seconds": 0,
                "active_processing_jobs": 0
            }
        })
    
    # Contract processing endpoints
    @app.post("/api/v1/process", response_model=ProcessingResponse, tags=["Processing"])
    async def process_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="Document file to process"),
        config: ProcessingRequest = Depends(),
    ):
        """
        Process a contract document and extract clauses.
        
        Accepts PDF files, images (PNG, JPEG, TIFF), and returns structured clause data.
        Processing happens asynchronously - use the returned processing_id to check status.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        try:
            # Initialize processing service
            processing_service = ProcessingService()
            
            # Start processing in background
            processing_config = {
                "enable_ocr_cache": config.enable_ocr_cache,
                "confidence_threshold": config.confidence_threshold,
                "extract_entities": config.extract_entities,
                "classify_risk": config.classify_risk,
            }
            
            # For now, process synchronously (in production, use background tasks)
            result = processing_service.process_document(temp_file_path, processing_config)
            
            # Save result to database
            result_repo = ProcessingResultRepository()
            result_repo.save(result)
            
            # Save contract if processing was successful
            if result.contract:
                contract_repo = ContractRepository()
                contract_repo.save(result.contract)
            
            return ProcessingResponse(
                processing_id=str(result.id),
                status=result.status.value,
                message="Processing completed" if result.is_successful() else "Processing failed",
                estimated_completion=None
            )
            
        except Exception as e:
            logger.exception(f"Error processing document {file.filename}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
    
    @app.get("/api/v1/process/{processing_id}/status", response_model=ProcessingStatusResponse, tags=["Processing"])
    async def get_processing_status(processing_id: str):
        """Get the status of a processing request."""
        try:
            result_repo = ProcessingResultRepository()
            result = result_repo.find_by_id(processing_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Processing request not found")
            
            # Calculate progress percentage
            progress = 0.0
            if result.status == ProcessingStatus.COMPLETED:
                progress = 100.0
            elif result.status == ProcessingStatus.FAILED:
                progress = result.get_success_rate() * 100
            elif result.status == ProcessingStatus.IN_PROGRESS:
                progress = len(result.metrics.stage_times) * 20  # Rough estimate
            
            return ProcessingStatusResponse(
                id=str(result.id),
                status=result.status.value,
                progress_percentage=progress,
                current_stage=result.current_stage.value,
                started_at=result.started_at.isoformat(),
                completed_at=result.completed_at.isoformat() if result.completed_at else None,
                processing_time_seconds=result.get_processing_time(),
                error_message=result.errors[0].message if result.errors else None
            )
            
        except Exception as e:
            logger.exception(f"Error getting status for {processing_id}")
            raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
    
    @app.get("/api/v1/process/{processing_id}/result", tags=["Processing"])
    async def get_processing_result(processing_id: str):
        """Get the full result of a completed processing request."""
        try:
            result_repo = ProcessingResultRepository()
            result = result_repo.find_by_id(processing_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Processing request not found")
            
            if result.status != ProcessingStatus.COMPLETED:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Processing not completed. Current status: {result.status.value}"
                )
            
            return result.extracted_data
            
        except Exception as e:
            logger.exception(f"Error getting result for {processing_id}")
            raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")
    
    # Contract management endpoints
    @app.get("/api/v1/contracts", response_model=List[ContractSummary], tags=["Contracts"])
    async def list_contracts(
        limit: int = 10,
        contract_type: Optional[str] = None,
        filename: Optional[str] = None
    ):
        """List contracts with optional filtering."""
        try:
            contract_repo = ContractRepository()
            
            if filename:
                contracts = contract_repo.find_by_filename(filename)
            elif contract_type:
                contracts = contract_repo.find_by_type(contract_type)
            else:
                contracts = contract_repo.find_recent(limit)
            
            return [
                ContractSummary(
                    id=str(contract.id),
                    title=contract.title,
                    contract_type=contract.contract_type.value,
                    filename=contract.filename,
                    pages=contract.pages,
                    overall_confidence=contract.overall_confidence,
                    processed_at=contract.processed_at.isoformat(),
                    parties_count=len(contract.parties),
                    clauses_count=len(contract.clauses)
                )
                for contract in contracts[:limit]
            ]
            
        except Exception as e:
            logger.exception("Error listing contracts")
            raise HTTPException(status_code=500, detail=f"Failed to list contracts: {str(e)}")
    
    @app.get("/api/v1/contracts/{contract_id}", tags=["Contracts"])
    async def get_contract(contract_id: str):
        """Get detailed information about a specific contract."""
        try:
            contract_repo = ContractRepository()
            contract = contract_repo.find_by_id(contract_id)
            
            if not contract:
                raise HTTPException(status_code=404, detail="Contract not found")
            
            return contract.to_dict()
            
        except Exception as e:
            logger.exception(f"Error getting contract {contract_id}")
            raise HTTPException(status_code=500, detail=f"Failed to get contract: {str(e)}")
    
    @app.delete("/api/v1/contracts/{contract_id}", tags=["Contracts"])
    async def delete_contract(contract_id: str):
        """Delete a contract and all associated data."""
        try:
            contract_repo = ContractRepository()
            success = contract_repo.delete(contract_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Contract not found")
            
            return {"message": "Contract deleted successfully"}
            
        except Exception as e:
            logger.exception(f"Error deleting contract {contract_id}")
            raise HTTPException(status_code=500, detail=f"Failed to delete contract: {str(e)}")
    
    # Statistics and analytics endpoints
    @app.get("/api/v1/stats", tags=["Analytics"])
    async def get_statistics():
        """Get system statistics and analytics."""
        try:
            contract_repo = ContractRepository()
            db = get_db_connection()
            
            contract_stats = contract_repo.get_statistics()
            db_stats = db.get_database_stats()
            
            return {
                "contracts": contract_stats,
                "database": db_stats,
                "processing": {
                    # TODO: Add processing statistics
                    "total_processed": contract_stats.get("total_contracts", 0),
                    "average_confidence": contract_stats.get("processing", {}).get("avg_confidence", 0)
                }
            }
            
        except Exception as e:
            logger.exception("Error getting statistics")
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
    
    # Validation endpoints
    @app.post("/api/v1/validate", tags=["Validation"])
    async def validate_document(file: UploadFile = File(...)):
        """Validate a document without processing it."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        try:
            validation_service = ValidationService()
            result = validation_service.validate_document(temp_file_path)
            
            return result.to_dict()
            
        except Exception as e:
            logger.exception(f"Error validating document {file.filename}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
    
    # System endpoints
    @app.get("/", tags=["System"])
    async def root():
        """API root endpoint with basic information."""
        return {
            "name": "Multimodal Contract Extractor API",
            "version": "0.1.0",
            "description": "AI-powered contract analysis and clause extraction",
            "docs_url": "/docs",
            "health_url": "/health",
            "api_base": "/api/v1"
        }
    
    logger.info("API routes registered successfully")