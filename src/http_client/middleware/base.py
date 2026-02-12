"""Базовый класс для middleware."""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from ...logger import logger
from ..models import HTTPRequest, HTTPResponse


class Middleware(ABC):
    """Базовый интерфейс для middleware."""
    
    @abstractmethod
    async def process_request(
        self,
        request: HTTPRequest,
        client: "AsyncHTTPClient",
    ) -> HTTPRequest:
        """
        Обработать запрос перед отправкой.
        
        Args:
            request: HTTP запрос
            client: Ссылка на HTTP клиент
            
        Returns:
            HTTPRequest: Модифицированный запрос
        """
        pass
    
    @abstractmethod
    async def process_response(
        self,
        response: HTTPResponse,
        request: HTTPRequest,
    ) -> HTTPResponse:
        """
        Обработать ответ после получения.
        
        Args:
            response: HTTP ответ
            request: Исходный запрос
            
        Returns:
            HTTPResponse: Модифицированный ответ
        """
        pass


class MiddlewareManager:
    """Менеджер middleware цепочки."""
    
    def __init__(self, middlewares: list[Middleware]) -> None:
        """
        Инициализация менеджера.
        
        Args:
            middlewares: Список middleware в порядке выполнения
        """
        self.middlewares = middlewares
    
    async def process_request(
        self,
        request: HTTPRequest,
        client: "AsyncHTTPClient",
    ) -> HTTPRequest:
        """Обработать запрос через все middleware."""
        for middleware in self.middlewares:
            try:
                request = await middleware.process_request(request, client)
            except Exception as e:
                logger.error(
                    f"Ошибка в middleware {middleware.__class__.__name__} "
                    f"при обработке запроса: {e}",
                    exc_info=True,
                )
                raise
        return request
    
    async def process_response(
        self,
        response: HTTPResponse,
        request: HTTPRequest,
    ) -> HTTPResponse:
        """Обработать ответ через все middleware в обратном порядке."""
        for middleware in reversed(self.middlewares):
            try:
                response = await middleware.process_response(response, request)
            except Exception as e:
                logger.error(
                    f"Ошибка в middleware {middleware.__class__.__name__} "
                    f"при обработке ответа: {e}",
                    exc_info=True,
                )
                raise
        return response
