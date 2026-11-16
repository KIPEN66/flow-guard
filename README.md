# FlowGuard

[![CI Pipeline](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square&logo=githubactions)](https://github.com/KIPEN66/flow-guard)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

Lightweight, async-first fault tolerance and traffic control toolkit for Python microservices. Provides zero-dependency implementations of **Token Bucket Rate Limiting** and **Circuit Breakers**.

---

## Architecture: Circuit Breaker State Machine

```
      +---------+
      | CLOSED  | <-------------------+
      +----+----+                     |
           |                          |
           | consecutive_failures     | probe succeeds
           | >= threshold             |
           v                          |
      +----+----+                     |
      |  OPEN   |                     |
      +----+----+                     |
           |                          |
           | recovery_timeout elapsed |
           v                          |
      +----+----+                     |
      |HALF-OPEN| --------------------+
      +---------+
```

---

## Quickstart

### 1. Token Bucket Rate Limiter
```python
import asyncio
from flow_guard import TokenBucketLimiter, RateLimitExceeded

limiter = TokenBucketLimiter(default_capacity=100, default_refill_per_sec=10.0)

async def handle_request(client_id: str):
    try:
        await limiter.check(key=client_id, cost=1)
        return {"status": "processed"}
    except RateLimitExceeded as exc:
        return {"error": "Too Many Requests", "retry_after": exc.retry_after}
```

### 2. Circuit Breaker
```python
from flow_guard import CircuitBreaker, CircuitBreakerOpen

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15.0)

async def query_external_payment_api():
    try:
        return await breaker.call(fetch_payment_gateway)
    except CircuitBreakerOpen as exc:
        # Fast fail without saturating failing downstream service
        return {"error": "Payment gateway degraded", "reset_in": exc.reset_in}
```

---

## Testing

```bash
pytest -v tests/
```

---

## Roadmap & Active Issues

- [ ] **[#1] Redis Distributed Backend**: Share token bucket state across multiple worker replicas using Lua scripts.
- [ ] **[#2] Concurrency Bulkhead Decorator**: Add bounded semaphore concurrency protection to isolate failing subsystems.
- [ ] **[#3] Prometheus Telemetry Exporter**: Emit circuit state change counters and rejected request rate metrics.

---

## License

MIT License (c) 2026 KIPEN66.
