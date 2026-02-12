"""Тесты для rate limiter."""

import asyncio
import time

import pytest

from src.http_client.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    """Тесты Token Bucket алгоритма."""
    
    def test_init_valid_params(self) -> None:
        """Тест валидных параметров."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=20)
        assert limiter.rate == 10.0
        assert limiter.burst == 20
        assert limiter.is_configured() is True
    
    def test_init_invalid_params(self) -> None:
        """Тест ошибок при невалидных параметрах."""
        with pytest.raises(ValueError, match="rate должен быть больше 0"):
            TokenBucketRateLimiter(rate=0, burst=10)
        with pytest.raises(ValueError, match="burst должен быть больше 0"):
            TokenBucketRateLimiter(rate=10, burst=0)
    
    @pytest.mark.asyncio
    async def test_initial_tokens(self) -> None:
        """Тест начального количества токенов."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        assert limiter.available_tokens == 5.0
    
    @pytest.mark.asyncio
    async def test_acquire_immediate(self) -> None:
        """Тест немедленного получения токена."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        wait_time = await limiter.acquire(1)
        assert wait_time == 0.0
        assert limiter.available_tokens == 4.0
    
    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self) -> None:
        """Тест получения нескольких токенов."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=10)
        wait_time = await limiter.acquire(3)
        assert wait_time == 0.0
        assert limiter.available_tokens == 7.0
    
    @pytest.mark.asyncio
    async def test_acquire_wait_when_empty(self) -> None:
        """Тест ожидания при пустом бакете."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=2)
        
        # Сначала забираем все токены
        await limiter.acquire(2)
        assert limiter.available_tokens < 0.1  # почти 0
        
        # Следующий запрос должен вернуть время ожидания (не блокировать)
        wait_time = await limiter.acquire(1)
        
        # Время ожидания должно быть положительным (примерно 0.1 секунды)
        assert wait_time > 0.05
        # Сам acquire не блокирует, поэтому elapsed должен быть мал
        # (не проверяем elapsed, так как acquire возвращает wait_time, а не ждет)
    
    @pytest.mark.asyncio
    async def test_refill(self) -> None:
        """Тест пополнения бакета."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=10)
        
        # Забираем все токены
        await limiter.acquire(10)
        assert limiter.available_tokens < 0.1  # почти 0
        
        # Ждем пополнения
        await asyncio.sleep(0.2)  # 0.2 секунды = 2 токена при rate=10
        
        # Вызываем acquire(0) чтобы триггерить refill и обновить внутреннее состояние
        await limiter.acquire(0)
        
        # Проверяем, что токены пополнились
        assert limiter.available_tokens > 0.0
    
    @pytest.mark.asyncio
    async def test_burst_limit(self) -> None:
        """Тест ограничения burst."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        
        # Пытаемся взять больше чем burst
        wait_time = await limiter.acquire(6)
        assert wait_time > 0.0  # Должны ждать, т.к. burst=5
        
        # После ожидания токены должны быть 0 (все использованы)
        assert limiter.available_tokens < 0.1
    
    def test_reset(self) -> None:
        """Тест сброса бакета."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        
        # Имитируем использование
        limiter._tokens = 1.0
        limiter.reset()
        
        assert limiter.available_tokens == 5.0
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire(self) -> None:
        """Тест конкурентного получения токенов."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=10)
        
        async def acquire_one() -> float:
            return await limiter.acquire(1)
        
        # Запускаем 10 конкурентных запросов
        tasks = [acquire_one() for _ in range(10)]
        wait_times = await asyncio.gather(*tasks)
        
        # Все должны получить токены без ожидания (burst=10)
        assert all(w == 0.0 for w in wait_times)
        assert limiter.available_tokens < 0.1
    
    @pytest.mark.asyncio
    async def test_acquire_zero_tokens(self) -> None:
        """Тест запроса 0 токенов."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst=5)
        wait_time = await limiter.acquire(0)
        assert wait_time == 0.0
