"""Пример использования rate limiting."""

import asyncio

from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    TokenBucketRateLimiter,
)


async def main() -> None:
    """Пример с rate limiting."""
    print("=== Rate Limiting Example ===")
    
    # Создаем rate limiter: 10 запросов в секунду с burst=20
    rate_limiter = TokenBucketRateLimiter(
        rate=10.0,  # 10 запросов в секунду
        burst=20,   # можно сделать всплеск до 20
    )
    
    config = ClientConfig(
        timeout=30.0,
        enable_rate_limiting=True,
        rate_limit_rate=10.0,
        rate_limit_burst=20,
    )
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        config=config,
        rate_limiter=rate_limiter,
    ) as client:
        # Выполняем несколько запросов
        for i in range(5):
            try:
                response = await client.get(f"/resource/{i}")
                print(f"Request {i}: {response.status_code}")
            except Exception as e:
                print(f"Request {i} failed: {e}")
            
            # Небольшая задержка для демонстрации
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
