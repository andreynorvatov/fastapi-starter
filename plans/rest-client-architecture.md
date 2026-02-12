# Архитектура универсального асинхронного REST клиента

## 1. Обзор

Разрабатывается универсальное асинхронное решение для интеграции с внешними API по REST. Решение должно быть:
- Асинхронным (на базе httpx)
- Надежным (retry, circuit breaker, rate limiting)
- Конфигурируемым (гибкие настройки для каждого API)
- Расширяемым (плагины для аутентификации, middleware)
- Простым в использовании (чистый API)
- Протестируемым (модульные и интеграционные тесты)

## 2. Структура проекта

```
src/
├── http_client/
│   ├── __init__.py
│   ├── client.py              # Основной класс AsyncHTTPClient
│   ├── config.py              # Конфигурация клиента
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── base.py            # Базовый класс аутентификации
│   │   ├── bearer.py          # Bearer токен
│   │   ├── api_key.py         # API Key (header/query)
│   │   ├── basic.py           # Basic Auth
│   │   └── oauth2.py          # OAuth2 (client credentials)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── base.py            # Базовый middleware
│   │   ├── logging.py         # Логирование запросов
│   │   ├── metrics.py         # Сбор метрик
│   │   └── retry.py           # Повторные попытки
│   ├── rate_limiter/
│   │   ├── __init__.py
│   │   ├── base.py            # Базовый лимитер
│   │   ├── token_bucket.py    # Token bucket алгоритм
│   │   └── sliding_window.py  # Sliding window алгоритм
│   ├── circuit_breaker/
│   │   ├── __init__.py
│   │   └── breaker.py         # Реализация circuit breaker
│   ├── exceptions.py          # Иерархия исключений
│   ├── models.py              # Pydantic модели (Request, Response)
│   └── serializers.py         # Сериализаторы (JSON, form-data)
tests/
├── http_client/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_auth.py
│   ├── test_middleware.py
│   ├── test_rate_limiter.py
│   ├── test_circuit_breaker.py
│   ├── test_exceptions.py
│   └── fixtures/
│       └── mock_server.py     # Mock HTTP сервер для тестов
examples/
├── basic_usage.py
├── with_auth.py
├── with_retry.py
├── with_rate_limiting.py
└── with_circuit_breaker.py
```

## 3. Ключевые компоненты

### 3.1 AsyncHTTPClient (client.py)

Основной класс для выполнения HTTP запросов.

```python
class AsyncHTTPClient:
    def __init__(
        self,
        base_url: str,
        config: ClientConfig,
        auth: Optional[AuthHandler] = None,
        middlewares: List[Middleware] = [],
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        ...

    async def request(
        self,
        method: HTTPMethod,
        url: str,
        *,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> HTTPResponse:
        ...

    async def get(self, url: str, **kwargs) -> HTTPResponse: ...
    async def post(self, url: str, **kwargs) -> HTTPResponse: ...
    async def put(self, url: str, **kwargs) -> HTTPResponse: ...
    async def delete(self, url: str, **kwargs) -> HTTPResponse: ...
    async def patch(self, url: str, **kwargs) -> HTTPResponse: ...
```

### 3.2 Конфигурация (config.py)

```python
@dataclass
class ClientConfig:
    """Конфигурация HTTP клиента"""
    timeout: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    follow_redirects: bool = False
    verify_ssl: bool = True
    retry_attempts: int = 3
    retry_backoff_factor: float = 1.0
    retry_max_delay: float = 60.0
    retry_statuses: Set[int] = {408, 429, 500, 502, 503, 504}
    retry_methods: Set[str] = {"GET", "POST", "PUT", "DELETE", "PATCH"}
```

### 3.3 Аутентификация (auth/)

Базовый класс:
```python
class AuthHandler(ABC):
    @abstractmethod
    async def prepare_request(self, request: PreparedRequest) -> PreparedRequest:
        """Модифицировать запрос перед отправкой"""
```

Реализации:
- `BearerAuth`: добавляет `Authorization: Bearer <token>`
- `APIKeyAuth`: добавляет API ключ в header или query param
- `BasicAuth`: добавляет `Authorization: Basic <credentials>`
- `OAuth2ClientCredentials`: получает токен через OAuth2, кэширует

### 3.4 Middleware (middleware/)

Middleware система для обработки запросов/ответов:

```python
class Middleware(ABC):
    @abstractmethod
    async def process_request(
        self,
        request: HTTPRequest,
        client: AsyncHTTPClient
    ) -> HTTPRequest:
        """Обработать запрос перед отправкой"""
        return request

    @abstractmethod
    async def process_response(
        self,
        response: HTTPResponse,
        request: HTTPRequest
    ) -> HTTPResponse:
        """Обработать ответ после получения"""
        return response
```

Готовые middleware:
- `LoggingMiddleware`: логирует запросы и ответы
- `MetricsMiddleware`: собирает метрики (длительность, размер)
- `RetryMiddleware`: выполняет повторные попытки при ошибках

### 3.5 Rate Limiting (rate_limiter/)

Абстракция для ограничения частоты запросов:

```python
class RateLimiter(ABC):
    @abstractmethod
    async def acquire(self, tokens: int = 1) -> float:
        """Получить разрешение на запрос. Возвращает время ожидания."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        ...
```

Реализации:
- `TokenBucketRateLimiter`: классический token bucket
- `SlidingWindowRateLimiter`: sliding window для точного контроля

### 3.6 Circuit Breaker (circuit_breaker/)

Защита от каскадных сбоев:

```python
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = HTTPClientError
    ):
        ...

    async def call(self, func: Callable, *args, **kwargs):
        """Выполнить функцию с защитой circuit breaker"""
        ...
```

Состояния: CLOSED, OPEN, HALF_OPEN

### 3.7 Исключения (exceptions.py)

```python
class HTTPClientError(Exception):
    """Базовое исключение клиента"""
    pass

class HTTPRequestError(HTTPClientError):
    """Ошибка отправки запроса"""
    pass

class HTTPResponseError(HTTPClientError):
    """Ошибка ответа (4xx, 5xx)"""
    def __init__(self, status_code: int, message: str, response: HTTPResponse):
        ...

class RateLimitError(HTTPResponseError):
    """Превышен лимит запросов"""
    pass

class RetryExhaustedError(HTTPClientError):
    """Исчерпаны все попытки повторения"""
    pass

class CircuitBreakerOpenError(HTTPClientError):
    """Circuit breaker открыт"""
    pass
```

### 3.8 Модели (models.py)

```python
@dataclass
class HTTPRequest:
    method: str
    url: str
    headers: Dict[str, str]
    params: Dict[str, Any]
    body: Optional[Any] = None
    timeout: Optional[float] = None

@dataclass
class HTTPResponse:
    status_code: int
    headers: Dict[str, str]
    content: bytes
    json_data: Optional[Any] = None

    def raise_for_status(self):
        """Вызвать исключение при ошибке"""
        ...
```

## 4. Поток выполнения запроса

```
1. Создание HTTPRequest
2. Применение middleware (process_request)
3. Применение аутентификации
4. Проверка rate limiter
5. Проверка circuit breaker
6. Выполнение запроса через httpx
7. Обработка ответа:
   - Если ошибка и есть retry middleware -> повтор
   - Если превышен лимит -> raise RateLimitError
   - Если circuit breaker открыт -> raise CircuitBreakerOpenError
8. Применение middleware (process_response)
9. Возврат HTTPResponse
```

## 5. Использование

### Базовый пример

```python
from src.http_client import AsyncHTTPClient, ClientConfig

config = ClientConfig(
    timeout=30.0,
    retry_attempts=3,
    retry_statuses={429, 500, 502, 503, 504}
)

client = AsyncHTTPClient(
    base_url="https://api.example.com",
    config=config
)

response = await client.get("/users")
data = response.json_data
```

### С аутентификацией

```python
from src.http_client import AsyncHTTPClient, BearerAuth, ClientConfig

client = AsyncHTTPClient(
    base_url="https://api.example.com",
    config=config,
    auth=BearerAuth(token="your-token")
)
```

### С rate limiting

```python
from src.http_client import AsyncHTTPClient, TokenBucketRateLimiter

rate_limiter = TokenBucketRateLimiter(
    rate=10,      # 10 запросов
    burst=20      # максимальный бакет
)

client = AsyncHTTPClient(
    base_url="https://api.example.com",
    config=config,
    rate_limiter=rate_limiter
)
```

### С circuit breaker

```python
from src.http_client import AsyncHTTPClient, CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

client = AsyncHTTPClient(
    base_url="https://api.example.com",
    config=config,
    circuit_breaker=circuit_breaker
)
```

### С кастомным middleware

```python
from src.http_client import Middleware

class CustomHeaderMiddleware(Middleware):
    async def process_request(self, request, client):
        request.headers["X-Custom-Header"] = "value"
        return request

    async def process_response(self, response, request):
        # Логика обработки ответа
        return response

client = AsyncHTTPClient(
    base_url="https://api.example.com",
    config=config,
    middlewares=[CustomHeaderMiddleware()]
)
```

## 6. Тестирование

- **Модульные тесты**: тестирование каждого компонента изолированно
- **Интеграционные тесты**: тестирование взаимодействия компонентов с mock сервером
- **Тесты на производительность**: нагрузочное тестирование rate limiter, circuit breaker

Использование pytest с pytest-asyncio, pytest-mock, respx для мокирования httpx.

## 7. Документация

- Docstrings для всех классов и методов
- Примеры использования в examples/
- Детальная документация в README.md
- API reference

## 8. Зависимости

Добавить в pyproject.toml:
- httpx (уже есть в dev, нужно в main dependencies)
- tenacity (для retry - опционально, можно свою реализацию)
- optional: prometheus-client для метрик

## 9. Конфигурация через settings.py

Добавить настройки по умолчанию для HTTP клиента в `src/config.py`:

```python
class Settings(BaseSettings):
    ...
    # HTTP Client defaults
    HTTP_CLIENT_TIMEOUT: float = 30.0
    HTTP_CLIENT_MAX_CONNECTIONS: int = 100
    HTTP_CLIENT_RETRY_ATTEMPTS: int = 3
    ...
```

## 10. План реализации

1. Создать структуру директорий
2. Реализовать базовые модели (HTTPRequest, HTTPResponse)
3. Реализовать исключения
4. Реализовать конфигурацию
5. Реализовать аутентификацию
6. Реализовать rate limiter
7. Реализовать circuit breaker
8. Реализовать middleware
9. Реализовать основной клиент
10. Написать тесты
11. Создать примеры
12. Обновить документацию

## 11. Критерии приемки

- [ ] Все компоненты покрыты unit-тестами (>80%)
- [ ] Клиент работает асинхронно без блокировок
- [ ] Поддерживаются все основные типы аутентификации
- [ ] Retry работает с экспоненциальной задержкой
- [ ] Rate limiter корректно ограничивает запросы
- [ ] Circuit breaker переключает состояния
- [ ] Middleware система расширяема
- [ ] Исключения информативны
- [ ] Логирование подробное
- [ ] Документация полная
- [ ] Примеры работают