"""Конфигурация HTTP клиента."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClientConfig:
    """
    Конфигурация HTTP клиента.
    
    Attributes:
        timeout: Таймаут запроса в секундах
        max_connections: Максимальное количество одновременных соединений
        max_keepalive_connections: Максимальное количество keepalive соединений
        keepalive_expiry: Время жизни keepalive соединения в секундах
        follow_redirects: Следовать за редиректами автоматически
        verify_ssl: Проверять SSL сертификаты
        retry_attempts: Количество попыток повторной отправки
        retry_backoff_factor: Множитель для экспоненциальной задержки
        retry_max_delay: Максимальная задержка между попытками в секундах
        retry_statuses: HTTP статусы для повторных попыток
        retry_methods: HTTP методы для повторных попыток
        enable_rate_limiting: Включить ограничение частоты запросов
        rate_limit_rate: Лимит запросов в секунду
        rate_limit_burst: Максимальный бакет (burst)
        enable_circuit_breaker: Включить circuit breaker
        circuit_breaker_failure_threshold: Порог срабатывания circuit breaker
        circuit_breaker_recovery_timeout: Время восстановления circuit breaker
    """
    
    timeout: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    follow_redirects: bool = False
    verify_ssl: bool = True
    
    # Retry configuration
    retry_attempts: int = 3
    retry_backoff_factor: float = 1.0
    retry_max_delay: float = 60.0
    retry_statuses: set[int] = field(default_factory=lambda: {408, 429, 500, 502, 503, 504})
    retry_methods: set[str] = field(default_factory=lambda: {"GET", "POST", "PUT", "DELETE", "PATCH"})
    
    # Rate limiting
    enable_rate_limiting: bool = False
    rate_limit_rate: float = 10.0
    rate_limit_burst: int = 1
    
    # Circuit breaker
    enable_circuit_breaker: bool = False
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    
    def __post_init__(self) -> None:
        """Нормализация множеств."""
        self.retry_statuses = set(self.retry_statuses)
        self.retry_methods = {m.upper() for m in self.retry_methods}
