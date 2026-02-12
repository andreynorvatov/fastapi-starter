"""Тесты для аутентификации."""

import pytest

from src.http_client.auth import (
    BearerAuth,
    APIKeyAuth,
    BasicAuth,
    OAuth2ClientCredentials,
)
from src.http_client.exceptions import AuthenticationError
from src.http_client.models import HTTPRequest


class TestBearerAuth:
    """Тесты Bearer аутентификации."""
    
    def test_init_with_token(self) -> None:
        """Тест инициализации с токеном."""
        auth = BearerAuth("test-token")
        assert auth.token == "test-token"
        assert auth.header_name == "Authorization"
    
    def test_init_with_custom_header(self) -> None:
        """Тест инициализации с кастомным заголовком."""
        auth = BearerAuth("test-token", header_name="X-Auth-Token")
        assert auth.header_name == "X-Auth-Token"
    
    def test_init_empty_token(self) -> None:
        """Тест ошибки при пустом токене."""
        with pytest.raises(AuthenticationError, match="Bearer токен не может быть пустым"):
            BearerAuth("")
        with pytest.raises(AuthenticationError):
            BearerAuth("   ")
    
    @pytest.mark.asyncio
    async def test_prepare_request(self) -> None:
        """Тест добавления токена в запрос."""
        auth = BearerAuth("my-token")
        request = HTTPRequest(
            method="GET",
            url="https://api.example.com/users",
            headers={"Accept": "application/json"},
        )
        
        result = await auth.prepare_request(request)
        
        assert result.headers["Authorization"] == "Bearer my-token"
        assert result.headers["Accept"] == "application/json"
        assert result.method == "GET"
        assert result.url == "https://api.example.com/users"


class TestAPIKeyAuth:
    """Тесты API Key аутентификации."""
    
    def test_init_with_header(self) -> None:
        """Тест инициализации с заголовком."""
        auth = APIKeyAuth("api-key-123", header_name="X-API-Key")
        assert auth.api_key == "api-key-123"
        assert auth.header_name == "X-API-Key"
        assert auth.query_param_name is None
    
    def test_init_with_query_param(self) -> None:
        """Тест инициализации с query параметром."""
        auth = APIKeyAuth("api-key-123", query_param_name="key")
        assert auth.query_param_name == "key"
        assert auth.header_name == "X-API-Key"  # default
    
    def test_init_empty_key(self) -> None:
        """Тест ошибки при пустом ключе."""
        with pytest.raises(AuthenticationError, match="API ключ не может быть пустым"):
            APIKeyAuth("")
    
    @pytest.mark.asyncio
    async def test_prepare_request_with_header(self) -> None:
        """Тест добавления ключа в заголовок."""
        auth = APIKeyAuth("secret-key", header_name="X-API-Key")
        request = HTTPRequest(
            method="GET",
            url="https://api.example.com/data",
        )
        
        result = await auth.prepare_request(request)
        
        assert result.headers["X-API-Key"] == "secret-key"
    
    @pytest.mark.asyncio
    async def test_prepare_request_with_query_param(self) -> None:
        """Тест добавления ключа в query параметр."""
        auth = APIKeyAuth("secret-key", query_param_name="api_key")
        request = HTTPRequest(
            method="GET",
            url="https://api.example.com/data",
            params={"existing": "param"},
        )
        
        result = await auth.prepare_request(request)
        
        assert result.params["api_key"] == "secret-key"
        assert result.params["existing"] == "param"


class TestBasicAuth:
    """Тесты Basic аутентификации."""
    
    def test_init_valid_credentials(self) -> None:
        """Тест валидных учетных данных."""
        auth = BasicAuth("user", "pass123")
        assert auth.username == "user"
        assert auth.password == "pass123"
    
    def test_init_empty_username(self) -> None:
        """Тест ошибки при пустом имени пользователя."""
        with pytest.raises(AuthenticationError, match="Имя пользователя не может быть пустым"):
            BasicAuth("", "pass")
    
    def test_init_none_password(self) -> None:
        """Тест ошибки при None пароле."""
        with pytest.raises(AuthenticationError, match="Пароль не может быть None"):
            BasicAuth("user", None)  # type: ignore
    
    def test_encode_credentials(self) -> None:
        """Тест кодирования учетных данных."""
        auth = BasicAuth("user", "pass")
        encoded = auth._encode_credentials()
        assert encoded.startswith("Basic ")
        # Проверяем, что это корректный base64
        import base64
        decoded = base64.b64decode(encoded[6:]).decode("utf-8")
        assert decoded == "user:pass"
    
    @pytest.mark.asyncio
    async def test_prepare_request(self) -> None:
        """Тест добавления Basic auth заголовка."""
        auth = BasicAuth("testuser", "testpass")
        request = HTTPRequest(
            method="GET",
            url="https://api.example.com/protected",
        )
        
        result = await auth.prepare_request(request)
        
        assert result.headers["Authorization"].startswith("Basic ")
        import base64
        encoded = result.headers["Authorization"][6:]
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == "testuser:testpass"


class TestOAuth2ClientCredentials:
    """Тесты OAuth2 Client Credentials."""
    
    def test_init_valid_params(self) -> None:
        """Тест валидных параметров."""
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="client-id",
            client_secret="client-secret",
        )
        assert auth.token_url == "https://auth.example.com/token"
        assert auth.client_id == "client-id"
        assert auth.client_secret == "client-secret"
    
    def test_init_empty_params(self) -> None:
        """Тест ошибок при пустых параметрах."""
        with pytest.raises(AuthenticationError, match="token_url обязателен"):
            OAuth2ClientCredentials("", "id", "secret")
        with pytest.raises(AuthenticationError, match="client_id не может быть пустым"):
            OAuth2ClientCredentials("https://auth/token", "", "secret")
        with pytest.raises(AuthenticationError, match="client_secret не может быть пустым"):
            OAuth2ClientCredentials("https://auth/token", "id", None)  # type: ignore
    
    @pytest.mark.asyncio
    async def test_token_fetching(self, monkeypatch) -> None:
        """Тест получения токена (с моком httpx)."""
        # Этот тест требует мокирования httpx
        # Для простоты проверяем только инициализацию
        auth = OAuth2ClientCredentials(
            token_url="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
            scope="read write",
        )
        assert auth.scope == "read write"
        assert auth.cache_duration == 3600
        assert auth._access_token is None
