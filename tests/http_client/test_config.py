"""Тесты для конфигурации клиента."""

import pytest

from src.http_client.config import ClientConfig


def test_client_config_defaults() -> None:
    """Тест значений по умолчанию."""
    config = ClientConfig()
    assert config.timeout == 30.0
    assert config.max_connections == 100
    assert config.max_keepalive_connections == 20
    assert config.retry_attempts == 3
    assert config.retry_backoff_factor == 1.0
    assert config.enable_rate_limiting is False
    assert config.enable_circuit_breaker is False


def test_client_config_custom() -> None:
    """Тест кастомной конфигурации."""
    config = ClientConfig(
        timeout=60.0,
        max_connections=200,
        retry_attempts=5,
        retry_backoff_factor=2.0,
        enable_rate_limiting=True,
        rate_limit_rate=20.0,
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=10,
    )
    assert config.timeout == 60.0
    assert config.max_connections == 200
    assert config.retry_attempts == 5
    assert config.retry_backoff_factor == 2.0
    assert config.enable_rate_limiting is True
    assert config.rate_limit_rate == 20.0
    assert config.enable_circuit_breaker is True
    assert config.circuit_breaker_failure_threshold == 10


def test_client_config_post_init_normalization() -> None:
    """Тест нормализации множеств в __post_init__."""
    config = ClientConfig(
        retry_statuses={408, 429, 500},
        retry_methods={"get", "post", "PUT"},
    )
    assert config.retry_statuses == {408, 429, 500}
    assert all(isinstance(s, int) for s in config.retry_statuses)
    assert config.retry_methods == {"GET", "POST", "PUT"}
    assert all(m.isupper() for m in config.retry_methods)
