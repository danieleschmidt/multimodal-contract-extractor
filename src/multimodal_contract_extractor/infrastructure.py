"""
Resilient infrastructure framework for production deployment.

This module provides connection pooling, caching layers, backup/recovery mechanisms,
failover capabilities, and infrastructure health monitoring for enterprise-grade reliability.
"""

from __future__ import annotations

import functools
import gzip
import logging
import pickle
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from sqlalchemy import create_engine, pool
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In, First Out


class BackupStrategy(Enum):
    """Backup strategies."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class HealthStatus(Enum):
    """Infrastructure component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size: int = 1000
    ttl_seconds: int = 3600
    strategy: CacheStrategy = CacheStrategy.LRU
    compression: bool = True
    persistence: bool = False
    persistence_path: Optional[str] = None


@dataclass
class BackupConfig:
    """Backup configuration."""
    enabled: bool = True
    strategy: BackupStrategy = BackupStrategy.INCREMENTAL
    backup_dir: str = "backups"
    retention_days: int = 30
    compression: bool = True
    schedule_hours: List[int] = field(default_factory=lambda: [2, 14])  # 2 AM and 2 PM


class CacheEntry:
    """Cache entry with metadata."""

    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 1
        self.ttl = ttl
        self.size = self._calculate_size(value)

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of the value."""
        try:
            return len(pickle.dumps(value))
        except Exception:
            return len(str(value).encode('utf-8'))

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1


class InMemoryCache:
    """High-performance in-memory cache with multiple eviction strategies."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU
        self.current_size = 0
        self._lock = threading.RLock()

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_name'])
            self.cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_name'])
            self.cache_evictions = Counter('cache_evictions_total', 'Cache evictions', ['cache_name', 'reason'])
            self.cache_size_gauge = Gauge('cache_size_bytes', 'Current cache size in bytes', ['cache_name'])
            self.cache_entries_gauge = Gauge('cache_entries_count', 'Number of cache entries', ['cache_name'])

        # Load from persistence if enabled
        if self.config.persistence and self.config.persistence_path:
            self._load_from_disk()

        # Start cleanup thread
        self._start_cleanup_thread()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self.cache:
                if PROMETHEUS_AVAILABLE:
                    self.cache_misses.labels(cache_name='inmemory').inc()
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                self._remove_entry(key, 'expired')
                if PROMETHEUS_AVAILABLE:
                    self.cache_misses.labels(cache_name='inmemory').inc()
                return None

            # Update access info
            entry.touch()

            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            if PROMETHEUS_AVAILABLE:
                self.cache_hits.labels(cache_name='inmemory').inc()

            return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in cache."""
        with self._lock:
            # Remove existing entry if present
            if key in self.cache:
                self._remove_entry(key, 'overwrite')

            # Create new entry
            ttl = ttl or self.config.ttl_seconds
            entry = CacheEntry(key, value, ttl)

            # Check if we need to evict entries
            while self._needs_eviction(entry.size):
                if not self._evict_entry():
                    # Cannot evict more entries
                    return False

            # Add entry
            self.cache[key] = entry
            self.access_order.append(key)
            self.current_size += entry.size

            self._update_metrics()
            return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self.cache:
                self._remove_entry(key, 'manual')
                return True
            return False

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_size = 0
            self._update_metrics()

    def _needs_eviction(self, new_entry_size: int) -> bool:
        """Check if eviction is needed."""
        return (len(self.cache) >= self.config.max_size or
                self.current_size + new_entry_size > self.config.max_size * 1024)  # Assume max_size is in KB

    def _evict_entry(self) -> bool:
        """Evict an entry based on the configured strategy."""
        if not self.cache:
            return False

        if self.config.strategy == CacheStrategy.LRU:
            key_to_evict = self.access_order[0]
        elif self.config.strategy == CacheStrategy.LFU:
            key_to_evict = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
        elif self.config.strategy == CacheStrategy.FIFO:
            key_to_evict = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        else:  # TTL or default to LRU
            key_to_evict = self.access_order[0]

        self._remove_entry(key_to_evict, 'evicted')
        return True

    def _remove_entry(self, key: str, reason: str):
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache[key]
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.current_size -= entry.size

            if PROMETHEUS_AVAILABLE:
                self.cache_evictions.labels(cache_name='inmemory', reason=reason).inc()

    def _start_cleanup_thread(self):
        """Start background thread for cache cleanup."""
        def cleanup():
            while True:
                try:
                    with self._lock:
                        expired_keys = [
                            key for key, entry in self.cache.items()
                            if entry.is_expired()
                        ]

                        for key in expired_keys:
                            self._remove_entry(key, 'expired')

                        if expired_keys:
                            self._update_metrics()
                            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

                    time.sleep(60)  # Cleanup every minute

                except Exception as e:
                    logger.error(f"Cache cleanup failed: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def _update_metrics(self):
        """Update Prometheus metrics."""
        if PROMETHEUS_AVAILABLE:
            self.cache_size_gauge.labels(cache_name='inmemory').set(self.current_size)
            self.cache_entries_gauge.labels(cache_name='inmemory').set(len(self.cache))

    def _load_from_disk(self):
        """Load cache from disk if persistence is enabled."""
        if not self.config.persistence_path:
            return

        try:
            cache_file = Path(self.config.persistence_path)
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.cache = data.get('cache', {})
                    self.access_order = data.get('access_order', [])
                    self.current_size = sum(entry.size for entry in self.cache.values())
                    logger.info(f"Loaded {len(self.cache)} entries from cache persistence")
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")

    def _save_to_disk(self):
        """Save cache to disk if persistence is enabled."""
        if not self.config.persistence or not self.config.persistence_path:
            return

        try:
            cache_file = Path(self.config.persistence_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'cache': self.cache,
                'access_order': self.access_order
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)

            logger.debug(f"Saved {len(self.cache)} entries to cache persistence")
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "entries": len(self.cache),
                "size_bytes": self.current_size,
                "max_size": self.config.max_size,
                "strategy": self.config.strategy.value,
                "ttl_seconds": self.config.ttl_seconds
            }


class RedisCache:
    """Redis-based distributed cache."""

    def __init__(self, config: CacheConfig, redis_url: str = "redis://localhost:6379"):
        self.config = config
        self.redis_url = redis_url
        self.client = None

        if REDIS_AVAILABLE:
            try:
                self.client = redis.from_url(redis_url)
                # Test connection
                self.client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.client = None

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.cache_hits = Counter('redis_cache_hits_total', 'Redis cache hits')
            self.cache_misses = Counter('redis_cache_misses_total', 'Redis cache misses')

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.client:
            return None

        try:
            data = self.client.get(key)
            if data is None:
                if PROMETHEUS_AVAILABLE:
                    self.cache_misses.inc()
                return None

            if self.config.compression:
                data = gzip.decompress(data)

            value = pickle.loads(data)

            if PROMETHEUS_AVAILABLE:
                self.cache_hits.inc()

            return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in Redis cache."""
        if not self.client:
            return False

        try:
            data = pickle.dumps(value)

            if self.config.compression:
                data = gzip.compress(data)

            ttl = ttl or self.config.ttl_seconds
            self.client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis put error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete entry from Redis cache."""
        if not self.client:
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all entries from Redis cache."""
        if not self.client:
            return False

        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self.client:
            return {"error": "Redis not available"}

        try:
            info = self.client.info()
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"error": str(e)}


class ConnectionPool:
    """Database connection pool manager."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.engine = None
        self.session_factory = None

        if SQLALCHEMY_AVAILABLE:
            try:
                self.engine = create_engine(
                    config.url,
                    poolclass=pool.QueuePool,
                    pool_size=config.pool_size,
                    max_overflow=config.max_overflow,
                    pool_timeout=config.pool_timeout,
                    pool_recycle=config.pool_recycle,
                    echo=config.echo
                )

                self.session_factory = sessionmaker(bind=self.engine)
                logger.info("Database connection pool initialized")

            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {e}")

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.active_connections = Gauge(
                'db_connections_active',
                'Number of active database connections'
            )
            self.connection_errors = Counter(
                'db_connection_errors_total',
                'Total database connection errors'
            )

    @contextmanager
    def get_session(self):
        """Get a database session from the pool."""
        if not self.session_factory:
            raise RuntimeError("Database connection pool not available")

        session = self.session_factory()

        try:
            if PROMETHEUS_AVAILABLE:
                self.active_connections.inc()

            yield session
            session.commit()

        except Exception as e:
            session.rollback()

            if PROMETHEUS_AVAILABLE:
                self.connection_errors.inc()

            logger.error(f"Database session error: {e}")
            raise

        finally:
            session.close()

            if PROMETHEUS_AVAILABLE:
                self.active_connections.dec()

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if not self.engine:
            return {"error": "Database engine not available"}

        try:
            pool = self.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> bool:
        """Perform a health check on the database connection."""
        if not self.engine:
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


class BackupManager:
    """Backup and recovery manager."""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.last_backup_time: Optional[datetime] = None
        self.backup_history: List[Dict[str, Any]] = []

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.backup_duration = Histogram(
                'backup_duration_seconds',
                'Time spent creating backups',
                ['backup_type']
            )
            self.backup_size_bytes = Gauge(
                'backup_size_bytes',
                'Size of backup files in bytes',
                ['backup_type']
            )

    def create_backup(self, source_paths: List[Path], backup_name: str = None) -> Dict[str, Any]:
        """Create a backup of specified paths."""
        if not self.config.enabled:
            return {"error": "Backups are disabled"}

        start_time = time.time()
        backup_name = backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_info = {
            "name": backup_name,
            "timestamp": datetime.now(timezone.utc),
            "strategy": self.config.strategy.value,
            "source_paths": [str(p) for p in source_paths],
            "compressed": self.config.compression
        }

        try:
            if self.config.strategy == BackupStrategy.FULL:
                backup_path = self._create_full_backup(source_paths, backup_name)
            elif self.config.strategy == BackupStrategy.INCREMENTAL:
                backup_path = self._create_incremental_backup(source_paths, backup_name)
            else:  # DIFFERENTIAL
                backup_path = self._create_differential_backup(source_paths, backup_name)

            # Get backup size
            backup_size = backup_path.stat().st_size if backup_path.exists() else 0

            backup_info.update({
                "path": str(backup_path),
                "size_bytes": backup_size,
                "success": True,
                "duration_seconds": time.time() - start_time
            })

            self.backup_history.append(backup_info)
            self.last_backup_time = backup_info["timestamp"]

            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self.backup_duration.labels(
                    backup_type=self.config.strategy.value
                ).observe(backup_info["duration_seconds"])

                self.backup_size_bytes.labels(
                    backup_type=self.config.strategy.value
                ).set(backup_size)

            # Cleanup old backups
            self._cleanup_old_backups()

            logger.info(f"Backup created: {backup_name} ({backup_size} bytes)")
            return backup_info

        except Exception as e:
            backup_info.update({
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            })

            logger.error(f"Backup creation failed: {e}")
            return backup_info

    def _create_full_backup(self, source_paths: List[Path], backup_name: str) -> Path:
        """Create a full backup."""
        backup_path = self.backup_dir / f"{backup_name}.tar"

        if self.config.compression:
            backup_path = backup_path.with_suffix(".tar.gz")

        # Create tar archive
        import tarfile

        mode = "w:gz" if self.config.compression else "w"
        with tarfile.open(backup_path, mode) as tar:
            for source_path in source_paths:
                if source_path.exists():
                    tar.add(source_path, arcname=source_path.name)

        return backup_path

    def _create_incremental_backup(self, source_paths: List[Path], backup_name: str) -> Path:
        """Create an incremental backup."""
        # For simplicity, this creates a full backup
        # In a real implementation, this would only backup changed files
        return self._create_full_backup(source_paths, backup_name)

    def _create_differential_backup(self, source_paths: List[Path], backup_name: str) -> Path:
        """Create a differential backup."""
        # For simplicity, this creates a full backup
        # In a real implementation, this would backup files changed since last full backup
        return self._create_full_backup(source_paths, backup_name)

    def restore_backup(self, backup_name: str, restore_path: Path) -> Dict[str, Any]:
        """Restore from a backup."""
        start_time = time.time()

        # Find backup file
        backup_files = list(self.backup_dir.glob(f"{backup_name}.*"))
        if not backup_files:
            return {
                "success": False,
                "error": f"Backup not found: {backup_name}"
            }

        backup_file = backup_files[0]

        try:
            import tarfile

            # Determine if compressed
            is_compressed = backup_file.suffix == ".gz"
            mode = "r:gz" if is_compressed else "r"

            # Extract backup
            restore_path.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_file, mode) as tar:
                tar.extractall(restore_path)

            restore_info = {
                "success": True,
                "backup_name": backup_name,
                "restore_path": str(restore_path),
                "duration_seconds": time.time() - start_time
            }

            logger.info(f"Backup restored: {backup_name} to {restore_path}")
            return restore_info

        except Exception as e:
            restore_info = {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }

            logger.error(f"Backup restore failed: {e}")
            return restore_info

    def _cleanup_old_backups(self):
        """Clean up old backup files."""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

        try:
            for backup_file in self.backup_dir.glob("backup_*"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.debug(f"Cleaned up old backup: {backup_file}")
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def get_backup_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get backup history."""
        return self.backup_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get backup statistics."""
        total_backups = len(self.backup_history)
        successful_backups = sum(1 for b in self.backup_history if b.get("success", False))

        return {
            "enabled": self.config.enabled,
            "strategy": self.config.strategy.value,
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "success_rate": successful_backups / total_backups if total_backups > 0 else 0,
            "last_backup": self.last_backup_time.isoformat() if self.last_backup_time else None,
            "retention_days": self.config.retention_days
        }


class HealthMonitor:
    """Infrastructure component health monitoring."""

    def __init__(self):
        self.components: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.health_checks: Dict[str, HealthStatus] = {}
        self._lock = threading.Lock()

        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.component_health = Gauge(
                'infrastructure_component_health',
                'Infrastructure component health status',
                ['component']
            )

    def register_component(self, name: str, health_check_func: Callable[[], Dict[str, Any]]):
        """Register a component for health monitoring."""
        self.components[name] = health_check_func
        logger.info(f"Registered health monitor for component: {name}")

    def check_health(self) -> Dict[str, Any]:
        """Check health of all registered components."""
        results = {}
        overall_status = HealthStatus.HEALTHY

        with self._lock:
            for name, check_func in self.components.items():
                try:
                    result = check_func()
                    status = HealthStatus.HEALTHY

                    # Determine status from result
                    if result.get("error"):
                        status = HealthStatus.UNHEALTHY
                    elif result.get("degraded"):
                        status = HealthStatus.DEGRADED

                    self.health_checks[name] = status
                    results[name] = {
                        "status": status.value,
                        "details": result
                    }

                    # Update overall status
                    if status == HealthStatus.UNHEALTHY:
                        overall_status = HealthStatus.UNHEALTHY
                    elif status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED

                    # Update metrics
                    if PROMETHEUS_AVAILABLE:
                        status_value = {
                            HealthStatus.HEALTHY: 1,
                            HealthStatus.DEGRADED: 0.5,
                            HealthStatus.UNHEALTHY: 0,
                            HealthStatus.UNKNOWN: -1
                        }[status]
                        self.component_health.labels(component=name).set(status_value)

                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    status = HealthStatus.UNKNOWN
                    self.health_checks[name] = status
                    results[name] = {
                        "status": status.value,
                        "error": str(e)
                    }
                    overall_status = HealthStatus.UNHEALTHY

        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": results
        }

    def get_component_status(self, name: str) -> Optional[HealthStatus]:
        """Get status of a specific component."""
        return self.health_checks.get(name)

    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        with self._lock:
            return all(
                status == HealthStatus.HEALTHY
                for status in self.health_checks.values()
            )


class InfrastructureManager:
    """Central infrastructure management."""

    def __init__(self):
        self.caches: Dict[str, Union[InMemoryCache, RedisCache]] = {}
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.backup_manager: Optional[BackupManager] = None
        self.health_monitor = HealthMonitor()

        # Initialize default components
        self._initialize_default_components()

    def _initialize_default_components(self):
        """Initialize default infrastructure components."""
        # Default in-memory cache
        default_cache_config = CacheConfig(
            max_size=1000,
            ttl_seconds=3600,
            strategy=CacheStrategy.LRU
        )
        self.register_cache("default", InMemoryCache(default_cache_config))

        # Default backup manager
        default_backup_config = BackupConfig()
        self.backup_manager = BackupManager(default_backup_config)

        # Register health checks
        self.health_monitor.register_component("caches", self._check_cache_health)
        self.health_monitor.register_component("backup", self._check_backup_health)

    def register_cache(self, name: str, cache: Union[InMemoryCache, RedisCache]):
        """Register a cache instance."""
        self.caches[name] = cache
        logger.info(f"Registered cache: {name}")

    def register_connection_pool(self, name: str, pool: ConnectionPool):
        """Register a connection pool."""
        self.connection_pools[name] = pool
        self.health_monitor.register_component(
            f"db_{name}",
            lambda: {"healthy": pool.health_check()}
        )
        logger.info(f"Registered connection pool: {name}")

    def get_cache(self, name: str = "default") -> Optional[Union[InMemoryCache, RedisCache]]:
        """Get a cache instance."""
        return self.caches.get(name)

    def get_connection_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get a connection pool."""
        return self.connection_pools.get(name)

    def _check_cache_health(self) -> Dict[str, Any]:
        """Check health of all caches."""
        cache_stats = {}
        for name, cache in self.caches.items():
            try:
                stats = cache.get_stats()
                cache_stats[name] = stats
            except Exception as e:
                cache_stats[name] = {"error": str(e)}

        return {"caches": cache_stats}

    def _check_backup_health(self) -> Dict[str, Any]:
        """Check backup system health."""
        if not self.backup_manager:
            return {"error": "Backup manager not initialized"}

        return self.backup_manager.get_stats()

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure status."""
        health_status = self.health_monitor.check_health()

        # Collect component statistics
        component_stats = {
            "caches": {
                name: cache.get_stats()
                for name, cache in self.caches.items()
            },
            "connection_pools": {
                name: pool.get_stats()
                for name, pool in self.connection_pools.items()
            },
            "backup": self.backup_manager.get_stats() if self.backup_manager else None
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health_status,
            "statistics": component_stats,
            "infrastructure_ready": health_status["overall_status"] in ["healthy", "degraded"]
        }

    def create_backup(self, source_paths: List[Path], backup_name: str = None) -> Dict[str, Any]:
        """Create a system backup."""
        if not self.backup_manager:
            return {"error": "Backup manager not available"}

        return self.backup_manager.create_backup(source_paths, backup_name)

    def restore_backup(self, backup_name: str, restore_path: Path) -> Dict[str, Any]:
        """Restore from a backup."""
        if not self.backup_manager:
            return {"error": "Backup manager not available"}

        return self.backup_manager.restore_backup(backup_name, restore_path)


# Global infrastructure manager instance
_infrastructure_manager: Optional[InfrastructureManager] = None


def get_infrastructure_manager() -> InfrastructureManager:
    """Get the global infrastructure manager instance."""
    global _infrastructure_manager
    if _infrastructure_manager is None:
        _infrastructure_manager = InfrastructureManager()
    return _infrastructure_manager


# Convenience functions
def get_cache(name: str = "default") -> Optional[Union[InMemoryCache, RedisCache]]:
    """Get a cache instance."""
    return get_infrastructure_manager().get_cache(name)


def get_connection_pool(name: str) -> Optional[ConnectionPool]:
    """Get a connection pool."""
    return get_infrastructure_manager().get_connection_pool(name)


# Decorators
def cached(cache_name: str = "default", ttl: Optional[int] = None,
          key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache(cache_name)
            if not cache:
                return func(*args, **kwargs)

            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__module__}.{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.put(key, result, ttl)
            return result

        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    # Initialize infrastructure
    manager = get_infrastructure_manager()

    # Test caching
    cache = get_cache()
    cache.put("test_key", "test_value")
    print(f"Cached value: {cache.get('test_key')}")

    # Test backup
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test.txt"
        test_file.write_text("Test content")

        backup_result = manager.create_backup([test_file])
        print(f"Backup result: {backup_result}")

    # Get system status
    status = manager.get_system_status()
    print(f"Infrastructure status: {status['health']['overall_status']}")

    # Test cached decorator
    @cached(ttl=300)
    def expensive_function(x: int) -> int:
        time.sleep(0.1)  # Simulate expensive operation
        return x * x

    start_time = time.time()
    result1 = expensive_function(5)
    first_call_time = time.time() - start_time

    start_time = time.time()
    result2 = expensive_function(5)  # Should be cached
    second_call_time = time.time() - start_time

    print(f"First call: {result1} in {first_call_time:.3f}s")
    print(f"Second call: {result2} in {second_call_time:.3f}s (cached: {second_call_time < first_call_time})")
