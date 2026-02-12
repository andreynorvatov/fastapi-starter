from fastapi import APIRouter

from src.example.routes import example_router
from src.system.health_check.routes import health_check_router
from src.system.home_page.routes import router as home_page_router
from src.example.sse import router as sse_router
from src.file_storage.routes import file_storage_router
from src.external.routes import external_router

api_router = APIRouter()

api_router.include_router(health_check_router, prefix="/system", tags=["Системные API."])
api_router.include_router(example_router, prefix="/example", tags=["Пример API."])
api_router.include_router(home_page_router, prefix="", tags=["Главная страница"])
api_router.include_router(sse_router, prefix="/example", tags=["SSE"])
api_router.include_router(file_storage_router, prefix="/files", tags=["Файловое хранилище"])
api_router.include_router(external_router, prefix="/external", tags=["Внешние API"])
