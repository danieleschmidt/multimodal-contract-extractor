"""
Advanced multi-level caching system for Generation 3 scaling.

This module provides intelligent caching with L1 in-memory, L2 Redis, L3 persistent
storage, cache warming, adaptive sizing, and performance analytics.
"""

import asyncio
import hashlib
import logging
import pickle
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels in the hierarchy."""
    L1_MEMORY = auto()
    L2_REDIS = auto()
    L3_PERSISTENT = auto()


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    RANDOM = "random"
    ADAPTIVE = "adaptive"  # AI-driven eviction


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    @property
    def age_seconds(self) -> float:
        """Get entry age in seconds."""
        return time.time() - self.created_at

    def touch(self) -> None:
        """Update access timestamp and count."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    avg_access_time: float = 0.0
    peak_size_bytes: int = 0
    peak_entry_count: int = 0
    warmup_completed: bool = False

    def update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        total_requests = self.hits + self.misses
        self.hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return asdict(self)


class CacheInterface(ABC):
    """Abstract cache interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def clear(self) -> int:
        """Clear all entries from cache."""
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass


class L1MemoryCache(CacheInterface):
    """L1 in-memory cache with intelligent eviction."""

    def __init__(
        self,
        max_size_mb: int = 128,
        max_entries: int = 10000,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        default_ttl: Optional[float] = None
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.eviction_policy = eviction_policy
        self.default_ttl = default_ttl

        self._cache: Dict[str, CacheEntry] = {}
        self._access_order = OrderedDict()  # For LRU
        self._frequency_counter = defaultdict(int)  # For LFU
        self._lock = RLock()
        self._stats = CacheStats()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        start_time = time.perf_counter()

        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._access_order.pop(key, None)
                self._stats.misses += 1
                self._stats.entry_count -= 1
                self._stats.update_hit_rate()
                return None

            # Update access patterns
            entry.touch()
            self._update_access_patterns(key)

            self._stats.hits += 1
            self._stats.update_hit_rate()

            # Update average access time
            access_time = time.perf_counter() - start_time
            if self._stats.avg_access_time == 0:
                self._stats.avg_access_time = access_time
            else:
                self._stats.avg_access_time = (
                    0.9 * self._stats.avg_access_time + 0.1 * access_time
                )

            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in L1 cache."""
        ttl = ttl or self.default_ttl

        # Calculate value size
        try:
            size_bytes = len(pickle.dumps(value))
        except Exception:
            size_bytes = 1024  # Fallback estimate

        with self._lock:
            # Check if we need to evict entries
            while (
                len(self._cache) >= self.max_entries or
                self._stats.size_bytes + size_bytes > self.max_size_bytes
            ):
                if not self._evict_entry():
                    break  # Couldn't evict anything

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size_bytes,
                ttl=ttl
            )

            # Update existing entry or add new one
            if key in self._cache:
                old_entry = self._cache[key]
                self._stats.size_bytes -= old_entry.size_bytes
            else:
                self._stats.entry_count += 1

            self._cache[key] = entry
            self._stats.size_bytes += size_bytes

            # Update peak stats
            self._stats.peak_size_bytes = max(self._stats.peak_size_bytes, self._stats.size_bytes)
            self._stats.peak_entry_count = max(self._stats.peak_entry_count, self._stats.entry_count)

            self._update_access_patterns(key)

            return True

    async def delete(self, key: str) -> bool:
        """Delete key from L1 cache."""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            del self._cache[key]
            self._access_order.pop(key, None)
            self._frequency_counter.pop(key, None)

            self._stats.size_bytes -= entry.size_bytes
            self._stats.entry_count -= 1

            return True

    async def clear(self) -> int:
        """Clear all entries from L1 cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            self._frequency_counter.clear()
            self._stats.size_bytes = 0
            self._stats.entry_count = 0
            return count

    def get_stats(self) -> CacheStats:
        """Get L1 cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size_bytes=self._stats.size_bytes,
                entry_count=self._stats.entry_count,
                hit_rate=self._stats.hit_rate,
                avg_access_time=self._stats.avg_access_time,
                peak_size_bytes=self._stats.peak_size_bytes,
                peak_entry_count=self._stats.peak_entry_count
            )

    def _update_access_patterns(self, key: str) -> None:
        """Update access patterns for eviction policies."""
        # Update LRU order
        self._access_order.pop(key, None)
        self._access_order[key] = time.time()

        # Update LFU counter
        self._frequency_counter[key] += 1

    def _evict_entry(self) -> bool:
        """Evict an entry based on eviction policy."""
        if not self._cache:
            return False

        key_to_evict = None

        if self.eviction_policy == EvictionPolicy.LRU:
            key_to_evict = next(iter(self._access_order))

        elif self.eviction_policy == EvictionPolicy.LFU:
            key_to_evict = min(self._frequency_counter, key=self._frequency_counter.get)

        elif self.eviction_policy == EvictionPolicy.TTL:
            # Find oldest entry
            oldest_key = None
            oldest_time = float('inf')
            for key, entry in self._cache.items():
                if entry.age_seconds < oldest_time:
                    oldest_time = entry.age_seconds
                    oldest_key = key
            key_to_evict = oldest_key

        elif self.eviction_policy == EvictionPolicy.ADAPTIVE:
            key_to_evict = self._adaptive_eviction()

        else:  # RANDOM
            key_to_evict = next(iter(self._cache))

        if key_to_evict:
            entry = self._cache[key_to_evict]
            del self._cache[key_to_evict]
            self._access_order.pop(key_to_evict, None)
            self._frequency_counter.pop(key_to_evict, None)

            self._stats.size_bytes -= entry.size_bytes
            self._stats.entry_count -= 1
            self._stats.evictions += 1

            return True

        return False

    def _adaptive_eviction(self) -> Optional[str]:
        """AI-driven adaptive eviction policy."""
        # Score entries based on multiple factors
        scored_entries = []

        for key, entry in self._cache.items():
            score = 0.0

            # Factor 1: Recency (0-1, higher is better)
            max_age = max(e.age_seconds for e in self._cache.values())
            if max_age > 0:
                recency_score = 1.0 - (entry.age_seconds / max_age)
                score += recency_score * 0.3

            # Factor 2: Frequency (0-1, higher is better)
            max_access = max(self._frequency_counter.values()) if self._frequency_counter else 1
            frequency_score = self._frequency_counter.get(key, 0) / max_access
            score += frequency_score * 0.4

            # Factor 3: Size efficiency (0-1, smaller is better for eviction)
            max_size = max(e.size_bytes for e in self._cache.values())
            if max_size > 0:
                size_score = entry.size_bytes / max_size
                score -= size_score * 0.2  # Penalty for large entries

            # Factor 4: TTL consideration (0-1, closer to expiration is worse)
            if entry.ttl:
                ttl_remaining = entry.ttl - entry.age_seconds
                if ttl_remaining <= 0:
                    score -= 1.0  # High penalty for expired
                elif entry.ttl > 0:
                    ttl_score = ttl_remaining / entry.ttl
                    score += ttl_score * 0.1

            scored_entries.append((score, key))

        # Return key with lowest score (best candidate for eviction)
        if scored_entries:
            scored_entries.sort()
            return scored_entries[0][1]

        return None

    def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired entries."""
        while True:
            try:
                time.sleep(60)  # Run every minute

                with self._lock:
                    expired_keys = []
                    for key, entry in self._cache.items():
                        if entry.is_expired:
                            expired_keys.append(key)

                    for key in expired_keys:
                        entry = self._cache[key]
                        del self._cache[key]
                        self._access_order.pop(key, None)
                        self._frequency_counter.pop(key, None)
                        self._stats.size_bytes -= entry.size_bytes
                        self._stats.entry_count -= 1

                    if expired_keys:
                        logger.debug(f"L1 cache cleanup: removed {len(expired_keys)} expired entries")

            except Exception as e:
                logger.error(f"L1 cache cleanup error: {e}")


class L2RedisCache(CacheInterface):
    """L2 Redis cache implementation."""

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "mce_l2"):
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis_client = None
        self._stats = CacheStats()
        self._initialize_redis()

    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis
            parsed_url = urlparse(self.redis_url)
            self.redis_client = redis.Redis(
                host=parsed_url.hostname or 'localhost',
                port=parsed_url.port or 6379,
                decode_responses=False  # Keep binary for pickle
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"L2 Redis cache connected: {self.redis_url}")
        except ImportError:
            logger.warning("Redis library not available for L2 cache")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to connect to Redis for L2 cache: {e}")
            self.redis_client = None

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L2 Redis cache."""
        if not self.redis_client:
            self._stats.misses += 1
            return None

        start_time = time.perf_counter()

        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)

            if data is None:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            # Deserialize data
            entry_data = pickle.loads(data)
            entry = CacheEntry(**entry_data)

            # Check expiration
            if entry.is_expired:
                self.redis_client.delete(redis_key)
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            self._stats.hits += 1
            self._stats.update_hit_rate()

            # Update average access time
            access_time = time.perf_counter() - start_time
            if self._stats.avg_access_time == 0:
                self._stats.avg_access_time = access_time
            else:
                self._stats.avg_access_time = (
                    0.9 * self._stats.avg_access_time + 0.1 * access_time
                )

            return entry.value

        except Exception as e:
            logger.error(f"L2 cache get error for key {key}: {e}")
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in L2 Redis cache."""
        if not self.redis_client:
            return False

        try:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl
            )

            # Serialize entry
            entry_data = asdict(entry)
            entry_data['tags'] = list(entry_data['tags'])  # Convert set to list
            data = pickle.dumps(entry_data)

            redis_key = self._make_key(key)

            # Set in Redis with TTL if specified
            if ttl:
                self.redis_client.setex(redis_key, int(ttl), data)
            else:
                self.redis_client.set(redis_key, data)

            return True

        except Exception as e:
            logger.error(f"L2 cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from L2 Redis cache."""
        if not self.redis_client:
            return False

        try:
            redis_key = self._make_key(key)
            result = self.redis_client.delete(redis_key)
            return result > 0

        except Exception as e:
            logger.error(f"L2 cache delete error for key {key}: {e}")
            return False

    async def clear(self) -> int:
        """Clear all entries from L2 Redis cache."""
        if not self.redis_client:
            return 0

        try:
            pattern = f"{self.prefix}:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                return self.redis_client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"L2 cache clear error: {e}")
            return 0

    def get_stats(self) -> CacheStats:
        """Get L2 cache statistics."""
        # Update entry count from Redis if possible
        if self.redis_client:
            try:
                pattern = f"{self.prefix}:*"
                keys = self.redis_client.keys(pattern)
                self._stats.entry_count = len(keys)
            except Exception:
                pass

        return self._stats


class L3PersistentCache(CacheInterface):
    """L3 persistent cache using file system."""

    def __init__(self, cache_dir: Union[str, Path] = "./cache/l3", max_size_mb: int = 1024):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._stats = CacheStats()
        self._lock = RLock()

        # Start maintenance thread
        self._maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._maintenance_thread.start()

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        # Hash key to create filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L3 persistent cache."""
        start_time = time.perf_counter()

        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return None

        try:
            with open(cache_file, 'rb') as f:
                entry_data = pickle.load(f)

            entry = CacheEntry(**entry_data)

            # Check expiration
            if entry.is_expired:
                cache_file.unlink()
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            # Update access time in metadata
            entry.touch()

            # Write back updated entry (async would be better)
            with open(cache_file, 'wb') as f:
                entry_data = asdict(entry)
                entry_data['tags'] = list(entry_data['tags'])
                pickle.dump(entry_data, f)

            self._stats.hits += 1
            self._stats.update_hit_rate()

            # Update average access time
            access_time = time.perf_counter() - start_time
            if self._stats.avg_access_time == 0:
                self._stats.avg_access_time = access_time
            else:
                self._stats.avg_access_time = (
                    0.9 * self._stats.avg_access_time + 0.1 * access_time
                )

            return entry.value

        except Exception as e:
            logger.error(f"L3 cache get error for key {key}: {e}")
            # Clean up corrupted file
            if cache_file.exists():
                cache_file.unlink()
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in L3 persistent cache."""
        cache_file = self._get_cache_file(key)

        try:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl
            )

            # Serialize to file
            with open(cache_file, 'wb') as f:
                entry_data = asdict(entry)
                entry_data['tags'] = list(entry_data['tags'])
                pickle.dump(entry_data, f)

            with self._lock:
                if not cache_file.exists():  # New entry
                    self._stats.entry_count += 1

                file_size = cache_file.stat().st_size
                self._stats.size_bytes += file_size
                self._stats.peak_size_bytes = max(self._stats.peak_size_bytes, self._stats.size_bytes)

            # Check if we need to evict old entries
            if self._stats.size_bytes > self.max_size_bytes:
                await self._evict_old_entries()

            return True

        except Exception as e:
            logger.error(f"L3 cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from L3 persistent cache."""
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return False

        try:
            file_size = cache_file.stat().st_size
            cache_file.unlink()

            with self._lock:
                self._stats.size_bytes -= file_size
                self._stats.entry_count -= 1

            return True

        except Exception as e:
            logger.error(f"L3 cache delete error for key {key}: {e}")
            return False

    async def clear(self) -> int:
        """Clear all entries from L3 persistent cache."""
        count = 0

        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
                count += 1

            with self._lock:
                self._stats.size_bytes = 0
                self._stats.entry_count = 0

            return count

        except Exception as e:
            logger.error(f"L3 cache clear error: {e}")
            return count

    def get_stats(self) -> CacheStats:
        """Get L3 cache statistics."""
        return self._stats

    async def _evict_old_entries(self) -> None:
        """Evict old entries to free space."""
        try:
            # Get all cache files with their modification times
            cache_files = []
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    stat = cache_file.stat()
                    cache_files.append((stat.st_mtime, cache_file, stat.st_size))
                except Exception:
                    continue

            # Sort by modification time (oldest first)
            cache_files.sort()

            # Remove files until we're under the limit
            current_size = self._stats.size_bytes
            target_size = int(self.max_size_bytes * 0.8)  # Leave some headroom

            for mtime, cache_file, file_size in cache_files:
                if current_size <= target_size:
                    break

                try:
                    cache_file.unlink()
                    current_size -= file_size
                    self._stats.evictions += 1
                except Exception:
                    continue

            with self._lock:
                self._stats.size_bytes = current_size

        except Exception as e:
            logger.error(f"L3 cache eviction error: {e}")

    def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes

                # Update stats
                total_size = 0
                count = 0

                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        total_size += cache_file.stat().st_size
                        count += 1
                    except Exception:
                        continue

                with self._lock:
                    self._stats.size_bytes = total_size
                    self._stats.entry_count = count

                # Clean up expired entries
                expired_count = 0
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        with open(cache_file, 'rb') as f:
                            entry_data = pickle.load(f)

                        entry = CacheEntry(**entry_data)
                        if entry.is_expired:
                            cache_file.unlink()
                            expired_count += 1

                    except Exception:
                        # Remove corrupted files
                        cache_file.unlink()
                        expired_count += 1

                if expired_count > 0:
                    logger.debug(f"L3 cache maintenance: removed {expired_count} expired/corrupted entries")

            except Exception as e:
                logger.error(f"L3 cache maintenance error: {e}")


class MultiLevelCache:
    """Multi-level hierarchical cache system."""

    def __init__(
        self,
        l1_config: Optional[Dict[str, Any]] = None,
        l2_config: Optional[Dict[str, Any]] = None,
        l3_config: Optional[Dict[str, Any]] = None,
        enable_cache_warming: bool = True
    ):
        # Initialize cache levels
        self.l1_cache = L1MemoryCache(**(l1_config or {}))
        self.l2_cache = L2RedisCache(**(l2_config or {})) if l2_config else None
        self.l3_cache = L3PersistentCache(**(l3_config or {})) if l3_config else None

        self.enable_cache_warming = enable_cache_warming
        self._warming_in_progress = set()
        self._warming_lock = RLock()

        # Cache analytics
        self._access_patterns = defaultdict(list)
        self._analytics_lock = RLock()

        logger.info(f"Multi-level cache initialized: L1={bool(self.l1_cache)}, "
                   f"L2={bool(self.l2_cache)}, L3={bool(self.l3_cache)}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache with promotion."""
        # Track access pattern
        self._track_access(key)

        # Try L1 first
        value = await self.l1_cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit L1: {key}")
            return value

        # Try L2 if available
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit L2: {key}, promoting to L1")
                # Promote to L1
                await self.l1_cache.set(key, value)
                return value

        # Try L3 if available
        if self.l3_cache:
            value = await self.l3_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit L3: {key}, promoting to L2 and L1")
                # Promote to higher levels
                if self.l2_cache:
                    await self.l2_cache.set(key, value)
                await self.l1_cache.set(key, value)
                return value

        # Cache miss at all levels
        logger.debug(f"Cache miss: {key}")

        # Trigger cache warming if enabled
        if self.enable_cache_warming:
            await self._consider_cache_warming(key)

        return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None, levels: Optional[Set[CacheLevel]] = None) -> bool:
        """Set value in specified cache levels."""
        if levels is None:
            levels = {CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_PERSISTENT}

        results = []

        # Set in L1
        if CacheLevel.L1_MEMORY in levels:
            result = await self.l1_cache.set(key, value, ttl)
            results.append(result)

        # Set in L2
        if CacheLevel.L2_REDIS in levels and self.l2_cache:
            result = await self.l2_cache.set(key, value, ttl)
            results.append(result)

        # Set in L3
        if CacheLevel.L3_PERSISTENT in levels and self.l3_cache:
            result = await self.l3_cache.set(key, value, ttl)
            results.append(result)

        return any(results)

    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels."""
        results = []

        # Delete from all levels
        results.append(await self.l1_cache.delete(key))

        if self.l2_cache:
            results.append(await self.l2_cache.delete(key))

        if self.l3_cache:
            results.append(await self.l3_cache.delete(key))

        return any(results)

    async def clear(self, levels: Optional[Set[CacheLevel]] = None) -> Dict[CacheLevel, int]:
        """Clear specified cache levels."""
        if levels is None:
            levels = {CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_PERSISTENT}

        results = {}

        if CacheLevel.L1_MEMORY in levels:
            results[CacheLevel.L1_MEMORY] = await self.l1_cache.clear()

        if CacheLevel.L2_REDIS in levels and self.l2_cache:
            results[CacheLevel.L2_REDIS] = await self.l2_cache.clear()

        if CacheLevel.L3_PERSISTENT in levels and self.l3_cache:
            results[CacheLevel.L3_PERSISTENT] = await self.l3_cache.clear()

        return results

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all cache levels."""
        stats = {
            'l1_stats': self.l1_cache.get_stats().to_dict(),
            'l2_stats': self.l2_cache.get_stats().to_dict() if self.l2_cache else None,
            'l3_stats': self.l3_cache.get_stats().to_dict() if self.l3_cache else None,
            'access_patterns': self._get_access_analytics(),
            'warming_stats': {
                'warming_in_progress': len(self._warming_in_progress),
                'warming_enabled': self.enable_cache_warming
            }
        }

        # Calculate overall hit rate
        total_hits = stats['l1_stats']['hits']
        total_misses = stats['l1_stats']['misses']

        if self.l2_cache:
            total_hits += stats['l2_stats']['hits']
            total_misses += stats['l2_stats']['misses']

        if self.l3_cache:
            total_hits += stats['l3_stats']['hits']
            total_misses += stats['l3_stats']['misses']

        total_requests = total_hits + total_misses
        stats['overall_hit_rate'] = total_hits / total_requests if total_requests > 0 else 0.0

        return stats

    def _track_access(self, key: str) -> None:
        """Track access patterns for analytics."""
        with self._analytics_lock:
            now = time.time()
            self._access_patterns[key].append(now)

            # Keep only recent accesses (last hour)
            cutoff = now - 3600
            self._access_patterns[key] = [
                t for t in self._access_patterns[key] if t > cutoff
            ]

    def _get_access_analytics(self) -> Dict[str, Any]:
        """Get access pattern analytics."""
        with self._analytics_lock:
            now = time.time()

            # Find hot keys (frequently accessed in last hour)
            hot_keys = []
            for key, accesses in self._access_patterns.items():
                recent_accesses = [t for t in accesses if t > now - 3600]
                if len(recent_accesses) >= 5:  # 5+ accesses in last hour
                    hot_keys.append((key, len(recent_accesses)))

            hot_keys.sort(key=lambda x: x[1], reverse=True)

            return {
                'total_tracked_keys': len(self._access_patterns),
                'hot_keys': hot_keys[:10],  # Top 10
                'avg_accesses_per_key': sum(len(accesses) for accesses in self._access_patterns.values()) / len(self._access_patterns) if self._access_patterns else 0
            }

    async def _consider_cache_warming(self, key: str) -> None:
        """Consider warming cache for related keys."""
        with self._warming_lock:
            if key in self._warming_in_progress:
                return

            # Simple warming strategy: if key follows a pattern, warm similar keys
            # This is a placeholder for more sophisticated warming algorithms

            if key.startswith('doc_') and key.endswith('_processed'):
                # Warm related document processing results
                base_key = key.replace('_processed', '')
                related_keys = [
                    f"{base_key}_metadata",
                    f"{base_key}_clauses",
                    f"{base_key}_summary"
                ]

                for related_key in related_keys:
                    if related_key not in self._warming_in_progress:
                        self._warming_in_progress.add(related_key)
                        # In a real implementation, this would trigger actual warming
                        # For now, just remove from warming set after a delay
                        asyncio.create_task(self._complete_warming(related_key))

    async def _complete_warming(self, key: str) -> None:
        """Complete cache warming for a key."""
        await asyncio.sleep(1)  # Simulate warming time
        with self._warming_lock:
            self._warming_in_progress.discard(key)


# Global multi-level cache instance
_global_cache: Optional[MultiLevelCache] = None


def get_advanced_cache(
    l1_config: Optional[Dict[str, Any]] = None,
    l2_config: Optional[Dict[str, Any]] = None,
    l3_config: Optional[Dict[str, Any]] = None
) -> MultiLevelCache:
    """Get global advanced cache instance."""
    global _global_cache

    if _global_cache is None:
        _global_cache = MultiLevelCache(l1_config, l2_config, l3_config)

    return _global_cache


@contextmanager
def cache_context(cache: MultiLevelCache, key_prefix: str = ""):
    """Context manager for cache operations."""
    start_time = time.perf_counter()

    try:
        yield cache
    finally:
        duration = time.perf_counter() - start_time
        logger.debug(f"Cache context '{key_prefix}' completed in {duration:.3f}s")
