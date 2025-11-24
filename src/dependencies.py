from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db_connection_pool


async def get_db_connection() -> AsyncGenerator[AsyncSession]:
    """Зависимость для получения сессии базы данных"""
    async for session in db_connection_pool.get_session():
        yield session
