import logging
import hashlib
import json
from typing import Any, Optional
import redis

from app.core.config import settings

logger = logging.getLogger("app.cache")

class RedisCacheService:
    """
    Resilient Redis caching layer using RESP2 compatibility.
    Gracefully degrades to non-cached operations if Redis is unreachable.
    """
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        try:
            # Enforce RESP2 compatibility with protocol=2 for older local Redis versions
            self.redis_client = redis.Redis.from_url(
                settings.redis_url, 
                socket_timeout=2.0, 
                socket_connect_timeout=2.0,
                protocol=2,
                decode_responses=True
            )
            # Ping to confirm connection
            self.redis_client.ping()
            logger.info("Cache Service: Successfully connected to Redis.")
        except Exception as e:
            self.redis_client = None
            logger.warning(
                f"Cache Service: Redis connection failed ({str(e)}). "
                "Caching will be disabled for this session."
            )

    def is_available(self) -> bool:
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    def _generate_query_key(self, dataset_id: int, query: str) -> str:
        """Generate a unique MD5 hash cache key for a specific query and dataset."""
        normalized_query = query.strip().lower()
        query_hash = hashlib.md5(normalized_query.encode("utf-8")).hexdigest()
        return f"analysis:{dataset_id}:{query_hash}"

    def get_cached_query(self, dataset_id: int, query: str) -> Optional[dict]:
        """Retrieve cached query response from Redis if available."""
        if not self.is_available():
            return None
        key = self._generate_query_key(dataset_id, query)
        try:
            val = self.redis_client.get(key)
            if val:
                logger.info(f"Cache Service: HIT for key: {key}")
                return json.loads(val)
        except Exception as e:
            logger.error(f"Cache Service: Failed to get key {key}: {str(e)}")
        return None

    def set_cached_query(self, dataset_id: int, query: str, response_data: dict, expire_seconds: int = 7200):
        """Cache a query response in Redis."""
        if not self.is_available():
            return
        key = self._generate_query_key(dataset_id, query)
        try:
            self.redis_client.setex(
                key,
                expire_seconds,
                json.dumps(response_data)
            )
            logger.info(f"Cache Service: SET key: {key} (Expires in {expire_seconds}s)")
        except Exception as e:
            logger.error(f"Cache Service: Failed to set key {key}: {str(e)}")

    def invalidate_dataset_cache(self, dataset_id: int):
        """Remove all cached analysis runs associated with a dataset ID."""
        if not self.is_available():
            return
        pattern = f"analysis:{dataset_id}:*"
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cache Service: Invalidated {len(keys)} cache keys for dataset {dataset_id}")
        except Exception as e:
            logger.error(f"Cache Service: Failed to invalidate cache pattern {pattern}: {str(e)}")

# Singleton instance
cache_service = RedisCacheService()
