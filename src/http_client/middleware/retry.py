"""Middleware для повторных попыток запросов."""

import asyncio
import random
from typing import Optional

from ...logger import logger
from .base import Middleware
from ..exceptions import RetryExhaustedError, RateLimitError, HTTPResponseError
from ..models import HTTPRequest, HTTPResponse, RetryConfig


class RetryMiddleware(Middleware):
    """Middleware для автоматических повторных попыток при ошибках."""
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
    ) -> None:
        """
        Инициализация retry middleware.
        
        Args:
            config: Конфигурация повторных попыток
        """
        self.config = config or RetryConfig()
    
    async def process_request(
        self,
        request: HTTPRequest,
        client: "AsyncHTTPClient",
    ) -> HTTPRequest:
        """
        Retry middleware не модифицирует запрос.
        
        Returns:
            HTTPRequest: Без изменений
        """
        return request
    
    async def process_response(
        self,
        response: HTTPResponse,
        request: HTTPRequest,
    ) -> HTTPResponse:
        """
        Обработка ответа с возможными повторными попытками.
        
        Note: Этот метод должен вызываться только при обработке исключений,
        поэтому реальная логика вынесена в метод execute_with_retry.
        """
        return response
    
    async def execute_with_retry(
        self,
        request_func,
        request: HTTPRequest,
    ) -> HTTPResponse:
        """
        Выполнить запрос с повторными попытками.
        
        Args:
            request_func: Асинхронная функция для выполнения запроса
            request: HTTP запрос
            
        Returns:
            HTTPResponse: Успешный ответ
            
        Raises:
            RetryExhaustedError: Если все попытки исчерпаны
        """
        last_exception: Optional[Exception] = None
        last_response: Optional[HTTPResponse] = None
        
        for attempt in range(self.config.attempts):
            try:
                response = await request_func()
                
                # Проверяем, нужно ли повторять при успешном статусе
                if self._should_retry_response(response, attempt):
                    last_response = response
                    raise self._create_retry_exception(response, attempt)
                
                return response
                
            except RateLimitError as e:
                # Rate limit ошибки - повторяем даже если attempts исчерпаны
                last_exception = e
                if attempt < self.config.attempts - 1:
                    wait_time = self._calculate_wait_time(attempt, e.retry_after)
                    logger.warning(
                        f"Rate limit достигнут, повтор через {wait_time:.2f}s "
                        f"(попытка {attempt + 1}/{self.config.attempts})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                break
                
            except HTTPResponseError as e:
                # Проверяем, является ли ошибка повторяемой
                if (
                    e.status_code in self.config.statuses
                    and request.method in self.config.methods
                ):
                    last_exception = e
                    if attempt < self.config.attempts - 1:
                        wait_time = self._calculate_wait_time(attempt)
                        logger.warning(
                            f"HTTP {e.status_code}, повтор через {wait_time:.2f}s "
                            f"(попытка {attempt + 1}/{self.config.attempts})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Последняя попытка, выходим для raising RetryExhaustedError
                        break
                else:
                    # Не повторяемая ошибка - сразу поднимаем
                    raise
                
            except Exception as e:
                # Сетевые ошибки и другие исключения - повторяем
                last_exception = e
                if attempt < self.config.attempts - 1:
                    wait_time = self._calculate_wait_time(attempt)
                    logger.warning(
                        f"Ошибка запроса: {e}, повтор через {wait_time:.2f}s "
                        f"(попытка {attempt + 1}/{self.config.attempts})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                break
        
        # Все попытки исчерпаны
        if last_exception:
            raise RetryExhaustedError(
                f"Исчерпаны все попытки ({self.config.attempts})",
                last_exception,
            )
        elif last_response:
            raise self._create_retry_exception(last_response, self.config.attempts)
        else:
            raise RetryExhaustedError(
                f"Исчерпаны все попытки ({self.config.attempts})",
                None,
            )
    
    def _should_retry_response(self, response: HTTPResponse, attempt: int) -> bool:
        """
        Проверить, нужно ли повторять запрос на основе ответа.
        
        Args:
            response: HTTP ответ
            attempt: Номер текущей попытки
            
        Returns:
            bool: True если нужно повторять
        """
        # Повторяем, если есть оставшиеся попытки и ответ - ошибка с повторяемым статусом
        return (
            attempt < self.config.attempts - 1
            and response.is_error()
            and response.status_code in self.config.statuses
        )
    
    def _create_retry_exception(
        self,
        response: HTTPResponse,
        attempt: int,
    ) -> HTTPResponseError:
        """Создать исключение для retry."""
        return HTTPResponseError(
            status_code=response.status_code,
            message=f"Retry after {attempt + 1} attempts",
            response_content=response.content,
            response_headers=response.headers,
        )
    
    def _calculate_wait_time(
        self,
        attempt: int,
        retry_after: Optional[int] = None,
    ) -> float:
        """
        Вычислить время ожидания перед следующей попыткой.
        
        Args:
            attempt: Номер попытки (0-based)
            retry_after: Заголовок Retry-After (в секундах)
            
        Returns:
            float: Время ожидания в секундах
        """
        if retry_after is not None:
            return float(retry_after)
        
        # Экспоненциальная задержка с jitter
        backoff = self.config.backoff_factor * (2 ** attempt)
        jitter = random.uniform(0, backoff * 0.1)  # 10% jitter
        wait_time = min(backoff + jitter, self.config.max_delay)
        
        return wait_time
