"""Схемы Pydantic для файлового хранилища."""

import uuid
from datetime import datetime

from pydantic import Field
from sqlmodel import SQLModel

from src.file_storage.models import File


class FileCreate(SQLModel):
    """Схема для создания записи о файле.
    
    Используется при регистрации нового файла в хранилище.
    """
    original_filename: str = Field(max_length=255)
    file_path: str
    file_size: int = Field(ge=0)
    mime_type: str | None = None
    extension: str | None = None


class FileUpdate(SQLModel):
    """Схема для обновления записи о файле.
    
    Все поля опциональны.
    """
    original_filename: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class FileRead(SQLModel):
    """Схема для чтения данных файла из БД.
    
    Возвращается в ответах API.
    """
    id: uuid.UUID
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str | None
    extension: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
