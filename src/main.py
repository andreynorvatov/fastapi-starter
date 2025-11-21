from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api import api_router

app = FastAPI(title="Starter", version="0.1", default_response_class=ORJSONResponse, routes=api_router.routes)
