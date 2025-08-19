"""
Intelligent Multi-Level Caching System with Advanced Invalidation Strategies.

This module provides a sophisticated caching architecture with multiple cache levels,
intelligent invalidation, predictive warming, and advanced analytics to optimize
performance across the distributed contract extraction system.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
import zlib
from collections import OrderedDict, defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

logger = logging.getLogger(__name__)

# Try to import cache libraries
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

try:
    import memcache
    HAS_MEMCACHE = True
except ImportError:
    HAS_MEMCACHE = False
    memcache = None


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "l1_memory"
    L2_DISTRIBUTED = "l2_distributed"
    L3_PERSISTENT = "l3_persistent"
    L4_COLD_STORAGE = "l4_cold_storage"


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TLRU = "tlru"  # Time-aware LRU
    ARC = "arc"  # Adaptive Replacement Cache
    RANDOM = "random"
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    TTL_BASED = "ttl_based"  # Time To Live based
    ADAPTIVE = "adaptive"  # Machine learning based


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "ttl"  # Time-based expiration
    DEPENDENCY = "dependency"  # Dependency-based invalidation
    VERSION = "version"  # Version-based invalidation
    EVENT_DRIVEN = "event_driven"  # Event-triggered invalidation
    PATTERN_BASED = "pattern_based"  # Pattern-based invalidation
    PREDICTIVE = "predictive"  # AI-driven predictive invalidation


class ConsistencyModel(Enum):
    """Cache consistency models."""
    EVENTUAL = "eventual"
    STRONG = "strong"
    WEAK = "weak"
    SESSION = "session"
    MONOTONIC_READ = "monotonic_read"
    CAUSAL = "causal"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    level: CacheLevel
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None
    version: str = "1.0"
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    compression_ratio: float = 1.0
    hit_probability: float = 0.0


@dataclass
class CacheStats:
    """Cache statistics."""
    level: CacheLevel
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    promotions: int = 0
    size_current: int = 0
    size_maximum: int = 0
    entries_count: int = 0
    access_time_avg: float = 0.0
    memory_efficiency: float = 0.0
    hit_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class InvalidationEvent:
    """Cache invalidation event."""
    event_id: str
    event_type: str
    affected_keys: Set[str]
    affected_patterns: Set[str]
    strategy: InvalidationStrategy
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryCache:
    """High-performance L1 memory cache."""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 256, policy: EvictionPolicy = EvictionPolicy.ADAPTIVE):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.policy = policy

        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = OrderedDict()  # For LRU
        self.access_frequency: Dict[str, int] = defaultdict(int)  # For LFU
        self.access_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))  # For TLRU

        # ARC (Adaptive Replacement Cache) data structures
        self.arc_t1 = OrderedDict()  # Recent pages
        self.arc_t2 = OrderedDict()  # Frequent pages
        self.arc_b1 = OrderedDict()  # Ghost entries for T1
        self.arc_b2 = OrderedDict()  # Ghost entries for T2
        self.arc_p = 0  # Target size for T1

        self.current_memory = 0
        self.stats = CacheStats(level=CacheLevel.L1_MEMORY, size_maximum=max_memory_mb)
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]

                # Check TTL
                if entry.ttl and time.time() > entry.created_at + entry.ttl:
                    self._evict_key(key)
                    self.stats.misses += 1
                    return None

                # Update access metadata
                entry.accessed_at = time.time()
                entry.access_count += 1

                # Update policy-specific structures
                self._update_access_structures(key)

                self.stats.hits += 1
                return entry.value
            else:
                self.stats.misses += 1
                return None

    def put(self, key: str, value: Any, ttl: Optional[float] = None, tags: Set[str] = None, dependencies: Set[str] = None) -> bool:
        """Put value in cache."""
        with self.lock:
            # Calculate entry size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 1024  # Fallback estimate

            # Check if we need to evict
            while (len(self.cache) >= self.max_size or
                   self.current_memory + size_bytes > self.max_memory_bytes):
                if not self._evict_one():
                    return False  # Cannot evict

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                level=CacheLevel.L1_MEMORY,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                size_bytes=size_bytes,
                ttl=ttl,
                tags=tags or set(),
                dependencies=dependencies or set()
            )

            # Store entry
            self.cache[key] = entry
            self.current_memory += size_bytes
            self.stats.entries_count += 1

            # Update policy structures
            self._update_policy_structures(key)

            return True

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific key."""
        with self.lock:
            if key in self.cache:
                self._evict_key(key)
                return True
            return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        with self.lock:
            keys_to_remove = []
            import fnmatch

            for key in self.cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._evict_key(key)

            return len(keys_to_remove)

    def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate entries with specific tags."""
        with self.lock:
            keys_to_remove = []

            for key, entry in self.cache.items():
                if entry.tags.intersection(tags):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._evict_key(key)

            return len(keys_to_remove)

    def _evict_one(self) -> bool:
        """Evict one entry based on policy."""
        if not self.cache:
            return False

        if self.policy == EvictionPolicy.LRU:
            key = next(iter(self.access_order))
        elif self.policy == EvictionPolicy.LFU:
            key = min(self.access_frequency.keys(), key=self.access_frequency.get)
        elif self.policy == EvictionPolicy.RANDOM:
            import random
            key = random.choice(list(self.cache.keys()))
        elif self.policy == EvictionPolicy.FIFO:
            key = next(iter(self.cache))
        elif self.policy == EvictionPolicy.ARC:
            key = self._arc_evict()
        else:  # ADAPTIVE or fallback to LRU
            key = self._adaptive_evict()

        self._evict_key(key)
        return True

    def _evict_key(self, key: str) -> None:
        """Remove a key from cache."""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory -= entry.size_bytes
            del self.cache[key]
            self.stats.entries_count -= 1
            self.stats.evictions += 1

            # Clean up policy structures
            self.access_order.pop(key, None)
            self.access_frequency.pop(key, None)
            self.access_times.pop(key, None)
            self.arc_t1.pop(key, None)
            self.arc_t2.pop(key, None)

    def _update_access_structures(self, key: str) -> None:
        """Update access tracking structures."""
        current_time = time.time()

        # Update access order (LRU)
        self.access_order.pop(key, None)
        self.access_order[key] = current_time

        # Update frequency (LFU)
        self.access_frequency[key] += 1

        # Update time-based access (TLRU)
        self.access_times[key].append(current_time)

        # Update ARC structures
        if key in self.arc_t1:
            self.arc_t2[key] = self.arc_t1.pop(key)
        elif key in self.arc_t2:
            self.arc_t2.move_to_end(key)

    def _update_policy_structures(self, key: str) -> None:
        """Update policy-specific structures when adding new entry."""
        current_time = time.time()

        self.access_order[key] = current_time
        self.access_frequency[key] = 1
        self.access_times[key].append(current_time)

        # For ARC, new entries go to T1
        self.arc_t1[key] = current_time

    def _arc_evict(self) -> str:
        """ARC eviction algorithm."""
        # Simplified ARC implementation
        if self.arc_t1 and len(self.arc_t1) >= self.arc_p:
            return next(iter(self.arc_t1))
        elif self.arc_t2:
            return next(iter(self.arc_t2))
        else:
            return next(iter(self.cache))

    def _adaptive_evict(self) -> str:
        """Adaptive eviction using multiple factors."""
        scores = {}
        current_time = time.time()

        for key, entry in self.cache.items():
            # Time-based score (older = higher eviction score)
            time_score = current_time - entry.accessed_at

            # Frequency-based score (less frequent = higher eviction score)
            freq_score = 1.0 / max(entry.access_count, 1)

            # Size-based score (larger = higher eviction score)
            size_score = entry.size_bytes / self.max_memory_bytes

            # Recency score (less recent = higher eviction score)
            access_times = self.access_times[key]
            if access_times:
                recency_score = current_time - access_times[-1]
            else:
                recency_score = time_score

            # Combined score (weighted average)
            combined_score = (time_score * 0.3 + freq_score * 0.3 +
                            size_score * 0.2 + recency_score * 0.2)
            scores[key] = combined_score

        # Return key with highest eviction score
        return max(scores.keys(), key=scores.get)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self.lock:
            self.stats.size_current = self.current_memory // (1024 * 1024)  # MB
            self.stats.hit_rate = self.stats.hits / max(self.stats.hits + self.stats.misses, 1) * 100
            self.stats.memory_efficiency = (self.current_memory / self.max_memory_bytes) * 100
            return self.stats


class DistributedCache:
    """L2 distributed cache using Redis/Memcached."""

    def __init__(self, redis_url: Optional[str] = None, prefix: str = "mce_l2"):
        self.prefix = prefix
        self.client = None

        if redis_url and HAS_REDIS:
            try:
                self.client = redis.Redis.from_url(redis_url, decode_responses=False)
                self.client.ping()  # Test connection
                self.cache_type = "redis"
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.client = None

        self.stats = CacheStats(level=CacheLevel.L2_DISTRIBUTED)
        self.serialization_cache = {}  # Cache serialized objects
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from distributed cache."""
        if not self.client:
            self.stats.misses += 1
            return None

        try:
            full_key = f"{self.prefix}:{key}"
            data = self.client.get(full_key)

            if data is not None:
                # Deserialize
                try:
                    # Try to decompress if compressed
                    if data.startswith(b'compressed:'):
                        data = zlib.decompress(data[11:])

                    value = pickle.loads(data)
                    self.stats.hits += 1
                    return value
                except Exception as e:
                    logger.error(f"Failed to deserialize cached value for {key}: {e}")
                    self.client.delete(full_key)  # Remove corrupted data

            self.stats.misses += 1
            return None

        except Exception as e:
            logger.error(f"Distributed cache get error for {key}: {e}")
            self.stats.misses += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None, compress: bool = True) -> bool:
        """Put value in distributed cache."""
        if not self.client:
            return False

        try:
            # Serialize value
            data = pickle.dumps(value)

            # Compress if beneficial
            if compress and len(data) > 1024:  # Only compress larger objects
                compressed = zlib.compress(data, level=6)
                if len(compressed) < len(data) * 0.8:  # Only use if 20%+ reduction
                    data = b'compressed:' + compressed

            full_key = f"{self.prefix}:{key}"

            if ttl:
                result = self.client.setex(full_key, ttl, data)
            else:
                result = self.client.set(full_key, data)

            return bool(result)

        except Exception as e:
            logger.error(f"Distributed cache put error for {key}: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific key."""
        if not self.client:
            return False

        try:
            full_key = f"{self.prefix}:{key}"
            return bool(self.client.delete(full_key))
        except Exception as e:
            logger.error(f"Distributed cache invalidate error for {key}: {e}")
            return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        if not self.client:
            return 0

        try:
            full_pattern = f"{self.prefix}:{pattern}"
            keys = self.client.keys(full_pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Distributed cache pattern invalidate error: {e}")
            return 0

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        if self.client:
            try:
                info = self.client.info()
                self.stats.size_current = info.get('used_memory', 0) // (1024 * 1024)  # MB
                self.stats.entries_count = info.get('db0', {}).get('keys', 0) if 'db0' in info else 0
            except:
                pass

        self.stats.hit_rate = self.stats.hits / max(self.stats.hits + self.stats.misses, 1) * 100
        return self.stats


class PersistentCache:
    """L3 persistent cache using SQLite/file system."""

    def __init__(self, cache_dir: str = "./cache/l3", max_size_gb: int = 5):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.db_path = self.cache_dir / "cache_index.db"

        # Initialize database
        self._init_database()

        self.stats = CacheStats(level=CacheLevel.L3_PERSISTENT, size_maximum=max_size_gb * 1024)
        self.lock = threading.RLock()

        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _init_database(self) -> None:
        """Initialize SQLite database for cache index."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    size_bytes INTEGER NOT NULL,
                    ttl REAL,
                    tags TEXT,
                    dependencies TEXT,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at ON cache_entries(accessed_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to initialize persistent cache database: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from persistent cache."""
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT file_path, created_at, ttl, access_count
                    FROM cache_entries WHERE key = ?
                """, (key,))

                result = cursor.fetchone()
                if not result:
                    conn.close()
                    self.stats.misses += 1
                    return None

                file_path, created_at, ttl, access_count = result

                # Check TTL
                if ttl and time.time() > created_at + ttl:
                    self._remove_entry(cursor, key, file_path)
                    conn.commit()
                    conn.close()
                    self.stats.misses += 1
                    return None

                # Load value from file
                full_path = self.cache_dir / file_path
                if not full_path.exists():
                    self._remove_entry(cursor, key, None)
                    conn.commit()
                    conn.close()
                    self.stats.misses += 1
                    return None

                try:
                    with open(full_path, 'rb') as f:
                        data = f.read()

                    # Check if compressed
                    if data.startswith(b'compressed:'):
                        data = zlib.decompress(data[11:])

                    value = pickle.loads(data)

                    # Update access information
                    cursor.execute("""
                        UPDATE cache_entries 
                        SET accessed_at = ?, access_count = access_count + 1 
                        WHERE key = ?
                    """, (time.time(), key))

                    conn.commit()
                    conn.close()

                    self.stats.hits += 1
                    return value

                except Exception as e:
                    logger.error(f"Failed to load cached file {full_path}: {e}")
                    self._remove_entry(cursor, key, file_path)
                    conn.commit()
                    conn.close()
                    self.stats.misses += 1
                    return None

            except Exception as e:
                logger.error(f"Persistent cache get error for {key}: {e}")
                self.stats.misses += 1
                return None

    def put(self, key: str, value: Any, ttl: Optional[float] = None, tags: Set[str] = None,
            dependencies: Set[str] = None, compress: bool = True) -> bool:
        """Put value in persistent cache."""
        with self.lock:
            try:
                # Serialize value
                data = pickle.dumps(value)

                # Compress if beneficial
                original_size = len(data)
                if compress and original_size > 2048:
                    compressed = zlib.compress(data, level=6)
                    if len(compressed) < original_size * 0.8:
                        data = b'compressed:' + compressed

                # Generate file path
                file_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
                file_path = f"cache_{file_hash}.pkl"
                full_path = self.cache_dir / file_path

                # Check space and clean if necessary
                self._ensure_space(len(data))

                # Write file
                with open(full_path, 'wb') as f:
                    f.write(data)

                # Update database
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()

                current_time = time.time()
                cursor.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, file_path, created_at, accessed_at, size_bytes, ttl, tags, dependencies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, file_path, current_time, current_time, len(data), ttl,
                    json.dumps(list(tags)) if tags else None,
                    json.dumps(list(dependencies)) if dependencies else None
                ))

                conn.commit()
                conn.close()

                self.stats.entries_count += 1
                return True

            except Exception as e:
                logger.error(f"Persistent cache put error for {key}: {e}")
                return False

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific key."""
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()

                cursor.execute("SELECT file_path FROM cache_entries WHERE key = ?", (key,))
                result = cursor.fetchone()

                if result:
                    file_path = result[0]
                    self._remove_entry(cursor, key, file_path)
                    conn.commit()
                    conn.close()
                    return True

                conn.close()
                return False

            except Exception as e:
                logger.error(f"Persistent cache invalidate error for {key}: {e}")
                return False

    def _remove_entry(self, cursor, key: str, file_path: Optional[str]) -> None:
        """Remove entry from database and file system."""
        try:
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))

            if file_path:
                full_path = self.cache_dir / file_path
                if full_path.exists():
                    full_path.unlink()

            self.stats.evictions += 1
            self.stats.entries_count = max(0, self.stats.entries_count - 1)

        except Exception as e:
            logger.error(f"Failed to remove cache entry {key}: {e}")

    def _ensure_space(self, required_bytes: int) -> None:
        """Ensure there's enough space for new entry."""
        try:
            # Get current size
            current_size = sum(f.stat().st_size for f in self.cache_dir.glob("cache_*.pkl") if f.is_file())

            if current_size + required_bytes <= self.max_size_bytes:
                return

            # Need to free space - remove oldest entries
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT key, file_path, size_bytes 
                FROM cache_entries 
                ORDER BY accessed_at ASC
            """)

            freed_bytes = 0
            target_bytes = required_bytes + (self.max_size_bytes * 0.1)  # 10% buffer

            for key, file_path, size_bytes in cursor.fetchall():
                if freed_bytes >= target_bytes:
                    break

                self._remove_entry(cursor, key, file_path)
                freed_bytes += size_bytes

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to ensure cache space: {e}")

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        try:
            loop = asyncio.get_event_loop()
            self.cleanup_task = loop.create_task(self._cleanup_loop())
        except RuntimeError:
            # No event loop running
            pass

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                with self.lock:
                    conn = sqlite3.connect(str(self.db_path))
                    cursor = conn.cursor()

                    current_time = time.time()

                    # Remove expired entries
                    cursor.execute("""
                        SELECT key, file_path FROM cache_entries 
                        WHERE ttl IS NOT NULL AND created_at + ttl < ?
                    """, (current_time,))

                    expired_entries = cursor.fetchall()
                    for key, file_path in expired_entries:
                        self._remove_entry(cursor, key, file_path)

                    conn.commit()
                    conn.close()

                    if expired_entries:
                        logger.info(f"Cleaned up {len(expired_entries)} expired cache entries")

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self.lock:
            try:
                # Calculate current size
                current_size = sum(f.stat().st_size for f in self.cache_dir.glob("cache_*.pkl") if f.is_file())
                self.stats.size_current = current_size // (1024 * 1024)  # MB

                # Get entry count from database
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cache_entries")
                self.stats.entries_count = cursor.fetchone()[0]
                conn.close()

            except Exception as e:
                logger.error(f"Failed to get persistent cache stats: {e}")

        self.stats.hit_rate = self.stats.hits / max(self.stats.hits + self.stats.misses, 1) * 100
        return self.stats


class InvalidationEngine:
    """Advanced cache invalidation engine."""

    def __init__(self):
        self.strategies: Dict[InvalidationStrategy, Callable] = {
            InvalidationStrategy.TTL: self._ttl_invalidation,
            InvalidationStrategy.DEPENDENCY: self._dependency_invalidation,
            InvalidationStrategy.VERSION: self._version_invalidation,
            InvalidationStrategy.EVENT_DRIVEN: self._event_driven_invalidation,
            InvalidationStrategy.PATTERN_BASED: self._pattern_invalidation,
            InvalidationStrategy.PREDICTIVE: self._predictive_invalidation
        }

        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # key -> dependents
        self.version_map: Dict[str, str] = {}
        self.event_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.invalidation_history: deque = deque(maxlen=1000)

        self.lock = threading.RLock()

    def register_dependency(self, key: str, depends_on: str) -> None:
        """Register a dependency relationship."""
        with self.lock:
            self.dependency_graph[depends_on].add(key)

    def register_version(self, key: str, version: str) -> None:
        """Register a version for a key."""
        with self.lock:
            self.version_map[key] = version

    def register_event_listener(self, event_type: str, callback: Callable) -> None:
        """Register an event listener for invalidation."""
        with self.lock:
            self.event_listeners[event_type].append(callback)

    def invalidate(self, key: str, strategy: InvalidationStrategy, cache_levels: List[Any], **kwargs) -> InvalidationEvent:
        """Execute invalidation with specified strategy."""
        event = InvalidationEvent(
            event_id=f"inv_{int(time.time() * 1000)}",
            event_type=f"{strategy.value}_invalidation",
            affected_keys=set(),
            affected_patterns=set(),
            strategy=strategy,
            metadata=kwargs
        )

        try:
            with self.lock:
                handler = self.strategies.get(strategy, self._ttl_invalidation)
                affected_keys = handler(key, cache_levels, **kwargs)
                event.affected_keys = affected_keys

                # Record invalidation
                self.invalidation_history.append(event)

                logger.info(f"Invalidation event {event.event_id} affected {len(affected_keys)} keys")

        except Exception as e:
            logger.error(f"Invalidation failed: {e}")
            event.metadata['error'] = str(e)

        return event

    def _ttl_invalidation(self, key: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """TTL-based invalidation."""
        affected_keys = set()

        for cache in cache_levels:
            if hasattr(cache, 'invalidate'):
                if cache.invalidate(key):
                    affected_keys.add(key)

        return affected_keys

    def _dependency_invalidation(self, key: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """Dependency-based invalidation."""
        affected_keys = {key}

        # Find all dependent keys
        to_process = [key]
        while to_process:
            current_key = to_process.pop()
            dependents = self.dependency_graph.get(current_key, set())

            for dependent in dependents:
                if dependent not in affected_keys:
                    affected_keys.add(dependent)
                    to_process.append(dependent)

        # Invalidate all affected keys
        for cache in cache_levels:
            for affected_key in affected_keys:
                if hasattr(cache, 'invalidate'):
                    cache.invalidate(affected_key)

        return affected_keys

    def _version_invalidation(self, key: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """Version-based invalidation."""
        new_version = kwargs.get('version')
        if not new_version:
            return set()

        old_version = self.version_map.get(key)
        if old_version == new_version:
            return set()  # No change

        self.version_map[key] = new_version
        affected_keys = {key}

        # Invalidate the key
        for cache in cache_levels:
            if hasattr(cache, 'invalidate'):
                cache.invalidate(key)

        return affected_keys

    def _event_driven_invalidation(self, key: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """Event-driven invalidation."""
        event_type = kwargs.get('event_type', 'generic')
        event_data = kwargs.get('event_data', {})

        affected_keys = set()

        # Notify event listeners
        for callback in self.event_listeners.get(event_type, []):
            try:
                callback_result = callback(key, event_data)
                if isinstance(callback_result, (set, list)):
                    affected_keys.update(callback_result)
            except Exception as e:
                logger.error(f"Event listener callback failed: {e}")

        # Invalidate affected keys
        for cache in cache_levels:
            for affected_key in affected_keys:
                if hasattr(cache, 'invalidate'):
                    cache.invalidate(affected_key)

        return affected_keys

    def _pattern_invalidation(self, pattern: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """Pattern-based invalidation."""
        affected_keys = set()

        for cache in cache_levels:
            if hasattr(cache, 'invalidate_by_pattern'):
                count = cache.invalidate_by_pattern(pattern)
                # Note: We can't get the exact keys, just the count
                affected_keys.add(f"pattern:{pattern}:{count}")

        return affected_keys

    def _predictive_invalidation(self, key: str, cache_levels: List[Any], **kwargs) -> Set[str]:
        """Predictive invalidation using ML models."""
        # Simplified predictive invalidation
        # In practice, this would use ML models to predict which keys should be invalidated

        confidence_threshold = kwargs.get('confidence_threshold', 0.8)
        affected_keys = {key}

        # Analyze invalidation history to predict related keys
        related_keys = self._analyze_invalidation_patterns(key, confidence_threshold)
        affected_keys.update(related_keys)

        # Invalidate predicted keys
        for cache in cache_levels:
            for affected_key in affected_keys:
                if hasattr(cache, 'invalidate'):
                    cache.invalidate(affected_key)

        return affected_keys

    def _analyze_invalidation_patterns(self, key: str, confidence_threshold: float) -> Set[str]:
        """Analyze historical patterns to predict related keys."""
        related_keys = set()

        try:
            # Simple co-occurrence analysis
            co_occurrences = defaultdict(int)
            total_events = 0

            for event in self.invalidation_history:
                if key in event.affected_keys:
                    total_events += 1
                    for other_key in event.affected_keys:
                        if other_key != key:
                            co_occurrences[other_key] += 1

            if total_events > 0:
                for other_key, count in co_occurrences.items():
                    confidence = count / total_events
                    if confidence >= confidence_threshold:
                        related_keys.add(other_key)

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")

        return related_keys


class IntelligentMultiLevelCache:
    """Intelligent multi-level cache with advanced features."""

    def __init__(self,
                 l1_config: Optional[Dict[str, Any]] = None,
                 l2_config: Optional[Dict[str, Any]] = None,
                 l3_config: Optional[Dict[str, Any]] = None):

        # Initialize cache levels
        l1_config = l1_config or {}
        self.l1_cache = MemoryCache(**l1_config)

        l2_config = l2_config or {}
        self.l2_cache = DistributedCache(**l2_config) if l2_config else None

        l3_config = l3_config or {}
        self.l3_cache = PersistentCache(**l3_config) if l3_config else None

        # Invalidation engine
        self.invalidation_engine = InvalidationEngine()

        # Cache warming system
        self.warming_patterns: Dict[str, int] = defaultdict(int)
        self.access_patterns: deque = deque(maxlen=10000)

        # Statistics
        self.global_stats = {
            'total_hits': 0,
            'total_misses': 0,
            'total_promotions': 0,
            'warming_hits': 0
        }

        self.lock = threading.RLock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        start_time = time.time()

        try:
            # L1 Cache (Memory)
            value = self.l1_cache.get(key)
            if value is not None:
                self._record_access(key, CacheLevel.L1_MEMORY, time.time() - start_time)
                self.global_stats['total_hits'] += 1
                return value

            # L2 Cache (Distributed)
            if self.l2_cache:
                value = self.l2_cache.get(key)
                if value is not None:
                    # Promote to L1
                    self.l1_cache.put(key, value)
                    self.global_stats['total_promotions'] += 1
                    self._record_access(key, CacheLevel.L2_DISTRIBUTED, time.time() - start_time)
                    self.global_stats['total_hits'] += 1
                    return value

            # L3 Cache (Persistent)
            if self.l3_cache:
                value = self.l3_cache.get(key)
                if value is not None:
                    # Promote to L2 and L1
                    if self.l2_cache:
                        self.l2_cache.put(key, value)
                    self.l1_cache.put(key, value)
                    self.global_stats['total_promotions'] += 1
                    self._record_access(key, CacheLevel.L3_PERSISTENT, time.time() - start_time)
                    self.global_stats['total_hits'] += 1
                    return value

            # Cache miss
            self.global_stats['total_misses'] += 1
            self._record_access(key, None, time.time() - start_time)
            return None

        except Exception as e:
            logger.error(f"Multi-level cache get error: {e}")
            self.global_stats['total_misses'] += 1
            return None

    async def put(self, key: str, value: Any,
                  ttl: Optional[float] = None,
                  tags: Set[str] = None,
                  dependencies: Set[str] = None,
                  warm_related: bool = True) -> bool:
        """Put value in multi-level cache."""
        try:
            success = False

            # Always put in L1
            if self.l1_cache.put(key, value, ttl, tags, dependencies):
                success = True

            # Put in L2 if available and value is significant
            if self.l2_cache:
                try:
                    size_estimate = len(pickle.dumps(value))
                    if size_estimate > 1024:  # Store larger objects in L2
                        self.l2_cache.put(key, value, int(ttl) if ttl else None)
                except:
                    pass

            # Put in L3 for persistence
            if self.l3_cache:
                self.l3_cache.put(key, value, ttl, tags, dependencies)

            # Warm related keys if requested
            if warm_related:
                await self._warm_related_keys(key)

            return success

        except Exception as e:
            logger.error(f"Multi-level cache put error: {e}")
            return False

    async def invalidate(self, key: str, strategy: InvalidationStrategy = InvalidationStrategy.TTL, **kwargs) -> bool:
        """Invalidate key across all cache levels."""
        try:
            cache_levels = [cache for cache in [self.l1_cache, self.l2_cache, self.l3_cache] if cache]

            event = self.invalidation_engine.invalidate(key, strategy, cache_levels, **kwargs)

            return len(event.affected_keys) > 0

        except Exception as e:
            logger.error(f"Multi-level cache invalidate error: {e}")
            return False

    def _record_access(self, key: str, level: Optional[CacheLevel], duration: float) -> None:
        """Record access pattern for analytics."""
        with self.lock:
            access_record = {
                'key': key,
                'level': level.value if level else 'miss',
                'timestamp': time.time(),
                'duration': duration
            }
            self.access_patterns.append(access_record)

            # Update warming patterns
            key_prefix = key.split(':')[0] if ':' in key else key[:10]
            self.warming_patterns[key_prefix] += 1

    async def _warm_related_keys(self, key: str) -> None:
        """Warm cache with related keys based on patterns."""
        try:
            # Analyze access patterns to find related keys
            key_prefix = key.split(':')[0] if ':' in key else key[:10]

            # Find recently accessed keys with similar patterns
            related_keys = []
            current_time = time.time()

            for access in reversed(list(self.access_patterns)):
                if current_time - access['timestamp'] > 300:  # Only last 5 minutes
                    break

                access_key = access['key']
                if access_key != key and access_key.startswith(key_prefix):
                    related_keys.append(access_key)

                if len(related_keys) >= 5:  # Limit warming
                    break

            # This is a placeholder - in practice, you'd generate values for these keys
            logger.debug(f"Would warm {len(related_keys)} related keys for {key}")

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'global': self.global_stats.copy(),
            'l1': self.l1_cache.get_stats().__dict__,
            'levels_active': sum(1 for cache in [self.l1_cache, self.l2_cache, self.l3_cache] if cache)
        }

        if self.l2_cache:
            stats['l2'] = self.l2_cache.get_stats().__dict__

        if self.l3_cache:
            stats['l3'] = self.l3_cache.get_stats().__dict__

        # Calculate overall hit rate
        total_requests = self.global_stats['total_hits'] + self.global_stats['total_misses']
        if total_requests > 0:
            stats['global']['overall_hit_rate'] = (self.global_stats['total_hits'] / total_requests) * 100
        else:
            stats['global']['overall_hit_rate'] = 0.0

        return stats


# Global cache instance
_intelligent_cache: Optional[IntelligentMultiLevelCache] = None


def get_intelligent_cache(
    l1_config: Optional[Dict[str, Any]] = None,
    l2_config: Optional[Dict[str, Any]] = None,
    l3_config: Optional[Dict[str, Any]] = None
) -> IntelligentMultiLevelCache:
    """Get the global intelligent multi-level cache instance."""
    global _intelligent_cache
    if _intelligent_cache is None:
        _intelligent_cache = IntelligentMultiLevelCache(l1_config, l2_config, l3_config)
    return _intelligent_cache


@asynccontextmanager
async def cache_context(key: str, ttl: Optional[float] = None) -> AsyncGenerator[Tuple[Optional[Any], Callable], None]:
    """Context manager for cache operations."""
    cache = get_intelligent_cache()
    value = await cache.get(key)

    def put_value(new_value: Any) -> None:
        asyncio.create_task(cache.put(key, new_value, ttl))

    try:
        yield value, put_value
    except Exception as e:
        logger.error(f"Cache context error: {e}")
        raise
