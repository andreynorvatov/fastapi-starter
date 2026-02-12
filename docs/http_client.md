# Универсальный асинхронный HTTP клиент

## Оглавление

1. [Обзор](#обзор)
2. [Установка](#установка)
3. [Быстрый старт](#быстрый-старт)
4. [Конфигурация](#конфигурация)
5. [Аутентификация](#аутентификация)
6. [Повторные попытки (Retry)](#повторные-попытки-retry)
7. [Ограничение частоты (Rate Limiting)](#ограничение-частоты-rate-limiting)
8. [Circuit Breaker](#circuit-breaker)
9. [Middleware](#middleware)
10. [Обработка ошибок](#обработка-ошибок)
11. [Примеры](#примеры)
12. [Тестирование](#тестирование)

## Обзор

Универсальный асинхронный HTTP клиент для Python, построенный на базе `httpx` и `FastAPI`. Предоставляет:

- ✅ Асинхронные запросы с connection pooling
- ✅ Гибкая конфигурация
- ✅ Несколько типов аутентификации (Bearer, API Key, Basic, OAuth2)
- ✅ Автоматические повторные попытки (retry) с экспоненциальной задержкой
- ✅ Ограничение частоты запросов (rate limiting) на основе Token Bucket
- ✅ Защита от каскадных сбоев (Circuit Breaker)
- ✅ Расширяемая система middleware
- ✅ Детальное логирование
- ✅ Полная типизация

## Установка

```bash
# Уже включено в проект как часть fastapi-starter
# httpx добавлен в зависимости pyproject.toml
```

## Быстрый старт

```python
import asyncio
from src.http_client import AsyncHTTPClient, ClientConfig

async def main():
    config = ClientConfig(timeout=30.0)
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        config=config,
    ) as client:
        response = await client.get("/users")
        data = response.json_data
        print(data)

asyncio.run(main())
```

## Конфигурация

### ClientConfig

```python
from src.http_client import ClientConfig

config = ClientConfig(
    # Основные настройки
    timeout=30.0,                    # Таймаут запроса (секунды)
    max_connections=100,             # Макс. количество соединений
    max_keepalive_connections=20,    # Макс. keepalive соединений
    keepalive_expiry=30.0,           # Время жизни keepalive
    follow_redirects=False,          # Следовать за редиректами
    verify_ssl=True,                 # Проверять SSL сертификаты
    
    # Retry настройки
    retry_attempts=3,                # Количество попыток
    retry_backoff_factor=1.0,        # Множитель экспоненты
    retry_max_delay=60.0,            # Макс. задержка
    retry_statuses={429, 500, 502, 503, 504},  # Статусы для retry
    retry_methods={"GET", "POST", "PUT", "DELETE", "PATCH"},
    
    # Rate limiting
    enable_rate_limiting=False,      # Включить rate limiting
    rate_limit_rate=10.0,            # Запросов в секунду
    rate_limit_burst=1,              # Размер бакета
    
    # Circuit breaker
    enable_circuit_breaker=False,    # Включить circuit breaker
    circuit_breaker_failure_threshold=5,  # Порог срабатывания
    circuit_breaker_recovery_timeout=60.0,  # Время восстановления
)
```

## Аутентификация

### Bearer Token

```python
from src.http_client import BearerAuth

auth = BearerAuth(token="your-token")
client = AsyncHTTPClient(base_url="...", auth=auth)
```

### API Key

```python
from src.http_client import APIKeyAuth

# В заголовке
auth = APIKeyAuth(api_key="key", header_name="X-API-Key")

# Или в query параметре
auth = APIKeyAuth(api_key="key", query_param_name="api_key")
```

### Basic Auth

```python
from src.http_client import BasicAuth

auth = BasicAuth(username="user", password="pass")
```

### OAuth2 Client Credentials

```python
from src.http_client import OAuth2ClientCredentials

auth = OAuth2ClientCredentials(
    token_url="https://auth.example.com/token",
    client_id="client-id",
    client_secret="client-secret",
    scope="read write",
    cache_duration=3600,  # 1 час
)
```

## Повторные попытки (Retry)

Retry автоматически включен при `retry_attempts > 1`:

```python
config = ClientConfig(
    retry_attempts=3,
    retry_backoff_factor=1.0,
    retry_max_delay=10.0,
)
```

### Алгоритм

1. Проверяет HTTP статус ответа
2. Если статус в `retry_statuses` и метод в `retry_methods` - повторяет
3. Экспоненциальная задержка: `backoff_factor * (2 ** attempt)`
4. Jitter (±10%) для предотвращения thundering herd
5. Учитывает заголовок `Retry-After` (429 Too Many Requests)

## Ограничение частоты (Rate Limiting)

Использует алгоритм Token Bucket:

```python
from src.http_client import TokenBucketRateLimiter

rate_limiter = TokenBucketRateLimiter(
    rate=10.0,   # 10 запросов в секунду
    burst=20,    # можно сделать всплеск до 20
)

config = ClientConfig(
    enable_rate_limiting=True,
    rate_limit_rate=10.0,
    rate_limit_burst=20,
)

client = AsyncHTTPClient(
    base_url="...",
    config=config,
    rate_limiter=rate_limiter,
)
```

## Circuit Breaker

Защищает от каскадных сбоев:

```python
from src.http_client import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # После 5 ошибок переходит в OPEN
    recovery_timeout=60.0,    # Через 60с переходит в HALF_OPEN
)

config = ClientConfig(
    enable_circuit_breaker=True,
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60.0,
)

client = AsyncHTTPClient(
    base_url="...",
    config=config,
    circuit_breaker=circuit_breaker,
)
```

### Состояния

- **CLOSED**: Нормальная работа, все запросы проходят
- **OPEN**: Запросы блокируются, возвращается `CircuitBreakerOpenError`
- **HALF_OPEN**: Разрешен один пробный запрос для проверки восстановления

## Middleware

### Встроенные middleware

#### LoggingMiddleware

```python
from src.http_client import LoggingMiddleware

middleware = LoggingMiddleware(
    log_request_body=True,   # Логировать тело запроса
    log_response_body=False, # Не логировать тело ответа (опасно для prod)
    sensitive_headers={"authorization", "x-api-key"},
)
```

#### RetryMiddleware

Автоматически добавляется при `retry_attempts > 1`.

### Кастомный middleware

```python
from src.http_client import Middleware, HTTPRequest, HTTPResponse

class CustomHeaderMiddleware(Middleware):
    async def process_request(self, request: HTTPRequest, client) -> HTTPRequest:
        request.headers["X-Custom"] = "value"
        return request
    
    async def process_response(self, response: HTTPResponse, request: HTTPRequest) -> HTTPResponse:
        # Обработка ответа
        return response

client = AsyncHTTPClient(
    base_url="...",
    middlewares=[CustomHeaderMiddleware()],
)
```

## Обработка ошибок

### Иерархия исключений

```
HTTPClientError (базовое)
├── HTTPRequestError          # Ошибка отправки запроса
├── HTTPResponseError         # Ошибка ответа (4xx, 5xx)
│   └── RateLimitError       # Превышен лимит запросов
├── RetryExhaustedError       # Исчерпаны все попытки
├── CircuitBreakerOpenError   # Circuit breaker открыт
├── AuthenticationError       # Ошибка аутентификации
└── ConfigurationError        # Ошибка конфигурации
```

### Пример обработки

```python
from src.http_client import (
    AsyncHTTPClient,
    HTTPResponseError,
    RateLimitError,
    RetryExhaustedError,
    CircuitBreakerOpenError,
)

async def make_request():
    try:
        response = await client.get("/resource")
        response.raise_for_status()  # Проверить статус
        return response.json_data
    
    except RateLimitError as e:
        print(f"Rate limited, retry after {e.retry_after}s")
        # Обработка rate limit
    
    except HTTPResponseError as e:
        print(f"HTTP error {e.status_code}: {e.message}")
        # Обработка HTTP ошибок
    
    except RetryExhaustedError as e:
        print(f"All retries exhausted: {e}")
        # Обработка исчерпания попыток
    
    except CircuitBreakerOpenError as e:
        print(f"Circuit breaker open, wait {e.recovery_timeout}s")
        # Обработка открытого circuit breaker
    
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Примеры

### Полный пример

```python
import asyncio
from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    BearerAuth,
    LoggingMiddleware,
)

async def main():
    config = ClientConfig(
        timeout=30.0,
        retry_attempts=3,
        enable_rate_limiting=True,
        rate_limit_rate=10.0,
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=5,
    )
    
    auth = BearerAuth(token="your-token")
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        config=config,
        auth=auth,
        middlewares=[LoggingMiddleware(log_request_body=True)],
    ) as client:
        try:
            response = await client.get("/users")
            data = response.json_data
            print(f"Got {len(data)} users")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
```

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/http_client/

# Конкретный модуль
pytest tests/http_client/test_auth.py

# С покрытием
pytest tests/http_client/ --cov=src/http_client --cov-report=html
```

### Фикстуры для тестирования

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.http_client import AsyncHTTPClient

@pytest.fixture
def mock_httpx(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock)
    return mock

@pytest.mark.asyncio
async def test_my_client(mock_httpx):
    mock_httpx.request.return_value = MockResponse(200, b'{"ok": true}')
    
    client = AsyncHTTPClient(base_url="https://test.com")
    response = await client.get("/test")
    
    assert response.status_code == 200
```

## Производительность

- Connection pooling: автоматическое управление пулом соединений
- Keepalive: повторное использование соединений
- Async/await: неблокирующие операции
- Оптимизированные структуры данных

## Лучшие практики

1. **Используйте context manager** для автоматического закрытия соединений
2. **Настраивайте таймауты** чтобы избежать висящих запросов
3. **Включайте retry** для временных сбоев (5xx, 429)
4. **Используйте rate limiting** для соблюдения лимитов API
5. **Добавляйте circuit breaker** для защиты от сбоев внешних сервисов
6. **Логируйте запросы** в production для отладки
7. **Маскируйте чувствительные данные** в логах

## Миграция с httpx

Если вы используете httpx напрямую, миграция проста:

```python
# До
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/users")
    data = response.json()

# После
from src.http_client import AsyncHTTPClient

async with AsyncHTTPClient(base_url="https://api.example.com") as client:
    response = await client.get("/users")
    data = response.json_data
```

## Отладка

Включите детальное логирование:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Или для конкретного логгера
logging.getLogger("src.http_client").setLevel(logging.DEBUG)
```

## Лицензия

MIT
