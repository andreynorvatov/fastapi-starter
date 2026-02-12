"""Basic аутентификация."""

import base64
from typing import Optional

from ..exceptions import AuthenticationError
from .base import AuthHandler
from ..models import HTTPRequest


class BasicAuth(AuthHandler):
    """Аутентификация Basic (логин/пароль)."""
    
    def __init__(
        self,
        username: str,
        password: str,
        header_name: str = "Authorization",
    ) -> None:
        """
        Инициализация Basic аутентификации.
        
        Args:
            username: Имя пользователя
            password: Пароль
            header_name: Имя заголовка (по умолчанию "Authorization")
            
        Raises:
            AuthenticationError: Если username или password пустые
        """
        if not username or not username.strip():
            raise AuthenticationError("Имя пользователя не может быть пустым", "basic")
        if password is None:  # password может быть пустой строкой, но не None
            raise AuthenticationError("Пароль не может быть None", "basic")
        
        self.username = username.strip()
        self.password = password
        self.header_name = header_name
    
    def _encode_credentials(self) -> str:
        """Закодировать credentials в Base64."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"
    
    async def prepare_request(self, request: HTTPRequest) -> HTTPRequest:
        """
        Добавить Basic auth заголовок в запрос.
        
        Args:
            request: Исходный запрос
            
        Returns:
            HTTPRequest: Запрос с добавленным заголовком авторизации
        """
        auth_header = self._encode_credentials()
        headers = self.update_headers(request.headers, **{self.header_name: auth_header})
        
        return HTTPRequest(
            method=request.method,
            url=request.url,
            headers=headers,
            params=request.params,
            json=request.json,
            data=request.data,
            timeout=request.timeout,
        )
