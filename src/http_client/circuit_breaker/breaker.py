"""Circuit breaker pattern implementation."""

import asyncio
import time
from enum import Enum
from typing import Callable, Optional, Type

from ..exceptions import CircuitBreakerOpenError, HTTPClientError


class CircuitState(Enum):
    """Состояния circuit breaker."""
    CLOSED = "closed"      # Нормальная работа
    OPEN = "open"          # Открыт, запросы блокируются
    HALF_OPEN = "half_open"  # Пробный запрос разрешен


class CircuitBreaker:
    """
    Реализация паттерна Circuit Breaker.
    
    Защищает от каскадных сбоев при вызовах внешних сервисов.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = HTTPClientError,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ) -> None:
        """
        Инициализация circuit breaker.
        
        Args:
            failure_threshold: Количество последовательных ошибок для открытия breaker
            recovery_timeout: Время в секундах перед переходом в HALF_OPEN
            expected_exception: Тип исключения, которое считается сбоем
            on_state_change: Callback при изменении состояния
        """
        if failure_threshold <= 0:
            raise ValueError("failure_threshold должен быть больше 0")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout должен быть больше 0")
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Текущее состояние circuit breaker."""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Количество последовательных ошибок."""
        return self._failure_count
    
    def is_configured(self) -> bool:
        """Circuit breaker всегда настроен при создании."""
        return True
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Выполнить функцию с защитой circuit breaker.
        
        Args:
            func: Функция для вызова
            *args: Аргументы функции
            **kwargs: Ключевые аргументы функции
            
        Returns:
            Результат вызова функции
            
        Raises:
            CircuitBreakerOpenError: Если breaker в состоянии OPEN
            Exception: Исключение от функции, если она завершилась с ошибкой
        """
        async with self._lock:
            if self._state == CircuitState.OPEN:
                # Проверить, прошло ли достаточно времени для перехода в HALF_OPEN
                if self._last_failure_time and (
                    time.monotonic() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerOpenError(
                        message="Circuit breaker открыт",
                        circuit_breaker_state=self._state.value,
                        recovery_timeout=self.recovery_timeout,
                    )
            
            if self._state == CircuitState.HALF_OPEN:
                # В HALF_OPEN разрешаем только один запрос для теста
                # (логика проверки результата будет после вызова)
                pass
        
        try:
            result = await func(*args, **kwargs)
            
            # Успешный вызов
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._transition_to_closed()
                elif self._state == CircuitState.CLOSED:
                    self._failure_count = 0
            
            return result
            
        except Exception as e:
            # Проверяем, является ли исключение ожидаемым
            if not isinstance(e, self.expected_exception):
                # Неожиданное исключение - не считаем за сбой
                raise
            
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.monotonic()
                
                if self._state == CircuitState.HALF_OPEN:
                    # В HALF_OPEN любой сбой возвращает в OPEN
                    self._transition_to_open()
                elif (
                    self._state == CircuitState.CLOSED
                    and self._failure_count >= self.failure_threshold
                ):
                    self._transition_to_open()
            
            raise
    
    def _transition_to_open(self) -> None:
        """Перейти в состояние OPEN."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._notify_state_change(old_state, self._state)
    
    def _transition_to_half_open(self) -> None:
        """Перейти в состояние HALF_OPEN."""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._notify_state_change(old_state, self._state)
    
    def _transition_to_closed(self) -> None:
        """Перейти в состояние CLOSED."""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._notify_state_change(old_state, self._state)
    
    def _notify_state_change(
        self,
        old_state: CircuitState,
        new_state: CircuitState
    ) -> None:
        """Уведомить о изменении состояния."""
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception:
                # Игнорируем ошибки в callback
                pass
    
    def reset(self) -> None:
        """Принудительно сбросить circuit breaker в состояние CLOSED."""
        asyncio.create_task(self._async_reset())
    
    async def _async_reset(self) -> None:
        """Асинхронный сброс."""
        async with self._lock:
            self._transition_to_closed()
