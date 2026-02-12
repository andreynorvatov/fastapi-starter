from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, ORJSONResponse

from src.api import api_router
from src.config import settings
from src.database import async_engine
from src.logger import logger
import asyncio
from src.background_tasks import periodic_task


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa
    """Управление жизненным циклом приложения."""
    # Startup
    logger.info(f"Приложение запущено. Уровень логирования: {settings.LOG_LEVEL}")
    asyncio.create_task(periodic_task())
    yield
    # Shutdown - корректное закрытие пула соединений
    await async_engine.dispose()
    logger.info("Приложение остановлено")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Глобальный обработчик необработанных исключений."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router)
