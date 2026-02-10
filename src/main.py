from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api import api_router
from src.config import settings
from src.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa
    # Startup

    logger.info("Application started")
    yield

    # Shutdown
    logger.info("Application stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1",
    default_response_class=ORJSONResponse,
    routes=api_router.routes,
    lifespan=lifespan,
)
