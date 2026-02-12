"""Продвинутый пример с комбинацией нескольких функций."""

import asyncio
from datetime import datetime

from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    BearerAuth,
    Middleware,
    HTTPRequest,
    HTTPResponse,
)


class RequestIDMiddleware(Middleware):
    """Кастомный middleware для добавления Request-ID."""
    
    def __init__(self, header_name: str = "X-Request-ID") -> None:
        self.header_name = header_name
        import uuid
        self._generate_id = lambda: str(uuid.uuid4())
    
    async def process_request(self, request: HTTPRequest, client) -> HTTPRequest:
        """Добавить уникальный ID к запросу."""
        request_id = self._generate_id()
        headers = request.headers.copy()
        headers[self.header_name] = request_id
        # Сохраняем ID для последующего логирования
        request.extra = {"_request_id": request_id}  # type: ignore
        return request
    
    async def process_response(self, response: HTTPResponse, request: HTTPRequest) -> HTTPResponse:
        """Логировать Request-ID в ответе."""
        request_id = getattr(request, "extra", {}).get("_request_id", "unknown")
        print(f"[{datetime.now()}] Request {request_id} completed with status {response.status_code}")
        return response


class TimingMiddleware(Middleware):
    """Middleware для измерения времени выполнения."""
    
    async def process_request(self, request: HTTPRequest, client) -> HTTPRequest:
        """Засечь время начала."""
        request.extra = {"_start_time": asyncio.get_event_loop().time()}  # type: ignore
        return request
    
    async def process_response(self, response: HTTPResponse, request: HTTPRequest) -> HTTPResponse:
        """Вычислить и залогировать время выполнения."""
        start_time = getattr(request, "extra", {}).get("_start_time")
        if start_time:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"Request took {elapsed:.3f} seconds")
        return response


async def main() -> None:
    """Продвинутый пример с комбинацией функций."""
    print("=== Advanced Example ===")
    
    # Конфигурация с включенными всеми функциями
    config = ClientConfig(
        timeout=30.0,
        retry_attempts=3,
        retry_backoff_factor=1.0,
        enable_rate_limiting=True,
        rate_limit_rate=5.0,  # 5 запросов в секунду
        rate_limit_burst=10,
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_timeout=30.0,
    )
    
    # Кастомные middleware
    custom_middlewares = [
        RequestIDMiddleware(),
        TimingMiddleware(),
    ]
    
    # Аутентификация
    auth = BearerAuth(token="your-secret-token")
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com/v1",
        config=config,
        auth=auth,
        middlewares=custom_middlewares,
    ) as client:
        # Пример нескольких запросов
        endpoints = [
            ("GET", "/users"),
            ("GET", "/posts"),
            ("POST", "/users", {"name": "John", "email": "john@example.com"}),
        ]
        
        for method, endpoint, *body in endpoints:
            try:
                kwargs = {}
                if body:
                    kwargs["json"] = body[0]
                
                response = await client.request(method, endpoint, **kwargs)
                print(f"{method} {endpoint} -> {response.status_code}")
                
                if response.json_data:
                    print(f"  Data: {response.json_data}")
                    
            except Exception as e:
                print(f"{method} {endpoint} -> ERROR: {e}")
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
