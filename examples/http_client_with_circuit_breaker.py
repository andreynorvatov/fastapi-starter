"""Пример использования circuit breaker."""

import asyncio

from src.http_client import (
    AsyncHTTPClient,
    ClientConfig,
    CircuitBreaker,
    CircuitState,
)


def on_circuit_breaker_state_change(
    old_state: CircuitState,
    new_state: CircuitState,
) -> None:
    """Callback для отслеживания изменений состояния circuit breaker."""
    print(f"Circuit breaker state changed: {old_state.value} -> {new_state.value}")


async def main() -> None:
    """Пример с circuit breaker."""
    print("=== Circuit Breaker Example ===")
    
    # Создаем circuit breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,  # После 3 ошибок переходит в OPEN
        recovery_timeout=10.0,  # Через 10 секунд переходит в HALF_OPEN
        on_state_change=on_circuit_breaker_state_change,
    )
    
    config = ClientConfig(
        timeout=5.0,
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_timeout=10.0,
    )
    
    async with AsyncHTTPClient(
        base_url="https://api.example.com",
        config=config,
        circuit_breaker=circuit_breaker,
    ) as client:
        # Симулируем несколько неудачных запросов
        for i in range(5):
            try:
                # Предположим, этот endpoint часто падает
                response = await client.get("/unstable-endpoint")
                print(f"Request {i}: Success")
            except Exception as e:
                print(f"Request {i}: Failed - {type(e).__name__}")
            
            await asyncio.sleep(1)
        
        print(f"\nCircuit breaker state: {circuit_breaker.state.value}")
        print(f"Failure count: {circuit_breaker.failure_count}")


if __name__ == "__main__":
    asyncio.run(main())
