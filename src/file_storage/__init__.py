"""Сервис для работы с локальным файловым хранилищем."""

from .models import File
from .schemas import FileCreate, FileRead, FileUpdate
from .service import FileStorageService, get_file_storage_service
from .crud import (
    create_file,
    get_file_by_uuid,
    get_files,
    count_files,
    update_file,
    soft_delete_file,
    hard_delete_file,
)
from .routes import file_storage_router

__all__ = [
    "FileStorageService",
    "get_file_storage_service",
    "File",
    "FileCreate",
    "FileUpdate",
    "FileRead",
    "create_file",
    "get_file_by_uuid",
    "get_files",
    "count_files",
    "update_file",
    "soft_delete_file",
    "hard_delete_file",
    "file_storage_router",
]
