"""Тесты для исключений."""

import pytest

from src.http_client.exceptions import (
    HTTPClientError,
    HTTPRequestError,
    HTTPResponseError,
    RateLimitError,
    RetryExhaustedError,
    CircuitBreakerOpenError,
    AuthenticationError,
    ConfigurationError,
)


def test_http_client_error_basic() -> None:
    """Тест базового исключения."""
    exc = HTTPClientError("Test message")
    assert str(exc) == "Test message"
    assert exc.message == "Test message"
    assert exc.details == {}


def test_http_client_error_with_details() -> None:
    """Тест исключения с деталями."""
    details = {"key": "value", "number": 42}
    exc = HTTPClientError("Test message", details)
    assert str(exc) == "Test message: {'key': 'value', 'number': 42}"
    assert exc.details == details


def test_http_request_error() -> None:
    """Тест исключения запроса."""
    original = ValueError("Original error")
    exc = HTTPRequestError("Request failed", original_exception=original)
    assert exc.original_exception is original
    assert "original_exception" in exc.details
    assert exc.details["exception_type"] == "ValueError"


def test_http_response_error() -> None:
    """Тест исключения ответа."""
    content = b'{"error": "test"}'
    headers = {"Content-Type": "application/json"}
    exc = HTTPResponseError(
        status_code=404,
        message="Not found",
        response_content=content,
        response_headers=headers,
    )
    assert exc.status_code == 404
    assert exc.response_content == content
    assert exc.response_headers == headers
    assert "response_content" in exc.details
    assert "response_headers" in exc.details


def test_rate_limit_error() -> None:
    """Тест исключения rate limit."""
    exc = RateLimitError(429, "Too many requests", retry_after=60)
    assert exc.retry_after == 60
    assert exc.details["retry_after"] == 60


def test_retry_exhausted_error() -> None:
    """Тест исключения исчерпания попыток."""
    original = TimeoutError("Timeout")
    exc = RetryExhaustedError("All retries exhausted", last_exception=original)
    assert exc.last_exception is original
    assert "last_exception" in exc.details


def test_circuit_breaker_open_error() -> None:
    """Тест исключения circuit breaker."""
    exc = CircuitBreakerOpenError(
        "Circuit breaker is open",
        circuit_breaker_state="open",
        recovery_timeout=30.0,
    )
    assert exc.circuit_breaker_state == "open"
    assert exc.recovery_timeout == 30.0
    assert exc.details["circuit_breaker_state"] == "open"


def test_authentication_error() -> None:
    """Тест исключения аутентификации."""
    exc = AuthenticationError("Invalid token", auth_type="bearer")
    assert exc.auth_type == "bearer"
    assert exc.details["auth_type"] == "bearer"


def test_configuration_error() -> None:
    """Тест исключения конфигурации."""
    exc = ConfigurationError("Invalid config", config_field="timeout")
    assert exc.config_field == "timeout"
    assert exc.details["config_field"] == "timeout"
