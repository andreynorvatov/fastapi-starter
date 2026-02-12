"""API Key аутентификация."""

from typing import Optional

from ..exceptions import AuthenticationError
from .base import AuthHandler
from ..models import HTTPRequest


class APIKeyAuth(AuthHandler):
    """Аутентификация с API ключом."""
    
    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
        query_param_name: Optional[str] = None,
    ) -> None:
        """
        Инициализация API Key аутентификации.
        
        Args:
            api_key: API ключ
            header_name: Имя заголовка для передачи ключа
            query_param_name: Имя query параметра (если None, используется заголовок)
            
        Raises:
            AuthenticationError: Если API ключ пустой
        """
        if not api_key or not api_key.strip():
            raise AuthenticationError("API ключ не может быть пустым", "api_key")
        
        self.api_key = api_key.strip()
        self.header_name = header_name
        self.query_param_name = query_param_name
        
        if not self.query_param_name and not self.header_name:
            raise AuthenticationError(
                "Необходимо указать либо header_name, либо query_param_name",
                "api_key"
            )
    
    async def prepare_request(self, request: HTTPRequest) -> HTTPRequest:
        """
        Добавить API ключ в запрос (в заголовок или query параметр).
        
        Args:
            request: Исходный запрос
            
        Returns:
            HTTPRequest: Запрос с добавленным API ключом
        """
        headers = request.headers.copy()
        params = request.params.copy()
        
        if self.query_param_name:
            params[self.query_param_name] = self.api_key
        else:
            headers[self.header_name] = self.api_key
        
        return HTTPRequest(
            method=request.method,
            url=request.url,
            headers=headers,
            params=params,
            json=request.json,
            data=request.data,
            timeout=request.timeout,
        )
