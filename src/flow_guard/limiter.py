import asyncio
import time
from typing import Dict, Optional
from flow_guard.exceptions import RateLimitExceeded


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def acquire(self, tokens: int = 1) -> None:
        async with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            needed = tokens - self.tokens
            retry_after = needed / self.refill_rate if self.refill_rate > 0 else 1.0
            raise RateLimitExceeded(retry_after=retry_after)


class TokenBucketLimiter:
    """Multi-tenant token bucket limiter with per-key partition."""

    def __init__(self, default_capacity: int = 60, default_refill_per_sec: float = 1.0) -> None:
        self.default_capacity = default_capacity
        self.default_refill = default_refill_per_sec
        self._buckets: Dict[str, TokenBucket] = {}
        self._global_lock = asyncio.Lock()

    async def get_bucket(self, key: str) -> TokenBucket:
        async with self._global_lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=self.default_capacity,
                    refill_rate_per_sec=self.default_refill,
                )
            return self._buckets[key]

    async def check(self, key: str = "default", cost: int = 1) -> None:
        bucket = await self.get_bucket(key)
        await bucket.acquire(tokens=cost)
