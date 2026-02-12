"""Circuit breaker для HTTP клиента."""

from .breaker import CircuitBreaker, CircuitState

__all__ = [
    "CircuitBreaker",
    "CircuitState",
]
