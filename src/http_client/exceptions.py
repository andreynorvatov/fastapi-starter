"""Исключения для HTTP клиента."""

from typing import Any, Dict, Optional


class HTTPClientError(Exception):
    """Базовое исключение для всех ошибок HTTP клиента."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class HTTPRequestError(HTTPClientError):
    """Ошибка при отправке HTTP запроса."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        details = {}
        if original_exception:
            details["original_exception"] = str(original_exception)
            details["exception_type"] = type(original_exception).__name__
        super().__init__(message, details)
        self.original_exception = original_exception


class HTTPResponseError(HTTPClientError):
    """Ошибка HTTP ответа (4xx, 5xx статусы)."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        response_content: Optional[bytes] = None,
        response_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        details = {
            "status_code": status_code,
        }
        if response_content:
            details["response_content"] = response_content.decode("utf-8", errors="replace")
        if response_headers:
            details["response_headers"] = dict(response_headers)
        
        super().__init__(message, details)
        self.status_code = status_code
        self.response_content = response_content
        self.response_headers = response_headers or {}


class RateLimitError(HTTPResponseError):
    """Превышен лимит запросов."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(status_code, message, **kwargs)
        self.retry_after = retry_after
        if retry_after is not None:
            self.details["retry_after"] = retry_after


class RetryExhaustedError(HTTPClientError):
    """Исчерпаны все попытки повторного отправки запроса."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None) -> None:
        details = {}
        if last_exception:
            details["last_exception"] = str(last_exception)
            details["exception_type"] = type(last_exception).__name__
        super().__init__(message, details)
        self.last_exception = last_exception


class CircuitBreakerOpenError(HTTPClientError):
    """Circuit breaker находится в открытом состоянии."""
    
    def __init__(
        self,
        message: str,
        circuit_breaker_state: str,
        recovery_timeout: float,
    ) -> None:
        details = {
            "circuit_breaker_state": circuit_breaker_state,
            "recovery_timeout": recovery_timeout,
        }
        super().__init__(message, details)
        self.circuit_breaker_state = circuit_breaker_state
        self.recovery_timeout = recovery_timeout


class AuthenticationError(HTTPClientError):
    """Ошибка аутентификации."""
    
    def __init__(self, message: str, auth_type: str) -> None:
        details = {"auth_type": auth_type}
        super().__init__(message, details)
        self.auth_type = auth_type


class ConfigurationError(HTTPClientError):
    """Ошибка конфигурации клиента."""
    
    def __init__(self, message: str, config_field: Optional[str] = None) -> None:
        details = {}
        if config_field:
            details["config_field"] = config_field
        super().__init__(message, details)
        self.config_field = config_field
