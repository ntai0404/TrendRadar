"""
Caching service

Implement TTL caching mechanism to improve data access performance.
"""

import hashlib
import json
import time
from typing import Any, Optional
from threading import Lock


def make_cache_key(namespace: str, **params) -> str:
    """
    Generate structured cache key

    By sorting and hashing parameters, it is ensured that the same parameter combination always generates the same key.

    Args:
        namespace: cache namespace, such as "latest_news", "trending_topics"
        **params: cache parameters

    Returns:
        Formatted cache key, such as "latest_news:a1b2c3d4"

    Examples:
        >>> make_cache_key("latest_news", platforms=["zhihu"], limit=50)
        'latest_news:8f14e45f'
        >>> make_cache_key("search", query="AI", mode="keyword")
        'search:3c6e0b8a'
    """
    if not params:
        return namespace

    # Normalize parameters
    normalized_params = {}
    for k, v in params.items():
        if v is None:
            continue # skip None values
        elif isinstance(v, (list, tuple)):
            # Convert the list to string after sorting
            normalized_params[k] = json.dumps(sorted(v) if all(isinstance(i, str) for i in v) else list(v), ensure_ascii=False)
        elif isinstance(v, dict):
            # Sort the dictionary by key and convert it to a string
            normalized_params[k] = json.dumps(v, sort_keys=True, ensure_ascii=False)
        else:
            normalized_params[k] = str(v)

    # Sort parameters and generate hash
    sorted_params = sorted(normalized_params.items())
    param_str = "&".join(f"{k}={v}" for k, v in sorted_params)

    # Use MD5 to generate a short hash (take the first 8 bits)
    hash_value = hashlib.md5(param_str.encode('utf-8')).hexdigest()[:8]

    return f"{namespace}:{hash_value}"


class CacheService:
    """Cache service class"""

    def __init__(self):
        """Initialize cache service"""
        self._cache = {}
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key: str, ttl: int = 900) -> Optional[Any]:
        """
        Get cached data

        Args:
            key: cache key
            ttl: survival time (seconds), default 15 minutes

        Returns:
            The cached value, returns None if it does not exist or has expired
        """
        with self._lock:
            if key in self._cache:
                # Check if it is expired
                if time.time() - self._timestamps[key] < ttl:
                    return self._cache[key]
                else:
                    # Expired, delete cache
                    del self._cache[key]
                    del self._timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set cache data

        Args:
            key: cache key
            value: cache value
        """
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()

    def delete(self, key: str) -> bool:
        """
        Delete cache

        Args:
            key: cache key

        Returns:
            Deleted successfully or not
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
        return False

    def clear(self) -> None:
        """Clear all caches"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def cleanup_expired(self, ttl: int = 900) -> int:
        """
        Clear expired cache

        Args:
            ttl: time to live (seconds)

        Returns:
            Number of entries cleaned
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if current_time - timestamp >= ttl
            ]

            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]

            return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Statistics Dictionary
        """
        with self._lock:
            return {
                "total_entries": len(self._cache),
                "oldest_entry_age": (
                    time.time() - min(self._timestamps.values())
                    if self._timestamps else 0
                ),
                "newest_entry_age": (
                    time.time() - max(self._timestamps.values())
                    if self._timestamps else 0
                )
            }


# Global cache instance
_global_cache = None


def get_cache() -> CacheService:
    """
    Get global cache instance

    Returns:
        Global cache service instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache
