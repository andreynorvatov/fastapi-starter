from datetime import datetime
import uuid
from sqlmodel import Field

class TimestampMixin:
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )


class UUIDMixin:
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={
            "server_default": str(uuid.uuid4())
        }
    )
