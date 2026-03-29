"""Redis-backed cache and rate limiter with graceful LRU fallback.

When REDIS_URL is set and reachable, uses Redis for:
- Search result caching (1h TTL)
- Distributed rate limiting (INCR + EXPIRE)

When Redis is unavailable, falls back silently to in-process LRUCache
and per-process RateLimiter from server.py.
"""

import json
import logging
import os
import time
from collections import OrderedDict

logger = logging.getLogger("dreams-atlas")

# ---------------------------------------------------------------------------
# In-memory LRU Cache (fallback)
# ---------------------------------------------------------------------------


class LRUCache:
    """Simple LRU cache backed by OrderedDict."""

    def __init__(self, capacity: int = 256):
        self._cache: OrderedDict[str, list] = OrderedDict()
        self._capacity = capacity

    async def get(self, key: str):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    async def put(self, key: str, value: list):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._capacity:
                self._cache.popitem(last=False)
        self._cache[key] = value

    @property
    def size(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# Redis Cache
# ---------------------------------------------------------------------------


class RedisCache:
    """Async Redis cache with connection pooling and TTL."""

    def __init__(self, redis_client, ttl: int = 3600):
        self._redis = redis_client
        self._ttl = ttl
        self._prefix = "dreams:cache:"

    async def get(self, key: str):
        try:
            raw = await self._redis.get(self._prefix + key)
            if raw is not None:
                return json.loads(raw)
        except Exception as exc:
            logger.warning(f"Redis cache GET failed: {exc}")
        return None

    async def put(self, key: str, value: list):
        try:
            await self._redis.set(
                self._prefix + key,
                json.dumps(value),
                ex=self._ttl,
            )
        except Exception as exc:
            logger.warning(f"Redis cache SET failed: {exc}")

    @property
    def size(self) -> int:
        return -1  # not cheaply queryable in Redis


# ---------------------------------------------------------------------------
# In-memory Rate Limiter (fallback)
# ---------------------------------------------------------------------------


class InMemoryRateLimiter:
    """Sliding-window rate limiter per IP address (single process)."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}

    async def is_allowed(self, ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        hits = self._hits.get(ip, [])
        hits = [t for t in hits if t > cutoff]
        if len(hits) >= self.max_requests:
            self._hits[ip] = hits
            return False
        hits.append(now)
        self._hits[ip] = hits
        return True


# ---------------------------------------------------------------------------
# Redis Rate Limiter (distributed INCR + EXPIRE)
# ---------------------------------------------------------------------------


class RedisRateLimiter:
    """Distributed sliding-window rate limiter using Redis INCR + EXPIRE."""

    def __init__(self, redis_client, max_requests: int = 60, window_seconds: int = 60):
        self._redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds
        self._prefix = "dreams:rate:"

    async def is_allowed(self, ip: str) -> bool:
        try:
            # Use a fixed window bucket (current window start second)
            bucket = int(time.time()) // self.window
            key = f"{self._prefix}{ip}:{bucket}"
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, self.window)
            return count <= self.max_requests
        except Exception as exc:
            logger.warning(f"Redis rate limiter failed, allowing request: {exc}")
            return True


# ---------------------------------------------------------------------------
# Factory: connect to Redis or fall back to in-memory
# ---------------------------------------------------------------------------

_redis_client = None


async def _try_connect_redis():
    """Attempt to connect to Redis. Returns client or None."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.info("REDIS_URL not set — using in-memory cache and rate limiter")
        return None

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # Verify connectivity
        await client.ping()
        logger.info(f"Connected to Redis at {redis_url.split('@')[-1]}")
        return client
    except Exception as exc:
        logger.warning(f"Redis connection failed ({exc}) — falling back to in-memory")
        return None


async def init_cache_and_limiter(
    cache_capacity: int = 512,
    cache_ttl: int = 3600,
    rate_max: int = 60,
    rate_window: int = 60,
) -> tuple:
    """Initialize and return (cache, rate_limiter, redis_client).

    Call once at app startup. The redis_client is exposed so /healthz
    can check connectivity.
    """
    global _redis_client
    _redis_client = await _try_connect_redis()

    if _redis_client is not None:
        cache = RedisCache(_redis_client, ttl=cache_ttl)
        limiter = RedisRateLimiter(_redis_client, max_requests=rate_max, window_seconds=rate_window)
    else:
        cache = LRUCache(capacity=cache_capacity)
        limiter = InMemoryRateLimiter(max_requests=rate_max, window_seconds=rate_window)

    return cache, limiter, _redis_client


async def check_redis_health() -> bool:
    """Return True if Redis is connected and responsive."""
    if _redis_client is None:
        return False
    try:
        await _redis_client.ping()
        return True
    except Exception:
        return False
