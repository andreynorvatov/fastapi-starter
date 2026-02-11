import uuid
from datetime import datetime

from sqlalchemy import func, text
from sqlmodel import Field


class TimestampMixin:
    """Миксин для добавления полей created_at и updated_at с автоматическими метками времени."""
    
    created_at: datetime = Field(
        default=None, sa_column_kwargs={"server_default": func.now(), "nullable": False}
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now(), "nullable": False},
    )


class UUIDMixin:
    """Миксин для добавления UUID первичного ключа с автоматической генерацией."""
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
