"""OAuth2 Client Credentials аутентификация."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx

from ..exceptions import AuthenticationError, HTTPClientError
from .base import AuthHandler
from ..models import HTTPRequest


class OAuth2ClientCredentials(AuthHandler):
    """
    OAuth2 Client Credentials flow.
    
    Получает и кэширует access token, обновляя при необходимости.
    """
    
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None,
        token_header_name: str = "Authorization",
        token_prefix: str = "Bearer",
        cache_duration: int = 3600,  # 1 час в секундах
    ) -> None:
        """
        Инициализация OAuth2 Client Credentials.
        
        Args:
            token_url: URL для получения токена
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: Scope для запроса токена
            token_header_name: Имя заголовка для токена
            token_prefix: Префикс в заголовке (обычно "Bearer")
            cache_duration: Время жизни токена в секундах (по умолчанию 1 час)
            
        Raises:
            AuthenticationError: При пустых параметрах
        """
        if not token_url:
            raise AuthenticationError("token_url обязателен", "oauth2")
        if not client_id or not client_id.strip():
            raise AuthenticationError("client_id не может быть пустым", "oauth2")
        if not client_secret or not client_secret.strip():
            raise AuthenticationError("client_secret не может быть пустым", "oauth2")
        
        self.token_url = token_url
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.scope = scope
        self.token_header_name = token_header_name
        self.token_prefix = token_prefix
        self.cache_duration = cache_duration
        
        # Кэш токена
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_lock = asyncio.Lock()
    
    def _is_token_valid(self) -> bool:
        """Проверить, валиден ли текущий токен."""
        if not self._access_token or not self._token_expires_at:
            return False
        return datetime.now() < self._token_expires_at
    
    async def _fetch_token(self) -> None:
        """
        Получить новый access token.
        
        Raises:
            AuthenticationError: При ошибке получения токена
        """
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
                if self.scope:
                    data["scope"] = self.scope
                
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", self.cache_duration)
                
                if not access_token:
                    raise AuthenticationError(
                        "В ответе отсутствует access_token",
                        "oauth2"
                    )
                
                self._access_token = access_token
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
        except httpx.HTTPError as e:
            raise AuthenticationError(
                f"Ошибка получения токена: {str(e)}",
                "oauth2"
            ) from e
        except (KeyError, ValueError) as e:
            raise AuthenticationError(
                f"Некорректный ответ при получении токена: {str(e)}",
                "oauth2"
            ) from e
    
    async def ensure_token(self) -> None:
        """
        Убедиться, что токен валиден, при необходимости обновить.
        
        Использует lock для предотвращения одновременных запросов токена.
        """
        if self._is_token_valid():
            return
        
        async with self._refresh_lock:
            # Двойная проверка (double-checked locking)
            if self._is_token_valid():
                return
            await self._fetch_token()
    
    async def prepare_request(self, request: HTTPRequest) -> HTTPRequest:
        """
        Добавить OAuth2 токен в заголовки запроса.
        
        Args:
            request: Исходный запрос
            
        Returns:
            HTTPRequest: Запрос с добавленным токеном
            
        Raises:
            AuthenticationError: При ошибке получения токена
        """
        await self.ensure_token()
        
        if not self._access_token:
            raise AuthenticationError("Токен не был получен", "oauth2")
        
        auth_header = f"{self.token_prefix} {self._access_token}"
        headers = self.update_headers(request.headers, **{self.token_header_name: auth_header})
        
        return HTTPRequest(
            method=request.method,
            url=request.url,
            headers=headers,
            params=request.params,
            json=request.json,
            data=request.data,
            timeout=request.timeout,
        )
