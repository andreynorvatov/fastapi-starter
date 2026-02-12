"""Интеграционные тесты HTTP клиента."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    BearerAuth,
    APIKeyAuth,
    BasicAuth,
    HTTPResponseError,
    RateLimitError,
)
from src.http_client.models import HTTPRequest


class MockResponse:
    """Мок HTTP ответа."""
    
    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b"",
        headers: dict | None = None,
        json_data: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self._json_data = json_data
        
        if json_data and not content:
            import json
            self.content = json.dumps(json_data).encode("utf-8")
    
    def raise_for_status(self) -> None:
        """Метод для совместимости с httpx."""
        if 400 <= self.status_code < 600:
            raise httpx.HTTPError(
                message=f"HTTP {self.status_code}",
                request=None,  # type: ignore
                response=self,
            )
    
    def json(self) -> dict | None:
        """Метод для совместимости с httpx."""
        if self._json_data is not None:
            return self._json_data
        import json
        return json.loads(self.content.decode("utf-8"))


class MockAsyncClient:
    """Мок httpx.AsyncClient."""
    
    def __init__(self, responses: list[MockResponse] | None = None) -> None:
        self.responses = responses or [MockResponse()]
        self.call_count = 0
        self.requests: list[httpx.Request] = []
    
    async def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
        timeout: float | None = None,
        **kwargs: any,
    ) -> MockResponse:
        """Метод request."""
        self.call_count += 1
        self.requests.append(httpx.Request(
            method=method,
            url=url,
            headers=headers or {},
            params=params or {},
        ))
        
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
        return self.responses[-1] if self.responses else MockResponse()
    
    async def aclose(self) -> None:
        """Закрытие клиента."""
        pass
    
    async def __aenter__(self) -> "MockAsyncClient":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.aclose()


@pytest.fixture
def mock_httpx_client(monkeypatch) -> AsyncMock:
    """Фикстура для мокирования httpx.AsyncClient."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock.limits = httpx.Limits()
    mock.request = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_client_basic_get(mock_httpx_client) -> None:
    """Тест базового GET запроса."""
    # Настраиваем мок
    mock_response = MockResponse(
        status_code=200,
        json_data={"users": [{"id": 1, "name": "John"}]},
    )
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        config = ClientConfig(timeout=10.0)
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            config=config,
        )
        
        response = await client.get("/users")
        
        assert response.status_code == 200
        assert response.json_data == {"users": [{"id": 1, "name": "John"}]}
        
        # Проверяем, что запрос был сделан с правильными параметрами
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert call_args.kwargs["url"] == "https://api.example.com/users"


@pytest.mark.asyncio
async def test_client_with_auth(mock_httpx_client) -> None:
    """Тест запроса с аутентификацией."""
    mock_response = MockResponse(status_code=200, json_data={"ok": True})
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        auth = BearerAuth("test-token")
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            auth=auth,
        )
        
        response = await client.get("/protected")
        
        # Проверяем заголовок авторизации
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_client_error_response(mock_httpx_client) -> None:
    """Тест обработки ошибки 4xx."""
    mock_response = MockResponse(
        status_code=404,
        content=b'{"error": "Not found"}',
    )
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = AsyncHTTPClient(base_url="https://api.example.com")
        
        with pytest.raises(HTTPResponseError) as exc_info:
            await client.get("/notfound")
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_client_with_params(mock_httpx_client) -> None:
    """Тест запроса с query параметрами."""
    mock_response = MockResponse(status_code=200, json_data={"result": "ok"})
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = AsyncHTTPClient(base_url="https://api.example.com")
        
        response = await client.get("/search", params={"q": "test", "limit": 10})
        
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["params"] == {"q": "test", "limit": 10}


@pytest.mark.asyncio
async def test_client_with_json_body(mock_httpx_client) -> None:
    """Тест POST запроса с JSON телом."""
    mock_response = MockResponse(status_code=201, json_data={"id": 123})
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = AsyncHTTPClient(base_url="https://api.example.com")
        
        response = await client.post("/users", json={"name": "Alice", "age": 30})
        
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["json"] == {"name": "Alice", "age": 30}
        assert call_args.kwargs["method"] == "POST"


@pytest.mark.asyncio
async def test_client_context_manager(mock_httpx_client) -> None:
    """Тест использования клиента как context manager."""
    mock_response = MockResponse(status_code=200)
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        async with AsyncHTTPClient(base_url="https://api.example.com") as client:
            response = await client.get("/test")
            assert response.status_code == 200
        
        # Проверяем, что клиент был закрыт
        mock_httpx_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_client_absolute_url(mock_httpx_client) -> None:
    """Тест запроса с абсолютным URL."""
    mock_response = MockResponse(status_code=200)
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = AsyncHTTPClient(base_url="https://api.example.com")
        
        # Абсолютный URL должен использоваться как есть
        await client.get("https://other.com/resource")
        
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["url"] == "https://other.com/resource"


@pytest.mark.asyncio
async def test_client_retry_integration(mock_httpx_client) -> None:
    """Тест интеграции с retry middleware."""
    # Первые два запроса падают, третий успешен
    mock_responses = [
        MockResponse(status_code=500, content=b"Server error"),
        MockResponse(status_code=502, content=b"Bad gateway"),
        MockResponse(status_code=200, json_data={"ok": True}),
    ]
    mock_httpx_client.request.side_effect = mock_responses
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        config = ClientConfig(retry_attempts=3)
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            config=config,
        )
        
        response = await client.get("/test")
        
        assert response.status_code == 200
        assert mock_httpx_client.request.call_count == 3


@pytest.mark.asyncio
async def test_client_rate_limit_integration(mock_httpx_client) -> None:
    """Тест интеграции с rate limiter."""
    mock_response = MockResponse(status_code=200)
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        from src.http_client.rate_limiter import TokenBucketRateLimiter
        
        config = ClientConfig(enable_rate_limiting=True, rate_limit_rate=10.0)
        rate_limiter = TokenBucketRateLimiter(rate=10.0, burst=1)
        
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            config=config,
            rate_limiter=rate_limiter,
        )
        
        # Первый запрос должен пройти сразу (есть токен)
        response = await client.get("/test")
        assert response.status_code == 200
        
        # Второй запрос должен ждать (токены на нуле)
        # Но в тесте мы не ждем, просто проверяем что запрос выполнился
        response = await client.get("/test")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_client_with_api_key_auth(mock_httpx_client) -> None:
    """Тест клиента с API Key аутентификацией."""
    mock_response = MockResponse(status_code=200)
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        auth = APIKeyAuth("my-secret-key", header_name="X-API-Key")
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            auth=auth,
        )
        
        response = await client.get("/data")
        
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["headers"]["X-API-Key"] == "my-secret-key"
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_client_with_basic_auth(mock_httpx_client) -> None:
    """Тест клиента с Basic аутентификацией."""
    mock_response = MockResponse(status_code=200)
    mock_httpx_client.request.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        auth = BasicAuth("testuser", "testpass")
        client = AsyncHTTPClient(
            base_url="https://api.example.com",
            auth=auth,
        )
        
        response = await client.get("/protected")
        
        call_args = mock_httpx_client.request.call_args
        auth_header = call_args.kwargs["headers"]["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Декодируем и проверяем
        import base64
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == "testuser:testpass"
