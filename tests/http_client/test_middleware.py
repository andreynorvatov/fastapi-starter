"""Тесты для middleware."""

import pytest

from src.http_client.middleware import (
    Middleware,
    MiddlewareManager,
    LoggingMiddleware,
    RetryMiddleware,
)
from src.http_client.models import HTTPRequest, HTTPResponse, RetryConfig
from src.http_client.exceptions import HTTPResponseError


class TestMiddlewareManager:
    """Тесты MiddlewareManager."""
    
    @pytest.fixture
    def dummy_middleware(self) -> type[Middleware]:
        """Фикстура для простого middleware."""
        class DummyMiddleware(Middleware):
            def __init__(self, modify: bool = True):
                self.modify = modify
                self.request_called = False
                self.response_called = False
            
            async def process_request(self, request, client):
                self.request_called = True
                if self.modify:
                    request.headers["X-Dummy"] = "processed"
                return request
            
            async def process_response(self, response, request):
                self.response_called = True
                if self.modify:
                    response.headers["X-Dummy-Response"] = "processed"
                return response
        
        return DummyMiddleware
    
    @pytest.mark.asyncio
    async def test_process_request_chain(self, dummy_middleware) -> None:
        """Тест цепочки обработки запросов."""
        mw1 = dummy_middleware()
        mw2 = dummy_middleware()
        manager = MiddlewareManager([mw1, mw2])
        
        request = HTTPRequest(
            method="GET",
            url="https://api.example.com/test",
        )
        
        result = await manager.process_request(request, None)
        
        assert mw1.request_called
        assert mw2.request_called
        assert result.headers["X-Dummy"] == "processed"
    
    @pytest.mark.asyncio
    async def test_process_response_chain(self, dummy_middleware) -> None:
        """Тест цепочки обработки ответов (в обратном порядке)."""
        mw1 = dummy_middleware()
        mw2 = dummy_middleware()
        manager = MiddlewareManager([mw1, mw2])
        
        request = HTTPRequest(method="GET", url="https://test.com")
        response = HTTPResponse(status_code=200)
        
        result = await manager.process_response(response, request)
        
        assert mw2.response_called  # сначала последний
        assert mw1.response_called  # потом первый
        assert result.headers["X-Dummy-Response"] == "processed"
    
    @pytest.mark.asyncio
    async def test_empty_manager(self) -> None:
        """Тест пустого менеджера."""
        manager = MiddlewareManager([])
        request = HTTPRequest(method="GET", url="https://test.com")
        response = HTTPResponse(status_code=200)
        
        result_request = await manager.process_request(request, None)
        result_response = await manager.process_response(response, request)
        
        assert result_request == request
        assert result_response == response


class TestLoggingMiddleware:
    """Тесты LoggingMiddleware."""
    
    @pytest.mark.asyncio
    async def test_process_request(self, caplog) -> None:
        """Тест логирования запроса."""
        import logging
        caplog.set_level(logging.DEBUG)
        middleware = LoggingMiddleware(log_request_body=True)
        request = HTTPRequest(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            json={"name": "test"},
        )
        
        result = await middleware.process_request(request, None)
        
        assert result == request
        # Проверяем, что лог был записан
        assert any("HTTP POST" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_process_response(self, caplog) -> None:
        """Тест логирования ответа."""
        import logging
        caplog.set_level(logging.DEBUG)
        middleware = LoggingMiddleware(log_response_body=True)
        request = HTTPRequest(method="GET", url="https://test.com")
        response = HTTPResponse(
            status_code=200,
            content=b'{"result": "ok"}',
        )
        
        result = await middleware.process_response(response, request)
        
        assert result == response
        assert any("HTTP 200" in record.message for record in caplog.records)
    
    def test_mask_sensitive_headers(self) -> None:
        """Тест маскировки чувствительных заголовков."""
        middleware = LoggingMiddleware()
        headers = {
            "Authorization": "Bearer secret-token",
            "X-API-Key": "my-secret-key",
            "Content-Type": "application/json",
        }
        
        masked = middleware._mask_sensitive_data(headers)
        
        assert masked["Authorization"] == "***MASKED***"
        assert masked["X-API-Key"] == "***MASKED***"
        assert masked["Content-Type"] == "application/json"


class TestRetryMiddleware:
    """Тесты RetryMiddleware."""
    
    @pytest.mark.asyncio
    async def test_success_no_retry(self) -> None:
        """Тест: успешный запрос без повторений."""
        config = RetryConfig(attempts=3)
        middleware = RetryMiddleware(config)
        
        async def success_func():
            return HTTPResponse(status_code=200, content=b"OK")
        
        request = HTTPRequest(method="GET", url="https://test.com")
        
        response = await middleware.execute_with_retry(success_func, request)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self) -> None:
        """Тест повторения при серверной ошибке."""
        config = RetryConfig(attempts=3)
        middleware = RetryMiddleware(config)
        
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise HTTPResponseError(500, "Server error")
            return HTTPResponse(status_code=200, content=b"OK")
        
        request = HTTPRequest(method="GET", url="https://test.com")
        
        response = await middleware.execute_with_retry(failing_func, request)
        assert response.status_code == 200
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self) -> None:
        """Тест: клиентские ошибки (4xx) не повторяются."""
        config = RetryConfig(attempts=3)
        middleware = RetryMiddleware(config)
        
        async def client_error_func():
            raise HTTPResponseError(404, "Not found")
        
        request = HTTPRequest(method="GET", url="https://test.com")
        
        with pytest.raises(HTTPResponseError) as exc_info:
            await middleware.execute_with_retry(client_error_func, request)
        
        assert exc_info.value.status_code == 404
        assert "RetryExhaustedError" not in str(type(exc_info.value))
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """Тест исчерпания всех попыток."""
        config = RetryConfig(attempts=2)
        middleware = RetryMiddleware(config)
        
        async def always_failing_func():
            raise HTTPResponseError(500, "Server error")
        
        request = HTTPRequest(method="GET", url="https://test.com")
        
        with pytest.raises(Exception) as exc_info:  # RetryExhaustedError
            await middleware.execute_with_retry(always_failing_func, request)
        
        assert "исчерпаны все попытки" in str(exc_info.value).lower()
    
    def test_calculate_wait_time(self) -> None:
        """Тест расчета времени ожидания."""
        config = RetryConfig(attempts=3, backoff_factor=1.0, max_delay=10.0)
        middleware = RetryMiddleware(config)
        
        # Первая попытка (attempt=0) -> backoff * 2^0 = 1.0 + jitter
        wait1 = middleware._calculate_wait_time(0)
        assert 0.9 <= wait1 <= 1.1
        
        # Вторая попытка (attempt=1) -> backoff * 2^1 = 2.0 + jitter
        wait2 = middleware._calculate_wait_time(1)
        assert 1.8 <= wait2 <= 2.2
        
        # Третья попытка (attempt=2) -> backoff * 2^2 = 4.0 + jitter
        wait3 = middleware._calculate_wait_time(2)
        assert 3.6 <= wait3 <= 4.4
    
    def test_calculate_wait_time_with_retry_after(self) -> None:
        """Тест использования заголовка Retry-After."""
        config = RetryConfig(attempts=3)
        middleware = RetryMiddleware(config)
        
        wait_time = middleware._calculate_wait_time(0, retry_after=120)
        assert wait_time == 120.0
    
    def test_calculate_wait_time_max_delay(self) -> None:
        """Тест ограничения максимальной задержки."""
        config = RetryConfig(attempts=10, backoff_factor=1.0, max_delay=5.0)
        middleware = RetryMiddleware(config)
        
        wait_time = middleware._calculate_wait_time(10)
        assert wait_time <= 5.0
