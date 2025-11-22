from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager

from src.api import api_router
from src.config import settings
from src.database import db_connection_pool

from src.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_connection_pool.connect()

    logger.info("Application started")
    engine_stats = db_connection_pool.engine_stats
    print(engine_stats)
    yield
    # Shutdown
    await db_connection_pool.disconnect()
    logger.info("Application stopped")
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1",
    default_response_class=ORJSONResponse,
    routes=api_router.routes,
    lifespan=lifespan
)
