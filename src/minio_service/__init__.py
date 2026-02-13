"""Minio Service Module."""

from .config import MinioSettings, get_minio_settings
from .client import MinioClient, minio_client
from .schemas import (
    MinioObjectCreate,
    MinioObjectUpdate,
    MinioObjectResponse,
    MinioListResponse,
    MinioPresignedUrlResponse,
)
from .crud import MinioCRUD, minio_crud
from .service import MinioService
from .routes import router as minio_router

__all__ = [
    "MinioSettings",
    "get_minio_settings",
    "MinioClient",
    "minio_client",
    "MinioObjectCreate",
    "MinioObjectUpdate",
    "MinioObjectResponse",
    "MinioListResponse",
    "MinioPresignedUrlResponse",
    "MinioCRUD",
    "minio_crud",
    "MinioService",
    "minio_router",
]
