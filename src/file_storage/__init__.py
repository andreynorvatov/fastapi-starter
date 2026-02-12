"""Сервис для работы с локальным файловым хранилищем."""

from .models import File
from .schemas import FileCreate, FileRead, FileUpdate
from .service import FileStorageService, get_file_storage_service

__all__ = [
    "FileStorageService",
    "get_file_storage_service",
    "File",
    "FileCreate",
    "FileUpdate",
    "FileRead",
]
