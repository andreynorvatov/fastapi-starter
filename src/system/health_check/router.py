from fastapi import APIRouter, status

from src.system.health_check.schemas import HealthCheck

health_check_router = APIRouter()


@health_check_router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Проверка состояния приложения",
    description="Дополнительная информация: отустствует",
)
async def get_health() -> HealthCheck:
    return HealthCheck(status="OK")
