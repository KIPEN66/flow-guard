import asyncio
import pytest
from flow_guard.exceptions import RateLimitExceeded
from flow_guard.limiter import TokenBucket, TokenBucketLimiter


@pytest.mark.asyncio
async def test_token_bucket_exhaustion():
    bucket = TokenBucket(capacity=2, refill_rate_per_sec=10.0)
    await bucket.acquire(1)
    await bucket.acquire(1)

    with pytest.raises(RateLimitExceeded) as exc_info:
        await bucket.acquire(1)

    assert exc_info.value.retry_after > 0


@pytest.mark.asyncio
async def test_token_bucket_refill():
    bucket = TokenBucket(capacity=1, refill_rate_per_sec=20.0)
    await bucket.acquire(1)
    await asyncio.sleep(0.06)
    # Should succeed after refill
    await bucket.acquire(1)


@pytest.mark.asyncio
async def test_multi_tenant_limiter():
    limiter = TokenBucketLimiter(default_capacity=1, default_refill_per_sec=1.0)
    await limiter.check("user_a")
    # user_b has its own independent bucket
    await limiter.check("user_b")

    # user_a should now be rate limited
    with pytest.raises(RateLimitExceeded):
        await limiter.check("user_a")
