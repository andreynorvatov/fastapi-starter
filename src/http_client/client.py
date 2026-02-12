"""Основной асинхронный HTTP клиент."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from src.logger import logger
from .config import ClientConfig
from .models import (
    HTTPRequest,
    HTTPResponse,
    RetryConfig,
    RateLimitConfig,
    CircuitBreakerConfig,
)
from .exceptions import (
    HTTPRequestError,
    RateLimitError,
    CircuitBreakerOpenError,
)
from .auth import AuthHandler
from .middleware import Middleware, MiddlewareManager, RetryMiddleware
from .rate_limiter import RateLimiter, TokenBucketRateLimiter
from .circuit_breaker import CircuitBreaker


class AsyncHTTPClient:
    """
    Универсальный асинхронный HTTP клиент с поддержкой:
    - Connection pooling
    - Аутентификации (Bearer, API Key, Basic, OAuth2)
    - Retry с экспоненциальной задержкой
    - Rate limiting (Token Bucket)
    - Circuit breaker
    - Middleware система
    - Детального логирования
    
    Пример использования:
        ```python
        from src.http_client import AsyncHTTPClient, ClientConfig, BearerAuth
        
        config = ClientConfig(
            timeout=30.0,
            retry_attempts=3,
            enable_rate_limiting=True,
            rate_limit_rate=10.0,
        )
        
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            config=config,
            auth=BearerAuth(token="your-token")
        )
        
        response = await client.get("/users")
        data = response.json_data
        ```
    """
    
    def __init__(
        self,
        base_url: str,
        config: Optional[ClientConfig] = None,
        auth: Optional[AuthHandler] = None,
        middlewares: Optional[list[Middleware]] = None,
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        **httpx_kwargs: Any,
    ) -> None:
        """
        Инициализация HTTP клиента.
        
        Args:
            base_url: Базовый URL API
            config: Конфигурация клиента
            auth: Обработчик аутентификации
            middlewares: Список middleware
            rate_limiter: Ограничитель частоты запросов
            circuit_breaker: Circuit breaker
            **httpx_kwargs: Дополнительные параметры для httpx.AsyncClient
        """
        self.base_url = base_url.rstrip("/")
        self.config = config or ClientConfig()
        self.auth = auth
        self.httpx_kwargs = httpx_kwargs
        
        # Инициализация rate limiter из конфига если не передан
        if rate_limiter is None and self.config.enable_rate_limiting:
            rate_limiter = TokenBucketRateLimiter(
                rate=self.config.rate_limit_rate,
                burst=self.config.rate_limit_burst,
            )
        self.rate_limiter = rate_limiter
        
        # Инициализация circuit breaker из конфига если не передан
        if circuit_breaker is None and self.config.enable_circuit_breaker:
            circuit_breaker = CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.circuit_breaker_recovery_timeout,
            )
        self.circuit_breaker = circuit_breaker
        
        # Middleware
        default_middlewares: list[Middleware] = []
        self.retry_middleware: Optional[RetryMiddleware] = None
        if self.config.retry_attempts > 1:
            retry_config = RetryConfig(
                attempts=self.config.retry_attempts,
                backoff_factor=self.config.retry_backoff_factor,
                max_delay=self.config.retry_max_delay,
                statuses=self.config.retry_statuses,
                methods=self.config.retry_methods,
            )
            self.retry_middleware = RetryMiddleware(config=retry_config)
            # Не добавляем в default_middlewares, так как retry обрабатывается отдельно
        self.middlewares = MiddlewareManager(middlewares or [] + default_middlewares)
        
        # httpx клиент будет создан лениво
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Получить или создать httpx клиент с connection pooling.
        
        Returns:
            httpx.AsyncClient: Настроенный клиент
        """
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    limits = httpx.Limits(
                        max_connections=self.config.max_connections,
                        max_keepalive_connections=self.config.max_keepalive_connections,
                        keepalive_expiry=self.config.keepalive_expiry,
                    )
                    self._client = httpx.AsyncClient(
                        limits=limits,
                        follow_redirects=self.config.follow_redirects,
                        verify=self.config.verify_ssl,
                        timeout=httpx.Timeout(self.config.timeout),
                        **self.httpx_kwargs,
                    )
        return self._client
    
    async def close(self) -> None:
        """Закрыть HTTP клиент и освободить ресурсы."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP клиент закрыт")
    
    async def __aenter__(self) -> AsyncHTTPClient:
        """Поддержка async context manager."""
        await self._get_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Выход из async context manager."""
        await self.close()
    
    def _build_url(self, url: str) -> str:
        """Построить полный URL из базового и относительного."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}{url}"
    
    async def _prepare_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> HTTPRequest:
        """
        Подготовить HTTP запрос с учетом middleware и аутентификации.
        
        Args:
            method: HTTP метод
            url: URL (относительный или абсолютный)
            **kwargs: Параметры запроса
            
        Returns:
            HTTPRequest: Подготовленный запрос
        """
        full_url = self._build_url(url)
        
        request = HTTPRequest(
            method=method,
            url=full_url,
            headers=kwargs.get("headers", {}),
            params=kwargs.get("params", {}),
            json=kwargs.get("json"),
            data=kwargs.get("data"),
            timeout=kwargs.get("timeout", self.config.timeout),
        )
        
        # Применить middleware
        request = await self.middlewares.process_request(request, self)
        
        # Применить аутентификацию
        if self.auth:
            request = await self.auth.prepare_request(request)
        
        return request
    
    async def _execute_request(
        self,
        request: HTTPRequest,
        apply_rate_limit: bool = True,
    ) -> HTTPResponse:
        """
        Выполнить HTTP запрос.
        
        Args:
            request: Подготовленный запрос
            apply_rate_limit: Применять ли rate limiting
            
        Returns:
            HTTPResponse: Ответ
            
        Raises:
            HTTPRequestError: При ошибке отправки запроса
            RetryExhaustedError: При исчерпании попыток повторения
        """
        # Rate limiting
        if apply_rate_limit and self.rate_limiter:
            wait_time = await self.rate_limiter.acquire()
            if wait_time > 0:
                logger.debug(f"Rate limit: ожидание {wait_time:.3f}s")
                await asyncio.sleep(wait_time)
        
        # Определяем функцию для выполнения запроса
        async def _perform_request() -> HTTPResponse:
            if self.circuit_breaker and self.circuit_breaker.is_configured():
                async def _make_request() -> HTTPResponse:
                    return await self._make_http_request(request)
                return await self.circuit_breaker.call(_make_request)
            else:
                return await self._make_http_request(request)
        
        # Retry logic если доступен
        if self.retry_middleware:
            response = await self.retry_middleware.execute_with_retry(_perform_request, request)
        else:
            response = await _perform_request()
        
        return response
    
    async def _make_http_request(self, request: HTTPRequest) -> HTTPResponse:
        """
        Выполнить фактический HTTP запрос через httpx.
        
        Args:
            request: HTTP запрос
            
        Returns:
            HTTPResponse: Ответ
            
        Raises:
            HTTPRequestError: При ошибке сети или HTTP
        """
        client = await self._get_client()
        
        try:
            httpx_response = await client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                json=request.json,
                data=request.data,
                timeout=request.timeout,
            )
            
            response = HTTPResponse(
                status_code=httpx_response.status_code,
                headers=dict(httpx_response.headers),
                content=httpx_response.content,
                request=request,
            )
            
            return response
            
        except httpx.HTTPError as e:
            raise HTTPRequestError(
                f"Ошибка HTTP запроса: {str(e)}",
                original_exception=e,
            ) from e
        except Exception as e:
            raise HTTPRequestError(
                f"Неожиданная ошибка при выполнении запроса: {str(e)}",
                original_exception=e,
            ) from e
    
    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> HTTPResponse:
        """
        Выполнить HTTP запрос с полной обработкой (middleware, retry, etc).
        
        Args:
            method: HTTP метод
            url: URL (относительный или абсолютный)
            **kwargs: Параметры запроса
            
        Returns:
            HTTPResponse: Ответ
            
        Raises:
            HTTPRequestError: При ошибке отправки запроса
            HTTPResponseError: При ошибке ответа (4xx, 5xx)
            RetryExhaustedError: При исчерпании попыток повторения
            CircuitBreakerOpenError: При открытом circuit breaker
        """
        request = await self._prepare_request(method, url, **kwargs)
        
        # Определяем, нужно ли применять retry
        # Retry уже встроен в middleware, поэтому просто выполняем запрос
        response = await self._execute_request(request)
        
        # Применить response middleware
        response = await self.middlewares.process_response(response, request)
        
        # Проверяем статус
        response.raise_for_status()
        
        return response
    
    async def get(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить GET запрос."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить POST запрос."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить PUT запрос."""
        return await self.request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить DELETE запрос."""
        return await self.request("DELETE", url, **kwargs)
    
    async def patch(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить PATCH запрос."""
        return await self.request("PATCH", url, **kwargs)
    
    async def head(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить HEAD запрос."""
        return await self.request("HEAD", url, **kwargs)
    
    async def options(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Выполнить OPTIONS запрос."""
        return await self.request("OPTIONS", url, **kwargs)
