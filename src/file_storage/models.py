"""Модели для файлового хранилища."""

import uuid
from datetime import datetime

from sqlalchemy import Text
from sqlmodel import Field, SQLModel

from src.model_mixins import TimestampMixin, UUIDMixin


class File(SQLModel, TimestampMixin, UUIDMixin, table=True):
    """Модель файла в базе данных.
    
    Хранит метаданные о файлах, которые физически расположены в локальном хранилище.
    Файлы на диске именуются по UUID и организованы в структуру:
    {storage_root}/{prefix1}/{prefix2}/{uuid}
    """
    __tablename__ = "files"

    original_filename: str = Field(
        max_length=255,
        description="Оригинальное имя файла при загрузке",
    )
    file_path: str = Field(
        sa_type=Text,
        description="Относительный путь к файлу от корня хранилища (например: 'ab/cd/uuid')",
    )
    file_size: int = Field(
        ge=0,
        description="Размер файла в байтах",
    )
    mime_type: str | None = Field(
        default=None,
        max_length=100,
        description="MIME-тип файла (например: 'image/jpeg')",
    )
    extension: str | None = Field(
        default=None,
        max_length=50,
        description="Расширение файла (например: '.jpg')",
    )
    is_active: bool = Field(
        default=True,
        description="Флаг активного файла (False означает мягкое удаление)",
    )
