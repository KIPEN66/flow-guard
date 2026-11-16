class FlowGuardError(Exception):
    """Base exception for all FlowGuard errors."""
    pass

class RateLimitExceeded(FlowGuardError):
    """Raised when rate limit quota is exceeded."""
    def __init__(self, retry_after: float):
        super().__init__(f"Rate limit exceeded. Try again in {retry_after:.2f}s")
        self.retry_after = retry_after

class CircuitBreakerOpen(FlowGuardError):
    """Raised when request is rejected because the circuit breaker is open."""
    def __init__(self, reset_in: float):
        super().__init__(f"Circuit is open. Service temporarily unavailable. Reset in {reset_in:.2f}s")
        self.reset_in = reset_in
