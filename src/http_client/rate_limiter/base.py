"""Базовый класс для ограничителей частоты запросов."""

from abc import ABC, abstractmethod
import time
from typing import Optional


class RateLimiter(ABC):
    """Базовый интерфейс для ограничителей частоты запросов."""
    
    @abstractmethod
    async def acquire(self, tokens: int = 1) -> float:
        """
        Запросить разрешение на выполнение запроса.
        
        Args:
            tokens: Количество токенов для запроса (обычно 1)
            
        Returns:
            float: Время ожидания в секундах (0 если разрешение получено сразу)
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Проверить, настроен ли rate limiter."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Сбросить состояние rate limiter."""
        pass
