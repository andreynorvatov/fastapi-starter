"""Тесты для circuit breaker."""

import asyncio
import time

import pytest

from src.http_client.circuit_breaker import CircuitBreaker, CircuitState
from src.http_client.exceptions import HTTPResponseError


class TestCircuitBreaker:
    """Тесты Circuit Breaker."""
    
    def test_init_valid_params(self) -> None:
        """Тест валидных параметров."""
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60.0
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_init_invalid_params(self) -> None:
        """Тест ошибок при невалидных параметрах."""
        with pytest.raises(ValueError, match="failure_threshold должен быть больше 0"):
            CircuitBreaker(failure_threshold=0)
        with pytest.raises(ValueError, match="recovery_timeout должен быть больше 0"):
            CircuitBreaker(recovery_timeout=0)
    
    @pytest.mark.asyncio
    async def test_initial_state_closed(self) -> None:
        """Тест начального состояния CLOSED."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_success_keeps_closed(self) -> None:
        """Тест: успешные вызовы сохраняют состояние CLOSED."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_single_failure(self) -> None:
        """Тест одной ошибки - состояние остается CLOSED."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        with pytest.raises(HTTPResponseError):
            await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_multiple_failures_to_open(self) -> None:
        """Тест перехода в OPEN после нескольких ошибок."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        # Вызываем 3 раза (порог)
        for _ in range(3):
            with pytest.raises(HTTPResponseError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_open_state_blocks_calls(self) -> None:
        """Тест блокировки вызовов в состоянии OPEN."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        # Переводим в OPEN
        for _ in range(2):
            with pytest.raises(HTTPResponseError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Следующий вызов должен быть заблокирован
        with pytest.raises(Exception) as exc_info:  # CircuitBreakerOpenError
            await breaker.call(failing_func)
        
        assert "Circuit breaker открыт" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self) -> None:
        """Тест перехода в HALF_OPEN после таймаута."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        # Переводим в OPEN
        for _ in range(2):
            with pytest.raises(HTTPResponseError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Ждем recovery_timeout
        await asyncio.sleep(0.15)
        
        # Следующий вызов должен перевести в HALF_OPEN и затем в OPEN из-за ошибки
        state_during_call = None
        
        async def failing_func_with_state():
            nonlocal state_during_call
            state_during_call = breaker.state
            raise HTTPResponseError(500, "Server error")
        
        with pytest.raises(HTTPResponseError):
            await breaker.call(failing_func_with_state)
        
        # Проверяем, что во время вызова состояние было HALF_OPEN
        assert state_during_call == CircuitState.HALF_OPEN
        # После ошибки в HALF_OPEN состояние вернется в OPEN
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_success_closes(self) -> None:
        """Тест перехода обратно в CLOSED после успеха в HALF_OPEN."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        # Переводим в OPEN
        for _ in range(2):
            with pytest.raises(HTTPResponseError):
                await breaker.call(failing_func)
        
        # Ждем для HALF_OPEN
        await asyncio.sleep(0.15)
        
        # Успешный вызов в HALF_OPEN должен закрыть breaker
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_failure_returns_to_open(self) -> None:
        """Тест возврата в OPEN при ошибке в HALF_OPEN."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        async def failing_func():
            raise HTTPResponseError(500, "Server error")
        
        # Переводим в OPEN
        for _ in range(2):
            with pytest.raises(HTTPResponseError):
                await breaker.call(failing_func)
        
        # Ждем для HALF_OPEN
        await asyncio.sleep(0.15)
        
        # Ошибка в HALF_OPEN возвращает в OPEN
        with pytest.raises(HTTPResponseError):
            await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_non_expected_exception_not_counted(self) -> None:
        """Тест: неожиданные исключения не считаются за сбой."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        async def value_error_func():
            raise ValueError("Not an HTTP error")
        
        # ValueError не должен считаться (expected_exception = HTTPResponseError)
        with pytest.raises(ValueError):
            await breaker.call(value_error_func)
        
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_custom_expected_exception(self) -> None:
        """Тест кастомного типа ожидаемого исключения."""
        class CustomError(Exception):
            pass
        
        breaker = CircuitBreaker(
            failure_threshold=2,
            expected_exception=CustomError,
        )
        
        async def custom_error_func():
            raise CustomError("Custom error")
        
        with pytest.raises(CustomError):
            await breaker.call(custom_error_func)
        
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_state_change_callback(self) -> None:
        """Тест callback при изменении состояния."""
        changes = []
        
        def on_change(old_state: CircuitState, new_state: CircuitState):
            changes.append((old_state, new_state))
        
        breaker = CircuitBreaker(
            failure_threshold=2,
            on_state_change=on_change,
        )
        
        async def failing_func():
            raise HTTPResponseError(500, "Error")
        
        # Имитируем сбои для перехода в OPEN
        for _ in range(2):
            try:
                await breaker.call(failing_func)
            except HTTPResponseError:
                pass
        
        # Проверяем, что callback был вызван при изменениях
        assert len(changes) >= 1
        # Последнее изменение должно быть CLOSED -> OPEN
        assert changes[-1] == (CircuitState.CLOSED, CircuitState.OPEN)
    
    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        """Тест принудительного сброса."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        # Имитируем состояние OPEN
        breaker._state = CircuitState.OPEN
        breaker._failure_count = 5
        
        breaker.reset()
        
        # Ждем асинхронного сброса
        await asyncio.sleep(0.01)
        
        # Проверяем сброс
        assert breaker._state == CircuitState.CLOSED
        assert breaker.failure_count == 0
