import asyncio
from src.logger import logger

async def periodic_task() -> None:
    """Пример фоновой асинхронной задачи, которая каждые 10 секунд пишет в лог."""
    while True:
        logger.info("Фоновая задача выполняется")
        await asyncio.sleep(10)
