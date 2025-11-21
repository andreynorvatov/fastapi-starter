from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from typing import AsyncGenerator

from src.database import db_connection_pool

async def get_db_connection() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии базы данных"""
    async for session in db_connection_pool.get_session():
        yield session