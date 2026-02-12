"""Базовый пример использования AsyncHTTPClient."""

import asyncio

from src.http_client import AsyncHTTPClient, ClientConfig


async def main() -> None:
    """Базовый пример."""
    # Создаем конфигурацию
    config = ClientConfig(
        timeout=30.0,
        max_connections=100,
    )
    
    # Создаем клиент
    async with AsyncHTTPClient(
        base_url="https://jsonplaceholder.typicode.com",
        config=config,
    ) as client:
        # Выполняем GET запрос
        response = await client.get("/posts/1")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json_data}")
        
        # POST запрос
        response = await client.post(
            "/posts",
            json={
                "title": "foo",
                "body": "bar",
                "userId": 1,
            },
        )
        print(f"Created: {response.json_data}")


if __name__ == "__main__":
    asyncio.run(main())
