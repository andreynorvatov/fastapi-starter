import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field


class TimestampMixin:
    created_at: datetime = Field(
        default=None, sa_column_kwargs={"server_default": func.now(), "nullable": False}
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now(), "nullable": False},
    )


class UUIDMixin:
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": str(uuid.uuid4())},
    )
