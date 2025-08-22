"""Real-time streaming processing for large documents.

Generation 1 Enhanced Feature: Enables processing of large contracts
in real-time with memory optimization and adaptive chunking.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Iterator

from .config import get_config
from .document import Document, DocumentPage

logger = logging.getLogger(__name__)


class StreamingMode(Enum):
    """Streaming processing modes."""
    ADAPTIVE = "adaptive"  # Adjust chunk size based on content
    FIXED = "fixed"        # Use fixed chunk size
    MEMORY_OPTIMIZED = "memory_optimized"  # Optimize for memory usage


@dataclass
class StreamingMetrics:
    """Metrics for streaming processing."""
    chunks_processed: int = 0
    total_processing_time: float = 0.0
    memory_peak_mb: float = 0.0
    throughput_pages_per_second: float = 0.0


class StreamingProcessor:
    """Real-time streaming processor for large documents."""
    
    def __init__(self, mode: StreamingMode = StreamingMode.ADAPTIVE, 
                 chunk_size: int = 5):
        """Initialize streaming processor.
        
        Args:
            mode: Streaming processing mode
            chunk_size: Initial chunk size for processing
        """
        self.mode = mode
        self.chunk_size = chunk_size
        self.chunks_processed = 0
        self.start_time = 0.0
        self.metrics = StreamingMetrics()
        
        config = get_config()
        self.max_memory_mb = getattr(config.extraction, 'max_memory_mb', 512)
        self.adaptive_threshold = getattr(config.extraction, 'adaptive_threshold', 0.8)
        
    def load_document(self, file_path: Path) -> Document:
        """Load document using streaming approach.
        
        Args:
            file_path: Path to document
            
        Returns:
            Document with streaming-optimized pages
        """
        self.start_time = time.perf_counter()
        
        try:
            if self.mode == StreamingMode.ADAPTIVE:
                return self._load_adaptive(file_path)
            elif self.mode == StreamingMode.MEMORY_OPTIMIZED:
                return self._load_memory_optimized(file_path)
            else:
                return self._load_fixed(file_path)
        finally:
            self.metrics.total_processing_time = time.perf_counter() - self.start_time
            
    def _load_adaptive(self, file_path: Path) -> Document:
        """Load document with adaptive chunk sizing."""
        pages = []
        current_chunk_size = self.chunk_size
        
        for page_batch in self._stream_pages(file_path, current_chunk_size):
            # Monitor processing time to adjust chunk size
            batch_start = time.perf_counter()
            processed_pages = self._process_page_batch(page_batch)
            batch_time = time.perf_counter() - batch_start
            
            pages.extend(processed_pages)
            self.chunks_processed += 1
            
            # Adaptive adjustment based on processing time
            if batch_time > 2.0 and current_chunk_size > 1:
                current_chunk_size = max(1, current_chunk_size - 1)
                logger.debug("Reduced chunk size to %d due to slow processing", current_chunk_size)
            elif batch_time < 0.5 and current_chunk_size < 10:
                current_chunk_size += 1
                logger.debug("Increased chunk size to %d due to fast processing", current_chunk_size)
                
        return Document(path=file_path, pages=pages)
        
    def _load_memory_optimized(self, file_path: Path) -> Document:
        """Load document with memory optimization."""
        import psutil
        process = psutil.Process()
        
        pages = []
        for page_batch in self._stream_pages(file_path, self.chunk_size):
            # Check memory usage before processing
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics.memory_peak_mb = max(self.metrics.memory_peak_mb, memory_mb)
            
            if memory_mb > self.max_memory_mb * self.adaptive_threshold:
                # Force garbage collection if memory is high
                import gc
                gc.collect()
                logger.warning("Memory usage high (%.1f MB), triggered GC", memory_mb)
            
            processed_pages = self._process_page_batch(page_batch)
            pages.extend(processed_pages)
            self.chunks_processed += 1
            
        return Document(path=file_path, pages=pages)
        
    def _load_fixed(self, file_path: Path) -> Document:
        """Load document with fixed chunk size."""
        pages = []
        for page_batch in self._stream_pages(file_path, self.chunk_size):
            processed_pages = self._process_page_batch(page_batch)
            pages.extend(processed_pages)
            self.chunks_processed += 1
            
        return Document(path=file_path, pages=pages)
        
    def _stream_pages(self, file_path: Path, chunk_size: int) -> Iterator[list[DocumentPage]]:
        """Stream document pages in chunks."""
        from .document import stream_document
        
        current_batch = []
        for page in stream_document(file_path, chunk_size=1):  # Stream one page at a time
            current_batch.append(page)
            
            if len(current_batch) >= chunk_size:
                yield current_batch
                current_batch = []
                
        # Yield remaining pages
        if current_batch:
            yield current_batch
            
    def _process_page_batch(self, pages: list[DocumentPage]) -> list[DocumentPage]:
        """Process a batch of pages with streaming optimizations."""
        processed_pages = []
        
        for page in pages:
            # Apply streaming-specific optimizations
            optimized_page = self._optimize_page_for_streaming(page)
            processed_pages.append(optimized_page)
            
        return processed_pages
        
    def _optimize_page_for_streaming(self, page: DocumentPage) -> DocumentPage:
        """Optimize a single page for streaming processing."""
        # Implement streaming-specific optimizations
        # Such as text compression, image optimization, etc.
        
        # For now, return the page as-is
        # Future enhancements could include:
        # - Text compression for large text blocks
        # - Image downsampling for memory efficiency
        # - Lazy loading of page content
        
        return page
        
    async def stream_extract_async(self, file_path: Path) -> AsyncIterator[dict]:
        """Asynchronously stream extraction results."""
        document = self.load_document(file_path)
        
        for i, page in enumerate(document.pages):
            # Simulate async processing
            await asyncio.sleep(0.01)  # Yield control
            
            # Extract from single page
            page_result = {
                "page_number": i + 1,
                "text_content": page.text if hasattr(page, 'text') else "",
                "processing_timestamp": time.time(),
                "streaming_chunk": self.chunks_processed
            }
            
            yield page_result
            
    def get_memory_efficiency(self) -> float:
        """Calculate memory efficiency score."""
        if self.metrics.memory_peak_mb == 0:
            return 1.0
            
        # Calculate efficiency as inverse of peak memory usage
        efficiency = min(1.0, 100.0 / self.metrics.memory_peak_mb)
        return round(efficiency, 3)
        
    def get_processing_speed(self) -> float:
        """Calculate processing speed in pages per second."""
        if self.metrics.total_processing_time == 0:
            return 0.0
            
        # Estimate pages processed (chunks * average chunk size)
        estimated_pages = self.chunks_processed * self.chunk_size
        speed = estimated_pages / self.metrics.total_processing_time
        return round(speed, 2)
        
    def get_throughput_metrics(self) -> dict:
        """Get comprehensive throughput metrics."""
        return {
            "chunks_processed": self.chunks_processed,
            "total_processing_time": round(self.metrics.total_processing_time, 2),
            "memory_peak_mb": round(self.metrics.memory_peak_mb, 2),
            "memory_efficiency": self.get_memory_efficiency(),
            "processing_speed_pages_per_sec": self.get_processing_speed(),
            "mode": self.mode.value,
            "adaptive_chunk_size": self.chunk_size
        }


class RealTimeContractProcessor:
    """Real-time contract processing with live updates."""
    
    def __init__(self):
        """Initialize real-time processor."""
        self.streaming_processor = StreamingProcessor(mode=StreamingMode.ADAPTIVE)
        self.active_sessions = {}
        
    async def process_contract_realtime(self, file_path: Path, 
                                      session_id: str) -> AsyncIterator[dict]:
        """Process contract in real-time with live updates.
        
        Args:
            file_path: Path to contract file
            session_id: Unique session identifier
            
        Yields:
            Real-time processing updates
        """
        self.active_sessions[session_id] = {
            "start_time": time.time(),
            "status": "processing",
            "file_path": str(file_path)
        }
        
        try:
            async for page_result in self.streaming_processor.stream_extract_async(file_path):
                # Add session context
                page_result["session_id"] = session_id
                page_result["status"] = "page_processed"
                
                # Update session progress
                self.active_sessions[session_id]["last_update"] = time.time()
                
                yield page_result
                
            # Final result
            yield {
                "session_id": session_id,
                "status": "completed",
                "throughput_metrics": self.streaming_processor.get_throughput_metrics(),
                "completion_time": time.time()
            }
            
        except Exception as e:
            yield {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
                "error_time": time.time()
            }
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                
    def get_active_sessions(self) -> dict:
        """Get information about active processing sessions."""
        return dict(self.active_sessions)
        
    def cancel_session(self, session_id: str) -> bool:
        """Cancel an active processing session.
        
        Args:
            session_id: Session to cancel
            
        Returns:
            True if session was cancelled, False if not found
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False