"""Token Bucket алгоритм ограничения частоты запросов."""

import asyncio
import time
from typing import Optional

from .base import RateLimiter


class TokenBucketRateLimiter(RateLimiter):
    """
    Token Bucket алгоритм для ограничения частоты запросов.
    
    Позволяет задавать среднюю скорость запросов (rate) с возможностью
    коротких всплесков (burst).
    """
    
    def __init__(
        self,
        rate: float,  # запросов в секунду
        burst: int = 1,
    ) -> None:
        """
        Инициализация Token Bucket.
        
        Args:
            rate: Средняя скорость запросов (токенов в секунду)
            burst: Максимальный размер бакета (количество токенов)
        """
        if rate <= 0:
            raise ValueError("rate должен быть больше 0")
        if burst <= 0:
            raise ValueError("burst должен быть больше 0")
        
        self.rate = rate
        self.burst = burst
        
        # Состояние бакета
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    def is_configured(self) -> bool:
        """Rate limiter всегда настроен при создании."""
        return True
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Запросить токены.
        
        Args:
            tokens: Количество необходимых токенов
            
        Returns:
            float: Время ожидания в секундах (0 если токены доступны сразу)
        """
        if tokens < 0:
            raise ValueError("Number of tokens must be non-negative")
        
        async with self._lock:
            await self._refill()
            
            if self._tokens >= tokens:
                # Достаточно токенов
                self._tokens -= tokens
                return 0.0
            
            # Нужно ждать
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self.rate
            
            # Обновляем состояние после ожидания
            self._tokens = 0.0
            self._last_update = time.monotonic() + wait_time
            
            return wait_time
    
    async def _refill(self) -> None:
        """Пополнить бакет в соответствии с прошедшим временем."""
        now = time.monotonic()
        time_passed = now - self._last_update
        
        if time_passed > 0:
            new_tokens = time_passed * self.rate
            self._tokens = min(self.burst, self._tokens + new_tokens)
            self._last_update = now
    
    def reset(self) -> None:
        """Сбросить бакет к максимальному размеру."""
        self._tokens = float(self.burst)
        self._last_update = time.monotonic()
    
    @property
    def available_tokens(self) -> float:
        """Текущее количество доступных токенов (thread-safe чтение)."""
        return self._tokens
