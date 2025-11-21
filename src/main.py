from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api import api_router
from src.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1",
    default_response_class=ORJSONResponse,
    routes=api_router.routes,
)
