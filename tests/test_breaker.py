import asyncio
import pytest
from flow_guard.breaker import CircuitBreaker, CircuitState
from flow_guard.exceptions import CircuitBreakerOpen


@pytest.mark.asyncio
async def test_circuit_trips_to_open_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    async def faulty_task():
        raise RuntimeError("database down")

    with pytest.raises(RuntimeError):
        await breaker.call(faulty_task)

    assert breaker.state == CircuitState.CLOSED

    with pytest.raises(RuntimeError):
        await breaker.call(faulty_task)

    assert breaker.state == CircuitState.OPEN

    # Fast fail while open
    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(faulty_task)


@pytest.mark.asyncio
async def test_circuit_recovers_to_closed():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, half_open_success_needed=1)

    async def fail():
        raise RuntimeError("temporary blip")

    async def succeed():
        return "ok"

    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    await asyncio.sleep(0.06)

    # First call will probe in HALF_OPEN and succeed -> state transitions back to CLOSED
    result = await breaker.call(succeed)
    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED
