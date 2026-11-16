import asyncio
import time
from enum import Enum
from typing import Callable, Optional
from flow_guard.exceptions import CircuitBreakerOpen


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker state machine for protecting downstream services."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_success_needed: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_success_needed = half_open_success_needed

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._opened_at: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def _before_call(self) -> None:
        now = time.monotonic()
        if self._state == CircuitState.OPEN:
            if self._opened_at and (now - self._opened_at >= self.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._consecutive_successes = 0
            else:
                elapsed = now - (self._opened_at or now)
                remaining = max(0.0, self.recovery_timeout - elapsed)
                raise CircuitBreakerOpen(reset_in=remaining)

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.half_open_success_needed:
                    self._state = CircuitState.CLOSED
                    self._consecutive_failures = 0
                    self._opened_at = None
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def record_failure(self) -> None:
        async with self._lock:
            self._consecutive_failures += 1
            if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                if self._consecutive_failures >= self.failure_threshold or self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.monotonic()

    async def call(self, func: Callable, *args, **kwargs):
        """Execute async function guarded by circuit breaker."""
        async with self._lock:
            await self._before_call()

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception:
            await self.record_failure()
            raise
