"""
Тесты для главной страницы (home page) приложения.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_home_page_returns_200(client: AsyncClient) -> None:
    """Главная страница должна возвращать статус 200."""
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_home_page_content_type_html(client: AsyncClient) -> None:
    """Content-Type должен быть text/html."""
    response = await client.get("/")
    # FastAPI may include charset in content-type
    assert response.headers.get("content-type", "").startswith("text/html")


@pytest.mark.asyncio
async def test_home_page_contains_service_name(client: AsyncClient) -> None:
    """Ответ должен содержать название проекта из настроек."""
    response = await client.get("/")
    content = response.text
    from src.config import settings
    assert settings.PROJECT_NAME in content


@pytest.mark.asyncio
async def test_home_page_method_not_allowed(client: AsyncClient) -> None:
    """Главная страница доступна только через GET."""
    for method in ("post", "put", "delete", "patch"):
        # getattr(client, method) returns the async method function
        response = await getattr(client, method)("/")
        assert response.status_code == 405
