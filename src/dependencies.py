from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database import async_engine


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Асинхронный генератор для получения соединения с БД.
    
    Используется как dependency injection в FastAPI для получения
    сырого соединения (AsyncConnection) вместо сессии (AsyncSession).
    Соединение автоматически закрывается при выходе из async with.
    
    Yields:
        AsyncConnection: Асинхронное соединение SQLAlchemy
        
    Example:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncConnection
        
        @router.get("/items")
        async def get_items(
            conn: AsyncConnection = Depends(get_db_connection)
        ):
            result = await conn.execute(text("SELECT * FROM items"))
            return result.fetchall()
    """
    async with async_engine.connect() as connection:
        yield connection
