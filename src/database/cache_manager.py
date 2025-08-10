"""Cache management for OCR results and processed documents."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of OCR results and processed documents for performance optimization."""

    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 100):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage. If None, uses ./cache
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = Path(cache_dir or "./cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def get_file_hash(self, file_path: Path) -> str:
        """
        Generate a hash for a file based on its content and metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of the file
        """
        hasher = hashlib.sha256()

        # Include file size and modification time in hash
        try:
            stat = file_path.stat()
            hasher.update(str(stat.st_size).encode())
            hasher.update(str(stat.st_mtime).encode())
        except OSError:
            pass

        # Hash file content in chunks
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except OSError as e:
            logger.warning(f"Could not read file for hashing: {e}")
            # Fallback to path-based hash
            hasher.update(str(file_path).encode())

        return hasher.hexdigest()

    def get_ocr_result(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get cached OCR result for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cached OCR result if available, None otherwise
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cache_file = self.cache_dir / f"ocr_{file_hash}.pkl"

            if not cache_file.exists():
                return None

            # Check if cache is still valid (file hasn't changed)
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Verify file hash matches
            if cached_data.get('file_hash') != file_hash:
                cache_file.unlink()  # Remove invalid cache
                return None

            # Update access time
            cached_data['last_accessed'] = time.time()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"OCR cache hit for {file_path.name}")
            return cached_data.get('result')

        except Exception as e:
            logger.warning(f"Error reading OCR cache for {file_path}: {e}")
            return None

    def store_ocr_result(self, file_path: Path, result: Dict[str, Any]) -> bool:
        """
        Store OCR result in cache.
        
        Args:
            file_path: Path to the source file
            result: OCR result to cache
            
        Returns:
            True if caching was successful, False otherwise
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cache_file = self.cache_dir / f"ocr_{file_hash}.pkl"

            cached_data = {
                'file_hash': file_hash,
                'file_path': str(file_path),
                'result': result,
                'created_at': time.time(),
                'last_accessed': time.time(),
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"OCR result cached for {file_path.name}")

            # Clean up cache if it's getting too large
            self._cleanup_cache_if_needed()

            return True

        except Exception as e:
            logger.warning(f"Error storing OCR cache for {file_path}: {e}")
            return False

    def get_document_processing_result(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get cached document processing result.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cached processing result if available, None otherwise
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cache_file = self.cache_dir / f"doc_{file_hash}.pkl"

            if not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Verify file hash matches
            if cached_data.get('file_hash') != file_hash:
                cache_file.unlink()
                return None

            # Update access time
            cached_data['last_accessed'] = time.time()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Document processing cache hit for {file_path.name}")
            return cached_data.get('result')

        except Exception as e:
            logger.warning(f"Error reading document cache for {file_path}: {e}")
            return None

    def store_document_processing_result(self, file_path: Path, result: Dict[str, Any]) -> bool:
        """
        Store document processing result in cache.
        
        Args:
            file_path: Path to the source file
            result: Processing result to cache
            
        Returns:
            True if caching was successful, False otherwise
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cache_file = self.cache_dir / f"doc_{file_hash}.pkl"

            cached_data = {
                'file_hash': file_hash,
                'file_path': str(file_path),
                'result': result,
                'created_at': time.time(),
                'last_accessed': time.time(),
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Document processing result cached for {file_path.name}")

            # Clean up cache if needed
            self._cleanup_cache_if_needed()

            return True

        except Exception as e:
            logger.warning(f"Error storing document cache for {file_path}: {e}")
            return False

    def clear_cache(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
                deleted_count += 1

            logger.info(f"Cleared {deleted_count} cache files")
            return deleted_count

        except Exception as e:
            logger.exception(f"Error clearing cache: {e}")
            return deleted_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            ocr_files = list(self.cache_dir.glob("ocr_*.pkl"))
            doc_files = list(self.cache_dir.glob("doc_*.pkl"))

            total_size = sum(f.stat().st_size for f in ocr_files + doc_files)

            return {
                'ocr_cache_files': len(ocr_files),
                'document_cache_files': len(doc_files),
                'total_files': len(ocr_files) + len(doc_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': str(self.cache_dir),
                'max_size_mb': self.max_size_bytes // (1024 * 1024),
            }

        except Exception as e:
            logger.exception(f"Error getting cache stats: {e}")
            return {'error': str(e)}

    def _cleanup_cache_if_needed(self) -> None:
        """Clean up old cache files if cache size exceeds limit."""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))

            # Calculate total size
            total_size = sum(f.stat().st_size for f in cache_files)

            if total_size <= self.max_size_bytes:
                return

            logger.info(f"Cache size {total_size / (1024*1024):.1f}MB exceeds limit, cleaning up...")

            # Sort files by last access time (oldest first)
            files_with_access_time = []
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)

                    access_time = cached_data.get('last_accessed', cache_file.stat().st_mtime)
                    files_with_access_time.append((access_time, cache_file))

                except Exception:
                    # If we can't read the file, consider it for deletion
                    files_with_access_time.append((0, cache_file))

            files_with_access_time.sort(key=lambda x: x[0])

            # Delete oldest files until we're under the limit
            deleted_count = 0
            current_size = total_size

            for _, cache_file in files_with_access_time:
                if current_size <= self.max_size_bytes * 0.8:  # Leave some headroom
                    break

                try:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    current_size -= file_size
                    deleted_count += 1

                except Exception as e:
                    logger.warning(f"Error deleting cache file {cache_file}: {e}")

            logger.info(f"Deleted {deleted_count} old cache files")

        except Exception as e:
            logger.exception(f"Error during cache cleanup: {e}")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_dir: Optional[str] = None, max_size_mb: int = 100) -> CacheManager:
    """
    Get the global cache manager instance.
    
    Args:
        cache_dir: Cache directory (only used on first call)
        max_size_mb: Maximum cache size in MB (only used on first call)
        
    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, max_size_mb)

    return _cache_manager
