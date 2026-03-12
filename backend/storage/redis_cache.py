"""
Redis Cache - High-performance caching layer for market data and computed features.
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching layer with TTL support and pub/sub capabilities.
    Used for caching market data, features, and inter-service communication.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "aether:",
    ):
        self.prefix = prefix
        self._connected = False

        try:
            import redis
            self.client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=True, socket_timeout=5,
            )
            self._connected = True
            logger.info(f"Redis connected: {host}:{port}/{db}")
        except ImportError:
            logger.warning("Redis package not installed, using in-memory fallback")
            self.client = None
            self._memory_store: Dict[str, Any] = {}
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            self.client = None
            self._memory_store: Dict[str, Any] = {}

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        full_key = self._key(key)
        try:
            if self.client:
                val = self.client.get(full_key)
                return json.loads(val) if val else None
            return self._memory_store.get(full_key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set a value in cache with TTL (seconds)."""
        full_key = self._key(key)
        try:
            if self.client:
                self.client.setex(full_key, ttl, json.dumps(value, default=str))
            else:
                self._memory_store[full_key] = value
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        full_key = self._key(key)
        try:
            if self.client:
                self.client.delete(full_key)
            else:
                self._memory_store.pop(full_key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        for key in keys:
            val = self.get(key)
            if val is not None:
                results[key] = val
        return results

    def set_many(self, mapping: Dict[str, Any], ttl: int = 300) -> bool:
        """Set multiple values in cache."""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success

    def publish(self, channel: str, message: Any) -> None:
        """Publish a message to a Redis channel."""
        if self.client:
            try:
                self.client.publish(
                    f"{self.prefix}{channel}",
                    json.dumps(message, default=str),
                )
            except Exception as e:
                logger.error(f"Publish error: {e}")

    def flush_prefix(self) -> None:
        """Delete all keys with the configured prefix."""
        if self.client:
            try:
                keys = self.client.keys(f"{self.prefix}*")
                if keys:
                    self.client.delete(*keys)
            except Exception as e:
                logger.error(f"Flush error: {e}")
        else:
            self._memory_store.clear()

    def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            if self.client:
                return self.client.ping()
            return True  # In-memory always healthy
        except Exception:
            return False
