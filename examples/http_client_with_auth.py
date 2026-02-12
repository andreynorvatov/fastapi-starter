"""Примеры использования различных типов аутентификации."""

import asyncio

from src.http_client import (
    AsyncHTTPClient,
    BearerAuth,
    APIKeyAuth,
    BasicAuth,
    OAuth2ClientCredentials,
    ClientConfig,
)


async def bearer_example() -> None:
    """Пример с Bearer токеном."""
    print("=== Bearer Auth Example ===")
    
    auth = BearerAuth(token="your-bearer-token-here")
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        auth=auth,
    ) as client:
        try:
            response = await client.get("/protected/resource")
            print(f"Success: {response.json_data}")
        except Exception as e:
            print(f"Error: {e}")


async def api_key_example() -> None:
    """Пример с API Key в заголовке."""
    print("\n=== API Key Example ===")
    
    auth = APIKeyAuth(
        api_key="your-api-key",
        header_name="X-API-Key",  # или используем query параметр
        # query_param_name="api_key"  # альтернативный вариант
    )
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        auth=auth,
    ) as client:
        try:
            response = await client.get("/data")
            print(f"Success: {response.json_data}")
        except Exception as e:
            print(f"Error: {e}")


async def basic_example() -> None:
    """Пример с Basic аутентификацией."""
    print("\n=== Basic Auth Example ===")
    
    auth = BasicAuth(username="user", password="password")
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        auth=auth,
    ) as client:
        try:
            response = await client.get("/secure")
            print(f"Success: {response.json_data}")
        except Exception as e:
            print(f"Error: {e}")


async def oauth2_example() -> None:
    """Пример с OAuth2 Client Credentials."""
    print("\n=== OAuth2 Example ===")
    
    auth = OAuth2ClientCredentials(
        token_url="https://auth.example.com/oauth/token",
        client_id="your-client-id",
        client_secret="your-client-secret",
        scope="read write",
        cache_duration=3600,  # 1 час
    )
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        auth=auth,
    ) as client:
        try:
            response = await client.get("/api/v1/users")
            print(f"Success: {response.json_data}")
        except Exception as e:
            print(f"Error: {e}")


async def main() -> None:
    """Запуск всех примеров."""
    await bearer_example()
    await api_key_example()
    await basic_example()
    # await oauth2_example()  # Раскомментируйте для реального использования


if __name__ == "__main__":
    asyncio.run(main())
