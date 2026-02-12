"""Модели данных для HTTP клиента."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type

from .exceptions import HTTPResponseError


@dataclass
class HTTPRequest:
    """Представление HTTP запроса."""
    
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    json: Optional[Any] = None
    data: Optional[Any] = None
    timeout: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Валидация после инициализации."""
        self.method = self.method.upper()
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        if self.method not in valid_methods:
            raise ValueError(f"Недопустимый HTTP метод: {self.method}. Допустимые: {valid_methods}")


@dataclass
class HTTPResponse:
    """Представление HTTP ответа."""
    
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    request: Optional[HTTPRequest] = None
    
    @property
    def json_data(self) -> Optional[Any]:
        """Возвращает распарсенный JSON, если содержимое в JSON формате."""
        import json
        if not self.content:
            return None
        try:
            return json.loads(self.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    def raise_for_status(self) -> None:
        """Вызывает HTTPResponseError если статус код указывает на ошибку."""
        from .exceptions import HTTPResponseError
        
        if 400 <= self.status_code < 600:
            message = f"HTTP {self.status_code} ошибка"
            raise HTTPResponseError(
                status_code=self.status_code,
                message=message,
                response_content=self.content,
                response_headers=self.headers,
            )
    
    def is_success(self) -> bool:
        """Проверяет, является ли ответ успешным (2xx-3xx)."""
        return 200 <= self.status_code < 400
    
    def is_error(self) -> bool:
        """Проверяет, является ли ответ ошибкой (4xx-5xx)."""
        return 400 <= self.status_code < 600
    
    def is_client_error(self) -> bool:
        """Проверяет, является ли ответ клиентской ошибкой (4xx)."""
        return 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """Проверяет, является ли ответ серверной ошибкой (5xx)."""
        return 500 <= self.status_code < 600


@dataclass
class RetryConfig:
    """Конфигурация повторных попыток."""
    
    attempts: int = 3
    backoff_factor: float = 1.0
    max_delay: float = 60.0
    statuses: set[int] = field(default_factory=lambda: {408, 429, 500, 502, 503, 504})
    methods: set[str] = field(default_factory=lambda: {"GET", "POST", "PUT", "DELETE", "PATCH"})
    
    def __post_init__(self) -> None:
        """Нормализует множества."""
        self.statuses = set(self.statuses)
        self.methods = {m.upper() for m in self.methods}


@dataclass
class RateLimitConfig:
    """Конфигурация ограничения частоты запросов."""
    
    rate: float  # запросов в секунду
    burst: int = 1  # максимальный размер бакета
    enabled: bool = True


@dataclass
class CircuitBreakerConfig:
    """Конфигурация circuit breaker."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = HTTPResponseError
    enabled: bool = True
