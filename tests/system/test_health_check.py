import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_async_endpoint(async_client: AsyncClient) -> None:
    response = await async_client.get("/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
