"""Универсальный асинхронный HTTP клиент."""

from .client import AsyncHTTPClient
from .config import ClientConfig
from .exceptions import (
    HTTPClientError,
    HTTPRequestError,
    HTTPResponseError,
    RateLimitError,
    RetryExhaustedError,
    CircuitBreakerOpenError,
    AuthenticationError,
    ConfigurationError,
)
from .models import (
    HTTPRequest,
    HTTPResponse,
    RetryConfig,
    RateLimitConfig,
    CircuitBreakerConfig,
)
from .auth import (
    AuthHandler,
    BearerAuth,
    APIKeyAuth,
    BasicAuth,
    OAuth2ClientCredentials,
)
from .middleware import (
    Middleware,
    MiddlewareManager,
    LoggingMiddleware,
    RetryMiddleware,
)
from .rate_limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)

__all__ = [
    # Main client
    "AsyncHTTPClient",
    "ClientConfig",
    
    # Exceptions
    "HTTPClientError",
    "HTTPRequestError",
    "HTTPResponseError",
    "RateLimitError",
    "RetryExhaustedError",
    "CircuitBreakerOpenError",
    "AuthenticationError",
    "ConfigurationError",
    
    # Models
    "HTTPRequest",
    "HTTPResponse",
    "RetryConfig",
    "RateLimitConfig",
    "CircuitBreakerConfig",
    
    # Auth
    "AuthHandler",
    "BearerAuth",
    "APIKeyAuth",
    "BasicAuth",
    "OAuth2ClientCredentials",
    
    # Middleware
    "Middleware",
    "MiddlewareManager",
    "LoggingMiddleware",
    "RetryMiddleware",
    
    # Rate Limiter
    "RateLimiter",
    "TokenBucketRateLimiter",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
]
