import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_basic_client(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 404
    # assert "message" in response.json()

@pytest.mark.asyncio
async def test_db_session(db_session: AsyncSession):
    # Проверяем что сессия работает
    assert db_session.is_active
    # Можно добавить простой запрос к БД для проверки


# def test_create_user(client):
#     response = client.get("/")
#     assert response.status_code == 404
