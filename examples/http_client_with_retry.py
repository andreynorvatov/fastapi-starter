"""Пример использования retry логики."""

import asyncio

from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    RetryConfig,
)


async def main() -> None:
    """Пример с настройкой retry."""
    print("=== Retry Example ===")
    
    # Конфигурация retry
    retry_config = RetryConfig(
        attempts=3,
        backoff_factor=1.0,
        max_delay=10.0,
        statuses={429, 500, 502, 503, 504},
        methods={"GET", "POST", "PUT"},
    )
    
    config = ClientConfig(
        timeout=30.0,
        retry_attempts=3,  # Включает встроенный RetryMiddleware
        retry_backoff_factor=1.0,
        retry_max_delay=10.0,
    )
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        config=config,
    ) as client:
        try:
            response = await client.get("/unstable-endpoint")
            print(f"Success after retries: {response.status_code}")
        except Exception as e:
            print(f"Failed after all retries: {e}")


if __name__ == "__main__":
    asyncio.run(main())
