"""Middleware для логирования HTTP запросов и ответов."""

import time
from typing import Optional

from ...logger import logger
from .base import Middleware
from ..models import HTTPRequest, HTTPResponse


class LoggingMiddleware(Middleware):
    """Middleware для детального логирования запросов и ответов."""
    
    def __init__(
        self,
        log_request_body: bool = True,
        log_response_body: bool = False,
        sensitive_headers: Optional[set[str]] = None,
    ) -> None:
        """
        Инициализация логирующего middleware.
        
        Args:
            log_request_body: Логировать тело запроса
            log_response_body: Логировать тело ответа (осторожно, может быть много данных)
            sensitive_headers: Набор заголовков, которые нужно маскировать в логах
        """
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_headers = sensitive_headers or {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-auth-token",
            "proxy-authorization",
        }
    
    def _mask_sensitive_data(self, headers: dict[str, str]) -> dict[str, str]:
        """Маскировать чувствительные заголовки."""
        masked = headers.copy()
        for key in masked:
            if key.lower() in self.sensitive_headers:
                masked[key] = "***MASKED***"
        return masked
    
    async def process_request(
        self,
        request: HTTPRequest,
        client: "AsyncHTTPClient",
    ) -> HTTPRequest:
        """Логировать исходящий запрос."""
        start_time = time.time()
        request.extra = {"_start_time": start_time}  # type: ignore[attr-defined]
        
        masked_headers = self._mask_sensitive_data(request.headers)
        
        logger.debug(
            f"→ HTTP {request.method} {request.url}",
            extra={
                "http_method": request.method,
                "http_url": request.url,
                "http_headers": masked_headers,
                "http_params": request.params,
                "http_body": request.json if self.log_request_body else None,
            },
        )
        
        return request
    
    async def process_response(
        self,
        response: HTTPResponse,
        request: HTTPRequest,
    ) -> HTTPResponse:
        """Логировать входящий ответ."""
        start_time = getattr(request, "extra", {}).get("_start_time", time.time())
        duration = time.time() - start_time
        
        masked_headers = self._mask_sensitive_data(response.headers)
        
        log_body = None
        if self.log_response_body and response.content:
            try:
                import json
                log_body = json.loads(response.content.decode("utf-8"))
            except Exception:
                log_body = response.content[:1000].decode("utf-8", errors="replace")
        
        log_level = logger.info if response.is_success() else logger.warning
        
        log_level(
            f"← HTTP {response.status_code} ({duration:.3f}s)",
            extra={
                "http_status": response.status_code,
                "http_duration": duration,
                "http_headers": masked_headers,
                "http_response_body": log_body,
                "http_success": response.is_success(),
            },
        )
        
        return response
