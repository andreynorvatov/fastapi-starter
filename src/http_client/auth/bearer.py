"""Bearer Token аутентификация."""

from typing import Optional

from ..exceptions import AuthenticationError
from .base import AuthHandler
from ..models import HTTPRequest


class BearerAuth(AuthHandler):
    """Аутентификация с Bearer токеном."""
    
    def __init__(self, token: str, header_name: str = "Authorization") -> None:
        """
        Инициализация Bearer аутентификации.
        
        Args:
            token: Bearer токен
            header_name: Имя заголовка (по умолчанию "Authorization")
            
        Raises:
            AuthenticationError: Если токен пустой
        """
        if not token or not token.strip():
            raise AuthenticationError("Bearer токен не может быть пустым", "bearer")
        
        self.token = token.strip()
        self.header_name = header_name
    
    async def prepare_request(self, request: HTTPRequest) -> HTTPRequest:
        """
        Добавить Bearer токен в заголовки запроса.
        
        Args:
            request: Исходный запрос
            
        Returns:
            HTTPRequest: Запрос с добавленным заголовком авторизации
        """
        auth_header = f"Bearer {self.token}"
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
