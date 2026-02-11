"""
Тесты для сервиса System (health_check).

Содержит тесты для:
- API эндпоинта GET /system/health
"""

import pytest
from httpx import AsyncClient


class TestHealthCheckEndpoint:
    """Тесты для GET /system/health эндпоинта."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client: AsyncClient) -> None:
        """Тест что health_check возвращает статус 200."""
        response = await client.get("/system/health")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_response_structure(self, client: AsyncClient) -> None:
        """Тест структуры ответа health_check."""
        response = await client.get("/system/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "OK"

    @pytest.mark.asyncio
    async def test_health_check_response_model(self, client: AsyncClient) -> None:
        """Тест соответствия ответа модели HealthCheck."""
        response = await client.get("/system/health")

        data = response.json()
        
        # Проверяем что ответ содержит только ожидаемые поля
        assert set(data.keys()) == {"status"}
        assert data["status"] == "OK"
        assert isinstance(data["status"], str)

    @pytest.mark.asyncio
    async def test_health_check_is_get_only(self, client: AsyncClient) -> None:
        """Тест что health_check доступен только через GET запрос."""
        # POST должен возвращать 405 Method Not Allowed
        response = await client.post("/system/health")
        assert response.status_code == 405

        # PUT должен возвращать 405 Method Not Allowed
        response = await client.put("/system/health")
        assert response.status_code == 405

        # DELETE должен возвращать 405 Method Not Allowed
        response = await client.delete("/system/health")
        assert response.status_code == 405
