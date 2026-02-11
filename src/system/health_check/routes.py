from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.system.health_check.schemas import HealthCheck

health_check_router = APIRouter()


@health_check_router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Проверка состояния приложения",
    description="Проверяет доступность базы данных и приложения",
)
async def get_health(session: AsyncSession = Depends(get_async_session)) -> HealthCheck:
    """Проверка здоровья приложения с проверкой подключения к БД."""
    await session.execute(text("SELECT 1"))
    return HealthCheck(status="OK")
