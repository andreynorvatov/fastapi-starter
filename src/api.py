from fastapi import APIRouter

from src.system.health_check.router import health_check_router

api_router = APIRouter(
)

api_router.include_router(health_check_router, prefix="/system", tags=["Системыне API."])