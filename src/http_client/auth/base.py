"""Базовые классы для аутентификации."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..models import HTTPRequest


class AuthHandler(ABC):
    """Базовый класс для обработчиков аутентификации."""
    
    @abstractmethod
    async def prepare_request(self, request: HTTPRequest) -> HTTPRequest:
        """
        Подготовить запрос с добавлением аутентификационных данных.
        
        Args:
            request: Исходный HTTP запрос
            
        Returns:
            HTTPRequest: Модифицированный запрос с аутентификацией
        """
        pass
    
    def update_headers(self, headers: Dict[str, str], **auth_headers: str) -> Dict[str, str]:
        """Обновить заголовки, сохраняя существующие."""
        updated = headers.copy()
        for key, value in auth_headers.items():
            if value:  # Добавляем только непустые значения
                updated[key] = value
        return updated
