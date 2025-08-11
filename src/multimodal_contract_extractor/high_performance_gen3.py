"""High-performance optimizations for Generation 3 - scalability and performance."""

from __future__ import annotations

import asyncio
import logging
import multiprocessing as mp
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine
from pathlib import Path

import psutil

from .config import get_config
from .document import Document

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    peak_memory_usage: float = 0.0
    cpu_time_used: float = 0.0
    throughput_docs_per_second: float = 0.0
    concurrent_processes: int = 0
    queue_wait_time: float = 0.0
    cache_hit_rate: float = 0.0
    optimization_strategy: str = ""
    
    def update_metrics(self, processing_time: float, success: bool) -> None:
        """Update performance metrics."""
        self.total_documents += 1
        if success:
            self.successful_documents += 1
        else:
            self.failed_documents += 1
            
        self.total_processing_time += processing_time
        self.average_processing_time = self.total_processing_time / self.total_documents
        
        if self.total_processing_time > 0:
            self.throughput_docs_per_second = self.successful_documents / self.total_processing_time

class AdaptiveResourceManager:
    """Intelligent resource management for optimal performance."""
    
    def __init__(self):
        self.config = get_config()
        self.cpu_count = mp.cpu_count()
        self.available_memory = psutil.virtual_memory().total
        self.current_load = 0.0
        self.optimization_history: list[dict] = []
        
    def get_optimal_worker_count(self, task_type: str = "cpu_bound") -> int:
        """Determine optimal number of workers based on system state."""
        system_load = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().percent
        
        # Base worker count on task type
        if task_type == "cpu_bound":
            base_workers = max(1, self.cpu_count - 1)
        elif task_type == "io_bound":
            base_workers = min(32, self.cpu_count * 4)
        else:
            base_workers = self.cpu_count
            
        # Adjust based on current system load
        if system_load > 80:
            workers = max(1, base_workers // 2)
        elif system_load > 60:
            workers = max(1, int(base_workers * 0.75))
        elif system_load < 30:
            workers = min(base_workers * 2, 32)
        else:
            workers = base_workers
            
        # Adjust for memory constraints
        if memory_usage > 85:
            workers = max(1, workers // 2)
            
        logger.info("Optimal workers for %s: %d (load: %.1f%%, memory: %.1f%%)",
                   task_type, workers, system_load, memory_usage)
                   
        return workers
        
    def estimate_memory_requirement(self, file_path: Path) -> float:
        """Estimate memory requirement for processing a file."""
        try:
            file_size = file_path.stat().st_size
            # Rough estimation: 3-5x file size for processing
            estimated_memory = file_size * 4
            return estimated_memory
        except Exception:
            # Default estimation
            return 50 * 1024 * 1024  # 50MB default

class HighPerformanceProcessor:
    """High-performance document processing with adaptive optimization."""
    
    def __init__(self):
        self.config = get_config()
        self.resource_manager = AdaptiveResourceManager()
        self.metrics = PerformanceMetrics()
        self._process_pool: ProcessPoolExecutor | None = None
        self._thread_pool: ThreadPoolExecutor | None = None
        
    def __enter__(self):
        """Initialize processing pools."""
        optimal_processes = self.resource_manager.get_optimal_worker_count("cpu_bound")
        optimal_threads = self.resource_manager.get_optimal_worker_count("io_bound")
        
        self._process_pool = ProcessPoolExecutor(max_workers=optimal_processes)
        self._thread_pool = ThreadPoolExecutor(max_workers=optimal_threads)
        
        self.metrics.concurrent_processes = optimal_processes
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup processing pools."""
        if self._process_pool:
            self._process_pool.shutdown(wait=True)
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            
    async def process_documents_batch(self, 
                                    file_paths: list[Path], 
                                    batch_size: int = None) -> list[dict[str, Any]]:
        """Process multiple documents in optimized batches."""
        if batch_size is None:
            batch_size = self.resource_manager.get_optimal_worker_count("cpu_bound")
            
        results = []
        total_files = len(file_paths)
        
        logger.info("Processing %d documents in batches of %d", total_files, batch_size)
        
        # Process in batches to avoid memory overload
        for i in range(0, total_files, batch_size):
            batch = file_paths[i:i + batch_size]
            batch_results = await self._process_batch_parallel(batch)
            results.extend(batch_results)
            
            # Update metrics
            for result in batch_results:
                success = result.get('success', False)
                processing_time = result.get('processing_time', 0.0)
                self.metrics.update_metrics(processing_time, success)
                
            logger.info("Completed batch %d/%d (%.1f%% done)", 
                       (i // batch_size) + 1, 
                       (total_files + batch_size - 1) // batch_size,
                       ((i + len(batch)) / total_files) * 100)
                       
        return results
        
    async def _process_batch_parallel(self, file_paths: list[Path]) -> list[dict[str, Any]]:
        """Process a batch of files in parallel."""
        from .extraction import extract_from_document
        
        # Use asyncio for I/O bound operations
        tasks = []
        for file_path in file_paths:
            task = self._process_single_document(file_path, extract_from_document)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'file_path': str(file_paths[i]),
                    'success': False,
                    'error': str(result),
                    'processing_time': 0.0
                })
            else:
                processed_results.append(result)
                
        return processed_results
        
    async def _process_single_document(self, 
                                     file_path: Path, 
                                     extraction_func: Callable) -> dict[str, Any]:
        """Process a single document with performance tracking."""
        start_time = time.perf_counter()
        
        try:
            # Check memory requirements
            estimated_memory = self.resource_manager.estimate_memory_requirement(file_path)
            available_memory = psutil.virtual_memory().available
            
            if estimated_memory > available_memory * 0.8:
                logger.warning("Large file detected: %s (estimated memory: %.1f MB)", 
                             file_path.name, estimated_memory / 1024 / 1024)
                # Use streaming processing for large files
                result = await self._process_large_document_streaming(file_path, extraction_func)
            else:
                # Standard processing
                result = await asyncio.to_thread(extraction_func, file_path)
                
            processing_time = time.perf_counter() - start_time
            
            return {
                'file_path': str(file_path),
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'memory_used': estimated_memory
            }
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error("Failed to process %s: %s", file_path.name, e)
            
            return {
                'file_path': str(file_path),
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
            
    async def _process_large_document_streaming(self, 
                                              file_path: Path, 
                                              extraction_func: Callable) -> dict[str, Any]:
        """Process large documents using streaming approach."""
        from .document import stream_document
        
        logger.info("Using streaming processing for large file: %s", file_path.name)
        
        # Use streaming document loader
        document_stream = stream_document(str(file_path))
        
        # Process document in chunks
        all_clauses = []
        total_pages = 0
        
        async for document_chunk in document_stream:
            chunk_result = await asyncio.to_thread(extraction_func, document_chunk)
            if 'clauses' in chunk_result:
                all_clauses.extend(chunk_result['clauses'])
            total_pages += document_chunk.pages
            
        # Combine results
        return {
            'document_info': {
                'filename': file_path.name,
                'pages': total_pages,
                'processing_method': 'streaming'
            },
            'clauses': all_clauses,
            'metadata': {
                'processing_method': 'high_performance_streaming',
                'chunks_processed': total_pages
            }
        }

class IntelligentCacheManager:
    """Advanced caching system with intelligent eviction and preloading."""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: dict[str, dict[str, Any]] = {}
        self.access_times: dict[str, float] = {}
        self.cache_sizes: dict[str, int] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
        
    def get_cache_key(self, file_path: Path, settings: dict[str, Any]) -> str:
        """Generate cache key from file path and processing settings."""
        import hashlib
        
        try:
            file_stat = file_path.stat()
            content_hash = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
        except Exception:
            content_hash = str(file_path)
            
        settings_str = str(sorted(settings.items()))
        combined = f"{content_hash}:{settings_str}"
        
        return hashlib.md5(combined.encode()).hexdigest()
        
    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Get item from cache."""
        with self._lock:
            if cache_key in self.cache:
                self.access_times[cache_key] = time.time()
                self.hit_count += 1
                logger.debug("Cache hit for key: %s", cache_key[:8])
                return self.cache[cache_key].copy()
            else:
                self.miss_count += 1
                logger.debug("Cache miss for key: %s", cache_key[:8])
                return None
                
    def put(self, cache_key: str, value: dict[str, Any]) -> None:
        """Store item in cache with intelligent eviction."""
        import json
        
        with self._lock:
            # Estimate size
            try:
                value_size = len(json.dumps(value, default=str).encode('utf-8'))
            except Exception:
                value_size = 1024  # Default size estimate
                
            # Check if we need to evict items
            current_memory = sum(self.cache_sizes.values())
            
            while current_memory + value_size > self.max_memory_bytes and self.cache:
                self._evict_lru_item()
                current_memory = sum(self.cache_sizes.values())
                
            # Store new item
            self.cache[cache_key] = value
            self.cache_sizes[cache_key] = value_size
            self.access_times[cache_key] = time.time()
            
            logger.debug("Cached item with key %s (size: %d bytes)", 
                        cache_key[:8], value_size)
                        
    def _evict_lru_item(self) -> None:
        """Evict least recently used item."""
        if not self.access_times:
            return
            
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        del self.cache[lru_key]
        del self.cache_sizes[lru_key]
        del self.access_times[lru_key]
        
        logger.debug("Evicted LRU item: %s", lru_key[:8])
        
    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / max(1, total_requests)
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'memory_used_bytes': sum(self.cache_sizes.values()),
            'memory_used_mb': sum(self.cache_sizes.values()) / 1024 / 1024
        }

# Global instances for Generation 3
intelligent_cache = IntelligentCacheManager()

def get_performance_processor() -> HighPerformanceProcessor:
    """Get high-performance processor instance."""
    return HighPerformanceProcessor()

def get_cache_manager() -> IntelligentCacheManager:
    """Get intelligent cache manager."""
    return intelligent_cache

async def process_documents_high_performance(file_paths: list[Path]) -> list[dict[str, Any]]:
    """High-level high-performance document processing."""
    with get_performance_processor() as processor:
        return await processor.process_documents_batch(file_paths)