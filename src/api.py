from fastapi import APIRouter

from src.example.routes import example_router
from src.system.health_check.routes import health_check_router
from src.system.home_page.routes import router as home_page_router

api_router = APIRouter()

api_router.include_router(health_check_router, prefix="/system", tags=["Системные API."])
api_router.include_router(example_router, prefix="/example", tags=["Пример API."])
api_router.include_router(home_page_router, prefix="", tags=["Главная страница"])
