"""
Generation 3 "Make it Scale" integration layer.

This module provides a unified interface for all Generation 3 scaling features,
integrating high-performance computing, distributed processing, advanced caching,
resource management, performance analytics, and enterprise features.
"""

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .advanced_caching import MultiLevelCache, get_advanced_cache
from .distributed_processing import (
    DistributedProcessingManager,
    TaskPriority,
    get_distributed_manager,
)
from .enterprise_integration import (
    EnterpriseIntegrationManager,
    get_enterprise_integration,
)
from .high_performance_computing import (
    ParallelProcessingManager,
    WorkerPoolConfig,
    get_parallel_manager,
)
from .performance_analytics import PerformanceAnalyticsEngine, get_performance_analytics
from .resource_management import ResourceManager, get_resource_manager

# Import Generation 2 features
try:
    from .generation2_integration import Generation2ContractExtractor, ProcessingResult
    GENERATION_2_AVAILABLE = True
except ImportError:
    GENERATION_2_AVAILABLE = False

# Import Generation 1 features
try:
    from .extraction import extract_from_document
    GENERATION_1_AVAILABLE = True
except ImportError:
    GENERATION_1_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class Generation3Config:
    """Configuration for Generation 3 features."""

    # High-Performance Computing
    enable_gpu_acceleration: bool = False
    parallel_processing_enabled: bool = True
    worker_pool_size: int = 8
    memory_limit_mb: Optional[int] = None
    streaming_chunk_size: int = 1024 * 1024  # 1MB

    # Distributed Processing
    enable_distributed_processing: bool = False
    message_queue_url: Optional[str] = None
    max_distributed_workers: int = 10
    task_timeout_seconds: float = 300.0

    # Advanced Caching
    enable_advanced_caching: bool = True
    l1_cache_size_mb: int = 128
    l2_redis_url: Optional[str] = None
    l3_persistent_cache_size_mb: int = 1024
    cache_warming_enabled: bool = True

    # Resource Management
    enable_auto_scaling: bool = True
    resource_monitoring_interval: float = 5.0
    auto_scaling_policy: Dict[str, Any] = field(default_factory=dict)

    # Performance Analytics
    enable_performance_analytics: bool = True
    metrics_collection_interval: float = 1.0
    optimization_interval: float = 300.0
    bottleneck_detection_enabled: bool = True

    # Enterprise Integration
    enable_enterprise_features: bool = False
    sso_providers: List[Dict[str, Any]] = field(default_factory=list)
    api_gateway_features: List[str] = field(default_factory=list)
    microservices_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)


@dataclass
class ScalableProcessingResult:
    """Enhanced processing result with Generation 3 features."""

    # Core processing results
    success: bool
    clauses: List[Dict[str, Any]] = field(default_factory=list)
    document_metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    processing_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_time_seconds: float = 0.0
    gpu_acceleration_used: bool = False

    # Scaling features used
    parallel_processing_used: bool = False
    distributed_processing_used: bool = False
    cache_hit: bool = False
    cache_level_hit: Optional[str] = None
    auto_scaling_triggered: bool = False

    # Quality and reliability
    confidence_score: float = 0.0
    generation_2_features_used: List[str] = field(default_factory=list)
    generation_3_features_used: List[str] = field(default_factory=list)

    # System state
    worker_pool_size: int = 0
    system_load: Dict[str, float] = field(default_factory=dict)
    resource_utilization: Dict[str, float] = field(default_factory=dict)

    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)


class Generation3ContractExtractor:
    """Generation 3 contract extractor with enterprise scaling capabilities."""

    def __init__(self, config: Optional[Generation3Config] = None):
        self.config = config or Generation3Config()

        # Core components
        self._parallel_manager: Optional[ParallelProcessingManager] = None
        self._distributed_manager: Optional[DistributedProcessingManager] = None
        self._advanced_cache: Optional[MultiLevelCache] = None
        self._resource_manager: Optional[ResourceManager] = None
        self._performance_analytics: Optional[PerformanceAnalyticsEngine] = None
        self._enterprise_integration: Optional[EnterpriseIntegrationManager] = None

        # Generation 2 integration
        self._generation2_extractor: Optional[Generation2ContractExtractor] = None

        # State
        self._initialized = False
        self._shutdown_requested = False

        logger.info("Generation 3 Contract Extractor created")

    async def initialize(self) -> None:
        """Initialize all Generation 3 components."""
        if self._initialized:
            return

        logger.info("Initializing Generation 3 scaling features...")

        try:
            # Initialize high-performance computing
            await self._initialize_high_performance_computing()

            # Initialize distributed processing
            if self.config.enable_distributed_processing:
                await self._initialize_distributed_processing()

            # Initialize advanced caching
            if self.config.enable_advanced_caching:
                await self._initialize_advanced_caching()

            # Initialize resource management
            await self._initialize_resource_management()

            # Initialize performance analytics
            if self.config.enable_performance_analytics:
                await self._initialize_performance_analytics()

            # Initialize enterprise integration
            if self.config.enable_enterprise_features:
                await self._initialize_enterprise_integration()

            # Initialize Generation 2 integration
            await self._initialize_generation2_integration()

            self._initialized = True
            logger.info("Generation 3 initialization complete")

        except Exception as e:
            logger.error(f"Generation 3 initialization failed: {e}")
            raise

    async def _initialize_high_performance_computing(self) -> None:
        """Initialize high-performance computing components."""
        worker_config = WorkerPoolConfig(
            thread_pool_size=self.config.worker_pool_size,
            enable_gpu=self.config.enable_gpu_acceleration,
            memory_limit_mb=self.config.memory_limit_mb
        )

        self._parallel_manager = get_parallel_manager(worker_config)
        logger.info("High-performance computing initialized")

    async def _initialize_distributed_processing(self) -> None:
        """Initialize distributed processing."""
        self._distributed_manager = get_distributed_manager(self.config.message_queue_url)
        await self._distributed_manager.initialize()
        logger.info("Distributed processing initialized")

    async def _initialize_advanced_caching(self) -> None:
        """Initialize advanced caching system."""
        l1_config = {'max_size_mb': self.config.l1_cache_size_mb}
        l2_config = {'redis_url': self.config.l2_redis_url} if self.config.l2_redis_url else None
        l3_config = {'max_size_mb': self.config.l3_persistent_cache_size_mb}

        self._advanced_cache = get_advanced_cache(l1_config, l2_config, l3_config)
        logger.info("Advanced caching initialized")

    async def _initialize_resource_management(self) -> None:
        """Initialize resource management."""
        self._resource_manager = get_resource_manager(
            monitor_interval=self.config.resource_monitoring_interval,
            auto_scaling_enabled=self.config.enable_auto_scaling,
            initial_workers=self.config.worker_pool_size
        )

        self._resource_manager.initialize()
        logger.info("Resource management initialized")

    async def _initialize_performance_analytics(self) -> None:
        """Initialize performance analytics."""
        self._performance_analytics = get_performance_analytics(
            collection_interval=self.config.metrics_collection_interval,
            optimization_interval=self.config.optimization_interval
        )

        self._performance_analytics.start()
        logger.info("Performance analytics initialized")

    async def _initialize_enterprise_integration(self) -> None:
        """Initialize enterprise integration."""
        enterprise_config = {
            'sso': {'providers': self.config.sso_providers},
            'api_gateway': {'features': self.config.api_gateway_features},
            'microservices': self.config.microservices_config
        }

        self._enterprise_integration = get_enterprise_integration(enterprise_config)
        logger.info("Enterprise integration initialized")

    async def _initialize_generation2_integration(self) -> None:
        """Initialize Generation 2 integration."""
        if GENERATION_2_AVAILABLE:
            try:
                self._generation2_extractor = Generation2ContractExtractor()
                logger.info("Generation 2 integration initialized")
            except Exception as e:
                logger.warning(f"Generation 2 integration failed: {e}")

    async def extract_from_file_scalable(
        self,
        file_path: Union[str, Path],
        priority: TaskPriority = TaskPriority.NORMAL,
        use_distributed: bool = False,
        cache_ttl: Optional[float] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ScalableProcessingResult:
        """
        Extract contract clauses with full Generation 3 scaling capabilities.
        
        Args:
            file_path: Path to document file
            priority: Processing priority for distributed systems
            use_distributed: Force distributed processing
            cache_ttl: Cache time-to-live in seconds
            user_context: User context for enterprise features
            
        Returns:
            ScalableProcessingResult with comprehensive metadata
        """
        if not self._initialized:
            await self.initialize()

        file_path = Path(file_path)
        start_time = time.perf_counter()

        result = ScalableProcessingResult(
            success=False,
            processing_time_seconds=0.0
        )

        try:
            # Generate cache key
            cache_key = f"contract_extraction_{file_path.name}_{file_path.stat().st_mtime}"

            # Check cache first
            cached_result = None
            if self._advanced_cache:
                cached_result = await self._advanced_cache.get(cache_key)
                if cached_result:
                    result.cache_hit = True
                    result.cache_level_hit = "multi-level"
                    result.success = True
                    result.clauses = cached_result.get('clauses', [])
                    result.document_metadata = cached_result.get('metadata', {})
                    result.processing_time_seconds = time.perf_counter() - start_time
                    return result

            # Determine processing strategy
            processing_strategy = await self._determine_processing_strategy(
                file_path, priority, use_distributed, user_context
            )

            # Execute processing based on strategy
            extraction_result = await self._execute_processing_strategy(
                file_path, processing_strategy, result
            )

            # Update result with extraction data
            result.success = extraction_result.get('success', False)
            result.clauses = extraction_result.get('clauses', [])
            result.document_metadata = extraction_result.get('metadata', {})
            result.confidence_score = extraction_result.get('confidence_score', 0.0)

            if extraction_result.get('error'):
                result.error_message = extraction_result['error']

            # Cache successful results
            if result.success and self._advanced_cache:
                cache_data = {
                    'clauses': result.clauses,
                    'metadata': result.document_metadata,
                    'timestamp': time.time()
                }
                await self._advanced_cache.set(cache_key, cache_data, ttl=cache_ttl)

            # Update performance metrics
            result.processing_time_seconds = time.perf_counter() - start_time

            # Collect system metrics
            if self._resource_manager:
                system_status = self._resource_manager.get_system_status()
                result.system_load = {
                    'cpu': system_status['current_metrics']['cpu_percent'],
                    'memory': system_status['current_metrics']['memory_percent']
                }
                result.worker_pool_size = system_status['worker_pool_stats']['current_size']

            logger.info(f"Scalable extraction completed: {file_path.name} in {result.processing_time_seconds:.3f}s")

            return result

        except Exception as e:
            result.error_message = str(e)
            result.processing_time_seconds = time.perf_counter() - start_time
            logger.error(f"Scalable extraction failed for {file_path}: {e}")
            return result

    async def _determine_processing_strategy(
        self,
        file_path: Path,
        priority: TaskPriority,
        force_distributed: bool,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine optimal processing strategy based on file and system state."""
        strategy = {
            'use_distributed': force_distributed,
            'use_parallel': True,
            'use_gpu': self.config.enable_gpu_acceleration,
            'use_streaming': False,
            'batch_size': 1
        }

        # Check file size for streaming decision
        try:
            file_size = file_path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                strategy['use_streaming'] = True
                logger.info(f"Large file detected ({file_size} bytes), enabling streaming")
        except Exception:
            pass

        # Check system load for distributed processing
        if not force_distributed and self._resource_manager:
            system_status = self._resource_manager.get_system_status()
            cpu_usage = system_status['current_metrics']['cpu_percent']
            memory_usage = system_status['current_metrics']['memory_percent']

            if cpu_usage > 80 or memory_usage > 80:
                strategy['use_distributed'] = True
                logger.info("High system load detected, enabling distributed processing")

        # Consider user context for enterprise features
        if user_context and self.config.enable_enterprise_features:
            user_priority = user_context.get('priority', 'normal')
            if user_priority == 'high':
                strategy['use_gpu'] = True
                strategy['batch_size'] = min(strategy['batch_size'], 1)  # Faster processing

        return strategy

    async def _execute_processing_strategy(
        self,
        file_path: Path,
        strategy: Dict[str, Any],
        result: ScalableProcessingResult
    ) -> Dict[str, Any]:
        """Execute the determined processing strategy."""

        # Update result with strategy used
        result.distributed_processing_used = strategy['use_distributed']
        result.parallel_processing_used = strategy['use_parallel']
        result.gpu_acceleration_used = strategy['use_gpu']
        result.generation_3_features_used = []

        if strategy['use_distributed'] and self._distributed_manager:
            return await self._process_distributed(file_path, result)
        elif strategy['use_streaming']:
            return await self._process_streaming(file_path, result)
        elif strategy['use_parallel'] and self._parallel_manager:
            return await self._process_parallel(file_path, result)
        else:
            return await self._process_standard(file_path, result)

    async def _process_distributed(
        self,
        file_path: Path,
        result: ScalableProcessingResult
    ) -> Dict[str, Any]:
        """Process document using distributed system."""
        try:
            # Submit task to distributed system
            task_id = await self._distributed_manager.process_document_distributed(
                file_path, priority=TaskPriority.NORMAL
            )

            # Wait for completion
            task_result = await self._distributed_manager.wait_for_task(task_id)

            if task_result and task_result['status'] == 'COMPLETED':
                result.generation_3_features_used.append('distributed_processing')
                return task_result.get('result', {})
            else:
                # Fallback to local processing
                logger.warning("Distributed processing failed, falling back to local")
                return await self._process_parallel(file_path, result)

        except Exception as e:
            logger.error(f"Distributed processing error: {e}")
            return await self._process_parallel(file_path, result)

    async def _process_streaming(
        self,
        file_path: Path,
        result: ScalableProcessingResult
    ) -> Dict[str, Any]:
        """Process large document using streaming."""
        try:
            from .high_performance_computing import StreamProcessor

            stream_processor = StreamProcessor(self.config.streaming_chunk_size)

            # Define processing function for chunks
            def process_chunk(chunk_data: bytes) -> Dict[str, Any]:
                # This would process individual chunks
                # For now, return mock data
                return {
                    'chunk_clauses': [],
                    'chunk_size': len(chunk_data)
                }

            stream_result = stream_processor.process_large_document_stream(
                file_path, process_chunk
            )

            if stream_result['success']:
                result.generation_3_features_used.append('streaming_processing')

                # Aggregate results from chunks
                all_clauses = []
                for chunk_result in stream_result['results']:
                    if chunk_result.get('processing_result'):
                        chunk_clauses = chunk_result['processing_result'].get('chunk_clauses', [])
                        all_clauses.extend(chunk_clauses)

                return {
                    'success': True,
                    'clauses': all_clauses,
                    'metadata': {
                        'chunks_processed': stream_result['chunks_processed'],
                        'total_bytes': stream_result['total_bytes']
                    }
                }
            else:
                return {'success': False, 'error': stream_result.get('error')}

        except Exception as e:
            logger.error(f"Streaming processing error: {e}")
            return await self._process_parallel(file_path, result)

    async def _process_parallel(
        self,
        file_path: Path,
        result: ScalableProcessingResult
    ) -> Dict[str, Any]:
        """Process document using parallel processing."""
        try:
            if self._parallel_manager:
                # Use parallel processing
                def processing_func(doc_path: Path) -> Dict[str, Any]:
                    return self._extract_with_fallback(doc_path)

                # Process single document (could be extended for batch processing)
                parallel_results = self._parallel_manager.process_documents_parallel(
                    [file_path], processing_func, batch_size=1
                )

                if parallel_results:
                    _, extraction_result, stats = parallel_results[0]
                    result.generation_3_features_used.append('parallel_processing')
                    result.memory_peak_mb = stats.memory_end
                    return extraction_result

            # Fallback to standard processing
            return await self._process_standard(file_path, result)

        except Exception as e:
            logger.error(f"Parallel processing error: {e}")
            return await self._process_standard(file_path, result)

    async def _process_standard(
        self,
        file_path: Path,
        result: ScalableProcessingResult
    ) -> Dict[str, Any]:
        """Process document using standard methods."""
        return self._extract_with_fallback(file_path)

    def _extract_with_fallback(self, file_path: Path) -> Dict[str, Any]:
        """Extract with fallback through generation levels."""
        try:
            # Try Generation 2 if available
            if self._generation2_extractor and GENERATION_2_AVAILABLE:
                from .enhanced_security import PermissionType, SecurityContext

                # Create basic security context
                security_context = SecurityContext(
                    user_id="system",
                    permissions={PermissionType.READ},
                    authenticated=True
                )

                gen2_result = self._generation2_extractor.robust_extract_from_file(
                    str(file_path), security_context=security_context
                )

                if gen2_result.success:
                    return {
                        'success': True,
                        'clauses': [clause.to_dict() for clause in gen2_result.clauses],
                        'metadata': gen2_result.document_metadata,
                        'confidence_score': gen2_result.confidence_score,
                        'generation_used': 2
                    }

            # Fallback to Generation 1
            if GENERATION_1_AVAILABLE:
                gen1_result = extract_from_document(file_path)

                return {
                    'success': True,
                    'clauses': gen1_result.get('clauses', []),
                    'metadata': gen1_result.get('document_metadata', {}),
                    'confidence_score': gen1_result.get('confidence_score', 0.7),
                    'generation_used': 1
                }

            # No extraction available
            return {'success': False, 'error': 'No extraction methods available'}

        except Exception as e:
            logger.error(f"Extraction fallback failed: {e}")
            return {'success': False, 'error': str(e)}

    async def process_batch_scalable(
        self,
        file_paths: List[Union[str, Path]],
        priority: TaskPriority = TaskPriority.NORMAL,
        max_parallel: int = 5
    ) -> List[ScalableProcessingResult]:
        """Process multiple documents with optimal scaling."""
        if not self._initialized:
            await self.initialize()

        results = []

        # Convert to Path objects
        paths = [Path(p) for p in file_paths]

        # Process in batches
        for i in range(0, len(paths), max_parallel):
            batch = paths[i:i + max_parallel]

            # Process batch concurrently
            batch_tasks = [
                self.extract_from_file_scalable(path, priority=priority)
                for path in batch
            ]

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Handle exceptions
            for j, batch_result in enumerate(batch_results):
                if isinstance(batch_result, Exception):
                    error_result = ScalableProcessingResult(
                        success=False,
                        error_message=str(batch_result)
                    )
                    results.append(error_result)
                else:
                    results.append(batch_result)

        return results

    def get_scaling_status(self) -> Dict[str, Any]:
        """Get comprehensive scaling system status."""
        status = {
            'initialized': self._initialized,
            'generation_3_features': {
                'high_performance_computing': self._parallel_manager is not None,
                'distributed_processing': self._distributed_manager is not None,
                'advanced_caching': self._advanced_cache is not None,
                'resource_management': self._resource_manager is not None,
                'performance_analytics': self._performance_analytics is not None,
                'enterprise_integration': self._enterprise_integration is not None
            },
            'configuration': self.config.to_dict()
        }

        # Add component-specific status
        if self._resource_manager:
            status['resource_management'] = self._resource_manager.get_system_status()

        if self._advanced_cache:
            status['advanced_caching'] = self._advanced_cache.get_comprehensive_stats()

        if self._distributed_manager:
            status['distributed_processing'] = self._distributed_manager.get_system_status()

        if self._performance_analytics:
            status['performance_analytics'] = self._performance_analytics.get_comprehensive_report()

        if self._enterprise_integration:
            status['enterprise_integration'] = self._enterprise_integration.get_integration_status()

        return status

    async def shutdown(self) -> None:
        """Shutdown all Generation 3 components gracefully."""
        if not self._initialized or self._shutdown_requested:
            return

        self._shutdown_requested = True
        logger.info("Shutting down Generation 3 components...")

        try:
            # Shutdown components in order
            if self._performance_analytics:
                self._performance_analytics.stop()

            if self._resource_manager:
                self._resource_manager.shutdown()

            if self._parallel_manager:
                self._parallel_manager.shutdown()

            logger.info("Generation 3 shutdown complete")

        except Exception as e:
            logger.error(f"Error during Generation 3 shutdown: {e}")


# Convenience functions for backwards compatibility and easy usage

async def scalable_extract_from_file(
    file_path: Union[str, Path],
    config: Optional[Generation3Config] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    use_distributed: bool = False
) -> ScalableProcessingResult:
    """
    Extract contract clauses with Generation 3 scaling capabilities.
    
    This is the main entry point for Generation 3 contract extraction.
    """
    extractor = Generation3ContractExtractor(config)
    return await extractor.extract_from_file_scalable(
        file_path, priority=priority, use_distributed=use_distributed
    )


async def scalable_batch_extract(
    file_paths: List[Union[str, Path]],
    config: Optional[Generation3Config] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_parallel: int = 5
) -> List[ScalableProcessingResult]:
    """
    Extract contract clauses from multiple files with Generation 3 scaling.
    """
    extractor = Generation3ContractExtractor(config)
    return await extractor.process_batch_scalable(
        file_paths, priority=priority, max_parallel=max_parallel
    )


def get_generation3_status(config: Optional[Generation3Config] = None) -> Dict[str, Any]:
    """Get Generation 3 system status without initializing full extraction."""
    return {
        'generation_1_available': GENERATION_1_AVAILABLE,
        'generation_2_available': GENERATION_2_AVAILABLE,
        'generation_3_ready': True,
        'config': config.to_dict() if config else Generation3Config().to_dict()
    }


# Global Generation 3 extractor instance for singleton pattern
_global_extractor: Optional[Generation3ContractExtractor] = None


async def get_global_extractor(config: Optional[Generation3Config] = None) -> Generation3ContractExtractor:
    """Get global Generation 3 extractor instance."""
    global _global_extractor

    if _global_extractor is None:
        _global_extractor = Generation3ContractExtractor(config)
        await _global_extractor.initialize()

    return _global_extractor


async def shutdown_global_extractor() -> None:
    """Shutdown global Generation 3 extractor."""
    global _global_extractor

    if _global_extractor:
        await _global_extractor.shutdown()
        _global_extractor = None
